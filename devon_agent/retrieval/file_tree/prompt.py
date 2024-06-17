def generate_file_summary_prompt(file_name, content):
    content = f"""

file name: {file_name}

content-
{content}"""
    
    system_prompt = """You are an advanced software engineer and your task is to understand the code and create a brief summary of the file. Look at at all the top level classes, functions, etc and create a quick overview of what each code block does are trying to achieve and then create a summary at the end.

output should be-

imports-
[mention any interesting imports.]

list of function/classes-

[function_name / names]-
[quick description]

summary of the file-
[quick summary of what you infer the file is trying to do]"""

    messages = [{"content": system_prompt, "role": "system"}, {"content": content, "role": "user"}]

    return messages