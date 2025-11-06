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
import asyncio
from collections import defaultdict
from pydantic import BaseModel, Field

# DATA MODELS
class WorkflowPath(BaseModel):
    """Workflow path with input requirements."""
    normalized_path: str = Field(description="Path with Kleene star (*) notation")
    variant_count: int = Field(description="Number of path variants this represents")
    required_input: str = Field(default="", description="What input is needed to trigger this workflow")
    example_query: str = Field(default="", description="Example user query that would trigger this workflow")
    recommended_evaluator: str = Field(default="", description="Best evaluator type for this workflow")
    evaluator_rationale: str = Field(default="", description="Why this evaluator is recommended")


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


# STEP 4: LLM ANALYSIS FOR INPUT REQUIREMENTS AND EVALUATOR RECOMMENDATION
async def analyze_workflow_input(normalized_path: str) -> tuple[str, str, str, str]:
    """Use LLM to determine what input triggers this workflow path and recommend evaluator.

    Args:
        normalized_path: The workflow path with Kleene star notation

    Returns:
        Tuple of (required_input_json, example_query, recommended_evaluator, evaluator_rationale)
    """
    from uipath_langchain.chat.models import UiPathAzureChatOpenAI

    llm = UiPathAzureChatOpenAI()

    prompt = f"""Analyze this workflow execution path and provide comprehensive testing recommendations:

Workflow Path: {normalized_path}

The agent accepts input following this JSON schema:
{{
    "question": "<string>",  // REQUIRED: The user's question
    "category": "<string>",  // Optional: Category hint (policy/procurement/hr)
    "human_feedback": "<string>",  // Optional: Human feedback for supervisor
    "email": "<string>",  // Optional: User email (required for procurement/hr)
    "code": "<string>"  // Optional: 4-digit code (required for procurement)
}}

Available UiPath Evaluators:
1. LLMJudgeTrajectoryEvaluator - Evaluates entire execution path through the graph
2. LLMJudgeOutputEvaluator - Evaluates final output quality
3. ExactMatchEvaluator - Checks for exact match between output and expected
4. ContainsEvaluator - Checks if output contains expected text
5. JsonSimilarityEvaluator - Compares JSON outputs for similarity
6. ToolCallOrderEvaluator - Checks order of tool calls
7. ToolCallArgsEvaluator - Evaluates tool call arguments
8. ToolCallCountEvaluator - Counts tool calls
9. ToolCallOutputEvaluator - Evaluates tool call outputs

Based on the workflow path, determine:
1. What input fields are needed to trigger this specific workflow
2. Provide an example JSON input that would trigger this workflow
3. Which evaluator(s) would be BEST for testing this workflow
4. Why that evaluator is the best choice

Respond in this exact format:
REQUIRED_INPUT: {{JSON object showing which fields are needed}}
EXAMPLE_INPUT: {{Complete JSON example that would trigger this workflow}}
RECOMMENDED_EVALUATOR: <evaluator name>
EVALUATOR_RATIONALE: <1-2 sentences explaining why>

Note: supervisor* means the supervisor node may loop for human-in-the-loop feedback when confidence < 50%.
"""

    try:
        response = await llm.ainvoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)

        # Parse the response
        required_input = ""
        example_input = ""
        recommended_evaluator = ""
        evaluator_rationale = ""

        lines = response_text.split('\n')
        for i, line in enumerate(lines):
            if 'REQUIRED_INPUT:' in line:
                start_idx = i
                required_parts = []
                for j in range(start_idx, len(lines)):
                    if any(keyword in lines[j] for keyword in ['EXAMPLE_INPUT:', 'RECOMMENDED_EVALUATOR:', 'EVALUATOR_RATIONALE:']):
                        break
                    required_parts.append(lines[j].replace('REQUIRED_INPUT:', '').strip())
                required_input = ' '.join(required_parts).strip()

            if 'EXAMPLE_INPUT:' in line:
                start_idx = i
                example_parts = []
                for j in range(start_idx, len(lines)):
                    if any(keyword in lines[j] for keyword in ['RECOMMENDED_EVALUATOR:', 'EVALUATOR_RATIONALE:']):
                        break
                    example_parts.append(lines[j].replace('EXAMPLE_INPUT:', '').strip())
                example_input = ' '.join(example_parts).strip()

            if 'RECOMMENDED_EVALUATOR:' in line:
                recommended_evaluator = line.replace('RECOMMENDED_EVALUATOR:', '').strip()

            if 'EVALUATOR_RATIONALE:' in line:
                start_idx = i
                rationale_parts = []
                for j in range(start_idx, len(lines)):
                    rationale_parts.append(lines[j].replace('EVALUATOR_RATIONALE:', '').strip())
                evaluator_rationale = ' '.join(rationale_parts).strip()

        return (
            required_input or "Analysis incomplete",
            example_input or "{}",
            recommended_evaluator or "LLMJudgeTrajectoryEvaluator",
            evaluator_rationale or "Default trajectory evaluator"
        )

    except Exception as e:
        print(f"WARNING: LLM analysis failed for path '{normalized_path}': {e}")
        import traceback
        traceback.print_exc()
        return "Analysis failed", "{}", "LLMJudgeTrajectoryEvaluator", "Fallback evaluator"


async def analyze_workflows_with_llm_async(workflows: list[WorkflowPath]) -> list[WorkflowPath]:
    """Analyze all workflows with LLM to determine input requirements and evaluators (async).

    Args:
        workflows: List of WorkflowPath objects

    Returns:
        Updated list of WorkflowPath objects with input analysis and evaluator recommendations
    """
    print("Analyzing workflows with LLM to determine input requirements and evaluators...")

    # Analyze each workflow
    updated_workflows = []
    for i, wf in enumerate(workflows, 1):
        print(f"  Analyzing workflow {i}/{len(workflows)}: {wf.normalized_path}")

        required_input, example_query, recommended_evaluator, evaluator_rationale = await analyze_workflow_input(wf.normalized_path)

        # Create updated workflow with input analysis and evaluator recommendation
        updated_wf = WorkflowPath(
            normalized_path=wf.normalized_path,
            variant_count=wf.variant_count,
            required_input=required_input,
            example_query=example_query,
            recommended_evaluator=recommended_evaluator,
            evaluator_rationale=evaluator_rationale
        )
        updated_workflows.append(updated_wf)

    print("LLM analysis complete!")
    return updated_workflows


def analyze_workflows_with_llm(workflows: list[WorkflowPath]) -> list[WorkflowPath]:
    """Analyze all workflows with LLM (sync wrapper).

    Args:
        workflows: List of WorkflowPath objects

    Returns:
        Updated list of WorkflowPath objects with input analysis
    """
    return asyncio.run(analyze_workflows_with_llm_async(workflows))


# STEP 5: EXTRACT AND NORMALIZE WORKFLOWS
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

    print("=" * 80)
    print("WORKFLOW EXTRACTION")
    print("=" * 80)
    print(f"\nExtracting from: {main_path}\n")

    # Extract and normalize workflows
    workflows = extract_and_normalize_workflows(main_path)
    print(f"Found {len(workflows)} workflow paths\n")

    # Save to files
    if len(sys.argv) > 1 and sys.argv[1] == "--save":
        print("="*80)
        print("ANALYZING WITH LLM & SAVING WORKFLOWS")
        print("="*80 + "\n")

        # Analyze workflows with LLM to determine input requirements
        workflows = analyze_workflows_with_llm(workflows)

        output_dir = os.path.dirname(__file__)

        # Save to JSON
        json_path = os.path.join(output_dir, "workflows.json")
        save_workflows_to_json(workflows, json_path)