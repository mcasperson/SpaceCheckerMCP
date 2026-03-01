import json
from typing import Annotated

from langchain_core.messages import ToolMessage, RemoveMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

@tool
def condense_tasks(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Condenses the details of tasks. Call this to free up memory when only the task IDs, Names, and states are required."""

    def name_and_id_only(result):
        if not result:
            return "{}"
        content_json = json.loads(result)
        normalized_dict = {k.casefold(): v for k, v in content_json.items()}
        return json.dumps({"id": normalized_dict.get("id"), "name": normalized_dict.get("name"), "state": normalized_dict.get("state")})

    def task_name_and_id_only(result):
        if not result:
            return "{}"
        content_json = json.loads(result).get("Task", {})
        normalized_dict = {k.casefold(): v for k, v in content_json.items()}
        return json.dumps({"id": normalized_dict.get("id"), "name": normalized_dict.get("name"),
                           "state": normalized_dict.get("state")})

    def trim_release(release):
        if isinstance(release, ToolMessage):
            if release.name == "get_task_by_id":
                release.name = "condensed_get_task_by_id"
                for content in release.content:
                    content["text"] = name_and_id_only(content.get("text"))

            if release.name == "get_task_details":
                release.name = "condensed_get_task_details"
                for content in release.content:
                    content["text"] = task_name_and_id_only(content.get("text"))
        return release

    trim_messages = [trim_release(msg) for msg in state["messages"]]

    return Command(
        update={
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *trim_messages,
                ToolMessage(
                    "Condensed list of tasks", tool_call_id=tool_call_id
                ),
            ],
        }
    )

@tool
def condense_deployments(
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
) -> Command:
    """Condenses the list of deployments. Call this to free up memory when only the Deployment IDs, Names, EnvironmentIds, ProjectIds, nd TaskIds are required."""

    trim_messages = condense_content(state, "list_deployments", additional_keys=["taskId", "projectId", "environmentId"])

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

def condense_content(state: Annotated[dict, InjectedState], tool_name, additional_keys=None) -> list:
    """
    Condense content to include only id, name, and optionally additional specified keys.

    :param state: The state dictionary containing messages
    :param tool_name: The name of the tool to condense
    :param additional_keys: Optional list of additional keys to include (e.g., ['taskId', 'projectId'])
    :return: List of trimmed messages
    """
    if additional_keys is None:
        additional_keys = []

    def name_and_id_only(result):
        if not result:
            return "[]"
        content_json = json.loads(result)
        normalized_items = [{k.casefold(): v for k, v in item.items()} for item in content_json.get("items", [])]

        # Build condensed dict with id, name, and any additional keys
        condensed_json = []
        for item in normalized_items:
            condensed_item = {
                "id": item.get("id"),
                "name": item.get("name")
            }
            # Add any additional keys requested
            for key in additional_keys:
                key_lower = key.casefold()
                if key_lower in item:
                    condensed_item[key] = item.get(key_lower)
            condensed_json.append(condensed_item)

        return json.dumps(condensed_json)

    def trim_release(release):
        if isinstance(release, ToolMessage) and release.name == tool_name:
            release.name = "condensed_" + tool_name
            for content in release.content:
                content["text"] = name_and_id_only(content.get("text"))
        return release

    return [trim_release(msg) for msg in state["messages"]]