# Claude prompt — Route 3 release record preparation through step 4

Peter authorizes this bounded assignment on 2026-11-03. Complete release-
preparation steps 1 through 4 from the active handover: verify the published
accepted revision, produce all off-production identities, run the single
authorized read-only production S0.0 observation, populate the release record,
and return it for independent review.

This is release preparation, not provisioning. The plan remains **NO-GO**
throughout this assignment. Do not execute S0.2, S1, S2, S3, S4, any rollback
block, migration/cutover, or RB-1. Do not create or install production
artifacts, packages, accounts, paths, units, sudoers or Polkit policy. Do not
restart a service or reboot. S1, S3 and S4 remain separate later decisions.

## Governing context

Before acting, read completely:

1. `.agents/AGENTS.md`;
2. the reading map and §§0, 16 and 20 of `docs/implementation-plan.md`, plus
   §§13, 14 and 17 because this assignment concerns evidence, operations and a
   release gate;
3. `docs/review/Handover information`;
4. `docs/operations/disposable-test-server.md`;
5. runbook part P, especially P.3, block D, block F, S0.0/S0.1/S0.2 and S3.2
   in `docs/operations/executor-supervisor-provisioning-runbook.md`; and
6. the cumulative evidence in
   `docs/review/route-3-production-readiness-handback.md`.

Apply the Claude guards and relevant procedural skills, but treat the governing
documents above as authority. Never read, print, copy or modify `.env`, secret
files, credentials, tokens, process environments, process argument lists or
player data.

## Exact release boundary

The expected accepted and published candidate is:

```text
dc1167aac1c132c6f9e855717c0947a0c1ceb606
```

It is expected at `docs/platform-plan` and `origin/docs/platform-plan`, with
subject `feat: add route 3 production provisioning plan and associated test
suite`. First verify the full 40-hex object, branch/upstream equality, clean
worktree apart from this newly supplied prompt, and that the commit contains
the accepted R6/R7 state. If any fact differs, or any unknown/unrelated change
is present, stop and report the discrepancy. Do not guess a replacement
revision, amend, rebase, reset, force-push or rewrite history.

When those checks pass, set:

```text
ROUTE3_RELEASE_REV=dc1167aac1c132c6f9e855717c0947a0c1ceb606
```

That value is immutable for this assignment. A later release-record commit is
not a new deployable revision. Prove before handback that the later commit does
not change any path in this archive pathspec:

```text
adapters application tools infra/executor infra/tmpfiles.d infra/rp11-h1
```

## 1. Produce the controlled artifacts and identities off production

Do all downloads, archive creation, extraction and reference builds on the
disposable non-production host `oracle-test` (`138.2.182.39`), never on the
current production host. Work from a fresh checkout or detached worktree at
the exact release revision. Do not substitute the mutable working tree.

Create a private evidence directory on `oracle-test` for this revision and
retain the resulting `code.tar`, `MANIFEST.sha256`, pinned Jeepney wheel and a
plain-text, secret-free command/result record until independent review. Do not
commit generated binaries.

Build `code.tar` with the exact P.3 command and pathspec:

```bash
git archive --format=tar --output=code.tar dc1167aac1c132c6f9e855717c0947a0c1ceb606 -- adapters application tools infra/executor infra/tmpfiles.d infra/rp11-h1
```

Extract it into a new empty directory. From the extraction root produce the
manifest exactly as P.3 specifies:

```bash
find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sed 's#  ./#  #' > MANIFEST.sha256
```

Record `sha256sum code.tar MANIFEST.sha256` as
`ROUTE3_ARCHIVE_SHA256` and `ROUTE3_MANIFEST_SHA256` **provisionally**. Neither
digest may be accepted, recorded in block F or reported as a release value until
the following mandatory validation of the **actual retained artifact pair**
passes.

Run the accepted `ROUTE3_STAGE_ENTRY` `archive` command, as defined in runbook
block D from the exact accepted release revision (not reimplemented or
paraphrased), against the exact retained `code.tar` and `MANIFEST.sha256` whose
SHA-256 values will populate block F. Do this on `oracle-test`, using the
documented isolated Python invocation of `route3_stage`:

```bash
/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3.14 -I -S -B -c "$ROUTE3_STAGE_ENTRY" archive <retained>/code.tar <retained>/MANIFEST.sha256
```

