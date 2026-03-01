import json
from typing import Annotated, Optional, Dict, Any

import aiohttp
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.prebuilt import InjectedState
from langgraph.types import Command


@tool
async def slack_web_hook(
    url: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    state: Annotated[dict, InjectedState],
    body: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
) -> Command:
    """
    Performs a slack webhook HTTP POST operation.

    Call this tool to send POST requests to a Slack webhook URL

    :param url: The URL to send the POST request to
    :param body: Optional JSON body to send with the request (as a dictionary)
    :param headers: Optional HTTP headers to include (as a dictionary)
    :param timeout: Request timeout in seconds (default: 30)
    :return: Command with the HTTP response
    """

    if not url.startswith("https://hooks.slack.com"):
        error_message = f"Invalid Slack webhook URL: {url}. URL must start with 'https://hooks.slack.com'."
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=json.dumps({"error": error_message}),
                        tool_call_id=tool_call_id,
                        name="http_post"
                    ),
                ],
            }
        )

    if body is None:
        body = {}

    if headers is None:
        headers = {"Content-Type": "application/json"}
    elif "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=body,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                response_text = await response.text()

                # Try to parse as JSON, otherwise return as text
                try:
                    response_data = json.loads(response_text)
                    response_content = json.dumps({
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "body": response_data
                    }, indent=2)
                except json.JSONDecodeError:
                    response_content = json.dumps({
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "body": response_text
                    }, indent=2)

                success_message = f"HTTP POST request to {url} completed with status {response.status}"

                return Command(
                    update={
                        "messages": [
                            ToolMessage(
                                content=response_content,
                                tool_call_id=tool_call_id,
                                name="http_post"
                            ),
                        ],
                    }
                )

    except aiohttp.ClientError as e:
        error_message = f"HTTP POST request to {url} failed: {str(e)}"
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=json.dumps({"error": error_message}),
                        tool_call_id=tool_call_id,
                        name="http_post"
                    ),
                ],
            }
        )
    except Exception as e:
        error_message = f"Unexpected error during HTTP POST to {url}: {str(e)}"
        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=json.dumps({"error": error_message}),
                        tool_call_id=tool_call_id,
                        name="http_post"
                    ),
                ],
            }
        )

