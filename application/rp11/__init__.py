"""RP-11 Route 3 role behaviour: the shared cleanup engine and its evidence formats.

Pure model and orchestration only. Filesystem, process, systemd and Polkit work
is reached through the small protocols in ``ports``; the concrete adapters live
in ``adapters/rp11`` and ``adapters/systemd``. Inactive in production
configuration: only the controlled RP-11 artifact imports it.
"""
