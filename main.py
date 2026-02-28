import asyncio
import os
import re

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langgraph.prebuilt import create_react_agent


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
            },
            "github": {
                "url": "https://api.githubcopilot.com/mcp/",
                "headers": {"Authorization": f"Bearer {os.getenv('GITHUB_PAT')}"},
                "transport": "streamable_http",
            },
        }
    )

    # Use an Azure AI model
    llm = AzureAIChatCompletionsModel(
        endpoint=os.getenv("AZURE_AI_URL"),
        credential=os.getenv("AZURE_AI_APIKEY"),
        model="gpt-5-mini",
    )

    tools = await client.get_tools()
    agent = create_react_agent(llm, tools)
    response = await agent.ainvoke(
        {
            "messages": remove_line_padding(
                """
                In Octopus, get all the projects from the "Octopus Copilot" space.
                In Octopus, for each project, get the latest release.
                In GitHub, for each release, get the git diff from the GitHub Commit. 
                Scan the diff and provide a summary-level risk assessment.
                You will be penalized for asking for user input.
                """
            )
        }
    )
    print(remove_thinking(response_to_text(response)))


asyncio.run(main())