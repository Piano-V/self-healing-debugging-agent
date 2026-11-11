import os
from langgraph.graph import END, START, StateGraph
from nodes import programmer_agent_node, test_runner_node
from state import AgentState


def route_after_test_run(state: AgentState) -> str:
    """Adaptive routing function that acts as a dynamic guardrail.

    Determines whether to continue debugging, end on success, or end early
    based on stagnation detection (repeating code or unchanged test errors)
    and iteration limits.
    """
    current_status = state.get("status")
    iterations = state.get("iteration_count", 0)
    max_limit = state.get("max_iterations") or int(os.environ.get("MAX_DEBUG_ITERATIONS", 5))

    # 1. Success condition: All unit tests passed
    if current_status == "success":
        print("\n[Router] >>> SUCCESS: All unit tests passed! Routing to END.")
        return END

    # 2. Hard iteration limit ceiling
    if iterations >= max_limit:
        print(
            f"\n[Router] >>> TERMINATED: Reached safety iteration limit ({iterations}/{max_limit}) with failing tests. Routing to END."
        )
        return END

    # 3. Adaptive Stagnation Detection (Active after at least 1 programmer iteration)
    if iterations > 0:
        current_code = state.get("code_content", "").strip()
        prev_code = state.get("previous_code", "").strip()
        curr_sig = state.get("error_signature", "").strip()
        prev_sig = state.get("previous_error_signature", "").strip()

        # Check if the programmer generated identical code without changes
        if prev_code and current_code == prev_code:
            print(
                f"\n[Router] >>> STAGNATION DETECTED: Programmer agent returned identical code without changes at iteration {iterations}. Routing to END."
            )
            return END

        # Check if test failures are completely identical across iterations
        if prev_sig and curr_sig and curr_sig == prev_sig:
            print(
                f"\n[Router] >>> STAGNATION DETECTED: Test failure signature did not improve at iteration {iterations}. Repeating the same error. Routing to END."
            )
            return END

    passed_count = state.get("passed_count", 0)
    failed_count = state.get("failed_count", 0)
    print(
        f"\n[Router] >>> IN PROGRESS: Tests failing ({passed_count} passed, {failed_count} failed) at iteration {iterations}/{max_limit}. Routing to programmer_agent."
    )
    return "programmer_agent"


# Build the Graph Workflow
builder = StateGraph(AgentState)

# 1. Register nodes
builder.add_node("test_runner", test_runner_node)
builder.add_node("programmer_agent", programmer_agent_node)

# 2. Establish connections
builder.add_edge(START, "test_runner")

# 3. Establish cyclic conditional edge from test_runner node
builder.add_conditional_edges(
    "test_runner",
    route_after_test_run,
    {
        "programmer_agent": "programmer_agent",
        END: END,
    },
)

# 4. Connect programmer back to test runner to verify fixes
builder.add_edge("programmer_agent", "test_runner")

# Compile the execution graph
graph = builder.compile()


def generate_visualization():
    """Generates and saves the graph architecture visualization."""
    # Attempt to output PNG diagram of compiled graph using Mermaid
    try:
        png_data = graph.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as f:
            f.write(png_data)
        print("Graph diagram successfully generated and saved to: graph.png")
    except Exception as e:
        print(
            f"Note: Could not generate graph.png natively (needs pygraphviz/mermaid dependencies): {e}"
        )

    # Save raw Mermaid text fallback so the user can easily render it in markdown
    try:
        mermaid_markup = graph.get_graph().draw_mermaid()
        with open("graph.mermaid", "w", encoding="utf-8") as f:
            f.write(mermaid_markup)
        print(
            "Graph raw Mermaid structure saved to: graph.mermaid (Open in any Mermaid viewer)"
        )
    except Exception as e:
        print(f"Could not write graph.mermaid representation: {e}")


if __name__ == "__main__":
    print("====================================================")
    print("  Stateful Multi-Agent Debugger (LangGraph System)   ")
    print("====================================================\n")

    # Generate graph documentation assets
    generate_visualization()

    # Check if target_code.py and test_suite.py exist in the current working directory
    target_file = "target_code.py"
    test_file = "test_suite.py"

    use_files = os.path.exists(target_file) and os.path.exists(test_file)

    if use_files:
        print(f"[CLI] Found target files on disk: '{target_file}' and '{test_file}'")
        print("Ingesting contents...")
        with open(target_file, "r", encoding="utf-8") as f:
            code_content = f.read()
        with open(test_file, "r", encoding="utf-8") as f:
            test_suite_code = f.read()
    else:
        print(f"[CLI] '{target_file}' or '{test_file}' not found in the current directory.")
        print("Falling back to the self-contained Fibonacci demo...\n")

        # Define a buggy Fibonacci calculator function to test
        code_content = """def fibonacci(n: int) -> int:
    \"\"\"Calculates the n-th Fibonacci number.
    Contains bugs: bad base cases and bad indices.
    \"\"\"
    if n == 0:
        return 0
    elif n == 1:
        return 1
    # BUG: recursive step has (n-3) instead of (n-2)
    return fibonacci(n - 1) + fibonacci(n - 3)
"""

        # Define the corresponding correct test suite
        test_suite_code = """from target_code import fibonacci

def test_fibonacci_base():
    assert fibonacci(0) == 0
    assert fibonacci(1) == 1

def test_fibonacci_values():
    assert fibonacci(2) == 1
    assert fibonacci(3) == 2
    assert fibonacci(4) == 3
    assert fibonacci(5) == 5
    assert fibonacci(6) == 8
"""

    # Initialize Graph State
    initial_state = {
        "code_content": code_content,
        "test_suite_code": test_suite_code,
        "test_logs": "",
        "iteration_count": 0,
        "max_iterations": int(os.environ.get("MAX_DEBUG_ITERATIONS", 5)),
        "passed_count": 0,
        "failed_count": 0,
        "previous_code": "",
        "error_signature": "",
        "previous_error_signature": "",
        "status": "pending",
    }

    # Verify model configuration
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not gemini_key and not openai_key:
        print("\n[WARNING] Neither GEMINI_API_KEY nor OPENAI_API_KEY detected.")
        print(
            "Graph will run but LLM invocations will fail unless API keys are set."
        )
        print("Set API keys using: export GEMINI_API_KEY='your_key'")

    print("\nStarting agent workflow execution...\n")

    # Run the compiled graph with the initial state inputs
    final_output = graph.invoke(initial_state)

    print("\n====================================================")
    print("                  FINAL GRAPH STATE                 ")
    print("====================================================")
    print(f"Execution Status: {final_output.get('status')}")
    print(f"Total Iterations: {final_output.get('iteration_count')}")
    print("\n--- FINAL CODE ---")
    print(final_output.get("code_content"))

    # If successfully corrected external files, save the result to a new file
    if use_files and final_output.get("status") == "success":
        output_file = "fixed_target_code.py"
        print(f"\n[CLI] Success! Saving the corrected code to '{output_file}'...")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_output.get("code_content"))
        print(f"[CLI] File saved successfully as '{output_file}'.")
    print("====================================================")
