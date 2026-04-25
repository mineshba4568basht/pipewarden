"""CLI sub-commands for the archiving feature."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipewarden.archiving import ArchivePolicy, archive_entries


def build_archiving_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("archive", help="Archive old history entries")
    sp = p.add_subparsers(dest="archive_cmd")

    run_p = sp.add_parser("run", help="Run the archive sweep")
    run_p.add_argument(
        "--history-file",
        default=".pipewarden_history.jsonl",
        help="Path to the history JSONL file",
    )
    run_p.add_argument(
        "--max-age-hours",
        type=int,
        default=168,
        help="Entries older than this many hours are archived (default: 168)",
    )
    run_p.add_argument(
        "--archive-path",
        default=".pipewarden_archive.jsonl.gz",
        help="Destination gzip archive file",
    )

    p.set_defaults(func=handle_archiving)


def handle_archiving(args: argparse.Namespace) -> None:
    if args.archive_cmd == "run":
        _cmd_run(args)
    else:
        print("Use 'archive run' to perform an archive sweep.")


def _cmd_run(args: argparse.Namespace) -> None:
    history_file = Path(args.history_file)
    if not history_file.exists():
        print(f"History file not found: {history_file}")
        return

    entries = []
    with history_file.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    policy = ArchivePolicy(
        max_age_hours=args.max_age_hours,
        archive_path=args.archive_path,
    )

    result = archive_entries(entries, policy)
    print(result)

    # Rewrite history file with only the current (non-archived) entries
    remaining_count = result.remaining
    if result.archived > 0:
        current = entries[-remaining_count:] if remaining_count else []
        with history_file.open("w") as fh:
            for rec in current:
                fh.write(json.dumps(rec) + "\n")
        print(f"History file updated: {remaining_count} entries kept.")
