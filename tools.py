import json
import sys
from typing import Annotated

from langchain_core.messages import ToolMessage, RemoveMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

@tool
def condense_deployments(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Condenses the list of deployments. Call this to free up memory when only the Deployment IDs and Names are required."""

    print("condense_deployments called", file=sys.stderr)

    trim_messages = condense_content(state, "list_deployments")

    return Command(
        update={
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *trim_messages,
                ToolMessage(
                    "Condensed list of deployments", tool_call_id=tool_call_id
                ),
            ],
        }
    )

@tool
def condense_releases(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Condenses the list of releases. Call this to free up memory when only the Release IDs and Names are required."""

    print("condense_releases called", file=sys.stderr)

    trim_messages = condense_content(state, "list_releases")

    return Command(
        update={
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *trim_messages,
                ToolMessage(
                    "Condensed list of releases", tool_call_id=tool_call_id
                ),
            ],
        }
    )

@tool
def condense_projects(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Condenses the list of environments. Call this to free up memory when only the Project IDs and Names are required."""

    print("condense_projects called", file=sys.stderr)

    trim_messages = condense_content(state, "list_projects")

    return Command(
        update={
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *trim_messages,
                ToolMessage(
                    "Condensed list of projects", tool_call_id=tool_call_id
                ),
            ],
        }
    )

@tool
def condense_spaces(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Condenses the list of spaces. Call this to free up memory when only the Space IDs and Names are required."""

    print("condense_spaces called", file=sys.stderr)

    trim_messages = condense_content(state, "list_spaces")

    return Command(
        update={
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *trim_messages,
                ToolMessage(
                    "Condensed list of spaces", tool_call_id=tool_call_id
                ),
            ],
        }
    )

@tool
def condense_environments(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Condenses the list of environments. Call this to free up memory when only the Environment IDs and Names are required."""

    print("condense_environments called", file=sys.stderr)

    trim_messages = condense_content(state, "list_environments")

    return Command(
        update={
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *trim_messages,
                ToolMessage(
                    "Condensed list of environments", tool_call_id=tool_call_id
                ),
            ],
        }
    )

def condense_content(state: Annotated[dict, InjectedState], tool_name) -> list:
    def name_and_id_only(result):
        if not result:
            return "[]"
        content_json = json.loads(result)
        condensed_json = list([{"id": item["id"], "name": item["name"]} for item in content_json.get("items", [])])
        return json.dumps(condensed_json)

    def trim_release(release):
        if isinstance(release, ToolMessage) and release.name == tool_name:
            release.name = "condensed_" + tool_name
            for content in release.content:
                content.text = name_and_id_only(content.get("text"))
        return release

    return [trim_release(msg) for msg in state["messages"]]