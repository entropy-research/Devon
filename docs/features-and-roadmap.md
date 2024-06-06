
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
- Create self-hostable Electron app
- Set SOTA on [SWE-bench Lite](https://www.swebench.com/lite.html)

> View our current thoughts on next steps [**here**](https://docs.google.com/document/d/e/2PACX-1vTjLCQcWE_n-uUHFhtBkxTCIJ4FFe5ftY_E4_q69SjXhuEZv_CYpLaQDh3HqrJlAxsgikUx0sTzf9le/pub)


### Past milestones

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
3. Introduce Electron app and new UI

