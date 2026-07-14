from typing import TypedDict
from pydantic import BaseModel, Field


class AgentState(TypedDict):
    """State definition for the autonomous code-debugging LangGraph.

    Tracks code content, test suite, test results, loop counts, and overall status.
    """

    code_content: str
    """The current content of the target Python file being debugged."""

    test_suite_code: str
    """The pytest suite code that runs against the code_content."""

    test_logs: str
    """The stdout/stderr logs from the latest pytest run, including traceback."""

    iteration_count: int
    """The count of debugging cycles completed (maximum is 3)."""

    status: str
    """Status indicating the workflow state (e.g., 'success', 'failed', 'max_iterations_reached')."""


class CodePatch(BaseModel):
    """Pydantic schema for structured code patches from the Programmer Agent.

    Enforces that the model returns both a textual rationale and the modified code.
    """

    explanation: str = Field(
        ...,
        description="Explanation of the bugs identified and why the proposed code patch resolves them.",
    )

    patched_code: str = Field(
        ...,
        description=(
            "The full source code of the file including the fix. Must be valid"
            " Python code without backticks or markdown formatting."
        ),
    )
