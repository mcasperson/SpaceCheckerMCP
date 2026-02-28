import sys
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
    """Discards the list of deployments. Call this tool when the list of deployments is no longer needed to free up memory."""

    print("discard_deployments called", file=sys.stderr)

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

@tool
def discard_releases(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Discards the list of releases. Call this tool when the list of releases is no longer needed to free up memory."""

    print("discard_releases called", file=sys.stderr)

    def trim_release(release):
        if isinstance(release, ToolMessage) and release.name == "list_releases":
            release.name = "trimmed_list_releases"
            release.content = ""
        return release

    trim_messages = [trim_release(msg) for msg in state["messages"]]

    return Command(
        update={
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *trim_messages,
                ToolMessage(
                    "Discarded list of releases", tool_call_id=tool_call_id
                ),
            ],
        }
    )

@tool
def discard_projects(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Discards the list of projects. Call this tool when the list of projects is no longer needed to free up memory."""

    print("discard_projects called", file=sys.stderr)

    def trim_release(release):
        if isinstance(release, ToolMessage) and release.name == "list_projects":
            release.name = "trimmed_list_projects"
            release.content = ""
        return release

    trim_messages = [trim_release(msg) for msg in state["messages"]]

    return Command(
        update={
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *trim_messages,
                ToolMessage(
                    "Discarded list of projects", tool_call_id=tool_call_id
                ),
            ],
        }
    )

@tool
def discard_spaces(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Discards the list of spaces. Call this tool when the list of spaces is no longer needed to free up memory."""

    print("discard_spaces called", file=sys.stderr)

    def trim_release(release):
        if isinstance(release, ToolMessage) and release.name == "list_spaces":
            release.name = "trimmed_list_spaces"
            release.content = ""
        return release

    trim_messages = [trim_release(msg) for msg in state["messages"]]

    return Command(
        update={
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *trim_messages,
                ToolMessage(
                    "Discarded list of spaces", tool_call_id=tool_call_id
                ),
            ],
        }
    )

@tool
def discard_environments(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Discards the list of environments. Call this tool when the list of spaces is no longer needed to free up memory."""

    print("discard_environments called", file=sys.stderr)

    def trim_release(release):
        if isinstance(release, ToolMessage) and release.name == "list_environments":
            release.name = "trimmed_list_environments"
            release.content = ""
        return release

    trim_messages = [trim_release(msg) for msg in state["messages"]]

    return Command(
        update={
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *trim_messages,
                ToolMessage(
                    "Discarded list of environments", tool_call_id=tool_call_id
                ),
            ],
        }
    )