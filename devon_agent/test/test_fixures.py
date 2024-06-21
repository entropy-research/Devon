


# import pytest
# from devon_agent.session import Session, SessionArguments
# from devon_agent.environment import LocalEnvironment

# @pytest.fixture
# def session_fixture():
#     """Fixture to provide a session object with a local environment setup."""
    
#     args = SessionArguments(path="/test/path", user_input=None, name="test_session")
#     env = LocalEnvironment("/test/path")
#     session = Session(args=args, agent=None)
#     session.default_environment = env
#     return session



import os
from devon_agent.agents.default.agent import AgentArguments, TaskAgent

from devon_agent.session import Session,SessionArguments


def session_fixture(tmp_path):
    agent = TaskAgent(
        name="test",
        args=AgentArguments(
            model="gpt4-o",
        ),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    session = Session(args=SessionArguments(path=tmp_path, user_input=None, name="test_session"), agent=agent,persist=False)
    return session

def test_session_lifecycle(tmp_path):
    """Test the event loop."""
    session = session_fixture(tmp_path)
    session.init_state()
    assert session.status == "paused"
    session.start()
    assert session.status == "running"
    session.pause()
    assert session.status == "paused"
    session.start()
    assert session.status == "running"
    # session.terminate()
    # assert session.status == "terminated"