import sys

game_world = {
    "Entrance": {
        "description": "You stand at the entrance of Hogwarts. The grand oak doors lead north into the castle.",
        "exits": {"north": "Great Hall"}
    },
    "Great Hall": {
        "description": "You enter the magnificent Great Hall. Four long tables fill the room, one for each Hogwarts house. Enchanted candles float above, illuminating the hall with a warm glow.",
        "exits": {"south": "Entrance", "east": "Grand Staircase", "west": "Classroom Corridor"}
    },
    "Classroom Corridor": {
        "description": "You are in a corridor lined with classrooms. The Charms classroom is to the north, Transfiguration to the south.",
        "exits": {"east": "Great Hall"}
    },
    "Grand Staircase": {
        "description": "You stand at the bottom of the grand staircase. The stairs shift above you, leading to multiple floors and wings of the castle.",
        "exits": {"west": "Great Hall", "up": "Gryffindor Common Room", "north": "Headmaster's Office"}
    },
    "Gryffindor Common Room": {
        "description": "You enter the cozy Gryffindor common room. A fire crackles in the hearth and students lounge on plush red sofas.",
        "exits": {"down": "Grand Staircase"}
    },
    "Headmaster's Office": {
        "description": "You approach the entrance to the headmaster's office. A large gargoyle statue guards the door.",
        "exits": {"south": "Grand Staircase"},
        "items": {
            "desk": "A large, ornate desk covered in various magical instruments.",
            "phoenix": "A majestic phoenix perches on a stand, watching you calmly."
        }
    }
}

current_location = "Entrance"

def main():
    print("Welcome to the Text Adventure Game!")
    
    while True:
        location = game_world[current_location]
        print(location["description"])
        print("Exits:", ", ".join(location["exits"].keys()))
        
        command = input("> ")
        if command.lower() in location["exits"]:
            current_location = location["exits"][command.lower()]
        elif command.lower().startswith("examine "):
            item_name = command.lower()[8:]
            if item_name in location.get("items", {}):
                print(location["items"][item_name])
            else:
                print(f"You don't see a {item_name} here.")
        if command.lower() in ["quit", "exit"]:
            print("Thanks for playing!")
            sys.exit()
        else:
            print(f"You entered: {command}")

if __name__ == "__main__":
    main()
