# Devon : Open Source SWE Agent

# Usage

To use simply install using pip

```bash
pip install devon_agent
```
Set the Anthropic API key as an environment variable

```bash
export ANTHROPIC_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Set the OpenAI API key
```bash
export OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Then you can use the agent to modify your code

```bash
devon --goal "print hello world when the application starts" --path agent/src/main.py
```

# Features
- Reliable Multi File Editing
- use tools such as git

# Coming soon
- UI for interacting with the agent
- Application generation from requirements 
- Find bugs in existing code
- SWE tasks such as architecture design, code review, and more
- Custom model for large context window and code ability

# About
Devin is an open-source SWE agent that aims to help software engineers with the development and maintenance of software. 

# Mission
Coding agents are powerful and we believe that the core of this technology should be open source. 
We are excited to be a part of the open source community and we are looking forward to collaborating with other developers to build a better future for software engineering.

# Contributing

If you would like to contribute to the project, please fill out this form:

[Contribution Form](https://forms.gle/VU7RN7mwNvqEYe3B9)


# Community

Join our discord server and say hi!
[discord](https://discord.gg/p5YpZ5vjd9)

