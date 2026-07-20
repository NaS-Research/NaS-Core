import argparse
from collections.abc import Sequence

from nas_core.config import get_settings
from nas_core.storage.layout import DataLayout


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nas-core")
    commands = parser.add_subparsers(dest="command", required=True)

    storage = commands.add_parser("storage", help="Manage the NaS Core data root")
    storage_commands = storage.add_subparsers(dest="storage_command", required=True)
    storage_commands.add_parser("init", help="Create and validate the data-root layout")
    storage_commands.add_parser("check", help="Validate the existing data-root layout")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    layout = DataLayout(settings.data_root)

    if args.command == "storage" and args.storage_command == "init":
        layout.initialize()
        print(f"Initialized NaS Core data root: {layout.root}")
        return 0

    if args.command == "storage" and args.storage_command == "check":
        layout.validate()
        print(f"NaS Core data root is valid: {layout.root}")
        return 0

    raise AssertionError("Unreachable command")
