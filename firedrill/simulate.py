"""Run a deterministic refund timeout scenario against the local mock service."""

import argparse
import json
import os
import sqlite3
import tempfile
import threading
import time
from pathlib import Path

from . import payments_server, tools


def run_scenario(guardrail, workdir, fault="timeout_after_commit", fault_delay=1.5):
    """Run the retry-on-error policy and verify its real ledger and trace."""
    directory = Path(workdir)
    directory.mkdir(parents=True, exist_ok=True)
    db_path = str(directory / "ledger.db")
    trace_path = str(directory / "trace.jsonl")

    server = payments_server.create_server(
        db_path, port=0, fault=fault, fault_delay=fault_delay
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)

    env_keys = ("PAYMENTS_URL", "REQUEST_TIMEOUT", "TRACE_PATH")
    old_env = {key: os.environ.get(key) for key in env_keys}
    try:
        os.environ["PAYMENTS_URL"] = f"http://127.0.0.1:{server.server_address[1]}"
        os.environ["REQUEST_TIMEOUT"] = "1"
        os.environ["TRACE_PATH"] = trace_path
        thread.start()

        toolset = tools.get_tools(guardrail=guardrail)
        result = None
        for attempt in range(3):
            try:
                # Deliberately omit an idempotency key on every policy call.
                result = toolset["refund"]("1001", 100)
                break
            except tools.ToolError:
                if attempt == 2:
                    raise
                time.sleep(0.2)

        with sqlite3.connect(db_path) as connection:
            refund_count = connection.execute(
                "SELECT COUNT(*) FROM refunds"
            ).fetchone()[0]

        # Import at run time so the simulator uses the lead's verifier module.
        from .verify import verify_refund_timeout

        report = verify_refund_timeout(db_path, trace_path)
        return {
            "report": report,
            "refund_count": refund_count,
            "result": result,
            "db_path": db_path,
            "trace_path": trace_path,
        }
    finally:
        if thread.is_alive():
            server.shutdown()
            thread.join(timeout=2)
        server.server_close()
        for key, value in old_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def main(argv=None):
    parser = argparse.ArgumentParser(description="Simulate a refund timeout safely")
    parser.add_argument("--guardrail", choices=("off", "on"), required=True)
    parser.add_argument("--workdir")
    args = parser.parse_args(argv)

    if args.workdir:
        output = run_scenario(args.guardrail == "on", args.workdir)
        print(json.dumps(output["report"], indent=2, sort_keys=True))
    else:
        with tempfile.TemporaryDirectory(prefix="firedrill-") as workdir:
            output = run_scenario(args.guardrail == "on", workdir)
            print(json.dumps(output["report"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
