



import os
from anthropic import Anthropic
from gilfoyle.agent.clients.client import ClaudeHaiku


system_prompt = """You are a diligent and patient requirements engineer. Your job is to ask questions to gather requirements. After each question summarize the intermediate requirements in a doc. After each question show the user the req document you have so far. Stick to one question at a time. Once you have gathered all requirements reply with <done></done>
"""




if __name__ == "__main__":

    anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    converstaion = [{"role": "user", "content": "Help me write requirements for a project"}]
    res = anthropic.messages.create(
        system=system_prompt,
        max_tokens=4000,
        temperature=0.5,
        model="claude-3-haiku-20240307",
        stop_sequences=["<done></done>"],
        messages=converstaion)

    converstaion.append({
        "role": "assistant",
        "content": res.content[0].text
    })
    while True:
        ans = input(res.content[0].text + "\n")
        # print(converstaion)
        print()
        converstaion.append({
            "role": "user",
            "content": ans
        })
        res = anthropic.messages.create(
            system=system_prompt,
            max_tokens=4000,
            temperature=0.5,
            model="claude-3-opus-20240229",
            stop_sequences=["<done></done>"],
            messages=converstaion)


        converstaion.append({
            "role": "assistant",
            "content": res.content[0].text
        })

        if "</done>" in res.content[0].text:
            print(res.content[0].text)
            break
        print()




# Project Purpose:
# - Download 1 million YouTube videos for training a machine learning model.

# Video Requirements:
# - Videos should be selected randomly to ensure data diversity.
# - Each video should have over 1,000 views.
# - No specific duration requirements for the videos.
# - Videos should be downloaded in MP4 format.
# - Videos should have a resolution of 480p.

# Storage Requirements:
# - All downloaded videos should be stored in a cloud object storage service, such as Amazon S3.
# - The naming convention for the stored videos should be "title-datecreated.mp4".

# Error Handling and Logging:
# - Logging should be implemented to track the video download process.
# - In case of any errors during the download process, a notification should be sent to the appropriate parties.
