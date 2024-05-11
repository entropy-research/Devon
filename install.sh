

# check if python3  is installed
if ! command -v python3 &> /dev/null
then
    echo "Python3 is not installed. Please install it first."
    exit 1
fi

# check if npm is installed
if ! command -v npm &> /dev/null
then
    echo "node is not installed. Please install it first."
    exit 1
fi

# check if pip3 is installed
if ! command -v pip3 &> /dev/null
then
    echo "Pip3 is not installed. Please install it first."
    exit 1
fi


# check if pipx is installed
if ! command -v pipx &> /dev/null
then
    # if OS is macOS, use brew to install pipx
    if [ "$(uname)" == "Darwin" ]; then
        echo "Pipx is not installed. Installing it using brew..."
        brew install pipx
    else
        echo "Pipx is not installed. Please install it first. Installation instructions: https://pipx.pypa.io/stable/installation/"
        exit 1
    fi
fi

echo "Installing Devon backend..."
pipx install devon_agent

echo "Devon Backend is installed successfully."

echo "Installing Devon TUI..."
npm install -g devon-tui

echo "Devon TUI is installed successfully."

echo "Devon is installed successfully."