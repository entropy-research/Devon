#!/bin/bash

# check if pipx is installed


# Check if poetry is installed
if ! command -v poetry &> /dev/null
then
    if ! command -v pipx &> /dev/null
    then
        echo "Please install pipx : https://pipx.pypa.io/stable/installation/"
        exit 1
    fi
    pipx install poetry
else
    echo "Poetry is already installed."
fi

poetry install

cd devon_tui
npm install
npm run build
npm install -g .
cd ..
echo "Devon is ready to use! Use the command 'devon-tui' to start the Devon TUI."
