"""Tests for the pipewarden CLI entry point."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from pipewarden.cli import build_parser, run
from pipewarden.runner import RunReport


@pytest.fixture
def parser():
    return build_parser()


@pytest.fixture
def mock_report_passed():
    report = MagicMock(spec=RunReport)
    report.passed = True
    report.failed_checks = []
    report.results = [MagicMock(), MagicMock()]
    report.alert_events = []
    return report


@pytest.fixture
def mock_report_failed():
    report = MagicMock(spec=RunReport)
    report.passed = False
    report.failed_checks = [MagicMock()]
    report.results = [MagicMock()]
    report.alert_events = [MagicMock()]
    return report


class TestBuildParser:
    def test_default_config(self, parser):
        args = parser.parse_args([])
        assert args.config == "pipewarden.yaml"

    def test_custom_config(self, parser):
        args = parser.parse_args(["--config", "my_config.yaml"])
        assert args.config == "my_config.yaml"

    def test_default_channels(self, parser):
        args = parser.parse_args([])
        assert args.channels == ["log"]

    def test_verbose_flag(self, parser):
        args = parser.parse_args(["--verbose"])
        assert args.verbose is True

    def test_verbose_short_flag(self, parser):
        args = parser.parse_args(["-v"])
        assert args.verbose is True


class TestRun:
    def test_returns_0_when_all_pass(self, parser, mock_report_passed):
        args = parser.parse_args(["--config", "pipewarden.yaml"])
        with patch("pipewarden.cli.load_config") as mock_load, \
             patch("pipewarden.cli.PipelineRunner") as MockRunner:
            MockRunner.return_value.run.return_value = mock_report_passed
            exit_code = run(args)
        assert exit_code == 0

    def test_returns_1_when_checks_fail(self, parser, mock_report_failed):
        args = parser.parse_args(["--config", "pipewarden.yaml"])
        with patch("pipewarden.cli.load_config") as mock_load, \
             patch("pipewarden.cli.PipelineRunner") as MockRunner:
            MockRunner.return_value.run.return_value = mock_report_failed
            exit_code = run(args)
        assert exit_code == 1

    def test_returns_2_on_file_not_found(self, parser):
        args = parser.parse_args(["--config", "nonexistent.yaml"])
        with patch("pipewarden.cli.load_config", side_effect=FileNotFoundError):
            exit_code = run(args)
        assert exit_code == 2

    def test_returns_2_on_config_error(self, parser):
        args = parser.parse_args(["--config", "bad.yaml"])
        with patch("pipewarden.cli.load_config", side_effect=ValueError("bad yaml")):
            exit_code = run(args)
        assert exit_code == 2

    def test_dispatches_alerts_on_failure(self, parser, mock_report_failed):
        args = parser.parse_args([])
        with patch("pipewarden.cli.load_config"), \
             patch("pipewarden.cli.PipelineRunner") as MockRunner, \
             patch("pipewarden.cli.AlertDispatcher") as MockDispatcher:
            MockRunner.return_value.run.return_value = mock_report_failed
            mock_dispatcher_instance = MagicMock()
            mock_dispatcher_instance.failed_dispatches = []
            MockDispatcher.return_value = mock_dispatcher_instance
            run(args)
            mock_dispatcher_instance.dispatch_all.assert_called_once()
