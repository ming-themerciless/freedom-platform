from __future__ import annotations

import pytest

from tools import rehearsal_seed
from tools.web_operator import TargetRefused


def test_rehearsal_seed_refuses_every_other_host(monkeypatch):
    monkeypatch.setenv("WEB_ENVIRONMENT", "staging")
    monkeypatch.setattr(rehearsal_seed.socket, "gethostname", lambda: "production")

    with pytest.raises(TargetRefused, match="hostname must be exactly"):
        rehearsal_seed._refuse_host_environment()


def test_rehearsal_seed_refuses_every_other_environment(monkeypatch):
    monkeypatch.setenv("WEB_ENVIRONMENT", "production")
    monkeypatch.setattr(rehearsal_seed.socket, "gethostname", lambda: "Test")

    with pytest.raises(TargetRefused, match="WEB_ENVIRONMENT must be exactly"):
        rehearsal_seed._refuse_host_environment()


def test_rehearsal_seed_accepts_only_the_named_disposable_pair(monkeypatch):
    monkeypatch.setenv("WEB_ENVIRONMENT", "staging")
    monkeypatch.setattr(rehearsal_seed.socket, "gethostname", lambda: "Test")

    rehearsal_seed._refuse_host_environment()


def test_dataset_identifiers_are_deterministic_and_non_overlapping():
    ids = {
        rehearsal_seed.PROTECTED_ACCOUNT,
        rehearsal_seed.DEMO_ACCOUNT,
        rehearsal_seed.DEMO_IDENTITY,
        rehearsal_seed.SNAPSHOT,
        *(character[0] for character in rehearsal_seed.CHARACTERS),
    }

    assert len(ids) == 7
    assert rehearsal_seed.DEMO_DISCORD_ID == 9_000_000_000_000_000_101

