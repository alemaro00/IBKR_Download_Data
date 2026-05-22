from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from trading.config import load_runtime_config
from trading.ibkr import IbkrConnectionError, preflight_ibkr_connection


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check local IBKR API setup before running data downloads.")
    parser.add_argument("--global-config", default=str(PROJECT_ROOT / "config" / "global.toml"))
    parser.add_argument("--algorithm-config", default=None)
    parser.add_argument("--run", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config_path = Path(args.global_config)
    config = load_runtime_config(
        global_path=config_path,
        algorithm_path=args.algorithm_config,
        run_path=args.run,
    )

    print("IBKR setup check")
    if config_path.exists():
        print(f"- Config: {config_path}")
    else:
        print(f"- Config: {config_path} not found; using defaults/env")
    print(f"- Endpoint: {config.ibkr.host}:{config.ibkr.port}")
    print(f"- Base client id: {config.ibkr.client_id}")

    if importlib.util.find_spec("ib_async") is None:
        print("- ib_async: missing. Install project dependencies before running IBKR commands.", file=sys.stderr)
        return 2
    print("- ib_async: installed")

    try:
        sys.stdout.flush()
        preflight_ibkr_connection(config.ibkr)
    except IbkrConnectionError as exc:
        print(f"- Socket: failed ({exc})", file=sys.stderr)
        print(
            "Open TWS or IB Gateway, then verify Global Configuration > API > Settings: "
            "Enable ActiveX and Socket Clients is on and the socket port matches this endpoint.",
            file=sys.stderr,
        )
        return 2

    print("- Socket: reachable")
    print("IBKR setup looks ready for the API handshake.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
