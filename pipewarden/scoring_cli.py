"""CLI sub-command: ``pipewarden scoring``."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pipewarden.history import HistoryStore
from pipewarden.scoring import ScoringPolicy, score_pipeline


def build_scoring_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("scoring", help="Pipeline health scoring")
    sp = p.add_subparsers(dest="scoring_cmd", required=True)

    info = sp.add_parser("info", help="Show scoring policy defaults")
    info.add_argument("--critical-weight", type=int, default=40)
    info.add_argument("--warning-weight", type=int, default=15)
    info.add_argument("--info-weight", type=int, default=5)
    info.add_argument("--max-score", type=int, default=100)

    score = sp.add_parser("score", help="Score a pipeline from history")
    score.add_argument("pipeline", help="Pipeline name to score")
    score.add_argument("--history-file", default=".pipewarden_history.json")
    score.add_argument("--limit", type=int, default=50)
    score.add_argument("--critical-weight", type=int, default=40)
    score.add_argument("--warning-weight", type=int, default=15)
    score.add_argument("--info-weight", type=int, default=5)
    score.add_argument("--max-score", type=int, default=100)
    score.add_argument("--json", dest="as_json", action="store_true")

    p.set_defaults(func=handle_scoring)


def handle_scoring(args: argparse.Namespace) -> None:
    if args.scoring_cmd == "info":
        _cmd_info(args)
    elif args.scoring_cmd == "score":
        _cmd_score(args)


def _cmd_info(args: argparse.Namespace) -> None:
    policy = ScoringPolicy(
        critical_weight=args.critical_weight,
        warning_weight=args.warning_weight,
        info_weight=args.info_weight,
        max_score=args.max_score,
    )
    print(policy)


def _cmd_score(args: argparse.Namespace) -> None:
    store = HistoryStore(Path(args.history_file))
    entries = [
        e for e in store.load(limit=args.limit)
        if e.pipeline == args.pipeline
    ]

    events = []
    for entry in entries:
        for ev in entry.events:
            events.append(ev)

    policy = ScoringPolicy(
        critical_weight=args.critical_weight,
        warning_weight=args.warning_weight,
        info_weight=args.info_weight,
        max_score=args.max_score,
    )
    result = score_pipeline(args.pipeline, events, policy)

    if args.as_json:
        print(json.dumps({
            "pipeline": result.pipeline,
            "score": result.score,
            "max_score": result.max_score,
            "pct": result.pct,
            "healthy": result.healthy,
            "event_count": result.event_count,
            "deductions": result.deductions,
        }))
    else:
        print(result)
        if result.deductions:
            for d in result.deductions:
                print(f"  {d}")
