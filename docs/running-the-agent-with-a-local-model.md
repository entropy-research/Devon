
# Running the agent with a *local* model

> [!WARNING]
> The current version of local model support is not mature, proceed with caution, and expect the performance to degrade significantly compared to the other options.

1. Get deepseek running with [ollama](https://ollama.com/library/deepseek-coder:6.7b)

2. Start the local ollama server by running
```
ollama run deepseek-coder:6.7b
```

4. Then configure devon to use the model
```bash
devon configure

Configuring Devon CLI...
? Select the model name: 
  claude-opus 
  gpt4-o 
  llama-3-70b 
❯ ollama/deepseek-coder:6.7b
```

4. And finally, run it with:
```
devon --api_key=FOSS
```
