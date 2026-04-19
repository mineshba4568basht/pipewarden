"""Tests for pipewarden.labeling_cli."""
from __future__ import annotations
import pytest
from pipewarden.labeling_cli import build_labeling_parser, handle_labeling


@pytest.fixture
def labeling_parser():
    return build_labeling_parser()


class TestBuildLabelingParser:
    def test_parser_created(self, labeling_parser):
        assert labeling_parser is not None

    def test_info_subcommand_exists(self, labeling_parser):
        args = labeling_parser.parse_args(["info"])
        assert args.label_cmd == "info"

    def test_info_default_key_none(self, labeling_parser):
        args = labeling_parser.parse_args(["info"])
        assert args.key is None

    def test_info_default_value_none(self, labeling_parser):
        args = labeling_parser.parse_args(["info"])
        assert args.value is None

    def test_info_default_pipeline_none(self, labeling_parser):
        args = labeling_parser.parse_args(["info"])
        assert args.pipeline is None

    def test_info_default_severity_none(self, labeling_parser):
        args = labeling_parser.parse_args(["info"])
        assert args.severity is None

    def test_info_accepts_key(self, labeling_parser):
        args = labeling_parser.parse_args(["info", "--key", "team"])
        assert args.key == "team"

    def test_info_accepts_value(self, labeling_parser):
        args = labeling_parser.parse_args(["info", "--value", "data"])
        assert args.value == "data"


class TestHandleLabeling:
    def test_info_prints_rule(self, labeling_parser, capsys):
        args = labeling_parser.parse_args(["info", "--key", "env", "--value", "prod"])
        handle_labeling(args)
        out = capsys.readouterr().out
        assert "env=prod" in out

    def test_no_cmd_prints_help(self, labeling_parser, capsys):
        args = labeling_parser.parse_args([])
        handle_labeling(args)
        out = capsys.readouterr().out
        assert "No label subcommand" in out

    def test_info_default_key_used(self, labeling_parser, capsys):
        args = labeling_parser.parse_args(["info"])
        handle_labeling(args)
        out = capsys.readouterr().out
        assert "env=production" in out
