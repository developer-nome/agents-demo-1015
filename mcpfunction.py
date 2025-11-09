import os
import shutil

from agents import Agent, Runner, set_default_openai_api, set_default_openai_client, set_tracing_disabled
from agents.mcp import MCPServer, MCPServerStdio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

async def run(mcp_server: MCPServer, message: str):
    client = AsyncOpenAI(
        api_key = os.getenv("API_KEY"),
        base_url = os.getenv("BASE_URL")
    )
    set_default_openai_client(client=client, use_for_tracing=False)
    set_default_openai_api("chat_completions")
    set_tracing_disabled(disabled=True)
    model_name = os.getenv("LLM_MODEL")
    agent = Agent(
        name="Assistant",
        instructions="Use the tools to return airline baggage policy info from the text files in the data directory.",
        mcp_servers=[mcp_server],
        model=model_name,
    )
    print(f"\n\nRunning: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)
    return result.final_output

async def run_mcp(message: str):
    if not shutil.which("npx"):
        raise RuntimeError("npx is not installed. Please install it with `npm install -g npx`.")

    # async with MCPServerStdio(
    #     name="Flight Info Bot",
    #     params={
    #         "command": "npx",
    #         "args": ["/Users/billhorn/code/javascript/acme-air-demo", message],
    #         "cache_tools_list": "True"
    #     },
    # ) as server:
    #     trace_id = gen_trace_id()
    #     with trace(workflow_name="MCP Filesystem Example", trace_id=trace_id):
    #         print(f"View trace: https://platform.openai.com/traces/{trace_id}\n")
    #         return await run(server, message)

    async with MCPServerStdio(
        name="Filesystem Server, via npx",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem@2025.8.18", "/Users/billhorn/code/python/langchainpostgres004/data"],
            "cache_tools_list": "True",
        },
    ) as server:
        return await run(server, message)
