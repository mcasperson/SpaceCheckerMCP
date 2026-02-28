# SpaceCheckerMCP

A Python application that checks Octopus Deploy deployment statuses using the MCP (Model Context Protocol) server and Azure AI.

## Prerequisites

- Docker and Docker Compose installed
- Octopus Deploy API key
- Azure AI credentials

## Environment Variables

The application requires the following environment variables:

- `OCTOPUS_CLI_API_KEY`: Your Octopus Deploy API key
- `OCTOPUS_CLI_SERVER`: Your Octopus Deploy server URL
- `AZURE_AI_URL`: Your Azure AI endpoint URL
- `AZURE_AI_APIKEY`: Your Azure AI API key

## Using Pre-built Images from GHCR

The Docker images are automatically built and published to GitHub Container Registry on every push to main/master and on version tags.

### Pull the latest image:

```bash
docker pull ghcr.io/OWNER/REPOSITORY:latest
```

### Run the pre-built image:

```bash
docker run --rm \
  -e OCTOPUS_CLI_API_KEY="your-api-key" \
  -e OCTOPUS_CLI_SERVER="https://your-octopus-server.com" \
  -e AZURE_AI_URL="your-azure-ai-url" \
  -e AZURE_AI_APIKEY="your-azure-ai-key" \
  ghcr.io/OWNER/REPOSITORY:latest
```

### Available tags:
- `latest` - Latest build from the default branch
- `v*` - Semantic version tags (e.g., `v1.0.0`, `v1.0`, `v1`)
- `main` or `master` - Latest build from the main/master branch
- `<branch>-<sha>` - Builds from specific commits

## Building the Docker Image Locally

```bash
docker build -t spacechecker:latest .
```

## Running with Docker

```bash
# Run with default message
docker run --rm \
  -e OCTOPUS_CLI_API_KEY="your-api-key" \
  -e OCTOPUS_CLI_SERVER="https://your-octopus-server.com" \
  -e AZURE_AI_URL="your-azure-ai-url" \
  -e AZURE_AI_APIKEY="your-azure-ai-key" \
  spacechecker:latest

# Run with custom message
docker run --rm \
  -e OCTOPUS_CLI_API_KEY="your-api-key" \
  -e OCTOPUS_CLI_SERVER="https://your-octopus-server.com" \
  -e AZURE_AI_URL="your-azure-ai-url" \
  -e AZURE_AI_APIKEY="your-azure-ai-key" \
  spacechecker:latest \
  --message "Get all projects in the 'Production' space"
```

## Running with Docker Compose

1. Set your environment variables:

```bash
export OCTOPUS_CLI_API_KEY="your-api-key"
export OCTOPUS_CLI_SERVER="https://your-octopus-server.com"
export AZURE_AI_URL="your-azure-ai-url"
export AZURE_AI_APIKEY="your-azure-ai-key"
```

2. Run the application:

```bash
docker-compose up
```

Alternatively, create a `.env` file in the project root with your credentials:

```
OCTOPUS_CLI_API_KEY=your-api-key
OCTOPUS_CLI_SERVER=https://your-octopus-server.com
AZURE_AI_URL=your-azure-ai-url
AZURE_AI_APIKEY=your-azure-ai-key
```

Then uncomment the `env_file` section in `docker-compose.yml` and run:

```bash
docker-compose up
```

## Development

To run locally without Docker:

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure Node.js is installed (required for the MCP server)

3. Set environment variables and run:
```bash
# Run with default message
python main.py

# Run with custom message
python main.py --message "Get all projects in the 'Production' space"

# Or use the short form
python main.py -m "List all environments in Octopus"

# View help
python main.py --help
```

### Command-line Options:
- `-m, --message MESSAGE`: The message/prompt to send to the agent (optional)
  - If not provided, uses a default message that checks for failed deployments in the "Easy Mode" space

## CI/CD

This repository includes a GitHub Actions workflow that automatically:

- Builds the Docker image for both `linux/amd64` and `linux/arm64` platforms
- Publishes the image to GitHub Container Registry (GHCR)
- Creates multiple tags based on branches, PRs, and version tags
- Generates build provenance attestations for security

### Workflow Triggers:
- **Push to main/master**: Builds and pushes with `latest` and branch tags
- **Version tags** (e.g., `v1.0.0`): Builds and pushes with semantic version tags
- **Pull requests**: Builds but doesn't push (validation only)
- **Manual trigger**: Can be triggered manually from GitHub Actions UI

### Publishing a Release:
```bash
git tag v1.0.0
git push origin v1.0.0
```

This will automatically build and publish the image with tags:
- `ghcr.io/OWNER/REPOSITORY:v1.0.0`
- `ghcr.io/OWNER/REPOSITORY:v1.0`
- `ghcr.io/OWNER/REPOSITORY:v1`
- `ghcr.io/OWNER/REPOSITORY:latest`

