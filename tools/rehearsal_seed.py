"""Seed the disposable ``oracle-test`` portal with deterministic rehearsal data.

This is deliberately narrower than a general fixture loader.  It will run only
for the staging environment, only against the local ``freedom_staging``
database, and only on the host whose hostname is exactly ``Test``.  It creates
no session, token or usable WebAuthn credential.  Browser access still has to
cross the real emergency-login boundary with a host-issued, single-use grant.

The protected account is created here because a dress rehearsal must be able to
exercise that grant before an operator has completed the physical passkey
ceremony.  Consequently the deployed health response remains degraded until two
real passkeys are enrolled.  That is truthful production behaviour, not a fake
green check.

Run through the staging wrapper, never by hand with copied settings::

    sudo bash infra/staging/portal-run.sh -m tools.rehearsal_seed \
        seed --operator "Peter Duscha"
"""

from __future__ import annotations

import argparse
import hashlib
import os
import socket
from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from adapters.database.tables import (
    audit_events,
    character_access,
    characters,
    discord_guild_memberships,
    discord_users,
    external_identities,
    foundry_snapshots,
    platform_accounts,
)
from tools.web_operator import (
    EXIT_CANNOT_CONNECT,
    EXIT_OK,
    EXIT_UNSAFE_TARGET,
    TargetRefused,
    require_operator,
    resolve_engine,
)

HOSTNAME = "Test"
DATABASE = "freedom_staging"
ENVIRONMENT = "staging"
DEMO_DISCORD_ID = 9_000_000_000_000_000_101

PROTECTED_ACCOUNT = UUID("10000000-0000-4000-8000-000000000001")
DEMO_ACCOUNT = UUID("10000000-0000-4000-8000-000000000002")
DEMO_IDENTITY = UUID("10000000-0000-4000-8000-000000000003")
CHARACTERS = (
    (UUID("20000000-0000-4000-8000-000000000001"), "Aster Vale", "Aster Vale, Lantern of the March", 8),
    (UUID("20000000-0000-4000-8000-000000000002"), "Brindle Quick", "Brindle Quick of Copper Row", 6),
    (UUID("20000000-0000-4000-8000-000000000003"), "Mara Voss", "Mara Voss, Keeper of Ash", 11),
)
SNAPSHOT = UUID("30000000-0000-4000-8000-000000000001")


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    subcommands = parser.add_subparsers(dest="command", required=True)
    seed = subcommands.add_parser("seed")
    seed.add_argument("--operator", required=True)
    subcommands.add_parser("status")
    return parser.parse_args(argv)


def _refuse_host_environment() -> None:
    if socket.gethostname() != HOSTNAME:
        raise TargetRefused(f"hostname must be exactly {HOSTNAME!r}.")
    if os.environ.get("WEB_ENVIRONMENT") != ENVIRONMENT:
        raise TargetRefused(f"WEB_ENVIRONMENT must be exactly {ENVIRONMENT!r}.")


def _refuse_unless_disposable(connection) -> None:
    _refuse_host_environment()
    database = connection.execute(select(func.current_database())).scalar_one()
    if database != DATABASE:
        raise TargetRefused(f"database must be exactly {DATABASE!r}.")


def _put(connection, table, values: dict, *conflict_columns: str) -> bool:
    statement = pg_insert(table).values(**values).on_conflict_do_nothing(
        index_elements=[table.c[column] for column in conflict_columns]
    )
    return connection.execute(statement).rowcount == 1


def _audit_id(index: int) -> UUID:
    return UUID(f"40000000-0000-4000-8000-{index:012d}")


