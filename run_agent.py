#!/usr/bin/env python3
import asyncio
import sys
from dotenv import load_dotenv

# Load local environment variables (.env with Vertex AI config)
load_dotenv()

from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from app.agent import root_agent

async def query_agent(prompt: str):
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    session = await session_service.create_session(app_name="app", user_id="test_user")
    runner = Runner(
        agent=root_agent,
        session_service=session_service,
        artifact_service=artifact_service,
        app_name="app",
    )
    
    content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
    events = runner.run_async(session_id=session.id, user_id="test_user", new_message=content)
    
    print(f"\nUser: {prompt}\nAgent: ", end="", flush=True)
    async for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is the weather and current time in San Francisco?"
    asyncio.run(query_agent(prompt))
