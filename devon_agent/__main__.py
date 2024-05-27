import asyncio
import json
import os
import signal
import click
from devon_agent.server import app


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


cli.add_command(server)


def main():
    cli()
