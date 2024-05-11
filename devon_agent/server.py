import asyncio
import json
import os
from time import sleep
from typing import Dict, List

import fastapi
from devon_agent.agent import TaskAgent
from devon_agent.session import (
    Event,
    Session,
    SessionArguments,
)
from fastapi.middleware.cors import CORSMiddleware


from fastapi.responses import StreamingResponse

# API
# SESSION
# - get sessions
# - create session
# - start session
# repond session
# interrupt session
# stop session
# delete session
# get session event history
# get session event stream


origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

sessions: Dict[str, Session] = {}


API_KEY = None


app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_buffers: Dict[str, str] = {}
running_sessions: List[str] = []


def get_user_input(session: str):
    if session not in session_buffers:
        while True:
            if session not in session_buffers:
                sleep(0.1)
                continue
            else:
                break

        result = session_buffers[session]
        del session_buffers[session]
        return result
    else:
        result = session_buffers[session]
        del session_buffers[session]
        return result


@app.get("/")
def read_root():
    return {"content": "Hello from Devon!"}


@app.get("/session")
def read_session():
    return list(sessions.keys())


@app.post("/session")
def create_session(session: str, path: str):
    if not os.path.exists(path):
        raise fastapi.HTTPException(status_code=404, detail="Path not found")

    agent = TaskAgent(
        name="Devon",
        model="claude-opus",
        temperature=0.0,
        api_key=API_KEY,
    )
    sessions[session] = Session(
        SessionArguments(
            path,
            environment="local",
            user_input=lambda: get_user_input(session),
            name=session,
        ),
        agent,
    )

    return session


@app.post("/session/{session}/start")
def start_session(background_tasks: fastapi.BackgroundTasks, session: str):
    if session not in sessions:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")

    if session in running_sessions:
        raise fastapi.HTTPException(status_code=304, detail="Session already running")

    sessions[session].enter()
    sessions[session].event_log.append(
        Event(
            type="Task",
            content="ask user for what to do",
            producer="system",
            consumer="devon",
        )
    )
    background_tasks.add_task(sessions[session].step_event)
    running_sessions.append(session)
    return session


@app.post("/session/{session}/response")
def create_response(session: str, response: str):
    if session not in sessions:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")
    session_buffers[session] = response
    return session_buffers[session]


@app.post("/session/{session}/interrupt")
def interrupt_session(session: str, message: str):
    if session not in sessions:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")
    session_obj = sessions.get(session)
    if not session_obj:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")
    session_obj.event_log.append(
        Event(type="Interrupt", content=message, producer="user", consumer="devon")
    )
    return session


@app.post("/session/{session}/stop")
def stop_session(session: str):
    if session not in sessions:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")
    session_obj = sessions.get(session)
    if not session_obj:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")
    session_obj.event_log.append(Event(type="stop", content="stop"))
    return session_obj


@app.get("/session/{session}/state")
def continue_session(session: str):
    if session not in sessions:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")
    session_obj = sessions.get(session)
    if not session_obj:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")
    print(session_obj.state)
    return session_obj.state.to_dict()


@app.delete("/session")
def delete_session(session: str):
    if session not in sessions:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")
    del sessions[session]
    return session


@app.get("/session/{session}/events")
def read_events(session: str):
    if session not in sessions:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")
    return sessions.get(session, None).event_log


@app.get("/session/{session}/events/stream")
async def read_events_stream(session: str):
    if session not in sessions:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")
    session_obj: Session = sessions.get(session)
    if not session_obj:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        initial_index = session_obj.event_index
        while True:
            current_index = session_obj.event_index
            if current_index > initial_index:
                for event in session_obj.event_log[initial_index:current_index]:
                    yield json.dumps(event) + "\n"
                initial_index = current_index
            else:
                await asyncio.sleep(0.1)  # Sleep to prevent busy waiting

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    import sys

    port = 8000  # Default port
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Warning: Invalid port number provided. Using default port 8000.")

        try:
            API_KEY = sys.argv[2]
        except IndexError:
            if os.environ.get("ANTHROPIC_API_KEY"):
                api_key = os.environ.get("ANTHROPIC_API_KEY")
            else:
                raise ValueError("API key not provided.")

    uvicorn.run(app, host="0.0.0.0", port=port)
