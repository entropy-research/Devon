import asyncio
import json
import os
import signal
import click
from devon_agent.agents.default.agent import TaskAgent
from devon_agent.server import app, get_user_input
from devon_agent.session import Session, SessionArguments
from devon_agent.utils import Event


@click.group()
def cli():
    """Devon Agent CLI application."""
    pass


@click.command()
@click.option("--port", default=8000, help="Port number for the server.")
@click.option("--model", required=False, default=None, help="Model for authentication.")
@click.option("--api_key", required=False, default=None, help="API key for authentication.")
@click.option("--prompt_type", required=False, default=None, help="Specify prompt type for the model.")
@click.option("--api_base", required=False, default=None, help="Specify API base url for the model.")
def server(port, model, api_key, prompt_type, api_base):
    """Start the Devon Agent server."""
    import uvicorn

    if api_key is None:
        raise Exception("Could not find api key")
    elif model is None:
        raise Exception("Could not find default model, please run devon `configure`")

    app.api_key = api_key
    app.api_base = api_base
    app.prompt_type = prompt_type
    app.model = model

    with open(os.path.join(os.getcwd(), ".devon.config"), "r") as f:
        config = f.read()
        app.config = json.loads(config)

    uvicorn.run(app, host="0.0.0.0", port=port)


@click.command()
@click.option("--model", required=False, default=None, help="Model for authentication.")
@click.option("--api_key", required=False, default=None, help="API key for authentication.")
@click.option("--prompt_type", required=False, default=None, help="Specify prompt type for the model.")
@click.option("--api_base", required=False, default=None, help="Specify API base url for the model.")
@click.option("--headless", required=False, default=None, help="Specify headless mode task.")
def headless(model, api_key, prompt_type, api_base, headless):
    """Start the Devon Agent server."""
    import uvicorn

    if api_key is None:
        raise Exception("Could not find api key")
    elif model is None:
        raise Exception("Could not find default model, please run devon `configure`")

    app.api_key = api_key
    app.api_base = api_base
    app.prompt_type = prompt_type
    app.model = model
    app.headless = headless

    with open(os.path.join(os.getcwd(), ".devon.config"), "r") as f:
        config = f.read()
        app.config = json.loads(config)

    agent = TaskAgent(
            name="Devon",
            model=app.model,
            temperature=0.0,
            api_key=app.api_key,
            api_base=app.api_base,
            prompt_type=app.prompt_type,
        )

    name = "headless"

    session = Session(
        SessionArguments(
            os.getcwd(),
            user_input=lambda: get_user_input(name),
            name=name,
            config=app.config,
            headless=app.headless
        ),
        agent,
    )
    session.enter()

    session.event_log.append(
        Event(
            type="ModelRequest",
            content="Your interaction with the user was paused, please resume.",
            producer="system",
            consumer="devon",
        )
    )

    session.run_event_loop()


cli.add_command(server)
cli.add_command(headless)


def main():
    cli()
