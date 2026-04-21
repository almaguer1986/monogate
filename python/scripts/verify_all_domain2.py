"""Run all 8 domain-2 verification scripts and report aggregate pass/fail."""
import subprocess, sys, pathlib

SCRIPTS = [
    "verify_fin_1.py",
    "verify_fin_2.py",
    "verify_info_1.py",
    "verify_qm_1.py",
    "verify_thermo_1.py",
    "verify_chem_1.py",
    "verify_bio_1.py",
    "verify_econ_1.py",
]

scripts_dir = pathlib.Path(__file__).parent
total_passed = total_failed = 0

for script in SCRIPTS:
    path = scripts_dir / script
    result = subprocess.run(
        [sys.executable, str(path)], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    stdout = result.stdout or ""
    stderr = result.stderr or ""
    lines = (stdout + stderr).strip().split("\n")
    last = lines[-1] if lines else ""
    ok = result.returncode == 0
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {script:30s}  {last}")
    if ok:
        total_passed += 1
    else:
        total_failed += 1
        for ln in lines:
            print(f"        {ln}")

print(f"\n{'='*60}")
print(f"Domain-2 aggregate: {total_passed}/{total_passed+total_failed} scripts PASS")
if total_failed:
    print("SOME SCRIPTS FAILED — see details above")
    sys.exit(1)
else:
    print("ALL DOMAIN-2 VERIFICATION SCRIPTS PASS")
