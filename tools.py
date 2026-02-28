from typing import Annotated

from langchain_core.messages import ToolMessage, RemoveMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.prebuilt import InjectedState
from langgraph.types import Command


@tool
def discard_deployments(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Discards the list of deployments."""

    def trim_release(release):
        if isinstance(release, ToolMessage) and release.name == "list_deployments":
            release.name = "trimmed_list_deployments"
            release.content = ""
        return release

    trim_messages = [trim_release(msg) for msg in state["messages"]]

    return Command(
        update={
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *trim_messages,
                ToolMessage(
                    "Discarded list of deployments", tool_call_id=tool_call_id
                ),
            ],
        }
    )