import os
import click
from devon_agent.server import app


@click.group()
def cli():
    """Devon Agent CLI application."""
    pass


@click.command()
@click.option("--port", default=8000, help="Port number for the server.")
@click.option("--key", required=False, default=None, help="API key for authentication.")
def server(port, key):
    """Start the Devon Agent server."""
    import uvicorn

    import sys

    uvicorn.run(app, host="0.0.0.0", port=port)


cli.add_command(server)


def main():
    cli()
