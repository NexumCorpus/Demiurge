"""Guard tests: on a machine without the author's gate (any fresh clone), the driver, the
autonomous loop and the hunt halt BEFORE launching an agent or recording an attempt, and a
gate crash is never ledgered as a rejection. Standard library only; no real gate, agent or
ledger is touched. Run by reproduce.py, or directly: python tests/test_driver_guard.py
"""
from __future__ import annotations

import contextlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import driver                                        # noqa: E402
import autoloop                                      # noqa: E402
import hunt                                          # noqa: E402


@contextlib.contextmanager
def no_gate_sandbox():
    """GATE points nowhere, LEDGER and KILL are temporary: nothing real is touched."""
    saved = (driver.GATE, driver.LEDGER, autoloop.KILL)
    with tempfile.TemporaryDirectory() as tmp:
        driver.GATE = str(Path(tmp) / "no-such-gate.mjs")
        driver.LEDGER = Path(tmp) / "ledger.jsonl"
        autoloop.KILL = Path(tmp) / "KILL"
        try:
            yield driver.LEDGER
        finally:
            driver.GATE, driver.LEDGER, autoloop.KILL = saved


def kinds(ledger: Path) -> list[str]:
    if not ledger.is_file():
        return []
    return [json.loads(line)["kind"] for line in ledger.read_text(encoding="utf-8").splitlines()]


def must_not_run(*_a, **_k):
    raise AssertionError("an agent was launched although the gate is unreachable")


def test_gate_unreachable_names_the_reason():
    with no_gate_sandbox():
        assert "unreachable" in (driver.gate_unreachable() or "")


def test_autoloop_halts_before_launching_an_agent():
    saved = autoloop.dispatch_proposer
    autoloop.dispatch_proposer = must_not_run
    try:
        with no_gate_sandbox() as ledger:
            assert autoloop.one_cycle(0) == "halted"
            assert kinds(ledger) == ["halt"]
            assert "gate unreachable" in ledger.read_text(encoding="utf-8")
    finally:
        autoloop.dispatch_proposer = saved


def test_hunt_halts_before_launching_a_proposer():
    saved = hunt.dispatch
    hunt.dispatch = must_not_run
    try:
        with no_gate_sandbox() as ledger:
            assert hunt.hunt("q2n14r2") == "halted"
            assert kinds(ledger) == ["halt"]
    finally:
        hunt.dispatch = saved


def test_cycle_without_a_gate_halts_and_never_ledgers_a_rejection():
    with no_gate_sandbox() as ledger:
        try:
            driver.cycle(HERE / "proposals" / "p001-dp-scheduler")
        except SystemExit as e:
            assert e.code == 4, e.code
        else:
            raise AssertionError("cycle should have exited")
        assert kinds(ledger) == ["halt"], kinds(ledger)


def test_a_gate_crash_is_not_a_rejection():
    saved = driver.subprocess.run

    def fake(code, err=""):
        return lambda *a, **k: subprocess.CompletedProcess(a, code, stdout="", stderr=err)

    bundle = HERE / "proposals" / "p001-dp-scheduler" / "bundle"
    try:
        driver.subprocess.run = fake(1, "Error: Cannot find module")
        try:
            driver.gate(bundle)
        except driver.GateError as e:
            assert "Cannot find module" in str(e)
        else:
            raise AssertionError("exit 1 must raise GateError, not return a verdict")
        driver.subprocess.run = fake(2)
        assert driver.gate(bundle)[0] is False          # a real rejection
        driver.subprocess.run = fake(0)
        assert driver.gate(bundle)[0] is True           # a real certification
    finally:
        driver.subprocess.run = saved


if __name__ == "__main__":
    failed = 0
    for name in sorted(n for n in dir() if n.startswith("test_")):
        try:
            globals()[name]()
            print("ok  ", name)
        except Exception as e:  # noqa: BLE001
            failed += 1
            print("FAIL", name, repr(e))
    sys.exit(1 if failed else 0)
