pyinstaller devon_agent/__main__.py --hidden-import=tiktoken_ext.openai_public --hidden-import=tiktoken_ext --clean --onefile --collect-all litellm --hidden-import=aiosqlite --hidden-import=dotenv

if [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]]; then
  mkdir -p newelectron/src/bin/$(uname -s)-$(uname -m)
  mv dist/__main__ newelectron/src/bin/$(uname -s)-$(uname -m)/devon_agent
fi

if [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "x86_64" ]]; then
  mkdir -p newelectron/src/bin/$(uname -s)-$(uname -m)
  mv dist/__main__ newelectron/src/bin/$(uname -s)-$(uname -m)/devon_agent
fi
