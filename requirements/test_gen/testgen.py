


user_prompt = lambda user_requirements: f"""
<prompt_explanation> You are a TDD expert. You will be given user requirements. Your job is to break them down and craft end to end tests that when pass indicate that the code meets the requirements. Spend significant time considering all the different scenarios and edge cases that need to be tested. Next, brainstorm a list of test cases you think will be necessary to match the requirements. Assume that if the application is a cli, you will be given a name of the binary. If the application is a webserver you will be given the name of the url. If it is a function you will be given the signature. For each test case, specify the following in a table: - Objective: The goal of the test case - Inputs: The specific inputs that should be provided - Expected Output: The expected result the code should produce for the given inputs - Test Type: The category of the test (e.g. positive test, negative test, edge case, etc.) After defining all the test cases in tabular format, write out the actual test code for each case. Ensure the test code follows these steps: 1. Arrange: Set up any necessary preconditions and inputs 2. Act: Execute the code being tested 3. Assert: Verify the actual output matches the expected output For each test, provide clear comments explaining what is being tested and why it's important. Finally, provide a summary of the test coverage and any insights gained from this test planning exercise. ALWAYS USE PYTEST. You should prefer integration tests, property tests over unit tests. If you are testing for an exception do not assume the error message, just check for an error state.</prompt_explanation> <response_format><repsponse> <code_analysis_section> <header>Code Analysis:</header> <analysis>$code_analysis</analysis> </code_analysis_section> <test_cases_section> <header>Test Cases:</header> <table> <header_row> <column1>Objective</column1> <column2>Inputs</column2> <column3>Expected Output</column3> <column4>Test Type</column4> </header_row> $test_case_table </table> </test_cases_section> <test_code_section> <header>Test Code:</header> $test_code </test_code_section> <test_review_section> <header>Test Review:</header> <review>$test_review</review> </test_review_section> <coverage_summary_section> <header>Test Coverage Summary:</header> <summary>$coverage_summary</summary> <insights>$insights</insights> </coverage_summary_section> </response> </response_format> Here are the requirements that you must generate test cases for: 

<requirements>
{user_requirements}
</requirements>
"""


import os
from anthropic import Anthropic
import xmltodict

def get_tests_from_reposne(response):

    response =  "<response>"  + response.split('<response>')[1].split('</response>')[0]  + "</response>"
    response = xmltodict.parse(response)
    print(response)
    return "\n".join(response["response"]["test_code_section"]["#text"].split("\n")[1:-1])

import random
def get_tests_from_requirements(requirements, temperature=0.5,model = "claude-3-haiku-20240307"):

    anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    converstaion = [{"role": "user", "content": user_prompt(requirements)}]

    res = anthropic.messages.create(
        system="You are a black box tester",
        max_tokens=4000,
        temperature=temperature,
        model=model,
        # stop_sequences=["<done></done>"],
        messages=converstaion)
    
    print(res.content[0].text)
    
    return get_tests_from_reposne(res.content[0].text)

if __name__ == "__main__":
    print(get_tests_from_requirements("""
    The CLI application is a simple command-line tool that performs basic arithmetic operations on two numbers. It accepts three command-line arguments: the operation to be performed (either "add" or "multiply"), the first number, and the second number. The application should handle these arguments correctly and perform the specified operation on the provided numbers. For the "add" operation, the application should add the two numbers together and display the result. Similarly, for the "multiply" operation, it should multiply the two numbers and display the result. The application should handle invalid operations gracefully by raising an exception or displaying an appropriate error message. The numbers provided as arguments should be parsed as integers. The application should be implemented in Python and should be executable from the command line using the python command followed by the script name and the required arguments. The result format is "Result: <result/>" where <result/> is the result of the operation. The python file should be named "cli_app.py".
"""))
    