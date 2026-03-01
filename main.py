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
from tools import slack_web_hook
from tools.octopus_tools import (
    condense_deployments,
    condense_projects,
    condense_releases,
    condense_spaces,
    condense_environments,
    condense_tasks,
)

# These instructions are required to manage the size of the context window as part of long-running conversations
# with multiple tool calls that return large lists of resources.
additional_instructions = """
CRITICAL MEMORY MANAGEMENT RULES - YOU WILL BE SEVERELY PENALIZED FOR NOT FOLLOWING THESE:

1. MANDATORY: You MUST call condense_deployments immediately after EVERY SINGLE call to list_deployments. This is NOT optional.
2. MANDATORY: You MUST call condense_tasks immediately after EVERY SINGLE call to get_task_details or get_task_by_id. This is NOT optional.
3. You are FORBIDDEN from calling list_deployments twice in a row without calling condense_deployments in between.
4. You are FORBIDDEN from calling get_task_details or get_task_by_id twice in a row without calling condense_tasks in between.

The correct pattern is ALWAYS:
- Call list_deployments → Immediately call condense_deployments → Then continue
- Call get_task_details → Immediately call condense_tasks → Then continue

ADDITIONAL MANDATORY CONDENSING RULES - YOU MUST FOLLOW THESE:
5. You MUST call condense_spaces immediately after list_spaces if only space names and IDs are needed. This is STRONGLY REQUIRED.
6. You MUST call condense_environments immediately after list_environments if only environment names and IDs are needed. This is STRONGLY REQUIRED.
7. You MUST call condense_projects immediately after list_projects if only project names and IDs are needed. This is STRONGLY REQUIRED.
8. You MUST call condense_releases immediately after list_releases if only release names and IDs are needed. This is STRONGLY REQUIRED.
9. IMPORTANT: In most cases, only the names and IDs ARE needed from list operations, so you should ALWAYS strongly consider calling the condense function.
10. You are FORBIDDEN from calling any list function twice in a row without first calling the corresponding condense function if only names and IDs were needed from the first call.

FAILURE TO FOLLOW THE MANDATORY RULES ABOVE WILL RESULT IN SEVERE PENALTIES.
"""

default_message = f"""
The Octopus instance URL is "{os.getenv("OCTOPUS_CLI_SERVER")}".
In Octopus, get all the projects from the "{os.getenv("OCTOPUS_SPACE")}" space.
In Octopus, for each project, get the latest deployment to each environment and its status.
If the deployment failed, output the project name, environment name, and deployment status like this:
FAILED: <URL to the deployment> - <Project Name> - <Environment Name>
The deployment url must be in the format "https://instancename.octopus.app/app#/Spaces-#/deployments/Deployments-#"
Replace "instancename" with the actual instance name, and replace "Spaces-#" and "Deployments-#" with the actual space ID and deployment ID from Octopus.
If there are no failed deployments, output "No failed deployments in space <Space Name>".
You will be penalized for providing additional instructions.
You will be penalized for reporting on deployments that were successful with warnings.
"""

if os.getenv("SLACK_WEBHOOK"):
    default_message += f'\nPost a slack message to the webook "{os.getenv("SLACK_WEBHOOK")}" with the results.'

# Configure logging for retry messages
logging.basicConfig(
    level=logging.WARNING, format="%(asctime)s - %(levelname)s - %(message)s"
)
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
                    "--no-read-only",
                ],
                "transport": "stdio",
                "session_kwargs": {"read_timeout_seconds": timedelta(seconds=60)},
            }
        }
    )

    model = os.getenv("AZURE_AI_MODEL", "gpt-5-mini")

    # Use an Azure AI model
    llm = AzureAIChatCompletionsModel(
        # The URL that ends in /models from the Overview page
        endpoint=os.getenv("AZURE_AI_URL"),
        credential=os.getenv("AZURE_AI_APIKEY"),
        model=model,
    )

    tools = await client.get_tools()
    tools.append(condense_deployments)
    tools.append(condense_projects)
    tools.append(condense_releases)
    tools.append(condense_spaces)
    tools.append(condense_environments)
    tools.append(condense_tasks)
    tools.append(slack_web_hook)
    agent = create_agent(llm, tools)
    response = await agent.ainvoke(
        {"messages": remove_line_padding(message + "\n" + additional_instructions)}
    )
    print(remove_thinking(response_to_text(response)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SpaceChecker MCP - Check Octopus Deploy deployment statuses"
    )
    parser.add_argument(
        "-m",
        "--message",
        type=str,
        help="The message/prompt to send to the agent",
        default=default_message,
    )

    args = parser.parse_args()
    asyncio.run(main(args.message))
