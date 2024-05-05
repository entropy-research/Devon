import asyncio
from contextlib import asynccontextmanager
import json
from time import sleep
from typing import Dict
import fastapi
from fastapi.responses import StreamingResponse
import sqlalchemy
from devon.environment.agent import Agent, TaskAgent
from devon.environment.model import ModelArguments

from devon.environment.session import Event, Session, SessionArguments


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

# persistence
# sqlite
# - sessions
# - events
from fastapi import Depends, FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os


DATABASE_PATH = "./devon_environment.db"
DATABASE_URL = "sqlite:///" + DATABASE_PATH


sessions: Dict[str, Session] = {}


add_or_update_sessions_sql = """
INSERT INTO sessions (name, JSON_STATE) VALUES (:name, :JSON_STATE)
ON CONFLICT(name) DO UPDATE SET JSON_STATE = excluded.JSON_STATE
"""

delete_session_sql = """
DELETE FROM sessions WHERE name = :name
"""

get_session_sql = """
SELECT * FROM sessions WHERE name = :name
"""

get_sessions_sql = """
SELECT * FROM sessions
"""


@asynccontextmanager
async def lifespan(app: FastAPI):

    engine = create_engine(DATABASE_URL, echo=True)

    # session table SQL DDL
    session_table_sql = """
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        JSON_STATE TEXT NOT NULL,
        PRIMARY KEY (id)
    );
    """

    # run the SQL DDL statement
    with engine.connect() as conn:
        conn.execute(text(session_table_sql))

    # get all sessions and load them into sessions dictionary
    with engine.connect() as conn:
        sessions = conn.execute(text(get_sessions_sql)).fetchall()
        for session in sessions:
            sessions[session["name"]] = Session.from_dict(session["JSON_STATE"])

    yield

    session_states = [(name, session.to_dict()) for name, session in sessions.items()]
    with engine.connect() as conn:
        for name, state in session_states:
            conn.execute(text(add_or_update_sessions_sql), name=name, JSON_STATE=state)


app = fastapi.FastAPI()

session_buffers: Dict[str, str] = {}


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
    return sessions.keys()


@app.post("/session")
def create_session(session: str, path: str):

    agent = TaskAgent(
        name="Devon",
        args=ModelArguments(model_name="claude-opus", temperature=0.0),
        model="claude-opus",
        temperature=0.0,
    )
    sessions[session] = Session(
        SessionArguments(
            path, environment="local", user_input=lambda: get_user_input(session)
        ),
        agent,
    )

    return session


@app.post("/session/{session}/start")
def start_session(background_tasks: fastapi.BackgroundTasks, session: str):
    sessions[session].enter()
    sessions[session].event_log.append(
        Event(type="Task", content="ask user for what to do")
    )
    background_tasks.add_task(sessions[session].step_event)
    return session


@app.post("/session/{session}/response")
def create_response(session: str, response: str):
    session_buffers[session] = response
    return session_buffers[session]


@app.post("/session/{session}/interrupt")
def interrup_session(session: str, message: str):
    session_obj = sessions.get(session)
    if not session_obj:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")
    session_obj.event_log.append(Event(type="interrupt", content=message))
    return session_obj


@app.post("/session/{session}/stop")
def stop_session(session: str):
    session_obj = sessions.get(session)
    if not session_obj:
        raise fastapi.HTTPException(status_code=404, detail="Session not found")
    session_obj.event_log.append(Event(type="stop", content="stop"))
    return session_obj


@app.delete("/session")
def delete_session(session: str):
    del sessions[session]
    return sessions


@app.get("/session/{session}/events")
def read_events(session: str):
    return sessions[session].event_log


@app.get("/session/{session}/events/stream")
async def read_events_stream(session: str):

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
    uvicorn.run(app, host="0.0.0.0", port=8000)