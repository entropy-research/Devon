
<!-- PROJECT LOGO -->
<div align="center">
  <h1 align="center">Devon: An open-source pair programmer</h1>
</div>
<div align="center">
  <a href="https://github.com/entropy-research/Devon/graphs/contributors"><img src="https://img.shields.io/github/contributors/entropy-research/devon?style=for-the-badge&color=lime" alt="Contributors"></a>
  <a href="https://github.com/entropy-research/Devon/network/members"><img src="https://img.shields.io/github/forks/entropy-research/devon?style=for-the-badge&color=orange" alt="Forks"></a>
  <a href="https://github.com/entropy-research/Devon/stargazers"><img src="https://img.shields.io/github/stars/entropy-research/devon?style=for-the-badge&color=yellow" alt="Stargazers"></a>
  <a href="https://github.com/entropy-research/Devon/issues"><img src="https://img.shields.io/github/issues/entropy-research/devon?style=for-the-badge&color=red" alt="Issues"></a>
  <br/>
  <a href="https://github.com/entropy-research/Devon/blob/main/LICENSE"><img src="https://img.shields.io/github/license/entropy-research/devon?style=for-the-badge&color=blue" alt="Apache 2.0 License"></a>
  <a href="https://discord.gg/p5YpZ5vjd9"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=for-the-badge" alt="Join our Discord community"></a>
  <br/>

https://github.com/entropy-research/Devon/assets/61808204/d42a8b9a-0211-4624-9804-d24df1d4dbf6
</div>

### How do y'all ship so quickly?
<a href="https://discord.gg/p5YpZ5vjd9"><img src="https://img.shields.io/badge/Discord-Join%20Us-purple?logo=discord&logoColor=white&style=for-the-badge" alt="Join our Discord community"></a> 
← We have a __**community-driven Dev Team**__ for this repo. Come join us! It's great.
  
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
# For the backend
pipx install devon_agent

# For the terminal ui
npm install -g devon-tui

# And for the main UI
npx devon-ui
```

If you already have devon_agent or devon-tui installed, update it by running:
```bash
npm uninstall -g devon-tui
npm install -g devon-tui

pipx install --force devon_agent
```

This installs the Python backend, and the cli command to run the tool

### Thats it! Happy building :)


# Running the agent

Then to *run* the main ui, the command is:
```bash
npx devon-ui
```

It's that simple.

For the terminal ui:

1. Navigate to your project folder and open the terminal.
2. Set your Anthropic API or OpenAI API key as an environment variable:

```bash
export ANTHROPIC_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

#OR

export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

#OR

export GROQ_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

3. Then to *run* the terminal-ui, the command is:
```bash
devon-tui
```

It's as easy as that.

> [!NOTE]
> Don't worry, the agent will be able to only access files and folders in the directory you started it from. You can also correct it while it's performing actions.

---

To run in *debug* mode, the command is:
```bash
devon-tui --debug
```

---

To run in *local* mode:
> [!WARNING]
> The current version of local model support is not mature, proceed with caution, and expect the performance to degrade significantly compared to the other options.

1. Get deepseek running with [ollama](https://ollama.com/library/deepseek-coder:6.7b)

2. Start the local ollama server by running
```
ollama run deepseek-coder:6.7b
```

4. Then configure devon to use the model
```bash
devon-tui configure

Configuring Devon CLI...
? Select the model name: 
  claude-opus 
  gpt4-o 
  llama-3-70b 
❯ ollama/deepseek-coder:6.7b
```

4. And finally, run it with:
```
devon-tui --api_key=FOSS
```

---

For a list of all commands available:
```bash
devon-tui --help
```

# Features
- Multi-file editing
- Codebase exploration
- Config writing
- Test writing
- Bug fixing
- Architecture exploration
- Local Model Support

### Limitations
- Minimal functionality for non-Python languages
- Sometimes have to specify the file where you want the change to happen
- Local mode is not good right now. Please try to avoid using it.

# Progress

### This project is still super early and <ins>we would love your help</ins> to make it great!

### Current goals
- Multi-model support
  - [x] Claude 3 Opus
  - [x] GPT4-o
  - [x] Groq llama3-70b
  - [x] Ollama deepseek-6.7b
  - [ ] Google Gemini 1.5 Pro
- Launch plugin system for tool and agent builders
- Improve our self-hostable Electron app
- Set SOTA on [SWE-bench Lite](https://www.swebench.com/lite.html)

> View our current thoughts on next steps [**here**](https://docs.google.com/document/d/e/2PACX-1vTjLCQcWE_n-uUHFhtBkxTCIJ4FFe5ftY_E4_q69SjXhuEZv_CYpLaQDh3HqrJlAxsgikUx0sTzf9le/pub)

### Star history
<p align="center">
  <a href="https://star-history.com/#entropy-research/Devon&Date">
    <img src="https://api.star-history.com/svg?repos=entropy-research/Devon&type=Date" width="500" alt="Star History Chart">
  </a>
</p>

### Past milestones

- [x] **June 14, 2024** - Launch Electron UI v0.0.13
- [x] **June 1, 2024** - Devon V2 Beta Electron UI
- [x] **May 19, 2024** - GPT4o support + better interface support v0.1.7
- [x] **May 10, 2024** - Complete interactive agent v0.1.0
- [x] **May 10, 2024** - Add steerability features
- [x] **May 8, 2024** - Beat AutoCodeRover on SWE-Bench Lite
- [x] **Mid April, 2024** - Add repo level code search tooling
- [x] **April 2, 2024** - Begin development of v0.1.0 interactive agent
- [x] **March 17, 2024** - Launch non-interactive agent v0.0.1


## Current development priorities

1. Improve context gathering and code indexing abilities ex:
    - Adding memory modules
    - Improved code indexing
2. Add alternative models and agents to:
    - a) Reduce end user cost and
    - b) Reduce end user latency
3. Electron app
    - Better code diff view
    - Timeline interface
    - Send user file events/changes to Devon



# How can I contribute?

Devon and the entropy-research org are community-driven, and we welcome contributions from everyone!
From tackling issues to building features to creating datasets, there are many ways to get involved:

- **Core functionality:** Help us develop the core agents, user experience, tool integrations, plugins, etc.
- **Research:** Help us research agent performance (including benchmarks!), build data pipelines, and finetune models.
- **Feedback and Testing:** Use Devon, report bugs, suggest features, or provide feedback on usability.

For details, please check [CONTRIBUTING.md](./CONTRIBUTING.md).

If you would like to contribute to the project, please join the discord: [Discord](https://discord.gg/p5YpZ5vjd9)

# Feedback

We would love feedback! Feel free to drop us a note on our [Discord](https://discord.gg/p5YpZ5vjd9) in the #feedback channel, or [create issues](https://github.com/entropy-research/Devon/issues)!

We collect basic event type (i.e. "tool call") and failure telemetry to solve bugs and improve the user experience, but if you want to reach out, we would love to hear from you!

To disable telemetry, set the environment variable `DEVON_TELEMETRY_DISABLED` to `true` 
```bash
export DEVON_TELEMETRY_DISABLED=true
```

# Community

Join our Discord server and say hi!
[Discord](https://discord.gg/p5YpZ5vjd9)


# License

Distributed under the AGPL License. See [`LICENSE`](./LICENSE) for more information.
