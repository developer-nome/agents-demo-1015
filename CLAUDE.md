# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a FastAPI-based web application that provides multiple AI agent endpoints for different tasks including SQL query generation, web browsing, and MCP (Model Context Protocol) server integration. The application serves a chat interface and streams AI responses.

## Development Setup

### Environment Configuration

The application supports both local (development) and external (production) LLM configurations. It currently uses the `_LOCAL` variants for development.

**Local Development** (default):
- `API_KEY_LOCAL`: API key for the local LLM provider
- `BASE_URL_LOCAL`: Base URL for the local LLM API (e.g., `http://127.0.0.1:1234/v1/`)
- `LLM_MODEL_LOCAL`: Model identifier for local LLM (e.g., `qwen/qwen3-4b-2507`)

**External** (optional, not currently used):
- `API_KEY_EXTERNAL`: API key for external LLM provider (e.g., OpenAI)
- `BASE_URL_EXTERNAL`: Base URL for external LLM API
- `LLM_MODEL_EXTERNAL`: Model identifier for external LLM

**Database**:
- `DB_PASSWORD`: PostgreSQL database password

See `.env.example` for a template of required variables.

**Using with VSCode Debugger (Recommended):**
Environment variables are loaded from `/Users/billhorn/code/python/.env` via `launch.json`. Edit that file to change values frequently during development, then use F5 or the Run and Debug panel to debug.

**Or set them in shell:**
```bash
export API_KEY_LOCAL="your_api_key"
export BASE_URL_LOCAL="http://127.0.0.1:1234/v1/"
export LLM_MODEL_LOCAL="qwen/qwen3-4b-2507"
export DB_PASSWORD="your_database_password"
```

### Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application

Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The web interface is served at the root endpoint via `static/index.html`.

## Architecture

### Main Application (`main.py`)

FastAPI server with streaming endpoints. Each endpoint wraps a specific agent implementation and returns streaming responses:

- `/processLLMfetchRequest` - Basic LLM streaming chat
- `/processLLMfetchRequestForAirlineInfo/` - MCP server using filesystem to read airline baggage policies
- `/processLLMfetchRequestForFlightInfo/` - Custom MCP server for flight information
- `/processLLMfetchRequestForSQLquery/` - LangChain SQL agent using LangChain's built-in SQL toolkit
- `/processLLMfetchRequestForSQLqueryCopilot/` - Pydantic AI SQL agent with custom validation
- `/processLLMfetchRequestForWebSurfer/` - AutoGen web surfing agent

### Agent Implementations

#### SQL Query Agents

Two different SQL agent implementations query a PostgreSQL database with schema:
- `airports` (airport_id, airport_name, location)
- `pilots` (pilot_id, first_name, last_name, email, phone_number, hire_date)
- `flight_delays` (flight_delay_id, delay_date, airport_id, pilot_id, flight_delay_minutes, flight_delay_reason)

**`asyncpgsqltest.py`**: Uses Pydantic AI for SQL generation with structured output (`SQLQuery` model). Validates queries with `EXPLAIN` before execution and handles both SELECT and modification queries. Returns formatted string results.

**`langchainsqltest.py`**: Uses LangChain's `create_sql_agent` with OpenAI tools agent type. Leverages LangChain's SQLDatabaseToolkit for automated schema introspection.

#### MCP Server Agents

**`mcpfunction.py`**: Uses the `agents` library (likely Anthropic's agents library) to interface with MCP filesystem server. Reads airline baggage policy from `data/airline_baggage_policy.txt` via `@modelcontextprotocol/server-filesystem`.

**`mcpfunction_custom.py`**: Similar MCP setup but points to a custom JavaScript MCP server at `/Users/billhorn/code/javascript/acme-air-demo`.

Both use `MCPServerStdio` to spawn MCP servers via `npx` and require Node.js/npx to be installed.

#### Web Surfer Agent

**`web_surfer.py`**: Uses AutoGen's `MultimodalWebSurfer` agent with a round-robin team approach. Includes an assistant agent and web surfer in a chat group, terminated after 6 messages or "TERMINATE" mention.

Key features:
- Collects `TextMessage` types and uses an LLM to select the one with bullet points
- Handles `MultiModalMessage` types containing images (screenshots)
- Saves screenshots to `static/screenshots/` directory with timestamped filenames
- Returns selected text with embedded HTML `<img>` tags for browser display
- Uses EXTERNAL LLM configuration for web surfing, LOCAL for message selection

### Database Configuration

PostgreSQL connection details:
- Host: `localhost:5432`
- Database: `postgres`
- User: `postgres`
- Password: From `DB_PASSWORD` environment variable

## Key Dependencies

- **FastAPI**: Web framework with streaming support
- **Pydantic AI**: AI agent framework with structured outputs
- **LangChain**: SQL agent and RAG capabilities
- **AutoGen**: Multi-agent orchestration and web surfing
- **MCP**: Model Context Protocol for tool integration
- **asyncpg**: Async PostgreSQL driver
- **OpenAI SDK**: LLM API client (works with OpenAI-compatible APIs)

## Common Patterns

### LLM Client Configuration

All modules use a common pattern for LLM configuration via environment variables:

```python
from openai import AsyncOpenAI
client = AsyncOpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)
model_name = os.getenv("LLM_MODEL")
```

### Streaming Responses

FastAPI endpoints use async generators to stream responses:

```python
async def stream_response():
    response = await some_agent_function(request.userRequestText)
    if isinstance(response, str):
        yield response
    else:
        async for chunk in response:
            yield chunk

return StreamingResponse(stream_response(), media_type="text/event-stream")
```

### MCP Server Pattern

MCP servers are spawned using context managers with `MCPServerStdio`:

```python
async with MCPServerStdio(
    name="Server Name",
    params={
        "command": "npx",
        "args": ["-y", "package-name", "/path/to/data"],
        "cache_tools_list": "True",
    },
) as server:
    return await run(server, message)
```

## Important Notes

- The application uses OpenAI-compatible API clients, allowing use of local LLMs or alternative providers
- SQL agents have direct database access with validation but allow modifications (UPDATE/DELETE/INSERT)
- MCP functionality requires Node.js and npx to be available in PATH
- Web surfer uses Playwright for headless browsing (requires Playwright installation: `playwright install`)
