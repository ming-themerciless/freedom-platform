r5_end() {
  block_status=$?
  date -u '+S8.end end_utc=%Y-%m-%dT%H:%M:%SZ'
  end_status=$?
  printf 'S8.end date exit=%s\n' "$end_status"
  final_status=$block_status
  if [ "$block_status" -eq 0 ]; then final_status=$end_status; fi
  printf 'S8 final exit=%s\n' "$final_status"
  exit "$final_status"
}
r5_block() {
  trap r5_end EXIT
  status=$?
  printf 'S8.trap exit=%s\n' "$status"
  if [ "$status" -ne 0 ]; then exit "$status"; fi
  date -u '+S8.start start_utc=%Y-%m-%dT%H:%M:%SZ'
  status=$?
  printf 'S8.start date exit=%s\n' "$status"
  if [ "$status" -ne 0 ]; then exit "$status"; fi
  cd /var/tmp/<RUN>-work/co-r2/build-out
  status=$?
  printf 'S8.1 cd exit=%s\n' "$status"
  if [ "$status" -ne 0 ]; then exit "$status"; fi
  sha256sum --strict -c /var/tmp/<RUN>-checkout/infra/rp11-launch/expected.sha256
  status=$?
  printf 'S8.2 expected-sha256-check exit=%s\n' "$status"
  if [ "$status" -ne 0 ]; then exit "$status"; fi
  /opt/freedom-blades/runtime/venv-web/bin/python -I -B -c 'import hashlib,sys
rows=[l.split("  ",1) for l in sys.stdin.read().splitlines()]
bad=0
for want,name in rows:
    got=hashlib.sha256(open(name,"rb").read()).hexdigest()
    ok=got==want
    bad+=not ok
    print(got,name,"OK" if ok else "MISMATCH")
c=open("cc1.v","rb").read()
print(hashlib.sha256(c).hexdigest(),len(c),"cc1.v diagnostic, judged in step 9")
if bad or len(rows)!=4:
    sys.exit(30)
out=open(sys.argv[1],encoding="utf-8",errors="replace").read().splitlines()
missing=[w+"  "+n for w,n in rows if w+"  "+n not in out]
for m in missing:
    print("missing_from_build_stdout",m)
sys.exit(31 if missing else 0)' /var/tmp/<RUN>-evidence/build.stdout <<'OUTPUTS'
7e2b7bde86a5ec8aaf112c3377fbdb3c862ffcb7acfff944c965b1aa0fddc67e  rp11-launch
498108223928ddaa1eb5d57cca15c7628f5bd30f331bb1930f10a68dcf7cdfc9  rp11-launch.x86_64.listing
5a8b058084edcb1e3f6f7ddea13b60da6af71102300ea276225ae4ab0e8bc34d  rp11-launch.map
3d65779e718d2cd1e8d199fd1db619712237613df975992ade1b8d48cd57786e  launch.s
OUTPUTS
  status=$?
  printf 'S8.3 independent-output-check exit=%s\n' "$status"
  if [ "$status" -ne 0 ]; then exit "$status"; fi
  cmp /var/tmp/<RUN>-work/co-r2/build-out/rp11-launch.x86_64.listing /var/tmp/<RUN>-checkout/infra/rp11-launch/rp11-launch.x86_64.listing
  status=$?
  printf 'S8.4 listing-cmp exit=%s\n' "$status"
  if [ "$status" -ne 0 ]; then exit "$status"; fi
  printf 'S8 block exit=0\n'
  exit 0
}
r5_block </dev/null
