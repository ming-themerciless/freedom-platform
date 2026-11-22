"""G11 start-time binding: service ``INVOCATION_ID`` against the consume ``run-start``.

Synthetic, pure unit tests. Journals are built with the production serializer
(``serialize_line``) so the grammar under test is the real one. Nothing touches a
filesystem, process, network, host or systemd.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest

from application.rp11.journal import (
    GENESIS,
    JournalKind,
    consume_run,
    serialize_line,
)
from tools.phase_5_0_evidence.execution import start_binding
from tools.phase_5_0_evidence.execution.start_binding import (
    MAX_JOURNAL_BYTES,
    REFUSAL_REASONS,
    StartBindingRefused,
    require_start_binding,
)

ACT = "rp11-act-20261018T120000Z-0123abcd"
OTHER_ACT = "rp11-act-20261018T120000Z-fedcba98"
INV = "0123456789abcdef0123456789abcdef"
OTHER_INV = "fedcba9876543210fedcba9876543210"
BOOT = "01234567-89ab-cdef-0123-456789abcdef"
SOURCE = Path(start_binding.__file__)

START = {
    "invocation_id": INV,
    "boot_id": BOOT,
    "claim": {"dev": 1, "ino": 2},
    "act_journal": {"sha256": "a" * 64, "length": 10},
    "lock": {"object": {"path": "/run/k", "dev": 1, "ino": 3}, "mode": "held", "wait_ms": 0},
    "helper": {"role": "consume", "tool_sha256": "absent"},
}


def journal(*lines, run=None, kind=JournalKind.CONSUME) -> bytes:
    """A chained journal of ``(op, fields)`` lines, built by the production serializer."""
    out, prev = b"", GENESIS
    for seq, (op, fields) in enumerate(lines, start=1):
        raw = serialize_line(
            kind, seq=seq, prev=prev, run=run or consume_run(ACT), op=op, fields=fields
        )
        out += raw
        prev = hashlib.sha256(raw).hexdigest()
    return out


def good(**start) -> bytes:
    return journal(
        ("run-start", {**START, **start}),
        ("consumed", {"pk_status": "not-authorized", "inactive_enter_us": 400}),
        ("run-end", {"outcome": "consumed"}),
    )


_UNSET = object()


def refusal(activation_id=ACT, invocation_id=INV, data=_UNSET) -> str:
    with pytest.raises(StartBindingRefused) as caught:
        require_start_binding(activation_id, invocation_id, good() if data is _UNSET else data)
    return caught.value.reason


# --- valid pairing -----------------------------------------------------------


def test_a_matching_complete_journal_is_accepted():
    assert require_start_binding(ACT, INV, good()) is None


def test_a_start_only_journal_is_accepted_because_lifecycle_completion_is_not_checked():
    # Contract: only the run-start pairing and record validity are checked; lifecycle
    # completion is the caller's, via successful consume ExecStartPre sequencing.
    assert require_start_binding(ACT, INV, journal(("run-start", START))) is None


def test_an_in_flight_journal_without_run_end_is_accepted_because_lifecycle_is_not_checked():
    # Same contract: no terminal run-end is required by this check.
    data = journal(("run-start", START), ("consumed", {"pk_status": "x", "inactive_enter_us": 1}))
    assert require_start_binding(ACT, INV, data) is None


# --- mismatch and wrong run --------------------------------------------------


def test_a_different_invocation_id_is_refused():
    assert refusal(invocation_id=OTHER_INV) == "invocation-mismatch"


def test_a_journal_recording_another_invocation_id_is_refused():
    assert refusal(data=good(invocation_id=OTHER_INV)) == "invocation-mismatch"


def test_a_journal_of_another_activation_is_refused():
    assert refusal(activation_id=OTHER_ACT) == "journal-invalid"


def test_a_journal_written_for_another_run_name_is_refused():
    other = journal(("run-start", START), run=f"{ACT}-deact-1")
    assert refusal(data=other) == "journal-invalid"


def test_a_journal_under_the_bare_activation_run_name_is_refused():
    # the bare activation id names the ACT run, not the consume run
    assert refusal(data=journal(("run-start", START), run=ACT)) == "journal-invalid"


# --- malformed or missing run-start -----------------------------------------


def test_an_absent_journaled_invocation_id_is_refused_even_against_a_valid_one():
    assert refusal(data=good(invocation_id="absent")) == "run-start-malformed"


def test_a_journal_without_a_run_start_is_refused():
    data = journal(("consumed", {"pk_status": "x", "inactive_enter_us": 1}))
    assert refusal(data=data) == "journal-invalid"


def test_a_run_start_that_is_not_the_first_line_is_refused():
    data = journal(
        ("consumed", {"pk_status": "x", "inactive_enter_us": 1}), ("run-start", START)
    )
    assert refusal(data=data) == "journal-invalid"


def test_a_second_run_start_is_refused():
    assert refusal(data=journal(("run-start", START), ("run-start", START))) == "journal-invalid"


@pytest.mark.parametrize(
    "bad",
    [
        {"invocation_id": "A" * 32},  # uppercase
        {"invocation_id": INV[:-1]},  # short
        {"invocation_id": INV + "0"},  # long
        {"invocation_id": 7},
        {"boot_id": "x"},
        {"helper": {"role": "hold", "tool_sha256": "absent"}},
    ],
)
def test_a_run_start_outside_the_consume_grammar_cannot_be_built(bad):
    # serialize_line applies the same closed schema parse_journal does.
    from application.rp11.journal import JournalSchemaError

    with pytest.raises(JournalSchemaError):
        journal(("run-start", {**START, **bad}))


def test_hand_edited_run_start_bytes_are_refused_by_the_shared_parser():
    data = good().replace(INV.encode(), b"A" * 32, 1)
    assert refusal(data=data) == "journal-invalid"


def test_a_missing_run_start_field_is_refused():
    data = good()
    # strip the claim object from the canonical bytes (compact, sorted keys)
    mangled = data.replace(b'"claim":{"dev":1,"ino":2},', b"", 1)
    assert mangled != data
    assert refusal(data=mangled) == "journal-invalid"


# --- invalid journal, torn tail, bad input -----------------------------------


def test_a_torn_tail_is_refused():
    assert refusal(data=good() + b'{"seq":4,"op":"run-e') == "journal-torn-tail"


def test_a_torn_tail_after_only_the_run_start_is_refused():
    assert refusal(data=journal(("run-start", START)) + b"{") == "journal-torn-tail"


def test_a_journal_that_is_only_a_torn_line_is_refused():
    assert refusal(data=journal(("run-start", START)).rstrip(b"\n")) == "journal-invalid"


@pytest.mark.parametrize("data", [b"", b"\n", b"not json\n", b"{}\n", b"[]\n", b"\x00\xff\n"])
def test_garbage_and_empty_journals_are_refused(data):
    assert refusal(data=data) == "journal-invalid"


def test_a_broken_hash_chain_is_refused():
    lines = good().splitlines(keepends=True)
    assert refusal(data=lines[0] + lines[2]) == "journal-invalid"


def test_a_tampered_later_line_is_refused():
    data = good().replace(b"not-authorized", b"authorized-xx", 1)
    assert refusal(data=data) == "journal-invalid"


@pytest.mark.parametrize("data", [bytearray(good()), memoryview(good()), good().decode(), None, 5])
def test_only_exact_bytes_are_accepted_as_a_journal(data):
    assert refusal(data=data) == "invalid-journal-input"


def test_the_size_cap_matches_the_authority_journal_cap():
    assert MAX_JOURNAL_BYTES == 4_194_304  # application.rp11.consume.ACT_FIRST_READ_BYTES


def test_a_journal_of_exactly_the_cap_is_not_refused_as_too_large():
    # Junk bytes: the size gate passes and the parser (not the size gate) refuses.
    assert refusal(data=b"x" * MAX_JOURNAL_BYTES) != "journal-too-large"


def test_an_oversized_journal_is_refused_before_parsing():
    assert refusal(data=b"x" * (MAX_JOURNAL_BYTES + 1)) == "journal-too-large"


# --- invalid IDs --------------------------------------------------------------


@pytest.mark.parametrize(
    "activation_id",
    [
        "",
        "rp11-act-20261018T120000Z-0123ABCD",
        "rp11-act-20261018T120000Z-0123abcd\n",
        " rp11-act-20261018T120000Z-0123abcd",
        "rp11-act-20261018T120000Z-0123abc",
        f"{ACT}-consume",
        "../" + ACT,
        None,
        7,
        b"rp11-act-20261018T120000Z-0123abcd",
    ],
)
def test_an_invalid_activation_id_is_refused(activation_id):
    assert refusal(activation_id=activation_id) == "invalid-activation-id"


@pytest.mark.parametrize(
    "invocation_id",
    [
        "",
        "absent",
        INV.upper(),
        INV + "\n",
        INV[:-1],
        INV + "0",
        f"{INV[:8]}-{INV[8:12]}-{INV[12:16]}-{INV[16:20]}-{INV[20:]}",
        " " + INV,
        None,
        7,
        INV.encode(),
    ],
)
def test_an_invalid_invocation_id_is_refused(invocation_id):
    assert refusal(invocation_id=invocation_id) == "invalid-invocation-id"


def test_ids_are_validated_before_the_journal_is_looked_at():
    assert refusal(activation_id="bad") == "invalid-activation-id"
    assert refusal(invocation_id="bad", data=b"garbage") == "invalid-invocation-id"
    assert refusal(activation_id="bad", invocation_id="bad", data=b"x") == "invalid-activation-id"


# --- the refusal is bounded and non-sensitive ---------------------------------


def test_a_refusal_carries_only_a_fixed_reason_code():
    cases = [
        dict(invocation_id=OTHER_INV),
        dict(activation_id=OTHER_ACT),
        dict(data=good(invocation_id=OTHER_INV)),
        dict(data=good() + b"{"),
        dict(data=b"secret-looking-bytes-0123456789abcdef0123456789abcdef"),
        dict(data=good(invocation_id="absent")),
    ]
    for case in cases:
        with pytest.raises(StartBindingRefused) as caught:
            require_start_binding(
                case.get("activation_id", ACT),
                case.get("invocation_id", INV),
                case.get("data", good()),
            )
        error = caught.value
        assert error.reason in REFUSAL_REASONS
        assert str(error) == error.reason and error.args == (error.reason,)
        assert error.__cause__ is None
        for secret in (ACT, OTHER_ACT, INV, OTHER_INV, BOOT, "secret-looking"):
            assert secret not in str(error) and secret not in repr(error)


def test_an_unknown_reason_cannot_be_raised():
    with pytest.raises(ValueError):
        StartBindingRefused("because " + INV)


def test_the_refusal_is_a_harness_error():
    from tools.phase_5_0_evidence.errors import HarnessError

    assert issubclass(StartBindingRefused, HarnessError)


# --- reuse and purity (by AST) ------------------------------------------------


def test_the_journal_grammar_is_reused_not_duplicated():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "application.rp11.journal"
        for alias in node.names
    }
    assert imported == {"JournalKind", "consume_run", "parse_journal"}
    assert start_binding.parse_journal.__module__ == "application.rp11.journal"
    assert start_binding.consume_run is consume_run
    # no regular expression, JSON or hashing of its own: see the import allow-list below


def test_the_module_is_pure_and_read_only():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imports = {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and not node.level
    } | {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert imports <= {"__future__", "application"}
    names = {
        getattr(node, "id", None) or getattr(node, "attr", None)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Name, ast.Attribute))
    }
    assert not names & {
        "open", "os", "subprocess", "socket", "sys", "environ", "getenv", "Path",
        "create_capture_session", "StreamCaptureLauncher", "ActRequest", "launch",
    }


def test_the_inert_entry_does_not_import_or_call_the_binding():
    entry = Path(__file__).resolve().parent.parent / "infra/rp11-h1/rp11_entry.py"
    text = entry.read_text(encoding="utf-8")
    assert "start_binding" not in text and "require_start_binding" not in text