Capture `ROUTE3_STAGE_ENTRY` from block D at the release revision (for example
from `git show` of that revision), pass it only as the `-c` argument and do not
source the Markdown file. Record the retained artifact paths, the exact
invocation, the return status and the printed result. The validator must return
**status 0** and print its success result `archive: ok` before either digest may
be accepted. A non-zero, missing or ambiguous result, or an inability to invoke
the block-D validator against the retained pair exactly as above, is a
**NO-GO**: leave block F unchanged, make no release-record commit and return the
conflict. Do not substitute another check.

That validation proves the archive contains exactly the manifest's regular-file
set and digests, with no links, special files, duplicate or prohibited members,
or other contract violation enforced by the accepted staging entry. Recompute
the two digests after validation and require them to equal the values recorded
before it, so the validated pair is the pair that is digested. The provisioning-
plan focused tests are additional regression evidence only and never a
substitute for validating the retained files.

Obtain the fixed wheel off production using P.3 and
`infra/rp11-h1/requirements.lock`. Verify its filename is
`jeepney-0.9.0-py3-none-any.whl` and its digest is exactly
`97e5714520c16fc0a45695e5365a2e11b81ea79bba796e26f9f1d178cb182683`.

Do not yet derive the interpreter digest: its exact package version must come
from the authorized production S0.0 observation below.

## 2. Authorized read-only production observation: S0.0 only

Peter's delivery of this prompt is explicit written authority for **only the
literal S0.0 read-only production observation** in the accepted runbook. It
authorizes the unprivileged reads and `apt-get --simulate`/`apt-cache` queries
in block D plus S0.0 against the production host's existing, already-downloaded
package lists. It authorizes no other production inspection or action.

Confirm that you are on the already-established production host without
probing secrets. Execute block D and the literal S0.0 block from the accepted
release revision in memory; do not source the Markdown file and do not create a
temporary script. Do not use `sudo`, root, `apt-get update`, download, install,
remove, upgrade, downgrade, hold/unhold, list refresh, artifact write or any
other production write. Do not run S0.1 or S0.2 on production.

Capture only the non-sensitive S0.0 command output and status. Require
`[S0.0 rc=0]`. If the solver reports any upgrade, downgrade, removal, other
non-`new` operation, failure, ambiguity, missing top-level package or source
outside the configured Ubuntu archive, stop. Do not repair or broaden the
observation.

From a clean successful result, review every proposed package. The proposed
`new` set must itself contain exact `name=version` tokens for all three
top-level packages: `python3.14`, `python3.14-minimal` and `python3.14-venv`.
Literal S0.0 does not report the version of an already-installed top-level
package, and this assignment authorizes no supplementary production query from
which to infer it. Therefore, if any of those three tokens is absent from the
S0.0 `new` set, stop, leave block F unchanged and return the omission as a
NO-GO blocker requiring a separately reviewed procedure and authority. Never
fill the gap from an earlier observation or an `oracle-test` value.

When all three top-level tokens are present, construct `ROUTE3_APT_PACKAGES` as
the complete, duplicate-free, deterministically sorted set of every exact
`name=version` member in S0.0's `new` result. Construct `ROUTE3_APT_ORIGIN` from
every accepted `<url> <suite>/<component>` origin that offers those exact
versions, in deterministic order. Do not promote the prior `oracle-test`
observation as a production value.

## 3. Finish the two reference identities on `oracle-test`

Using the exact `python3.14-minimal` version obtained from production S0.0,
follow P.3's reference-identity procedure on `oracle-test`, as an unprivileged
user and in an empty directory:

1. download `python3.14-minimal=<exact version>`;
2. prove the downloaded `.deb` SHA-256 equals the `SHA256:` value from
   `apt-cache show` for that exact version in the archive's signed index; and
3. extract `/usr/bin/python3.14` through `dpkg-deb --fsys-tarfile ... | tar
   -xO ./usr/bin/python3.14 | sha256sum`.

The resulting file digest is `ROUTE3_PY_SHA256`. Stop if the exact production
version or matching signed-index identity is unavailable off production.

Build the SA-2 reference tree on `oracle-test` from the extracted and verified
release archive and the verified pinned wheel, following the same build inputs,
isolated interpreter behavior, ownership-neutral file content and destination
layout as S3.2. Use a fresh destination; do not run the production S3 block.
Validate that the tree contains no links, group/other-writable files or
unexpected files. Compute its identity exactly as S3.2 does:

