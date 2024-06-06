# Installation

## Prerequisites

1. `node.js` and `npm`
2. `pipx`, if you don't have this go [here](https://pipx.pypa.io/stable/installation/)
3. API Key <samp>(just one is required)</samp>
   - [**Anthropic**](https://console.anthropic.com/settings/keys)
    - [**OpenAI**](https://platform.openai.com/api-keys)
    - [**Groq**](https://console.groq.com/keys) (not released in package yet, run locally)
> We're currently working on supporting Windows! (Let us know if you can help)

## Installation commands

To install, simply run:

```bash
curl -sSL https://raw.githubusercontent.com/entropy-research/Devon/main/install.sh | bash
```


*Or to install using `pipx` + `npm`:*

```bash
pipx install devon_agent
npm install -g devon-tui 
```

This installs the Python backend, and the cli command to run the tool

---


For a list of all commands available:
```bash
devon --help
```



