import openai
import os
import dotenv
from anthropic import Anthropic

from thread import Thread

dotenv.load_dotenv()

def main():
    repo_url = input("Please enter the GitHub repository URL: ")
    file_path = input("Please enter the file path: ")
    goal = input("Please describe your goal: ")

    agent = Thread(repo_url=repo_url, task=goal, file_path=file_path)
    agent.run()

if __name__ == "__main__":
    main()
