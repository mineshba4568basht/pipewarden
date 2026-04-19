"""Tests for pipewarden.dependency_cli."""
import argparse
import pytest
from pipewarden.dependency_cli import build_dependency_parser


@pytest.fixture
def dep_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="cmd")
    build_dependency_parser(sub)
    return root


class TestBuildDependencyParser:
    def test_subcommand_registered(self, dep_parser):
        args = dep_parser.parse_args(["dependency", "cycle"])
        assert args.dep_cmd == "cycle"

    def test_list_subcommand_exists(self, dep_parser):
        args = dep_parser.parse_args(["dependency", "list"])
        assert args.dep_cmd == "list"

    def test_list_upstream_default_none(self, dep_parser):
        args = dep_parser.parse_args(["dependency", "list"])
        assert args.upstream is None

    def test_list_upstream_option(self, dep_parser):
        args = dep_parser.parse_args(["dependency", "list", "--upstream", "ingest"])
        assert args.upstream == "ingest"

    def test_check_subcommand_stores_pipeline(self, dep_parser):
        args = dep_parser.parse_args(["dependency", "check", "export"])
        assert args.pipeline == "export"

    def test_check_default_failed_empty(self, dep_parser):
        args = dep_parser.parse_args(["dependency", "check", "export"])
        assert args.failed == []

    def test_check_failed_pipelines(self, dep_parser):
        args = dep_parser.parse_args(
            ["dependency", "check", "export", "--failed", "ingest", "transform"]
        )
        assert "ingest" in args.failed
        assert "transform" in args.failed
