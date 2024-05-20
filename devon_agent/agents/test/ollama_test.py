import unittest


from devon_agent.agents.default.agent import TaskAgent
from devon_agent.session import SessionArguments, Session
from devon_agent.agents.model import ModelArguments, OllamaModel
from devon_agent.agents.default.ollama_prompts import (
    ollama_system_prompt_template,
    ollama_user_prompt_template,
    ollama_commands_to_command_docs,
    parse_response
)


class OllamaTest(unittest.TestCase):
    def setUp(self):
        agent = TaskAgent(model='gpt4-o', name='test_agent')

        se_args = SessionArguments(
            name='test_session',
            path='../../../../',
            user_input='Hello World'
        )
        session = Session(se_args, agent)

        command_docs = list(session.generate_command_docs().values())
        command_docs = (
                "Custom Commands Documentation:\n"
                + ollama_commands_to_command_docs(command_docs)
                + "\n"
        )

        self.sys_prompt = ollama_system_prompt_template('phi3', command_docs)
        self.model_args = ModelArguments(
            model_name='phi3',
            temperature=0.1
        )

    def test_sys_correct_format(self):
        """Ensure system prompt yields a response with correct formatting"""
        model = OllamaModel(self.model_args)
        test_queries = [
            {'role': 'user', 'content': 'search the file test.txt'},
            {'role': 'user', 'content': 'Create a Python script called hello.py with content print("Hello, World!")'},
            {'role': 'user', 'content': 'Could you please open the file existing_file.txt?'}
        ]

        for q in test_queries:
            response = model.query(
                system_message=self.sys_prompt,
                messages=[q]
            )
            err_msg = f"OllamaModel Test: wrong response format\n{response}"

            out = parse_response(response)
            self.assertIsNotNone(out, err_msg)

            thought, action, scratchpad = out
            self.assertIsNotNone(thought, err_msg)
            self.assertIsNotNone(action, err_msg)

    def test_usr_correct_format(self):
        pass


if __name__ == '__main__':
    unittest.main()
