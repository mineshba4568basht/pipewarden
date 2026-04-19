"""Pipeline dependency tracking and validation."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set


@dataclass
class DependencyEdge:
    upstream: str
    downstream: str

    def __str__(self) -> str:
        return f"{self.upstream} -> {self.downstream}"


@dataclass
class DependencyGraph:
    edges: List[DependencyEdge] = field(default_factory=list)

    def add(self, upstream: str, downstream: str) -> None:
        self.edges.append(DependencyEdge(upstream, downstream))

    def upstream_of(self, pipeline: str) -> List[str]:
        return [e.upstream for e in self.edges if e.downstream == pipeline]

    def downstream_of(self, pipeline: str) -> List[str]:
        return [e.downstream for e in self.edges if e.upstream == pipeline]

    def all_pipelines(self) -> Set[str]:
        result: Set[str] = set()
        for e in self.edges:
            result.add(e.upstream)
            result.add(e.downstream)
        return result

    def has_cycle(self) -> bool:
        visited: Set[str] = set()
        path: Set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            path.add(node)
            for nb in self.downstream_of(node):
                if nb not in visited:
                    if dfs(nb):
                        return True
                elif nb in path:
                    return True
            path.discard(node)
            return False

        for p in self.all_pipelines():
            if p not in visited:
                if dfs(p):
                    return True
        return False


@dataclass
class DependencyCheckResult:
    pipeline: str
    blocking_upstreams: List[str]
    checked_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_blocked(self) -> bool:
        return len(self.blocking_upstreams) > 0

    def __str__(self) -> str:
        status = "BLOCKED" if self.is_blocked else "CLEAR"
        return f"[{status}] {self.pipeline} | blocking={self.blocking_upstreams}"


def check_dependencies(
    pipeline: str,
    graph: DependencyGraph,
    failed_pipelines: List[str],
) -> DependencyCheckResult:
    """Return which upstream pipelines are currently failed."""
    upstreams = graph.upstream_of(pipeline)
    blocking = [u for u in upstreams if u in failed_pipelines]
    return DependencyCheckResult(pipeline=pipeline, blocking_upstreams=blocking)
