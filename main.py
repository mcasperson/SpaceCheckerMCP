import asyncio
import os
import re
from datetime import timedelta

import wrapt
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain.agents import create_agent
from purgatory import AsyncCircuitBreakerFactory
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from tools import discard_deployments

circuitbreaker = AsyncCircuitBreakerFactory(default_threshold=3)

@wrapt.patch_function_wrapper("langchain_core.tools", "StructuredTool.ainvoke")
@circuitbreaker("StructuredTool.ainvoke")
async def structuredtool_ainvoke(wrapped, instance, args, kwargs):
    print("StructuredTool.ainvoke called")
    return await wrapped(*args, **kwargs)

@wrapt.patch_function_wrapper("langchain_core.tools", "StructuredTool.ainvoke")
@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(Exception),
)
async def structuredtool_ainvoke(wrapped, instance, args, kwargs):
    print("StructuredTool.ainvoke called")
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


async def main():
    """
    The entrypoint to our AI agent.
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
    agent = create_agent(llm, tools)
    response = await agent.ainvoke(
        {
            "messages": remove_line_padding(
                """
                In Octopus, get all the projects from the "Easy Mode" space.
                In Octopus, for each project, get the latest deployment to each environment and its status.
                If the deployment failed, output the project name, environment name, and deployment status.
                """
            )
        }
    )
    print(remove_thinking(response_to_text(response)))


asyncio.run(main())