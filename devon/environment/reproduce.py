
import unittest

class TestEnvironment(unittest.TestCase):
    def test_parse_command_to_function(self):
        env = TaskEnvironment(".")
        result = env.parse_command_to_function("search_dir test")
        self.assertIsInstance(result, str)

if __name__ == '__main__':
    unittest.main()

