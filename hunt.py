"""Demiurge II — autonomous world-record hunt against mission M2 (covering
codes). The estate attempting a real frozen record, unwatched, in the
verifiable medium: each cycle a proposer (dispatched agent, or local model
when up) writes a construction; the DRIVER assembles a claim bundle with the
CANONICAL check + snapshotted champion; the gate certifies only a genuinely
smaller valid covering code on seeds the proposer never saw. Certified ->
new champion (the ladder climbs); the moment champion < record, that is a
world-first. Rejections ledgered. Pulse-runnable.

Usage: python hunt.py <cell_id> [proposer_model]     (default q2n14r2, sonnet)
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import driver                                        # noqa: E402
from missions.m2 import CELLS, baseline, is_covering, score  # noqa: E402

SANDBOX = Path("E:/demiurge-runs")
CHAMPIONS = HERE / "champions.json"                  # per-cell best certified
PROPOSER_TIMEOUT_S = 900


def champion_size(cell: str) -> int:
    try:
        return json.loads(CHAMPIONS.read_text(encoding="utf-8")).get(
            cell, len(baseline(cell)))
    except (OSError, json.JSONDecodeError):
        return len(baseline(cell))


def set_champion(cell: str, size: int):
    try:
        d = json.loads(CHAMPIONS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        d = {}
    d[cell] = size
    CHAMPIONS.write_text(json.dumps(d, indent=1), encoding="utf-8")


PROMPT = """\
You are attacking an open combinatorics record: a q-ary COVERING CODE.
Cell {cell}: q={q}, n={n}, covering radius R={R}. A code C (a set of length-{n}
words over symbols 0..{q_1}) is valid iff EVERY word in Z_{q}^{n} is within
Hamming distance {R} of some codeword. Goal: a VALID code with FEWER than
{champ} codewords (current best here). The all-time record is {record}.

mission.py in this directory has is_covering(code,q,n,R) and score(cell,code)
- USE THEM to self-check. Write construct.py that:
  1. builds a covering code by any method (algebraic construction, greedy +
     local search / simulated annealing removing redundant codewords from a
     valid start, LP/ILP-free heuristics — your choice; deterministic, seed
     any randomness with a constant, < 12 min runtime);
  2. imports mission, ASSERTS is_covering(code,{q},{n},{R}) is True and
     len(code) < {champ} before emitting — if you cannot beat {champ}, still
     emit your smallest VALID code (a valid code is worth confirming);
  3. prints ONLY the JSON list of codewords (each a list of {n} ints) to
     stdout as the last line.
Claim only a valid, verified code. A code that does not cover, or is not
smaller, will be rejected by an external gate on unseen audit seeds."""


def dispatch(cell: str, model: str) -> list | None:
    c = CELLS[cell]
    champ = champion_size(cell)
    sandbox = SANDBOX / f"hunt_{cell}_{time.strftime('%Y%m%d_%H%M%S')}"
    sandbox.mkdir(parents=True)
    shutil.copy2(HERE / "missions" / "m2.py", sandbox / "mission.py")
    prompt = PROMPT.format(cell=cell, q=c["q"], n=c["n"], R=c["R"],
                           q_1=c["q"] - 1, champ=champ, record=c["record"])
    claude = shutil.which("claude")
    proc = subprocess.run(
        [claude, "-p", prompt, "--model", model,
         "--permission-mode", "bypassPermissions"],
        cwd=str(sandbox), capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=PROPOSER_TIMEOUT_S)
    (sandbox / "_proposer.log").write_text(proc.stdout + proc.stderr,
                                           encoding="utf-8")
    construct = sandbox / "construct.py"
    if not construct.is_file():
        return None
    r = subprocess.run([sys.executable, "construct.py"], cwd=str(sandbox),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=900)
    for line in reversed((r.stdout or "").splitlines()):
        line = line.strip()
        if line.startswith("["):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def hunt(cell: str, model: str = "sonnet"):
    if not driver.verify():
        driver._ledger("halt", {"hunt": cell, "reason": "substrate mismatch"})
        return "halted"
    c = CELLS[cell]
    champ = champion_size(cell)
    code = dispatch(cell, model)
    if not code:
        driver._ledger("hunt-noemit", {"cell": cell})
        return "no-emit"
    # substrate-side sanity BEFORE spending the gate (the gate is truth, this
    # is triage): valid + strictly smaller.
    sz = score(cell, code)
    if sz == 0 or not is_covering(code, c["q"], c["n"], c["R"]):
        driver._ledger("hunt-invalid", {"cell": cell})
        return "invalid"
    if sz >= champ:
        driver._ledger("hunt-not-smaller", {"cell": cell, "size": sz,
                                            "champ": champ})
        return "not-smaller"
    # assemble the claim bundle: code.json + champion.json + canonical check
    pdir = HERE / "proposals" / f"hunt_{cell}_{time.strftime('%Y%m%d_%H%M%S')}"
    bundle = pdir / "bundle"
    bundle.mkdir(parents=True)
    (bundle / "code.json").write_text(json.dumps(code), encoding="utf-8")
    (bundle / "champion.json").write_text(
        json.dumps({"cell": cell, "size": champ}), encoding="utf-8")
    shutil.copy2(HERE / "missions" / "m2_check.py", bundle / "check.py")
    (bundle / "claim.json").write_text(json.dumps({
        "id": f"demiurge-cover-{cell}-{sz}",
        "statement": f"covering code for {cell} of size {sz} < prior best "
                     f"{champ} (record {c['record']}); valid on the domain's "
                     f"own is_covering + seeded 200k-word audit",
        "check": ["python", "check.py", "{seed}"],
        "claimed_seeds": [1, 2, 3],
    }, indent=1), encoding="utf-8")
    driver._ledger("hunt-attempt", {"cell": cell, "size": sz, "champ": champ,
                                    "record": c["record"]})
    ok, holdouts = driver.gate(bundle)
    if ok:
        set_champion(cell, sz)
        world_first = sz < c["record"]
        driver._ledger("hunt-certified", {"cell": cell, "size": sz,
                                          "record": c["record"],
                                          "WORLD_FIRST": world_first,
                                          "holdouts": holdouts})
        return f"CERTIFIED size={sz}" + (" **WORLD-FIRST**" if world_first else "")
    driver._ledger("hunt-rejected", {"cell": cell, "size": sz,
                                     "holdouts": holdouts})
    return "rejected"


if __name__ == "__main__":
    cell = sys.argv[1] if len(sys.argv) > 1 else "q2n14r2"
    model = sys.argv[2] if len(sys.argv) > 2 else "sonnet"
    print(f"[hunt] {cell} champ={champion_size(cell)} "
          f"record={CELLS[cell]['record']}")
    print("[hunt]", hunt(cell, model))
