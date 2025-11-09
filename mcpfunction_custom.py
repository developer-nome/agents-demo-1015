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
        instructions="Use the tools based on the user prompt.",
        mcp_servers=[mcp_server],
        model=model_name,
    )
    print(f"\n\nRunning: {message}")
    result = await Runner.run(starting_agent=agent, input=message)
    print(result.final_output)
    return result.final_output

async def run_mcp_custom(message: str):
    if not shutil.which("npx"):
        raise RuntimeError("npx is not installed or not found in PATH. Please install Node.js and ensure npx is available.")
    
    async with MCPServerStdio(
        name="Flight Info Bot",
        params={
            "command": "npx",
            "args": ["/Users/billhorn/code/javascript/acme-air-demo", message],
            "cache_tools_list": "True",
        },
    ) as server:
        return await run(server, message)