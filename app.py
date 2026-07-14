import os
import streamlit as st
from graph import graph

st.set_page_config(
    page_title="Self-Healing Debugging Agent", layout="wide"
)

st.title("Autonomous Self-Healing Code Debugging Agent")
st.markdown(
    "A stateful multi-agent system built with LangGraph, Pydantic v2, and pytest "
    "that repairs Python bugs by validating changes through dynamic execution feedback."
)

# Sidebar setup for configuration
st.sidebar.header("Configuration")

# API Keys and Model Configuration
api_provider = st.sidebar.selectbox(
    "LLM Provider", ["Google Gemini", "Local Model (Ollama)", "OpenAI"]
)

# Configure environment variables dynamically based on user inputs
if api_provider == "Google Gemini":
    has_env_key = bool(os.environ.get("GEMINI_API_KEY"))
    placeholder_text = "API Key loaded from secrets" if has_env_key else "Enter Gemini API Key..."
    gemini_key = st.sidebar.text_input(
        "Gemini API Key",
        type="password",
        placeholder=placeholder_text,
        help="If configured in deployment secrets, you can leave this field empty."
    )
    gemini_model = st.sidebar.text_input(
        "Gemini Model", value=os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
    )
    
    # Only override if the user entered a custom key
    if gemini_key:
        os.environ["GEMINI_API_KEY"] = gemini_key
    os.environ["GEMINI_MODEL"] = gemini_model
    os.environ["USE_LOCAL_FALLBACK"] = ""

elif api_provider == "Local Model (Ollama)":
    local_model = st.sidebar.text_input(
        "Ollama Model Name",
        value=os.environ.get("LOCAL_MODEL", "qwen2.5-coder:1.5b"),
    )
    os.environ["USE_LOCAL_FALLBACK"] = "true"
    os.environ["LOCAL_MODEL"] = local_model

elif api_provider == "OpenAI":
    has_env_key = bool(os.environ.get("OPENAI_API_KEY"))
    placeholder_text = "API Key loaded from secrets" if has_env_key else "Enter OpenAI API Key..."
    openai_key = st.sidebar.text_input(
        "OpenAI API Key",
        type="password",
        placeholder=placeholder_text,
        help="If configured in deployment secrets, you can leave this field empty."
    )
    openai_model = st.sidebar.text_input(
        "OpenAI Model", value=os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    )
    
    # Only override if the user entered a custom key
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    os.environ["OPENAI_MODEL"] = openai_model
    os.environ["USE_LOCAL_FALLBACK"] = ""

# Demo setup buttons
st.sidebar.markdown("---")
st.sidebar.subheader("Demo Presets")

demo_selection = st.sidebar.selectbox(
    "Select Preset Buggy Code",
    [
        "Merge Intervals (LeetCode Medium)",
        "Fibonacci Sequence (Recursion Bug)",
        "Custom Code",
    ],
)

# Set presets
if demo_selection == "Merge Intervals (LeetCode Medium)":
    default_code = """def merge_intervals(intervals: list[list[int]]) -> list[list[int]]:
    \"\"\"Merges all overlapping intervals in a list and returns the merged list.
    \"\"\"
    if not intervals:
        return []

    merged = []
    current = intervals[0]
    for next_int in intervals[1:]:
        # BUG: Strict < fails boundary merges, missing sort step fails out-of-order inputs
        if next_int[0] < current[1]:
            current[1] = max(current[1], next_int[1])
        else:
            merged.append(current)
            current = next_int

    merged.append(current)
    return merged
"""
    default_tests = """from target_code import merge_intervals

def test_boundary_touching_merge():
    # [1, 2] and [2, 3] should merge to [1, 3]
    assert merge_intervals([[1, 2], [2, 3]]) == [[1, 3]]

def test_unsorted_intervals():
    # Requires sorting first to merge correctly
    assert merge_intervals([[8, 10], [1, 3], [2, 6], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
"""
elif demo_selection == "Fibonacci Sequence (Recursion Bug)":
    default_code = """def fibonacci(n: int) -> int:
    \"\"\"Calculates the n-th Fibonacci number.
    \"\"\"
    if n == 0:
        return 0
    elif n == 1:
        return 1
    # BUG: uses (n-3) which causes stack overflow / negative numbers
    return fibonacci(n - 1) + fibonacci(n - 3)
"""
    default_tests = """from target_code import fibonacci

def test_fibonacci_values():
    assert fibonacci(5) == 5
    assert fibonacci(6) == 8
"""
else:
    default_code = ""
    default_tests = ""

# Main Content layout
col1, col2 = st.columns(2)

with col1:
    st.subheader("Target Code (target_code.py)")
    code_input = st.text_area(
        "Paste the buggy Python code here:",
        value=default_code,
        height=350,
        help="The python file under test containing the logical or syntactic bug.",
    )

with col2:
    st.subheader("Test Suite (test_suite.py)")
    test_input = st.text_area(
        "Paste pytest unit tests here:",
        value=default_tests,
        height=350,
        help="pytest assertions that will run against the target code.",
    )

# Execution Action
if st.button("Start Self-Healing Loop", use_container_width=True):
    if not code_input.strip() or not test_input.strip():
        st.error("Please supply both target code and unit tests.")
    else:
        # Prepare initial state
        initial_state = {
            "code_content": code_input,
            "test_suite_code": test_input,
            "test_logs": "",
            "iteration_count": 0,
            "status": "pending",
        }

        # Stream the graph execution events in real-time
        try:
            # Using Streamlit's professional st.status container
            with st.status("Orchestrating agent execution workflow...", expanded=True) as status_box:
                for event in graph.stream(initial_state):
                    for node, output in event.items():
                        status_box.write(f"Executing Node: **{node}**")
                        if "status" in output:
                            status_box.write(f"- Test runner status: `{output['status'].upper()}`")
                        if "iteration_count" in output:
                            status_box.write(f"- Completed iteration: `{output['iteration_count']}/3`")
                
                # Fetch final state
                final_state = graph.invoke(initial_state)
                
                # Update status component on completion
                if final_state.get("status") == "success":
                    status_box.update(label="Self-healing completed successfully", state="complete")
                else:
                    status_box.update(label="Self-healing completed with failures", state="error")

            # Columns for final results
            res_col1, res_col2 = st.columns(2)

            with res_col1:
                st.subheader("Final Repaired Code")
                st.code(final_state.get("code_content"), language="python")

            with res_col2:
                st.subheader("Summary Statistics")
                status = final_state.get("status")
                if status == "success":
                    st.metric(label="Workflow Status", value="PASSED")
                    st.success("The agent successfully compiled and fixed all tests.")
                else:
                    st.metric(label="Workflow Status", value="FAILED")
                    st.error("The agent reached the execution limit without passing all tests.")

                st.metric(
                    label="Total Debugging Attempts",
                    value=f"{final_state.get('iteration_count')} / 3",
                )

        except Exception as e:
            st.error(f"Execution Error: {e}")
