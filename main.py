import argparse
import asyncio
import logging
import os
import re
import sys
from datetime import timedelta

import wrapt
from langchain.agents import create_agent
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_mcp_adapters.client import MultiServerMCPClient
from purgatory import AsyncCircuitBreakerFactory
from ratelimit import limits
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from tools import condense_deployments, condense_projects, condense_releases, condense_spaces, condense_environments

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
    tools.append(condense_deployments)
    tools.append(condense_projects)
    tools.append(condense_releases)
    tools.append(condense_spaces)
    tools.append(condense_environments)
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
                If there are no failed deployments, output "No failed deployments".
                You will be penalized for providing additional instructions.
                You will be penalized for reporting on deployments that were successful with warnings.
                You must condense any information about deployments, projects, releases, spaces, and environments after reporting on them to avoid memory issues. 
                Be aggressive with condensing information, and call the condense tools when only the name and ID of resources that were just accessed are required.
                """
    )

    args = parser.parse_args()
    asyncio.run(main(args.message))
