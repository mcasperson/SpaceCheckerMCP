import argparse
import asyncio
import logging
import os
from datetime import timedelta

# Import for side effects - registers patches for StructuredTool.ainvoke
import aspects.aspects  # noqa: F401

from langchain.agents import create_agent
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_mcp_adapters.client import MultiServerMCPClient

from messages.messages import remove_thinking, response_to_text, remove_line_padding
from tools import http_post
from tools.octopus_tools import condense_deployments, condense_projects, condense_releases, condense_spaces, condense_environments, \
    condense_tasks

# These instructions are required to manage the size of the context window as part of long-running conversations
# with multiple tool calls that return large lists of resources.
additional_instructions = """
You must condense any information about deployments, projects, releases, spaces, and environments after reporting on them to avoid memory issues. 
Be aggressive with condensing information, and call the condense tools when only the name and ID of resources that were just accessed are required.
You must consider running the condense tool after every tool call that returns a resource or list of resources to free up memory, especially if the list is long.
You will be severely penalized for calling list or get tools (such as list_deployments, list_deployments, or get_task_details) in succession without considering the condense tools. 
You must strongly consider calling the condense_deployments tool after every call to list_deployments.
You must strongly consider calling the condense_tasks tool after every call to get_task_details.
You must condense the list of spaces after getting the list of spaces if only the space names and IDs are likely to be required later in the conversation.
You must condense the list of environments after getting the list of environments if only the environment names and IDs are likely to be required later in the conversation.
You must condense the list of projects after getting the list of projects if only the project names and IDs are likely to be required later in the conversation.
You must condense the list of releases after getting the list of releases if only the release names and IDs are likely to be required later in the conversation.
You must condense the list of deployments after getting the list of deployments if only the deployment names, IDs, EnvironmentIds, ProjectIds, and TaskIDs are likely to be required later in the conversation.
You must condense the details of tasks after getting task details if only the task name, ID, and state are likely to be required later in the conversation.
"""

default_message = f"""
The Octopus instance URL is mattc.octopus.app.
In Octopus, get all the projects from the "Easy Mode" space.
In Octopus, for each project, get the latest deployment to each environment and its status.
If the deployment failed, output the project name, environment name, and deployment status like this:
<URL to the deployment> - <Project Name> - <Environment Name>
If there are no failed deployments, output "No failed deployments in space <Space Name>".
You will be penalized for providing additional instructions.
You will be penalized for reporting on deployments that were successful with warnings.
Post a slack message to the webook {os.getenv("SLACK_WEBHOOK")} with the results.
"""

# Configure logging for retry messages
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    tools.append(condense_tasks)
    tools.append(http_post)
    agent = create_agent(llm, tools)
    response = await agent.ainvoke(
        {
            "messages": remove_line_padding(message + "\n" + additional_instructions)
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
        default=default_message
    )

    args = parser.parse_args()
    asyncio.run(main(args.message))
