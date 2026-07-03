"""Demiurge II — substrate loop driver (Phase D1: human-triggered cycles).

The substrate side of the DESIGN.md anatomy. The organism NEVER runs this;
the driver runs the organism's proposals through the gate. Structural rules
enforced here (not requested — enforced):

  1. SUBSTRATE HASH CHECK first, every cycle. Manifest in substrate.sha256;
     any mismatch halts cold. `python driver.py seal` (operator-only) reseals.
  2. PROPOSAL SHAPE: a directory with organ files + bundle/{claim.json,
     check.py}. Organ files map ONLY into organ/ — INCIDENT-001's lesson as
     code: a proposal that names a path outside organ/ is REFUSED unseen.
  3. THE GATE IS OUTSIDE: certification is atlas-station's claim-gate
     (generator≠grader at the repo level); HOLDOUT SEEDS ARE DRIVER-CHOSEN
     (cryptographic randomness, never the proposer's).
  4. HONEST LEDGER: every cycle appends attempted/refused/rejected/certified
     to ledger.jsonl with reasons. Silence is a substrate violation.

Usage:
  python driver.py seal                     # operator: (re)write the manifest
  python driver.py verify                   # substrate integrity check
  python driver.py cycle <proposal_dir>     # one full gated cycle
"""
from __future__ import annotations

import hashlib
import json
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "substrate.sha256"
LEDGER = HERE / "ledger.jsonl"
ORGAN = HERE / "organ"
SUBSTRATE_FILES = ["driver.py", "DESIGN.md", "missions/m0.py"]
GATE = r"E:\atlas-station\scripts\claim-gate.mjs"
HOLDOUT_RANGE = 10_000_000


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _ledger(kind: str, body: dict):
    entry = {"t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "kind": kind, **body}
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"[ledger] {kind}: {json.dumps(body)[:160]}")


def seal():
    manifest = {f: _sha(HERE / f) for f in SUBSTRATE_FILES}
    MANIFEST.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"[seal] {len(manifest)} substrate files sealed")


def verify() -> bool:
    if not MANIFEST.is_file():
        print("[verify] NO MANIFEST — run seal first")
        return False
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    bad = [f for f, h in manifest.items()
           if not (HERE / f).is_file() or _sha(HERE / f) != h]
    if bad:
        print(f"[verify] SUBSTRATE MISMATCH: {bad} — HALT")
        return False
    print(f"[verify] substrate intact ({len(manifest)} files)")
    return True


def validate_proposal(pdir: Path):
    """Returns (organ_files, bundle_dir) or raises ValueError with the reason."""
    bundle = pdir / "bundle"
    if not (bundle / "claim.json").is_file() or not (bundle / "check.py").is_file():
        raise ValueError("no bundle/claim.json + bundle/check.py — nothing to gate")
    organ_src = pdir / "organ"
    if not organ_src.is_dir() or not any(organ_src.iterdir()):
        raise ValueError("no organ/ payload")
    files = []
    for f in organ_src.rglob("*"):
        if f.is_file():
            rel = f.relative_to(organ_src)
            if "__pycache__" in rel.parts or rel.suffix == ".pyc":
                continue                        # build debris, never organ
            # INCIDENT-001 rule: organ files land in organ/ and nowhere else.
            if ".." in rel.parts or rel.is_absolute():
                raise ValueError(f"path escape in proposal: {rel}")
            files.append(rel)
    if not files:
        raise ValueError("no organ payload after debris filter")
    return files, bundle


def gate(bundle: Path, n_holdout: int = 2) -> tuple[bool, list[int]]:
    claimed = json.loads((bundle / "claim.json").read_text(
        encoding="utf-8"))["claimed_seeds"]
    holdouts = []
    while len(holdouts) < n_holdout:                # driver-chosen, unseen
        s = secrets.randbelow(HOLDOUT_RANGE)
        if s not in claimed and s not in holdouts:
            holdouts.append(s)
    proc = subprocess.run(
        ["node", GATE, str(bundle)] + [str(s) for s in holdouts],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=1800)
    print(proc.stdout.strip())
    return proc.returncode == 0, holdouts


def adopt(pdir: Path, organ_files, claim_id: str):
    ORGAN.mkdir(exist_ok=True)
    for rel in organ_files:
        dst = ORGAN / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdir / "organ" / rel, dst)
    subprocess.run(["git", "add", "organ"], cwd=HERE, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m",
         f"organ: adopt {pdir.name} (certified claim {claim_id})"],
        cwd=HERE, capture_output=True)


def cycle(pdir: Path):
    pdir = pdir.resolve()
    if not verify():
        _ledger("halt", {"proposal": pdir.name, "reason": "substrate mismatch"})
        sys.exit(3)
    try:
        organ_files, bundle = validate_proposal(pdir)
    except ValueError as e:
        _ledger("refused", {"proposal": pdir.name, "reason": str(e)})
        sys.exit(2)
    claim = json.loads((bundle / "claim.json").read_text(encoding="utf-8"))
    _ledger("attempt", {"proposal": pdir.name, "id": claim.get("id"),
                        "organ_files": [str(f) for f in organ_files]})
    ok, holdouts = gate(bundle)
    if not ok:
        _ledger("rejected", {"proposal": pdir.name, "id": claim.get("id"),
                             "holdouts": holdouts})
        sys.exit(2)
    adopt(pdir, organ_files, claim.get("id", "?"))
    _ledger("certified", {"proposal": pdir.name, "id": claim.get("id"),
                          "holdouts": holdouts,
                          "adopted": [str(f) for f in organ_files]})
    print(f"[cycle] {pdir.name} CERTIFIED and adopted")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if cmd == "seal":
        seal()
    elif cmd == "verify":
        sys.exit(0 if verify() else 3)
    elif cmd == "cycle":
        cycle(Path(sys.argv[2]))
    else:
        print(__doc__)
        sys.exit(1)
