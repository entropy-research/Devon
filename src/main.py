import openai
import os
import dotenv
from anthropic import Anthropic

dotenv.load_dotenv()

def fix_code(broken_code):

    client = Anthropic(
        # This is the default and can be omitted
        api_key = os.environ.get("ANTHROPIC_API_KEY"),
    )

    message = client.messages.create(
        max_tokens=1024,
        system="It's your job to solve bugs for people, people will present you with code and you should do your best to help them, its ok if you dont know, just say that",
        messages=[
            {
                "role": "user",
                "content": "```python print('hi) ```",
            }
        ],
        model="claude-3-opus-20240229",
    )

    os.system("ls .")

if __name__ == "__main__":
    fix_code("bad_code")