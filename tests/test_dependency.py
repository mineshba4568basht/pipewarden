"""Tests for pipewarden.dependency."""
import pytest
from pipewarden.dependency import (
    DependencyEdge,
    DependencyGraph,
    DependencyCheckResult,
    check_dependencies,
)


def _graph() -> DependencyGraph:
    g = DependencyGraph()
    g.add("ingest", "transform")
    g.add("transform", "export")
    return g


class TestDependencyEdge:
    def test_str(self):
        e = DependencyEdge("a", "b")
        assert str(e) == "a -> b"


class TestDependencyGraph:
    def test_upstream_of(self):
        g = _graph()
        assert g.upstream_of("transform") == ["ingest"]

    def test_downstream_of(self):
        g = _graph()
        assert g.downstream_of("transform") == ["export"]

    def test_all_pipelines(self):
        g = _graph()
        assert g.all_pipelines() == {"ingest", "transform", "export"}

    def test_no_cycle(self):
        g = _graph()
        assert g.has_cycle() is False

    def test_cycle_detected(self):
        g = DependencyGraph()
        g.add("a", "b")
        g.add("b", "c")
        g.add("c", "a")
        assert g.has_cycle() is True

    def test_empty_graph_no_cycle(self):
        assert DependencyGraph().has_cycle() is False


class TestDependencyCheckResult:
    def test_is_blocked_true(self):
        r = DependencyCheckResult(pipeline="export", blocking_upstreams=["transform"])
        assert r.is_blocked is True

    def test_is_blocked_false(self):
        r = DependencyCheckResult(pipeline="export", blocking_upstreams=[])
        assert r.is_blocked is False

    def test_str_blocked(self):
        r = DependencyCheckResult(pipeline="export", blocking_upstreams=["transform"])
        assert "BLOCKED" in str(r)
        assert "export" in str(r)

    def test_str_clear(self):
        r = DependencyCheckResult(pipeline="export", blocking_upstreams=[])
        assert "CLEAR" in str(r)


class TestCheckDependencies:
    def test_no_failed_pipelines(self):
        g = _graph()
        result = check_dependencies("transform", g, [])
        assert not result.is_blocked

    def test_upstream_failed_blocks(self):
        g = _graph()
        result = check_dependencies("transform", g, ["ingest"])
        assert result.is_blocked
        assert "ingest" in result.blocking_upstreams

    def test_unrelated_failure_does_not_block(self):
        g = _graph()
        result = check_dependencies("transform", g, ["export"])
        assert not result.is_blocked

    def test_multiple_upstreams(self):
        g = DependencyGraph()
        g.add("src1", "merge")
        g.add("src2", "merge")
        result = check_dependencies("merge", g, ["src1", "src2"])
        assert len(result.blocking_upstreams) == 2
