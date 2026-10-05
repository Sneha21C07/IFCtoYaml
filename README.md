# AI Agents for Confluence IFC to OpenAPI

This workspace helps turn Interface Control (IFC) content from Confluence into two useful outputs:

- a formatted Word document for review and sharing
- an OpenAPI 3.0 YAML specification for API documentation

The workflow is designed for teams that maintain API specifications in Confluence and want a faster path to documentation artifacts.

## What this repository does

The project currently provides three main parts:

1. A Confluence client to read pages and fetch their content
2. A converter that turns Confluence HTML into a professional Word document
3. An agent workflow that can use the generated document as input for OpenAPI-style YAML generation

## Repository contents

- [confluence_mcp.py](confluence_mcp.py) – fetches and searches Confluence pages using the REST API
- [confluence_to_word.py](confluence_to_word.py) – converts page content into a Word document
- [run_confluence_extraction.py](run_confluence_extraction.py) – command-line entry point for extraction
- [.github/agents/ifc-swagger.agent.md](.github/agents/ifc-swagger.agent.md) – instructions for the IFC Swagger agent


## Prerequisites

Before using the workflow, make sure you have:

- Python 3.9 or newer
- access to a Confluence instance
- a valid Confluence email and API token

## Setup

1. Install the Python dependencies:

   ```bash
   pip install -r confluence_requirements.txt
   ```

2. Create your environment file:

   ```bash
   cp .env.example .env
   ```

3. Update [.env](.env) with your values:

   ```dotenv
   CONFLUENCE_URL=https://your-company.atlassian.net/wiki
   CONFLUENCE_EMAIL=your.email@company.com
   CONFLUENCE_TOKEN=your-api-token
   CONFLUENCE_PAGE_ID=your-page-id
   ```

> You can also provide a page ID at runtime in a prompt such as "CONFLUENCE_PAGE_ID=9399669064509". The agent workflow will write that value into [.env](.env) before running the extraction step.

## Run the extraction

From the project root, run:

```bash
python run_confluence_extraction.py "IFC_Specification.docx"
```

This command will:

- read the Confluence page from [.env](.env)
- fetch the page content
- create a Word document named IFC_Specification.docx

## Generate an OpenAPI YAML

Once the Word document exists, you can use the IFC Swagger agent to continue the workflow. A typical prompt looks like this:

```text
@IFC Swagger agent extract IFC with CONFLUENCE_PAGE_ID=9399669064509 and generate the word and convert it into .yaml
```

The agent is expected to:

- update the page ID in [.env](.env) if provided
- run the extraction
- produce a Word document
- convert that document into an OpenAPI YAML file

## Example output

The repository already includes example output files such as:

- [IFC_Specification.docx](IFC_Specification.docx)
- [IFC_Specification.yaml](IFC_Specification.yaml)
- the sample YAML specs listed above

## Project workflow

```text
Confluence page
   ↓
Fetch content
   ↓
Convert to Word document
   ↓
Use agent workflow to generate OpenAPI YAML
```

## Notes

- Keep [.env](.env) private. It contains sensitive credentials.
- The extraction process depends on the Confluence page being accessible to the provided account.
- If a page ID is invalid or the account lacks permission, the extraction will fail and the script will report the issue.

## Quick reference

```bash
pip install -r confluence_requirements.txt
cp .env.example .env
python run_confluence_extraction.py "IFC_Specification.docx"
```
