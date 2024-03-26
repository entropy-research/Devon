import openai
import os
import dotenv
from anthropic import Anthropic

from gilfoyle.agent.kernel.thread import Thread
from gilfoyle.sandbox.shell import Shell

dotenv.load_dotenv()

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Process inputs for the agent.")
    parser.add_argument('--repo_url', type=str, help='GitHub repository URL')
    parser.add_argument('--goal', type=str, help='Describe your goal')
    args = parser.parse_args()

    repo_url = args.repo_url
    goal = args.goal

    agent = Thread(repo_url=repo_url, task=goal, shell_environment=Shell)
    agent.run()

if __name__ == "__main__":
    main()