```bash
cd <fresh-SA2-destination>
find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1
```

Record this as `ROUTE3_SA2_TREE_SHA256`. Rebuild once in a second fresh
destination and require the same digest before accepting it.

## 4. Populate and validate the release record

Edit block F in
`docs/operations/executor-supervisor-provisioning-runbook.md` with the seven
evidence-backed values. Preserve the fixed wheel name and digest. Never paste
values ad hoc into an operator shell; block F in the reviewed repository is the
release record.

Reconcile all current documentation that still says the candidate is
uncommitted or every field is `UNSET`: at minimum the active handover, current
status, active delivery plan, implementation-plan current pointer, cumulative
handback, and any current RAID/decision/change-log entries whose live state is
affected. Keep the result concise and factual. Preserve the conclusion that
the release record is returned for independent review and the plan remains
NO-GO; this assignment does not accept the record or authorize S0.2/S1.

Do not rewrite historical evidence under `docs/review/archive/` or status
archives. Do not create a new remediation chain. Update tests that intentionally
asserted all fields were `UNSET` so they instead prove the supplied record is
complete, well formed and accepted by S0.1, while retaining malformed-field
and fail-closed coverage. Do not weaken any security or artifact check.

Validate on the exact final tree:

- shell syntax for every affected extracted block;
- the provisioning-plan focused suite, release-field tests and guard suite;
- `git diff --check`;
- S0.1 in a non-production shell, requiring `rc=0`;
- recomputation of every archive, manifest, wheel, interpreter and SA-2 digest
  from the retained non-production evidence;
- the block-D `ROUTE3_STAGE_ENTRY` `archive` validator, re-run on `oracle-test`
  against the same retained `code.tar` and `MANIFEST.sha256` whose digests are in
  the final block F, returns status 0 with `archive: ok`;
- no `UNSET` remains in live block F;
- the diff from `ROUTE3_RELEASE_REV` to the release-record result contains no
  change in the archive pathspec; and
- repository-wide current-state searches show no stale live claim that the
  candidate is uncommitted or all release fields are unset. Historical text
  may retain those facts.

Run relevant tests on `oracle-test` under the documented environment. When
synchronizing the final uncommitted release-record tree for testing, use the
documented secret-excluding rsync procedure with these additional exclusions:

```text
--exclude='.git/'
--exclude='.aws/'
--exclude='.codex/'
```

The exclusions are mandatory because those repository-local paths are not
release inputs and can contain local repository, cloud or agent state. Do not
inspect their contents. A secrets-guard refusal is a stop condition; do not
weaken or work around the guard. After synchronization, verify the remote files
under review match the local final tree by a secret-safe path inventory and
digests of the files changed by this assignment, rather than by relying on the
remote Git metadata.

Full bot, web and Foundry suites are not required for a release-record-only
change unless you change executable behavior or focused evidence exposes a
wider regression. Report exact commands, counts, skips and return statuses; do
not reuse an older tree's figures.

## Commit, publication and return

After all checks pass, make one normal commit on the non-default
`docs/platform-plan` branch containing this prompt, the populated release
record, necessary current-document reconciliation and directly affected test
updates. Peter authorizes that bounded commit and a normal push to
`origin/docs/platform-plan`. Do not include generated artifacts, evidence
bundles, unrelated files or archived historical rewrites. Do not amend, rebase,
force-push or bypass a guard. A guard refusal or branch mismatch is a stop.

Return one concise handback containing:

- the immutable `ROUTE3_RELEASE_REV` and the separate release-record commit;
- all seven populated field values and the fixed wheel identity;
- the exact production S0.0 status and reviewed package/origin derivation;
- the off-production artifact locations, commands and digest proofs;
- the artifact-bound archive validation: retained `code.tar` and
  `MANIFEST.sha256` paths, the exact `route3_stage archive` invocation, its
  return status and its printed success result;
- focused validation results and final-tree commit/push status;
- proof that the archive pathspec is unchanged after the release revision;
- every remaining blocker or uncertainty; and
- an explicit statement that independent review is still required and S0.2,
  S1, S3, S4, provisioning, activation and migration/cutover remain
  unauthorized.

If any required proof cannot be obtained exactly, leave block F unchanged,
make no release-record commit, preserve the safe non-production evidence, and
return a precise NO-GO blocker. Never convert uncertainty into a release value.
