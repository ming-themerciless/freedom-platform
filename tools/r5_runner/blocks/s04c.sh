r5_end() {
  block_status=$?
  date -u '+S4c.end end_utc=%Y-%m-%dT%H:%M:%SZ'
  end_status=$?
  printf 'S4c.end date exit=%s\n' "$end_status"
  final_status=$block_status
  if [ "$block_status" -eq 0 ]; then final_status=$end_status; fi
  printf 'S4c final exit=%s\n' "$final_status"
  exit "$final_status"
}
r5_block() {
  trap r5_end EXIT
  status=$?
  printf 'S4c.trap exit=%s\n' "$status"
  if [ "$status" -ne 0 ]; then exit "$status"; fi
  date -u '+S4c.start start_utc=%Y-%m-%dT%H:%M:%SZ'
  status=$?
  printf 'S4c.start date exit=%s\n' "$status"
  if [ "$status" -ne 0 ]; then exit "$status"; fi
  cd /opt/freedom-blades/platform
  status=$?
  printf 'S4c.1 cd exit=%s\n' "$status"
  if [ "$status" -ne 0 ]; then exit "$status"; fi
  PYTHONDONTWRITEBYTECODE=1 python3 -I -B -c 'import subprocess,sys
paths=["infra","tests","tools","pytest.ini"]
r=subprocess.run(["git","status","--porcelain","--untracked-files=all","--"]+paths,capture_output=True,text=True)
sys.stdout.write(r.stdout)
sys.stderr.write(r.stderr)
if r.returncode:
    sys.exit(r.returncode)
print("repository_state="+("drift" if r.stdout else "clean"))
sys.exit(28 if r.stdout else 0)'
  status=$?
  printf 'S4c.2 repository-state exit=%s\n' "$status"
  if [ "$status" -ne 0 ]; then exit "$status"; fi
  sha256sum --strict -c <<'SUMS'
f704c0f4f0ddbe9de92da9812dde6929f681ba778263746a603bde8b4b3563d6  infra/rp11-launch/toolchain.lock
f08ba9de4374374fa91012021ce12fb83f6370be5547ee4e214232100c38e76f  infra/rp11-launch/build-root.manifest
651ff85df120a6b8bddfff7b359074b4c239e94988544c9ef60af7c3af28dd16  infra/rp11-launch/expected.sha256
e99cee65a228339e304d4e578643de409961539a8240230d4e41bb1baf6bb13a  infra/rp11-launch/verify/fixtures/cc1.v.baseline
4fa1c2b1fcf9cedf7fb1028feeeda4d0e229ed061ef3cc19047ca24cd42bca8d  docs/review/phase-5-0-evidence-harness-review-manifest.json
d827b7552f0ad48a13ae899c6fb40d0c47815d3f1332d158f5c519e77b09d617  docs/review/phase-5-0-evidence-harness-concrete-plan.md
87e318cdd77f1fae0a354f707d9fe32d163ba48b708bb455c670f6d4d333cfd1  infra/rp11-launch/build.sh
62050b5dc1816f4f673b8c49b94c7463391edb6dbed9f69459f0bc6c5f1dc2a7  infra/rp11-launch/launch.c
34b56cfc1adb4f14f2e09c740e5e25915194778ebf73c74c1d24502121425c4b  infra/rp11-launch/select.h
ca631f087ad09c16d5e45d2088c7be81593f2fb8efb805b66ed65aff0a1a5139  infra/rp11-launch/start.s
ed5519ef1994d4b32eb92f754f008a5aeb88e08d5194ede92491ddda1ac95326  infra/rp11-launch/rp11-launch.ld
498108223928ddaa1eb5d57cca15c7628f5bd30f331bb1930f10a68dcf7cdfc9  infra/rp11-launch/rp11-launch.x86_64.listing
40496661f5d7e251b557b6d4f9f13a1d76e59619a608c39e576424352d0c0300  infra/rp11-launch/buildroot/provision.py
cf467c17df4135cc5f431a3ffe5c86afef930df3b880ae4425ad6209e397807a  infra/rp11-launch/buildroot/enter.py
16b784622d46150dee768e399d3e89ddb8a996111af5264928761a5bc08a4b72  infra/rp11-launch/verify/cc1check.py
167d16ae0b1cf6e82a5099b5e5b5c6b571b1f0273f8bdde7b79c55b9af2fceed  infra/rp11-launch/verify/ic1check.py
b742552c6d200dd1c0536f29a444dcc4a00405f758788bc82c8b2c4f2df2aceb  infra/rp11-launch/verify/elfcheck.py
cb1b8d835983b625e8e42dda2d46aa2d5e56816cf90fb8c3a397e291c3d0e676  infra/rp11-launch/verify/tl11.py
eea9f843ef87cabff7baafbd21a05e60742c1219741f6a56571ce152bd342a31  infra/rp11-launch/verify/ctverify.py
84598d0683f377fcdb2282ae8080d07d4ce144e46adcc236d1d0677766038c97  infra/rp11-launch/verify/xdecode.py
d20406488804d7d3559917a3d55512d44b40789c018849977d6737a86ba67b66  infra/rp11-launch/verify/xdecode-spelling.table
f0e811a4bd61782789b66f31ab4401797e52b8ac00ffeebb984bfcd71afb4a8a  infra/rp11-launch/verify/xdecode-corpus.txt
603099e0f7279e4158023a63b6bc1411c0d9d3ac7c9372c7f77fa9d42f0b0a94  infra/rp11-launch/test-harness/select_harness.c
8c4ad99c0a1f3452923dab46149e7f4b202060ef5bf981b732ec9e9724dd91fd  infra/rp11-launch/test-harness/select_shim.c
ff3d458cabae91512562cca6143542337b1306dc3df791da505c51a9519ab76f  tests/test_rp11_launch_toolchain.py
bc24c0ee7b0c9f58853479adc908c60cf013b9652409e3d5cee0d710074a18b6  tests/rp11_launch_support.py
a51bacda94ef5ed2fe1bea6a7e90bc7c94925237bd6f72f518f7ef0c338381ed  tools/phase_5_0_evidence/rp11_launch.py
f18d8fdf897961167ee58da475d1483de14bf01ba90c0a2e537a49dd2eef3879  tools/phase_5_0_evidence/review_manifest.py
SUMS
  status=$?
  printf 'S4c.3 sha256sum-check exit=%s\n' "$status"
  if [ "$status" -ne 0 ]; then exit "$status"; fi
  printf 'S4c block exit=0\n'
  exit 0
}
r5_block </dev/null
