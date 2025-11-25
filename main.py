import os
from openai import AsyncOpenAI

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from asyncpgsqltest import run_sql_query_copilot
from langchainsqltest import run_sql_query
from mcpfunction import run_mcp
from mcpfunction_custom import run_mcp_custom
from web_surfer import run_web_surfer

from pydantic import BaseModel

class RequestJSONdata(BaseModel):
    userRequestText: str

app = FastAPI()

favicon_path = 'favicon.ico'

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)


@app.post("/processLLMfetchRequest")
async def processLLMfetchRequest(requestJSONdata: RequestJSONdata):
    client = AsyncOpenAI(
        api_key=os.getenv("API_KEY_LOCAL"),
        base_url=os.getenv("BASE_URL_LOCAL")
    )
    stream = await client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": requestJSONdata.userRequestText
        }
    ],
    model = os.getenv("LLM_MODEL_LOCAL"),
    stream=True,
    max_tokens=500,
    )

    async def generator():
        async for chunk in stream:
            if chunk.choices:
                yield chunk.choices[0].delta.content or ""
    
    response_messages = generator()
    return StreamingResponse(response_messages, media_type="text/event-stream")


@app.post("/processLLMfetchRequestForAirlineInfo/")
async def processLLMfetchRequestForAirlineInfo(requestJSONdata: RequestJSONdata):
    async def stream_mcp_response():
        response = await run_mcp(requestJSONdata.userRequestText)
        # If response is a string, yield it in chunks or all at once
        if isinstance(response, str):
            yield response
        else:
            # If response is already an async generator, iterate through it
            async for chunk in response:
                yield chunk

    return StreamingResponse(stream_mcp_response(), media_type="text/event-stream")


@app.post("/processLLMfetchRequestForFlightInfo/")
async def processLLMfetchRequestForFlightInfo(requestJSONdata: RequestJSONdata):
    async def stream_mcp_response():
        response = await run_mcp_custom(requestJSONdata.userRequestText)
        # If response is a string, yield it in chunks or all at once
        if isinstance(response, str):
            yield response
        else:
            # If response is already an async generator, iterate through it
            async for chunk in response:
                yield chunk

    return StreamingResponse(stream_mcp_response(), media_type="text/event-stream")


@app.post("/processLLMfetchRequestForSQLquery/")
async def processLLMfetchRequestForSQLquery(requestJSONdata: RequestJSONdata):
    async def stream_sql_response():
        response = await run_sql_query(requestJSONdata.userRequestText)
        # If response is a string, yield it in chunks or all at once
        if isinstance(response, str):
            yield response
        else:
            # If response is already an async generator, iterate through it
            async for chunk in response:
                yield chunk

    return StreamingResponse(stream_sql_response(), media_type="text/event-stream")


@app.post("/processLLMfetchRequestForSQLqueryCopilot/")
async def processLLMfetchRequestForSQLqueryCopilot(requestJSONdata: RequestJSONdata):
    async def stream_sql_response():
        response = await run_sql_query_copilot(requestJSONdata.userRequestText)
        # If response is a string, yield it in chunks or all at once
        if isinstance(response, str):
            yield response
        else:
            # If response is already an async generator, iterate through it
            async for chunk in response:
                yield chunk

    return StreamingResponse(stream_sql_response(), media_type="text/event-stream")

@app.post("/processLLMfetchRequestForWebSurfer/")
async def processLLMfetchRequestForWebSurfer(requestJSONdata: RequestJSONdata):
    async def stream_websurfer_response():
        response = await run_web_surfer(requestJSONdata.userRequestText)
        for chunk in response:
            if isinstance(chunk, str):
                yield chunk
            elif isinstance(chunk, list):
                # Handle list items (e.g., [text, image_object])
                for item in chunk:
                    if isinstance(item, str):
                        yield item

    return StreamingResponse(stream_websurfer_response(), media_type="text/event-stream")
