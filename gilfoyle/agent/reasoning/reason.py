class ReasoningPrompts:
    system="You're a helpful assistant who is incredibly good at understanding what the user wants, the user will provide an AST and you need to reason about what needs to change for the code to be correct, do NOT update the code. ONLY describe the required changes"
    
    def user_msg(goal, code):
        return f"{goal}\n ```code\n{code}```"