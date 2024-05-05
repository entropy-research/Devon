def main():
    from devon.environment.agent import TaskAgent
    from devon.environment.session import Session, SessionArguments

    args = SessionArguments(
        path="/Users/mihirchintawar/agent/examples",
        model="claude-opus",
        temperature=0.0,
        environment="local",
        user_input=input,
    )

    chat_history = []

    task = (
        "Make a python application that can read a json file and covert it a csv file"
    )

    agent = TaskAgent(
        "Devon", args, args.model, args.temperature, chat_history=chat_history
    )

    session = Session(args, agent)

    session.enter()
    session.event_log.append(
        {"type": "Task", "content": task, "identifier": agent.name}
    )
    session.step_event()


if __name__ == "__main__":
    main()
