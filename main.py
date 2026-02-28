import argparse
import asyncio
import os
import re
import sys
from datetime import timedelta

import wrapt
from langchain_core.messages.human import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain.agents import create_agent
from purgatory import AsyncCircuitBreakerFactory
from ratelimit import limits
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, before_sleep_log
import logging

from tools import discard_deployments, discard_projects, discard_releases, discard_spaces, discard_environments

# Configure logging for retry messages
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

circuitbreaker = AsyncCircuitBreakerFactory(default_threshold=3)

@wrapt.patch_function_wrapper("langchain_core.tools", "StructuredTool.ainvoke")
@circuitbreaker("StructuredTool.ainvoke")
async def structuredtool_ainvoke(wrapped, instance, args, kwargs):
    return await wrapped(*args, **kwargs)

@wrapt.patch_function_wrapper("langchain_core.tools", "StructuredTool.ainvoke")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(3),
    retry=retry_if_exception_type(Exception),
)
@limits(calls=1, period=2)
async def structuredtool_ainvoke(wrapped, instance, args, kwargs):
    print("StructuredTool.ainvoke called", file=sys.stderr)
    return await wrapped(*args, **kwargs)

def remove_line_padding(text):
    """
    Remove leading and trailing whitespace from each line in the text.
    :param text: The text to process.
    :return: The text with leading and trailing whitespace removed from each line.
    """
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def remove_thinking(text):
    """
    Remove <think>...</think> tags and their content from the text.
    :param text: The text to process.
    :return: The text with <think>...</think> tags and their content removed.
    """
    stripped_text = text.strip()
    if stripped_text.startswith("<think>") and "</think>" in stripped_text:
        return re.sub(r"<think>.*?</think>", "", stripped_text, flags=re.DOTALL)
    return stripped_text


def response_to_text(response):
    """
    Extract the content from the last message in the response.
    :param response: The response dictionary containing messages.
    :return: The content of the last message, or an empty string if no messages are present.
    """
    messages = response.get("messages", [])
    if not messages or len(messages) == 0:
        return ""
    return messages.pop().content


async def main(message: str):
    """
    The entrypoint to our AI agent.
    :param message: The message/prompt to send to the agent.
    """
    client = MultiServerMCPClient(
        {
            "octopus": {
                "command": "npx",
                "args": [
                    "-y",
                    "@octopusdeploy/mcp-server",
                    "--api-key",
                    os.getenv("OCTOPUS_CLI_API_KEY"),
                    "--server-url",
                    os.getenv("OCTOPUS_CLI_SERVER"),
                ],
                "transport": "stdio",
                "session_kwargs": {"read_timeout_seconds": timedelta(seconds=60)}
            }
        }
    )

    # Use an Azure AI model
    llm = AzureAIChatCompletionsModel(
        # The URL that ends in /models from the Overview page
        endpoint=os.getenv("AZURE_AI_URL"),
        credential=os.getenv("AZURE_AI_APIKEY"),
        model="gpt-5-mini",
    )

    tools = await client.get_tools()
    tools.append(discard_deployments)
    tools.append(discard_projects)
    tools.append(discard_releases)
    tools.append(discard_spaces)
    tools.append(discard_environments)
    agent = create_agent(llm, tools)
    response = await agent.ainvoke(
        {
            "messages": remove_line_padding(message)
        }
    )
    print(remove_thinking(response_to_text(response)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SpaceChecker MCP - Check Octopus Deploy deployment statuses"
    )
    parser.add_argument(
        "-m", "--message",
        type=str,
        help="The message/prompt to send to the agent",
        default="""
                In Octopus, get all the projects from the "Easy Mode" space.
                In Octopus, for each project, get the latest deployment to each environment and its status.
                If the deployment failed, output the project name, environment name, and deployment status like this:
                <URL to the deployment> - <Project Name> - <Environment Name>
                You will be penalized for reporting on deployments that were successful with warnings.
                You must discard any information about deployments after reporting on them to avoid memory issues. 
                Use the provided tools to discard deployments, projects, releases, spaces, and environments when they are no longer needed.
                """
    )

    args = parser.parse_args()
    asyncio.run(main(args.message))
