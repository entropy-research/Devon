import openai
import os
import dotenv
from anthropic import Anthropic

from gilfoyle.agent.kernel.thread import Thread

dotenv.load_dotenv()

def main():
    repo_url = input("Please enter the GitHub repository URL: ")
    goal = input("Please describe your goal: ")

    agent = Thread(repo_url=repo_url, task=goal)
    agent.run()

if __name__ == "__main__":
    main()
