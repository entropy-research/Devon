import os
import openai

openai.api_key = os.environ["OPENAI_API_KEY"]

def main():
    print("Welcome to the LLM Dungeon Master RPG!")
    
    while True:
        player_input = input("> ")
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful dungeon master in a text-based RPG game."},
                {"role": "user", "content": player_input}
            ],
            max_tokens=100,
            n=1,
            stop=None,
            temperature=0.7,
        )
        
        print(f"Dungeon Master: {response.choices[0].message.content.strip()}")

if __name__ == "__main__":
    main()
