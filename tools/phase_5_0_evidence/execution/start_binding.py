"""RP-11 G11 start-time binding: service ``INVOCATION_ID`` against the consume ``run-start``.

The consume role (``ExecStartPre=+``) journals ``run-start.invocation_id``, the
systemd InvocationID it ran under. systemd uses one InvocationID for every command
of one start, so the capture entry (``ExecStart=``) must see the same value in its
own ``INVOCATION_ID``. This module is the pairing check, and nothing else:

* **Pure.** It receives the validated activation id, the launcher's InvocationID and
  the consume journal *bytes*. It reads no file, environment, process or network,
  starts no capture session and runs no command.
* **No second grammar.** The journal is parsed by ``application.rp11.journal``
  (``parse_journal`` with ``JournalKind.CONSUME`` and ``consume_run``); the
  activation id by ``application.unit_control.validate_activation_id`` (the one
  consume applies); the InvocationID by ``capture_contract.require_invocation_id``.
* **Fail closed.** Any invalid, torn, foreign or mismatching input raises
  ``StartBindingRefused`` with a fixed reason code. The refusal carries neither
  identifier, nor journal bytes, nor a parser message, so it is safe to log.

It is **not wired**: ``rp11_entry.main`` does not import or call it (the entry stays
inert). It is in ``ENTRY_SOURCES`` so it is in the fixed ``lib/`` closure the
eventual entry will load it from.
"""

from __future__ import annotations

from application.rp11.journal import JournalKind, consume_run, parse_journal
from application.unit_control import ControlSpecError, validate_activation_id

from ..capture_contract import CaptureContractRefused, require_invocation_id
from ..errors import HarnessError

#: Defensive cap on the journal handed in; it keeps the parse bounded. It is 4 MiB
#: (4_194_304) to match the repository's established maximum authority-journal cap,
#: ``application.rp11.consume.ACT_FIRST_READ_BYTES``, so this check never refuses a
#: journal the authority side would read. A real consume journal is far smaller.
MAX_JOURNAL_BYTES = 4_194_304

#: The only reason codes a refusal can carry.
REFUSAL_REASONS = frozenset(
    {
        "invalid-activation-id",
        "invalid-invocation-id",
        "invalid-journal-input",
        "journal-too-large",
        "journal-invalid",
        "journal-torn-tail",
        "run-start-missing",
        "run-start-malformed",
        "invocation-mismatch",
    }
)


class StartBindingRefused(HarnessError):
    """The service InvocationID is not proved equal to the consume ``run-start``'s.

    ``reason`` is one of ``REFUSAL_REASONS``; the message is that code alone."""

    def __init__(self, reason: str) -> None:
        if reason not in REFUSAL_REASONS:
            raise ValueError("unknown start-binding refusal")
        self.reason = reason
        super().__init__(reason)


def require_start_binding(activation_id: str, invocation_id: str, consume_journal: bytes) -> None:
    """Return only if ``consume_journal``'s ``run-start.invocation_id`` equals ``invocation_id``.

    Raises ``StartBindingRefused`` otherwise.

    What is validated: every complete canonical record supplied (chain and schema,
    via the shared parser) belongs to *this* activation (``run`` is
    ``consume_run(activation_id)``); the first record is the single ``run-start``,
    schema- and pairing-checked; and there is no torn tail.

    What is deliberately NOT established: lifecycle completion. A start-only or
    in-flight journal (no ``consumed`` / terminal ``run-end``) is accepted. The
    caller must rely on the successful ``consume`` ``ExecStartPre`` sequencing
    (systemd starts ``ExecStart=`` only after it succeeded) for that."""
    try:
        validate_activation_id(activation_id)
    except ControlSpecError:
        raise StartBindingRefused("invalid-activation-id") from None
    try:
        require_invocation_id(invocation_id)
    except CaptureContractRefused:
        raise StartBindingRefused("invalid-invocation-id") from None
    if type(consume_journal) is not bytes:
        raise StartBindingRefused("invalid-journal-input")
    if len(consume_journal) > MAX_JOURNAL_BYTES:
        raise StartBindingRefused("journal-too-large")
    parsed = parse_journal(
        consume_journal, kind=JournalKind.CONSUME, run=consume_run(activation_id)
    )
    if not parsed.valid:
        raise StartBindingRefused("journal-invalid")
    if parsed.torn_tail:
        raise StartBindingRefused("journal-torn-tail")
    starts = parsed.ops("run-start")
    if len(starts) != 1 or parsed.lines[0].op != "run-start":
        raise StartBindingRefused("run-start-missing")
    journaled = starts[0].fields.get("invocation_id")
    if type(journaled) is not str:
        raise StartBindingRefused("run-start-malformed")
    try:
        require_invocation_id(journaled)
    except CaptureContractRefused:
        # e.g. the journal's ``"absent"``: the consume role had no InvocationID.
        raise StartBindingRefused("run-start-malformed") from None
    if journaled != invocation_id:
        raise StartBindingRefused("invocation-mismatch")