def seed(connection, *, operator: str) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    guild_id = int(os.environ["WEB_DISCORD_GUILD_ID"])
    counts = {"accounts": 0, "identities": 0, "characters": 0, "snapshots": 0, "audit": 0}

    counts["accounts"] += _put(
        connection,
        platform_accounts,
        {
            "id": PROTECTED_ACCOUNT,
            "status": "active",
            "is_protected_admin": True,
            "display_label": f"Rehearsal Administrator (prepared by {operator})"[:80],
        },
        "id",
    )
    counts["accounts"] += _put(
        connection,
        platform_accounts,
        {
            "id": DEMO_ACCOUNT,
            "status": "active",
            "display_label": "Synthetic Guild Member",
        },
        "id",
    )
    _put(
        connection,
        discord_users,
        {
            "id": DEMO_DISCORD_ID,
            "username": "rehearsal.member",
            "global_name": "Synthetic Guild Member",
        },
        "id",
    )
    _put(
        connection,
        discord_guild_memberships,
        {
            "discord_user_id": DEMO_DISCORD_ID,
            "guild_id": guild_id,
            "active": True,
            "observed_at": now,
        },
        "discord_user_id",
        "guild_id",
    )
    counts["identities"] += _put(
        connection,
        external_identities,
        {
            "id": DEMO_IDENTITY,
            "platform_account_id": DEMO_ACCOUNT,
            "provider_key": "discord",
            "subject": str(DEMO_DISCORD_ID),
            "state": "active",
            "audit_correlation_id": _audit_id(1),
        },
        "provider_key",
        "subject",
    )

    for index, (character_id, display_name, long_name, level) in enumerate(CHARACTERS, 1):
        counts["characters"] += _put(
            connection,
            characters,
            {
                "id": character_id,
                "display_name": display_name,
                "long_name": long_name,
                "level": level,
                "active": True,
            },
            "id",
        )
        _put(
            connection,
            character_access,
            {
                "id": UUID(f"21000000-0000-4000-8000-{index:012d}"),
                "character_id": character_id,
                "discord_user_id": DEMO_DISCORD_ID,
                "platform_account_id": DEMO_ACCOUNT,
                "access_kind": "owner",
                "active": True,
                "default_character": index == 1,
                "granted_by_discord_user_id": DEMO_DISCORD_ID,
                "granted_by_account_id": DEMO_ACCOUNT,
                "reason": "Deterministic disposable-host dress rehearsal",
                "audit_correlation_id": _audit_id(10 + index),
            },
            "id",
        )

    counts["snapshots"] += _put(
        connection,
        foundry_snapshots,
        {
            "id": SNAPSHOT,
            "checksum": hashlib.sha256(b"freedom-blades-oracle-test-rehearsal-v1").hexdigest(),
            "size_bytes": 4096,
            "schema_version": 1,
            "exporter_id": "freedom-blades-rehearsal",
            "exporter_version": "1.0.0",
            "exported_at": now,
            "world_id": "rehearsal-world",
            "world_title": "Freedom Blades Dress Rehearsal",
            "core_version": "14.367",
            "system_id": "dnd5e",
            "system_version": "5.3.3",
            "actor_count": len(CHARACTERS),
            "selected_folder_ids": ["RehearsalHeroes"],
            "artifact_location": None,
            "received_by_account_id": PROTECTED_ACCOUNT,
            "received_via": "operator",
            "submitted_by_principal": None,
            "correlation_id": _audit_id(20),
        },
        "id",
    )

    events = (
        (21, "rehearsal.environment.prepared", "environment", "oracle-test", "system"),
        (22, "rehearsal.identity.seeded", "platform_account", str(DEMO_ACCOUNT), "system"),
        (23, "rehearsal.characters.seeded", "character_set", "oracle-test-v1", "import"),
        (24, "foundry.snapshot.received", "foundry_snapshot", str(SNAPSHOT), "foundry"),
    )
    for number, action, entity_type, entity_id, source in events:
        counts["audit"] += _put(
            connection,
            audit_events,
            {
                "id": _audit_id(number),
                "occurred_at": now,
                "actor_platform_account_id": PROTECTED_ACCOUNT,
                "actor_capability": "platform_administrator",
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "source": source,
                "correlation_id": _audit_id(number),
                "payload": {"dataset": "oracle-test-rehearsal-v1", "synthetic": True},
            },
            "id",
        )
    return counts


def status(connection) -> dict[str, int]:
    return {
        "accounts": connection.execute(select(func.count()).select_from(platform_accounts)).scalar_one(),
        "characters": connection.execute(select(func.count()).select_from(characters)).scalar_one(),
        "snapshots": connection.execute(select(func.count()).select_from(foundry_snapshots)).scalar_one(),
        "audit": connection.execute(select(func.count()).select_from(audit_events)).scalar_one(),
    }


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parse_arguments(argv)
    try:
        operator = require_operator(arguments.operator) if arguments.command == "seed" else None
        _refuse_host_environment()
        engine = resolve_engine()
        with engine.begin() as connection:
            _refuse_unless_disposable(connection)
            result = seed(connection, operator=operator) if arguments.command == "seed" else status(connection)
    except TargetRefused as refusal:
        print(f"Refused: {refusal}")
        return EXIT_UNSAFE_TARGET
    except Exception as error:  # noqa: BLE001 - operator command has a classified exit
        print(f"Rehearsal database operation failed: {type(error).__name__}")
        return EXIT_CANNOT_CONNECT

    prefix = "inserted" if arguments.command == "seed" else "present"
    for name, count in result.items():
        print(f"{prefix:8} {name:12} {count}")
    if arguments.command == "seed":
        print("No session, token or usable passkey was created.")
        print("Issue a one-use recovery grant host-locally when the browser rehearsal begins.")
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover - operator entry point
    raise SystemExit(main())

