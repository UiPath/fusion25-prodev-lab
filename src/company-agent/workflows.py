"""
Programmatic workflow extraction and documentation using Kleene star notation.

This module automatically extracts all possible execution paths from the LangGraph
structure and represents them using formal automata notation with Kleene star (*).

The extraction is fully programmatic - it parses main.py to find:
- Nodes: builder.add_node() calls
- Direct edges: builder.add_edge() calls
- Conditional edges: builder.add_conditional_edges() calls

Then uses DFS to find all paths from START to END, and normalizes them using
Kleene star notation to eliminate redundancy from self-loops.

Usage:
    from workflows import extract_and_normalize_workflows, print_workflows

    # Automatic extraction and normalization
    workflows = extract_and_normalize_workflows("main.py")
    print_workflows(workflows)
"""
import os
import re
from collections import defaultdict
from pydantic import BaseModel, Field

# DATA MODELS
class WorkflowPath(BaseModel):
    """Simple workflow path representation."""
    normalized_path: str = Field(description="Path with Kleene star (*) notation")
    variant_count: int = Field(description="Number of path variants this represents")


# STEP 1: EXTRACT GRAPH STRUCTURE FROM CODE
def extract_graph_from_code(file_path: str) -> dict:
    """Extract graph structure by parsing Python code.

    Args:
        file_path: Path to main.py

    Returns:
        Dictionary with adjacency list representation
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    graph = defaultdict(list)

    # Extract direct edges: builder.add_edge(START, "supervisor")
    edge_pattern = r'builder\.add_edge\((["\']?\w+["\']?)\s*,\s*(["\']?\w+["\']?)\)'
    edges = re.findall(edge_pattern, code)

    for src, tgt in edges:
        src = src.strip('"\'')
        tgt = tgt.strip('"\'')
        graph[src].append(tgt)

    # Extract conditional edges: builder.add_conditional_edges("source", func, {...})
    conditional_pattern = r'builder\.add_conditional_edges\s*\(\s*["\'](\w+)["\'][^{]*\{([^}]+)\}'
    conditional_matches = re.findall(conditional_pattern, code, re.DOTALL)

    for source, targets_str in conditional_matches:
        target_pattern = r'["\'](\w+)["\']\s*:\s*["\']?(\w+)["\']?'
        targets = re.findall(target_pattern, targets_str)

        for _, target in targets:
            if target:
                normalized_target = "END" if target == "END" else target
                graph[source].append(normalized_target)

    return graph


# STEP 2: FIND ALL PATHS USING DFS
def find_all_paths(graph: dict, start: str = "START", end: str = "END") -> list[list[str]]:
    """Find all possible paths from start to end using DFS.

    Args:
        graph: Adjacency list representation
        start: Starting node
        end: Ending node

    Returns:
        List of paths (each path is a list of node names)
    """
    all_paths = []

    def dfs(current: str, path: list[str], visited: set[str]):
        if len(path) > 20:  # Prevent infinite loops
            return

        if current == end:
            all_paths.append(path.copy())
            return

        next_nodes = graph.get(current, [])

        for next_node in next_nodes:
            # Allow self-loops once (for human feedback)
            if next_node not in visited or (next_node == current and path.count(current) < 2):
                new_visited = visited.copy()
                if next_node != current:
                    new_visited.add(next_node)

                path.append(next_node)
                dfs(next_node, path, new_visited)
                path.pop()

    dfs(start, [start], {start})
    return all_paths


# STEP 3: NORMALIZE PATHS WITH KLEENE STAR
def normalize_path_with_kleene(path: list[str]) -> str:
    """Convert a path with self-loops to Kleene star notation.

    Args:
        path: List of node names

    Returns:
        String representation using Kleene star for repeated nodes

    Example:
        ["START", "supervisor", "supervisor", "policy", "END"]
        -> "START -> supervisor* -> policy -> END"
    """
    if not path:
        return ""

    normalized = []
    i = 0

    while i < len(path):
        current = path[i]

        # Check if next node is the same (self-loop)
        if i + 1 < len(path) and path[i + 1] == current:
            normalized.append(f"{current}*")
            # Skip all consecutive occurrences
            while i < len(path) and path[i] == current:
                i += 1
        else:
            normalized.append(current)
            i += 1

    return " -> ".join(normalized)


def group_paths_by_base(paths: list[list[str]]) -> dict[str, list[list[str]]]:
    """Group paths by their base structure (ignoring self-loops).

    Args:
        paths: List of paths

    Returns:
        Dictionary mapping base path to all variants
    """
    groups = defaultdict(list)

    for path in paths:
        # Create base path by removing consecutive duplicates
        base = []
        for i, node in enumerate(path):
            if i == 0 or node != path[i - 1]:
                base.append(node)

        base_key = " -> ".join(base)
        groups[base_key].append(path)

    return groups


# STEP 4: EXTRACT AND NORMALIZE WORKFLOWS
def extract_and_normalize_workflows(file_path: str) -> list[WorkflowPath]:
    """Complete pipeline: extract, normalize workflows.

    Args:
        file_path: Path to main.py

    Returns:
        List of WorkflowPath objects with normalized paths
    """
    # Step 1: Extract graph structure
    graph = extract_graph_from_code(file_path)

    # Step 2: Find all paths
    paths = find_all_paths(graph)

    # Step 3: Group and normalize
    groups = group_paths_by_base(paths)

    # Step 4: Create workflow path objects
    workflows = []
    for base_path, variants in groups.items():
        # Use the longest variant to get the normalized path with *
        normalized = normalize_path_with_kleene(max(variants, key=len))

        workflow = WorkflowPath(
            normalized_path=normalized,
            variant_count=len(variants)
        )
        workflows.append(workflow)

    return workflows


def save_workflows_to_json(workflows: list[WorkflowPath], output_path: str) -> None:
    """Save workflows to JSON file.

    Args:
        workflows: List of WorkflowPath objects
        output_path: Path to output JSON file
    """
    import json

    data = [wf.model_dump() for wf in workflows]

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(workflows)} workflow paths to {output_path}")

if __name__ == "__main__":
    import sys

    # Automatic extraction from main.py
    main_path = os.path.join(os.path.dirname(__file__), "main.py")

    print(" WORKFLOW EXTRACTION")
    print(f"\nExtracting from: {main_path}\n")

    # Extract and normalize workflows
    workflows = extract_and_normalize_workflows(main_path)

    # Save to files
    if len(sys.argv) > 1 and sys.argv[1] == "--save":
        print("="*80)
        print("SAVING WORKFLOWS")
        print("="*80 + "\n")

        output_dir = os.path.dirname(__file__)

        # Save to JSON
        json_path = os.path.join(output_dir, "workflows.json")
        save_workflows_to_json(workflows, json_path)