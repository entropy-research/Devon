# Running the agent
Navigate to your project folder and open the terminal.

Set your provider's API key as an environment variable:

```bash
export ANTHROPIC_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

#OR

export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

#OR

export GROQ_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Then to *run*, the command is:
```bash
devon
```

It's as easy as that.

> [!NOTE]
> Don't worry, the agent will be able to only access files and folders in the directory you started it from. You can also correct it while it's performing actions.

---

To run in *debug* mode, the command is:
```bash
devon --debug
```

---
To disable telemetry, set the environment variable `DEVON_TELEMETRY_DISABLED` to `true` 
```bash
export DEVON_TELEMETRY_DISABLED=true
```