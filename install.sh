#!/usr/bin/env bash

# Source the user's profile to ensure dependencies are in PATH
if [[ "$SHELL" == "/bin/bash" ]]; then
    source ~/.bashrc
elif [[ "$SHELL" == "/bin/zsh" ]]; then
    source ~/.zshrc
fi

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "python3 is not installed. Installing it..."
    if [ "$(uname)" == "Darwin" ]; then
        brew install python
    elif [ -f /etc/os-release ]; then
        . /etc/os-release
        case $ID in
            ubuntu|debian)
                sudo apt-get update
                sudo apt install -y python3
                ;;
            fedora)
                sudo dnf install -y python3
                ;;
            arch)
                sudo pacman -Sy --noconfirm python
                ;;
            *)
                exit 1
                ;;
        esac
    fi
fi

# Check again if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. The automatic install has failed. Please install it manually."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "node is not installed. Installing it..."
    if [ "$(uname)" == "Darwin" ]; then
        brew install node
    elif [ -f /etc/os-release ]; then
        . /etc/os-release
        case $ID in
            ubuntu|debian)
                sudo apt-get update
                sudo apt install -y nodejs
                ;;
            fedora)
                sudo dnf install -y nodejs
                ;;
            arch)
                sudo pacman -Sy --noconfirm nodejs
                ;;
            *)
                exit 1
                ;;
        esac
    fi
fi

# Check again if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. The automatic install has failed. Please install it manually."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Installing it..."
    if [ "$(uname)" == "Darwin" ]; then
        brew install npm
    elif [ -f /etc/os-release ]; then
        . /etc/os-release
        case $ID in
            ubuntu|debian)
                sudo apt-get update
                sudo apt install -y npm
                ;;
            fedora)
                sudo dnf install -y npm
                ;;
            arch)
                sudo pacman -Sy --noconfirm npm
                ;;
            *)
                exit 1
                ;;
        esac
    fi
fi

# Check again if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. The automatic install has failed. Please install it manually."
    exit 1
fi

# Check if pip3 is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Installing it..."
    if [ "$(uname)" == "Darwin" ]; then
        brew install python
    elif [ -f /etc/os-release ]; then
        . /etc/os-release
        case $ID in
            ubuntu|debian)
                sudo apt-get update
                sudo apt install -y python3-pip
                ;;
            fedora)
                sudo dnf install -y python3-pip
                ;;
            arch)
                sudo pacman -Sy --noconfirm python-pip
                ;;
            *)
                exit 1
                ;;
        esac
    fi
fi

# Check again if pip3 is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. The automatic install has failed. Please install it manually."
    exit 1
fi

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "pipx is not installed. Installing it..."

    # Install pipx based on OS
    if [ "$(uname)" == "Darwin" ]; then
        brew install pipx
        pipx ensurepath
    elif [ -f /etc/os-release ]; then
        . /etc/os-release
        case $ID in
            ubuntu|debian)
                sudo apt-get update
                sudo apt-get install -y pipx
                ;;
            fedora)
                sudo dnf install -y pipx
                ;;
            arch)
                sudo pacman -Sy --noconfirm pipx
                ;;
            *)
                python3 -m pip install --user pipx
                python3 -m pipx ensurepath
                ;;
        esac
    fi
fi

# Check again if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "Pipx is not installed. The automatic install has failed. Please install it manually. Installation instructions: https://pipx.pypa.io/stable/installation/"
    exit 1
fi

# Install Devon backend
echo "Installing Devon backend..."
pipx install devon_agent

if ! command -v devon_agent &> /dev/null; then
    echo "Something went wrong. Devon Backend is not installed. Please install it manually by running 'pipx install devon_agent'"
    exit 1
fi

echo "Devon Backend is installed successfully."

# Install Devon TUI
echo "Installing Devon TUI..."
npm install -g devon-tui

if ! command -v devon &> /dev/null; then
    echo "Something went wrong. Devon TUI is not installed. Please install it manually by running 'npm install -g devon-tui' or 'sudo npm install -g devon-tui'."
    exit 1
fi

echo "Devon TUI is installed successfully."
echo "Devon is installed successfully."
echo "Run 'devon' to start the Devon TUI."
