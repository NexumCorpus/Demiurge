"""Demiurge II — autonomous world-record hunt against mission M2 (covering
codes). The estate attempting a real frozen record, unwatched, in the
verifiable medium: each cycle a proposer (dispatched agent, or local model
when up) writes a construction; the DRIVER assembles a claim bundle with the
CANONICAL check + snapshotted champion; the gate certifies only a genuinely
smaller valid covering code on seeds the proposer never saw. Certified ->
new champion (the ladder climbs); the moment champion < record, that is a
world-first. Rejections ledgered. Pulse-runnable.

Usage: python hunt.py <cell_id> [proposer_model]     (default q2n14r2, sonnet)

INTEGRITY (analyzed 2026-07-03, flags named not hidden):
- CLAIM SEMANTICS: for covering codes the whole space is tiny (2^14=16384,
  3^8=6561 words), so is_covering is EXHAUSTIVE — a certification here is a
  near-PROOF, not a statistical generalization. The gate's holdout seeds do
  DEFENSE-IN-DEPTH (an independent xor+popcount path catching a bug in the
  oracle), not anti-overfitting (a code cannot overfit; it covers all words
  or it does not). Stronger evidence than the ML-domain claims, not weaker.
- OUTWARD GATE: a certified code is an INTERNAL proof of validity+size. It is
  NOT a published world-record. Announcing/submitting against Keri's tables
  is outward-facing + irreversible -> HUMAN GATE (DESIGN.md physical-phase
  rule). hunt NEVER announces; it ledgers WORLD_FIRST=true for the operator
  to verify externally and decide.
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


def _ollama_up() -> bool:
    """Local free proposer available? (organ preferred over metered calls.)"""
    try:
        r = subprocess.run(["wsl", "-d", "Ubuntu", "--", "bash", "-lc",
                            "curl -s http://localhost:11434/api/tags"],
                           capture_output=True, text=True, timeout=15)
        return "models" in (r.stdout or "")
    except Exception:
        return False


def _ollama_dispatch(prompt: str, model: str, sandbox: Path) -> bool:
    """Free local proposer: the model emits construct.py source directly
    (no tool access, unlike the claude path — we extract the code block).
    Returns True iff construct.py was written."""
    body = json.dumps({
        "model": model,
        "prompt": prompt + "\n\nOutput ONLY the complete construct.py source "
                           "in a single ```python fenced block, nothing else.",
        "stream": False,
        "options": {"temperature": 0.2},
    })
    try:
        r = subprocess.run(
            ["wsl", "-d", "Ubuntu", "--", "curl", "-s", "--max-time", "840",
             "http://localhost:11434/api/generate", "-d", "@-"],
            input=body, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=PROPOSER_TIMEOUT_S)
        text = json.loads(r.stdout).get("response", "")
    except Exception as e:
        (sandbox / "_proposer.log").write_text(f"ollama error: {e}",
                                               encoding="utf-8")
        return False
    (sandbox / "_proposer.log").write_text(text, encoding="utf-8")
    src = text
    if "```" in text:                       # prefer the fenced block
        parts = text.split("```")
        blocks = [p for i, p in enumerate(parts) if i % 2 == 1]
        if blocks:
            src = max(blocks, key=len)
            if src.startswith(("python", "py")):
                src = src.split("\n", 1)[1] if "\n" in src else ""
    if "import" not in src:                 # not plausibly a script
        return False
    (sandbox / "construct.py").write_text(src, encoding="utf-8")
    return True


def dispatch(cell: str, model: str) -> list | None:
    c = CELLS[cell]
    champ = champion_size(cell)
    sandbox = SANDBOX / f"hunt_{cell}_{time.strftime('%Y%m%d_%H%M%S')}"
    sandbox.mkdir(parents=True)
    shutil.copy2(HERE / "missions" / "m2.py", sandbox / "mission.py")
    prompt = PROMPT.format(cell=cell, q=c["q"], n=c["n"], R=c["R"],
                           q_1=c["q"] - 1, champ=champ, record=c["record"])
    if model.startswith("ollama:"):
        if not _ollama_dispatch(prompt, model.split(":", 1)[1], sandbox):
            return None
    else:
        claude = shutil.which("claude")
        proc = subprocess.run(
            [claude, "-p", prompt, "--model", model,
             "--permission-mode", "bypassPermissions"],
            cwd=str(sandbox), capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=PROPOSER_TIMEOUT_S)
        (sandbox / "_proposer.log").write_text(proc.stdout + proc.stderr,
                                               encoding="utf-8")
        log = (proc.stdout + proc.stderr).lower()
        if "resets" in log and "limit" in log:
            (sandbox / "_hardwall").write_text("1")     # signal to caller
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
