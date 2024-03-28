import openai
import os
import dotenv
from anthropic import Anthropic

from devon.agent.kernel.thread import Thread
from devon.sandbox.environments import LocalEnvironment

dotenv.load_dotenv()

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Process inputs for the agent.")

    parser.add_argument('--path', type=str, help='File Path', default=os.getcwd())
    parser.add_argument('--repo_url', type=str, help='GitHub Repository URL', default=None)
    parser.add_argument('--goal', type=str, help='Describe your goal')
    args = parser.parse_args()

    repo_url = args.repo_url
    goal = args.goal
    path = args.path

    env = LocalEnvironment()

    if repo_url:
        env.tools.git(path=path).clone(repo_url=repo_url, path=path)

    agent = Thread(task=goal, environment=env)

    agent.run()

if __name__ == "__main__":
    main()
