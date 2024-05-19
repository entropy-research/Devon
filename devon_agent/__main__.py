import os
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
def server(port, model, api_key):
    """Start the Devon Agent server."""
    import uvicorn

    import sys

    if api_key is None:
        raise Exception("Could not find api key")
    elif model is None:
        raise Exception("Could not find default model, please run devon `configure`")

    app.api_key = api_key
    app.model = model

    uvicorn.run(app, host="0.0.0.0", port=port)


cli.add_command(server)


def main():
    cli()
