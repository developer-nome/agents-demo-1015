import asyncio
import os
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.models import ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from dotenv import load_dotenv

load_dotenv()

async def run_web_surfer(user_message: str):
    model_client = OpenAIChatCompletionClient(
        base_url=os.getenv("BASE_URL"), # omit for OpenAI calls
        model=os.getenv("LLM_MODEL"),
        api_key=os.getenv("API_KEY"),
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": ModelFamily.GPT_4O,
        }
    )
    
    assistant = AssistantAgent("assistant", model_client, system_message="You are a helpful assistant that can provide information to the user based on web searches conducted by the Web Surfer agent.")
    web_surfer = MultimodalWebSurfer("web_surfer", model_client=model_client, headless=True)
    user_proxy = UserProxyAgent("user_proxy")
    #termination = TextMentionTermination("exit") # Type 'exit' to end the conversation.
    termination =  MaxMessageTermination(6) | TextMentionTermination("TERMINATE")
    team = RoundRobinGroupChat([web_surfer, assistant], termination_condition=termination)
    # await Console(team.run_stream(task="Find information about current weather in St. Charles, MO, and write a short summary."))
    stream = team.run_stream(task=user_message)
    results = []
    async for message in stream:
        # handle any streamed message that exposes a 'content' attribute
        content = getattr(message, "content", None)
        if content is not None:
            print(type(message))
            print("--Begin message--")
            print(content)
            print("--End message--")
            results.append(content)
    # return only the last collected message
    return [results[-1]] if results else []


