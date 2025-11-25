import asyncio
import os
from datetime import datetime
from pathlib import Path
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage, MultiModalMessage
from autogen_core.models import ModelFamily
from autogen_core import Image
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.agents.web_surfer import MultimodalWebSurfer
from openai import AsyncOpenAI
# Environment variables are loaded from the system environment

async def run_web_surfer(user_message: str):
    model_client = OpenAIChatCompletionClient(
        base_url=os.getenv("BASE_URL_EXTERNAL"), # omit for OpenAI calls
        model=os.getenv("LLM_MODEL_EXTERNAL"),
        api_key=os.getenv("API_KEY_EXTERNAL"),
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
    image_paths = []

    # Create screenshots directory if it doesn't exist
    screenshots_dir = Path("static/screenshots")
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    async for message in stream:
        # handle any streamed message that exposes a 'content' attribute
        content = getattr(message, "content", None)
        if content is not None:
            print(type(message))
            print("--Begin message--")
            print(content)
            print("--End message--")

            # Collect TextMessage types
            if isinstance(message, TextMessage):
                results.append(content)

            # Handle MultiModalMessage with images
            elif isinstance(message, MultiModalMessage):
                text_parts = []
                for item in content:
                    if isinstance(item, str):
                        text_parts.append(item)
                    elif isinstance(item, Image):
                        # Save the image to static/screenshots
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                        image_filename = f"screenshot_{timestamp}.png"
                        image_path = screenshots_dir / image_filename

                        # Save the image using PIL (access the PIL Image via .image attribute)
                        pil_image = item.image
                        pil_image.save(str(image_path))

                        # Store the web-accessible path
                        web_path = f"/static/screenshots/{image_filename}"
                        image_paths.append(web_path)
                        print(f"Saved screenshot to: {image_path}")

                # Add text content to results if any
                if text_parts:
                    results.append(" ".join(text_parts))

    # If we have collected TextMessages, use LLM to select the one with bullet points
    if results:
        # Create a prompt with all numbered messages
        messages_text = ""
        for i, msg in enumerate(results, 1):
            messages_text += f"\n\n---MESSAGE {i}---\n{msg}"

        prompt = f"""You have received multiple messages below. Please identify and return ONLY the message that is formatted with bullet points. If multiple messages have bullet points, choose the most comprehensive one. If no messages have bullet points, return the most detailed message.

Return ONLY the exact content of the selected message, with no additional commentary, explanations, or modifications.

Here are the messages:{messages_text}"""

        # Use LLM to select the best message
        llm_client = AsyncOpenAI(
            api_key=os.getenv("API_KEY_LOCAL"),
            base_url=os.getenv("BASE_URL_LOCAL")
        )

        response = await llm_client.chat.completions.create(
            model=os.getenv("LLM_MODEL_LOCAL"),
            messages=[
                {"role": "system", "content": "You are a helpful assistant that selects the best formatted message."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        selected_message = response.choices[0].message.content
        print("\n\n===SELECTED MESSAGE (with bullet points)===")
        print(selected_message)
        print("===END SELECTED MESSAGE===\n")

        # If we have images, append them as HTML img tags
        if image_paths:
            image_html = "\n\n" + "\n".join([f'<img src="{path}" style="max-width: 100%; margin: 10px 0;">' for path in image_paths])
            selected_message += image_html

        return [selected_message]

    # If no text results but we have images, return just the images
    if image_paths:
        image_html = "\n".join([f'<img src="{path}" style="max-width: 100%; margin: 10px 0;">' for path in image_paths])
        return [image_html]

    return []


