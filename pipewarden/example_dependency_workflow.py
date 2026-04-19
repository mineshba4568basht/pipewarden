"""Example showing dependency graph usage in pipewarden."""
from pipewarden.dependency import DependencyGraph, check_dependencies


def main() -> None:
    graph = DependencyGraph()
    graph.add("ingest", "transform")
    graph.add("transform", "export")
    graph.add("transform", "report")

    print("=== Dependency Graph ===")
    for edge in graph.edges:
        print(f"  {edge}")

    print(f"\nCycle detected: {graph.has_cycle()}")

    print("\n=== Dependency Checks (ingest failed) ===")
    failed = ["ingest"]
    for pipeline in ["transform", "export", "report"]:
        result = check_dependencies(pipeline, graph, failed)
        print(f"  {result}")

    print("\n=== Cycle Detection Example ===")
    cyclic = DependencyGraph()
    cyclic.add("a", "b")
    cyclic.add("b", "c")
    cyclic.add("c", "a")
    print(f"  Cyclic graph has cycle: {cyclic.has_cycle()}")


if __name__ == "__main__":
    main()
