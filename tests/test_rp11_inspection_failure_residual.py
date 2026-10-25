"""Characterization of the transient inspection-failure residual (Route 3 production-readiness input).

Pins what the *current, accepted* cleanup and BS-3 do when the genuine grant is kept because its attribution could not
be established, so Peter's decision rests on executable behavior rather than on a historical description. No rule is
changed here.

* A failed *inspection of the rule* (lookup, ``fstat``, content read, attribute listing) is ``uninspected``: BS-3 never
  disarms the backstop for it whatever Polkit answers, and once the failure clears the next firing's cleanup removes
  the grant.
* A rule that lost *both* identity sources (``grant.id`` and a usable ACT journal) is positively ``foreign`` by the
  accepted rule (no identity makes any present object A0). BS-3 disarms the backstop for it only when Polkit positively
  reports ``not-authorized`` after cleanup; a Polkit series that still finds the rule authorizing is recorded as
  ``unconfirmed`` (reason ``still-authorized``) and keeps the recovery owner. A firing's own cleanup (BS-4) never
  disarms while the rule path exists. The residual is therefore a coincidence of two failures: the identity is lost
  *and* Polkit answers ``not-authorized`` for a rule file that is still present.
* A transient failure of ``grant.id`` alone does not leave the grant live: the journal-based removal removes it; the
  unreadable ``grant.id`` is only a residual that blocks the disarm until a later attempt can clear it.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_rp11_backstop import (  # noqa: E402,F401  (fixtures and helpers shared with the backstop tests)
    ACT_ID,
    Units,
    _umask,
    fire,
    fx,
    layout,
    record_doc,
    stop_post,
)
from test_rp11_cleanup import GRR_FAULTS, InspectionFault, close_fault  # noqa: E402,F401

from application.rp11.backstop import BsTerminal, hard_stop_permits_disarm  # noqa: E402
from application.rp11.cleanup import Terminal  # noqa: E402
from application.rp11.paths import ActivationPaths  # noqa: E402
from application.rp11.pk import PkOutcome  # noqa: E402

pytestmark = pytest.mark.skipif(os.geteuid() == 0, reason="the local tree tests run unprivileged")

PK_RESULTS = [PkOutcome.AUTHORIZED, PkOutcome.UNCONFIRMED, PkOutcome.NOT_AUTHORIZED]


@pytest.mark.parametrize("pk", PK_RESULTS)
@pytest.mark.parametrize("call,_attribution,_grr", GRR_FAULTS)
def test_a_failed_rule_inspection_never_lets_bs3_disarm_and_the_next_firing_removes_the_grant(
    layout, fx, monkeypatch, call, _attribution, _grr, pk
):
    fx.activate()
    rule = ActivationPaths(layout, ACT_ID).rule
    fault = InspectionFault(monkeypatch, rule, call)
    assert stop_post(layout, fx, pk=pk).terminal is Terminal.HARD_STOP
    fault.active = False
    assert fault.hits >= 1 and os.path.exists(rule)  # kept, and still the genuine file
    doc = record_doc(layout, 1)
    assert doc["active_rule"]["class"] == "present-uninspected-unremoved"
    assert hard_stop_permits_disarm(doc) is False  # whatever Polkit said
    units = Units()
    out = fire(layout, fx.a2_sha256, units)  # the failure has cleared: the timer is still the owner and retries
    assert out.terminal is BsTerminal.CLEANUP and "terminal=st1-verified" in out.lines[0]
    assert not os.path.lexists(rule)  # removed by the retry, not merely abandoned


def _lose_identity(layout, fx) -> str:
    """The genuine, intact rule with neither ``grant.id`` nor a usable ACT journal."""
    fx.activate(grant_id=False)
    paths = ActivationPaths(layout, ACT_ID)
    (Path(paths.act_dir) / "journal").unlink()
    return paths.rule


@pytest.mark.parametrize("pk", PK_RESULTS)
def test_a_rule_that_lost_both_identity_sources_is_foreign_and_only_a_positive_not_authorized_disarms(layout, fx, pk):
    rule = _lose_identity(layout, fx)
    before = os.stat(rule)
    assert stop_post(layout, fx, pk=pk).terminal is Terminal.HARD_STOP
    doc = record_doc(layout, 1)
    assert doc["active_rule"]["class"] == "present-foreign-unremoved"
    # A rule that still authorizes is recorded by the series as ``unconfirmed`` (``still-authorized``), never as ``authorized``.
    assert doc["grant_check"]["after_cleanup"] == ("not-authorized" if pk is PkOutcome.NOT_AUTHORIZED else "unconfirmed")
    assert hard_stop_permits_disarm(doc) is (pk is PkOutcome.NOT_AUTHORIZED)
    units = Units()
    out = fire(layout, fx.a2_sha256, units)
    assert os.stat(rule).st_ino == before.st_ino  # never removed without an identity
    if pk is PkOutcome.NOT_AUTHORIZED:
        assert out.terminal is BsTerminal.DISARMED and units.disarms == [ACT_ID]  # the residual: the file stays, the owner goes
    else:
        assert units.disarms == [] and out.terminal is not BsTerminal.DISARMED  # the recovery owner is kept


def test_a_transient_grant_id_failure_alone_still_removes_the_grant_and_blocks_the_disarm_until_cleared(layout, fx):
    fx.activate()
    paths = ActivationPaths(layout, ACT_ID)
    os.chmod(paths.grant_id, 0o000)  # unreadable for this attempt only
    try:
        out = stop_post(layout, fx, pk=PkOutcome.NOT_AUTHORIZED)
    finally:
        os.chmod(paths.grant_id, 0o600)
    assert not os.path.lexists(paths.rule)  # the journal-based removal removed the genuine grant
    assert out.rule_class == "removed-verified" and out.terminal is Terminal.HARD_STOP  # grant.id itself is a residual
    assert hard_stop_permits_disarm(record_doc(layout, 1)) is False  # an A1-intact leftover keeps the recovery owner
    units = Units()
    assert fire(layout, fx.a2_sha256, units).terminal is BsTerminal.CLEANUP  # the next firing clears it
