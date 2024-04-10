# PROMPT 
# Few shot examples
# State
# Observation

# Expect
# Thought
# Action


import os
from typing import Dict, List, Union


# def history_to_bash_prompt(history : List[Dict]):
#   shell = """"""
#   for h in history:
#     observation, action, state, thought = h['observation'], h['action'], h['state'], h['thought']
#     shell += f"""
#     (Thought: {thought})
#     (cwd {state["cwd"]})
#     bash-$ {action} 
#     {observation}\n"""

#   return shell


def commands_to_command_docs(commands : List[Dict]):
   doc = """"""
   for command in commands:
      signature, docstring = command['signature'], command['docstring']
      doc += f"""
      {signature}
      {docstring}


      """
   return doc


def system_prompt_template(command_docs : str):
   return f"""
<SETTING>
    You are an autonomous programmer, and you're working directly in the command line and a special workspace.

    This workspace contians a folder tree viewer of your existing project, editor containing files that you can edit, and a terminal that you can use to run commands.

    You will also get a history of your previous actions and why you did them.
</SETTING>
<COMMANDS>
  {command_docs}
</COMMANDS>
<REPONSE FORMAT>
  Your shell prompt is formatted as follows:
  <cwd> $

  You need to format your output using two fields; thought and command.
  Your output should always include _one_ thought and _one_ command field EXACTLY as in the following example:
  <EXAMPLE>
  <THOUGHT>
  Let me start by reproducing the issue I'm trying to solve.
  </THOUGHT>
  <COMMAND>
  create_file reproduce_issue.py
  </COMMAND>
  </EXAMPLE>

  You will be given a <EDITOR> containing all the files that you have opened. Close all the files that you are not using. Use the open files to understand the content of those files.

  COMMAND OUTPUT SYNTAX:

  WRONG: 
  command1 arg1 arg2 arg3
  command2 arg1 arg2

  CORRECT:
  command1 arg1
  
  You should only include a *SINGLE* command in the command section and then wait for a response from the shell before continuing with more discussion and commands. Everything you include in the THOUGHT section will be saved for future reference.
  If you'd like to issue two commands at once, PLEASE DO NOT DO THAT! Please instead first submit just the first command, and then after receiving a response you'll be able to issue the second command.
  You're free to use any other bash commands you want (e.g. find, grep, cat, ls, cd) in addition to the special commands listed above.
  However, the environment does NOT support interactive session commands (e.g. python, vim), so please do not invoke them.
</REPONSE FORMAT>
"""

# TODO: More description for the workspace

def history_to_bash_history(history):
    
            # self.history.append(
            # {
            #     "role": "assistant",
            #     "content": output,
            #     "thought": thought,
            #     "action": action,
            #     "agent": self.name,

  bash_history = ""
  for entry in history:

    if entry["role"] == "user":
      bash_history += f"{entry['content']}\n"
    elif entry["role"] == "assistant":
        bash_history += f"""
(thought: {entry['thought']})
(current_dir: {entry['state']['cwd']})
bash $ {entry['action'][1:]}
"""
  return bash_history



def object_to_xml(data: Union[dict, bool], root='object'):
    xml = f'<{root}>'
    if isinstance(data, dict):
        for key, value in data.items():
            xml += object_to_xml(value, key)

    elif isinstance(data, (list, tuple, set)):
        for item in data:
            xml += object_to_xml(item, 'item')

    else:
        xml += str(data)

    xml += f'</{root}>'
    return xml

def print_tree(directory, level=0, indent=''):
    string =""
    for name, content in directory.items():
        if isinstance(content, dict):
            string += f"\n{indent}├── {name}/"
            string += print_tree(content, level + 1, indent + '│   ')
        else:
            string += f"\n{indent}├── {name}"
            
    return string

def last_user_prompt_template(issue,history,filetree,editor,working_dir):
   return f"""
  We're currently solving the following issue within our repository. Here's the issue text:
  <ISSUE>
  {issue}
  </ISSUE>

  <INSTRUCTIONS>
  Edit all the files you need to and run any checks or tests that you want. 
  Remember, YOU CAN ONLY ENTER ONE COMMAND AT A TIME. 
  You should always wait for feedback after every command. 
  When you're satisfied with all of the changes you've made, you can submit your changes to the code base by simply running the submit command.
  Note however that you cannot use any interactive session commands (e.g. python, vim) in this environment, but you can write scripts and run them. E.g. you can write a python script and then run it with `python <script_name>.py`.

  </INSTRUCTIONS>
  
  NOTE ABOUT THE EDIT COMMAND: Indentation really matters! When editing a file, make sure to insert appropriate indentation before each line! 

  IMPORTANT TIPS:
  1. Always start by trying to replicate the bug that the issues discusses. Make reproduce_issue.py a script that does this.
     If the issue includes code for reproducing the bug, we recommend that you re-implement that in your environment, and run it to make sure you can reproduce the bug.
     Then start trying to fix it.
     When you think you've fixed the bug, re-run the bug reproduction script to make sure that the bug has indeed been fixed.
     
     If the bug reproduction script does not print anything when it succesfully runs, we recommend adding a print("Script completed successfully, no errors.") command at the end of the file,
     so that you can be sure that the script indeed ran fine all the way through. 

  2. If you run a command and it doesn't work, try running a different command. A command that did not work once will not work the second time unless you modify it!

  3. If you have files open in your editor, make sure to close them if you're not going to be editing them. Too many open files can slow down your environment and confuse you.

  4. If the bug reproduction script requires inputting/reading a specific file, such as buggy-input.png, and you'd like to understand how to input that file, conduct a search in the existing repo code, to see whether someone else has already done that. Do this by running the command: find_file "buggy-input.png" If that doensn't work, use the linux 'find' command. 

  5. Always make sure to look at the currently open file and the current working directory (which appears right after the currently open file). The currently open file might be in a different directory than the working directory! Note that some commands, such as 'create', open files, so they might change the current  open file.

  6. When editing files, make sure that those files are open in your editor.

  7. Always think step by step. Write pseudocode in case you're not sure how to do something.

  8. If you are not sure how to do something, try to find a similar command in the documentation. If you are still not sure exit

  9. Once you're done use the submit command to submit your solution.

  10. Avoid searching. Open files in editor and use the content in editor to understand the file.

  11. Before trying to make a fix, try to identify the root cause. Explore the codebase and pinpoint the source of the problem. Then fix it.

  <WORKSPACE>
  <FOLDERTREE>
  {filetree}
  </FOLDERTREE>
  <EDITOR>
  {editor}
  </EDITOR> 
  </WORKSPACE>
  <HISTORY>
  {history}
  </HISTORY>

  ONLY GENERATE ONE COMMAND AT A TIME. DO NOT USE MULTIPLE COMMANDS AT THE SAME TIME. ONLY THE FIRST COMMAND WILL BE EXECUTED. 
  Make sure to not repeat the same command more than once.
"""

"""
  <WORKSPACE>
  <FOLDERTREE>
  {filetree}
  </FOLDERTREE>
  <EDITOR>
  {editor}
  </EDITOR> 
  </WORKSPACE>
  <SHELL>
  {observation}
  (Open file: {open_file})
  (Current directory: {working_dir})
  bash-$
  </SHELL>
"""
"""
  Here is a demonstration of how to correctly accomplish this task.
  It is included to show you how to correctly use the interface.
  You do not need to follow exactly what is done in the demonstration.
  --- DEMONSTRATION ---
  {demonstration}
  --- END OF DEMONSTRATION ---
state_command:
"""

system_prompt = lambda actions : f"""
You are an expert software engineer.

<actions>
{actions}
</actions>

example response:
<reponse>
<thought>
The code is not working because the function is not returning the correct value. I should change the function
</thought>
<action>

</action>"""

user_prompt_template = lambda FS, editor, observation: f"""

<state>
<FS>
{FS}
</FS>
Here is the current editor. Conatins files you have opened.
<editor>
{editor}
</editor>
</state>
<observation>
{observation}
</observation>

"""

def parse_response(response):
    thought = response.split("<THOUGHT>")[1].split("</THOUGHT>")[0]
    action = response.split("<COMMAND>")[1].split("</COMMAND>")[0]
    try:
      assert response.count("<COMMAND>") == 1
      assert response.count("<THOUGHT>") == 1
    except AssertionError as e:
       print(response)
       raise e
    return thought, action


if __name__ == "__main__":
   
  history = [{'role': 'system', 'content': "\nYou are an expert software engineer.\n\n<actions>\n['submit', 'exit_context', 'exit_cost', 'exit_error', 'exit_format', 'exit_api', 'skip', 'list_files', 'list_files_recursive', 'close_file', 'open_file', 'view_open_files', 'execute_python_file', 'search_dir', 'search_file', 'search_files', 'get_cwd']\n</actions>\n\nexample response:\n<reponse>\n<thought>\nThe code is not working because the function is not returning the correct value. I should change the function\n</thought>\n<action>\n\n</action>"}, 
             {'role': 'user', 'content': None, 'agent': 'primary'}, 
             {'role': 'assistant', 'content': '<THOUGHT>\nTo start, I should create a script to reproduce the issue described in the problem statement. This will allow me to verify that I can replicate the bug before attempting to fix it.\n</THOUGHT>\n\n<COMMAND>\ncreate_file reproduce_issue.py\n</COMMAND>', 'thought': '\nTo start, I should create a script to reproduce the issue described in the problem statement. This will allow me to verify that I can replicate the bug before attempting to fix it.\n', 'action': '\ncreate_file reproduce_issue.py\n', 'agent': 'primary', 'state': {'file_tree': {'sqlfluff__sqlfluff': {'.git': {'branches': {}, 'hooks': {}, 'info': {}, 'refs': {'heads': {}, 'tags': {}, 'remotes': {'origin': {}}}, 'objects': {'pack': {}, 'info': {}}, 'logs': {'refs': {'remotes': {'origin': {}}, 'heads': {}}}}, '.github': {'ISSUE_TEMPLATE': {}, 'workflows': {}}, 'docs': {'source': {'_static': {'images': {}}}}, 'examples': {}, 'images': {}, 'plugins': {'sqlfluff-plugin-example': {'test': {'rules': {'test_cases': {}}}, 'src': {'example': {}}}, 'sqlfluff-templater-dbt': {'sqlfluff_templater_dbt': {}}}, 'src': {'sqlfluff': {'api': {}, 'cli': {}, 'core': {'dialects': {}, 'linter': {}, 'parser': {'grammar': {}, 'segments': {}}, 'plugin': {}, 'rules': {'analysis': {}}, 'templaters': {}}, 'dialects': {}, 'rules': {}, 'testing': {}}, 'sqlfluff.egg-info': {}}, 'test': {'api': {}, 'cli': {}, 'core': {'parser': {}, 'rules': {}, 'templaters': {}}, 'dialects': {}, 'fixtures': {'cli': {}, 'config': {'inheritance_a': {'nested': {}}, 'inheritance_b': {'nested': {}}, 'toml': {}}, 'dialects': {'ansi': {}, 'bigquery': {}, 'exasol': {}, 'hive': {}, 'mysql': {}, 'snowflake': {}, 'sqlite': {}, 'teradata': {}, 'tsql': {}, 'postgres': {}}, 'lexer': {}, 'linter': {'autofix': {'ansi': {'001_long_line': {}, '002_indentation': {}, '003_long_line': {}, '004_indentation': {}, '005_function_spacing': {}, '006_indentation': {}, '007_with_clause': {}, '008_with_clause': {}, '009_keyword_capitalisation': {}, '010_CTEs_and_newlines': {}, '011_indentation': {}, '012_templating': {}, '013_order_by_explicit': {}, '014_looping_interaction_between_l008_and_l030': {}, '015_jinja_leading_whitespace': {}, '016_index_error_with_jinja_if': {}, '016_index_error_with_jinja_if2': {}, '019_trailing_comma_to_leading': {}, '020_L008_trailing_comma': {}, '021_fix_respects_noqa': {}, '008_looping_rules_l003_l016_l019': {}, '016_no_fix_in_template_loops': {}, '017_lintresult_fixes_cannot_span_block_boundaries': {}, '018_l003_indent_templated_code': {}}, 'bigquery': {'001_templating': {}, '002_templating': {}, '003_templating': {}, '004_templating': {}, '005_unnest_spacing': {}}, 'snowflake': {'001_semi_structured': {}}}, 'diffquality': {}, 'sqlfluffignore': {'path_a': {}, 'path_b': {}}}, 'rules': {'custom': {'bad_rule_name': {}}, 'std_rule_cases': {}}, 'templater': {'jinja_a': {}, 'jinja_b': {}, 'jinja_d_roundtrip': {}, 'jinja_e': {}, 'jinja_f': {}, 'jinja_g_macros': {'macros': {}}, 'jinja_h_macros': {'macros': {}}, 'jinja_i_raw': {}, 'jinja_j_libraries': {'libs': {}}, 'jinja_k_config_override_path_macros': {'macros': {}}, 'jinja_l_metas': {}, 'jinja_c_dbt': {}}, 'dbt': {'dbt_project': {'macros': {}, 'models': {'depends_on_ephemeral': {}, 'my_new_project': {}}, 'tests': {}}, 'error_models': {}}}, 'rules': {}}, 'benchmarks': {'bench_002': {}}}, '': {}}, 'editor': {}, 'cwd': '/', 'issue': 'TSQL - L031 incorrectly triggers "Avoid using aliases in join condition" when no join present\n## Expected Behaviour\r\n\r\nBoth of these queries should pass, the only difference is the addition of a table alias \'a\':\r\n\r\n1/ no alias\r\n\r\n```\r\nSELECT [hello]\r\nFROM\r\n    mytable\r\n```\r\n\r\n2/ same query with alias\r\n\r\n```\r\nSELECT a.[hello]\r\nFROM\r\n    mytable AS a\r\n```\r\n\r\n## Observed Behaviour\r\n\r\n1/ passes\r\n2/ fails with: L031: Avoid using aliases in join condition.\r\n\r\nBut there is no join condition :-)\r\n\r\n## Steps to Reproduce\r\n\r\nLint queries above\r\n\r\n## Dialect\r\n\r\nTSQL\r\n\r\n## Version\r\n\r\nsqlfluff 0.6.9\r\nPython 3.6.9\r\n\r\n## Configuration\r\n\r\nN/A\n'}}, {'role': 'user', 'content': '"OCI runtime exec failed: exec failed: unable to start container process: exec: \\"create_file\\": executable file not found in $PATH: unknown\\r\\n"', 'agent': 'primary'}, {'role': 'assistant', 'content': '<THOUGHT>\nTo start, I should create a script to reproduce the issue described in the problem statement. This will allow me to verify that I can replicate the bug before attempting to fix it.\n</THOUGHT>\n\n<COMMAND>\ncreate_file reproduce_issue.py\n</COMMAND>', 'thought': '\nTo start, I should create a script to reproduce the issue described in the problem statement. This will allow me to verify that I can replicate the bug before attempting to fix it.\n', 'action': '\ncreate_file reproduce_issue.py\n', 'agent': 'primary', 'state': {'file_tree': {'sqlfluff__sqlfluff': {'.git': {'branches': {}, 'hooks': {}, 'info': {}, 'refs': {'heads': {}, 'tags': {}, 'remotes': {'origin': {}}}, 'objects': {'pack': {}, 'info': {}}, 'logs': {'refs': {'remotes': {'origin': {}}, 'heads': {}}}}, '.github': {'ISSUE_TEMPLATE': {}, 'workflows': {}}, 'docs': {'source': {'_static': {'images': {}}}}, 'examples': {}, 'images': {}, 'plugins': {'sqlfluff-plugin-example': {'test': {'rules': {'test_cases': {}}}, 'src': {'example': {}}}, 'sqlfluff-templater-dbt': {'sqlfluff_templater_dbt': {}}}, 'src': {'sqlfluff': {'api': {}, 'cli': {}, 'core': {'dialects': {}, 'linter': {}, 'parser': {'grammar': {}, 'segments': {}}, 'plugin': {}, 'rules': {'analysis': {}}, 'templaters': {}}, 'dialects': {}, 'rules': {}, 'testing': {}}, 'sqlfluff.egg-info': {}}, 'test': {'api': {}, 'cli': {}, 'core': {'parser': {}, 'rules': {}, 'templaters': {}}, 'dialects': {}, 'fixtures': {'cli': {}, 'config': {'inheritance_a': {'nested': {}}, 'inheritance_b': {'nested': {}}, 'toml': {}}, 'dialects': {'ansi': {}, 'bigquery': {}, 'exasol': {}, 'hive': {}, 'mysql': {}, 'snowflake': {}, 'sqlite': {}, 'teradata': {}, 'tsql': {}, 'postgres': {}}, 'lexer': {}, 'linter': {'autofix': {'ansi': {'001_long_line': {}, '002_indentation': {}, '003_long_line': {}, '004_indentation': {}, '005_function_spacing': {}, '006_indentation': {}, '007_with_clause': {}, '008_with_clause': {}, '009_keyword_capitalisation': {}, '010_CTEs_and_newlines': {}, '011_indentation': {}, '012_templating': {}, '013_order_by_explicit': {}, '014_looping_interaction_between_l008_and_l030': {}, '015_jinja_leading_whitespace': {}, '016_index_error_with_jinja_if': {}, '016_index_error_with_jinja_if2': {}, '019_trailing_comma_to_leading': {}, '020_L008_trailing_comma': {}, '021_fix_respects_noqa': {}, '008_looping_rules_l003_l016_l019': {}, '016_no_fix_in_template_loops': {}, '017_lintresult_fixes_cannot_span_block_boundaries': {}, '018_l003_indent_templated_code': {}}, 'bigquery': {'001_templating': {}, '002_templating': {}, '003_templating': {}, '004_templating': {}, '005_unnest_spacing': {}}, 'snowflake': {'001_semi_structured': {}}}, 'diffquality': {}, 'sqlfluffignore': {'path_a': {}, 'path_b': {}}}, 'rules': {'custom': {'bad_rule_name': {}}, 'std_rule_cases': {}}, 'templater': {'jinja_a': {}, 'jinja_b': {}, 'jinja_d_roundtrip': {}, 'jinja_e': {}, 'jinja_f': {}, 'jinja_g_macros': {'macros': {}}, 'jinja_h_macros': {'macros': {}}, 'jinja_i_raw': {}, 'jinja_j_libraries': {'libs': {}}, 'jinja_k_config_override_path_macros': {'macros': {}}, 'jinja_l_metas': {}, 'jinja_c_dbt': {}}, 'dbt': {'dbt_project': {'macros': {}, 'models': {'depends_on_ephemeral': {}, 'my_new_project': {}}, 'tests': {}}, 'error_models': {}}}, 'rules': {}}, 'benchmarks': {'bench_002': {}}}, '': {}}, 'editor': {}, 'cwd': '/', 'issue': 'TSQL - L031 incorrectly triggers "Avoid using aliases in join condition" when no join present\n## Expected Behaviour\r\n\r\nBoth of these queries should pass, the only difference is the addition of a table alias \'a\':\r\n\r\n1/ no alias\r\n\r\n```\r\nSELECT [hello]\r\nFROM\r\n    mytable\r\n```\r\n\r\n2/ same query with alias\r\n\r\n```\r\nSELECT a.[hello]\r\nFROM\r\n    mytable AS a\r\n```\r\n\r\n## Observed Behaviour\r\n\r\n1/ passes\r\n2/ fails with: L031: Avoid using aliases in join condition.\r\n\r\nBut there is no join condition :-)\r\n\r\n## Steps to Reproduce\r\n\r\nLint queries above\r\n\r\n## Dialect\r\n\r\nTSQL\r\n\r\n## Version\r\n\r\nsqlfluff 0.6.9\r\nPython 3.6.9\r\n\r\n## Configuration\r\n\r\nN/A\n'}}, {'role': 'user', 'content': '"OCI runtime exec failed: exec failed: unable to start container process: exec: \\"create_file\\": executable file not found in $PATH: unknown\\r\\n"', 'agent': 'primary'}, {'role': 'assistant', 'content': '<THOUGHT>\nTo start, I should create a script to reproduce the issue described in the problem statement. This will allow me to verify that I can replicate the bug before attempting to fix it.\n</THOUGHT>\n\n<COMMAND>\ncreate_file reproduce_issue.py\n</COMMAND>', 'thought': '\nTo start, I should create a script to reproduce the issue described in the problem statement. This will allow me to verify that I can replicate the bug before attempting to fix it.\n', 'action': '\ncreate_file reproduce_issue.py\n', 'agent': 'primary', 'state': {'file_tree': {'sqlfluff__sqlfluff': {'.git': {'branches': {}, 'hooks': {}, 'info': {}, 'refs': {'heads': {}, 'tags': {}, 'remotes': {'origin': {}}}, 'objects': {'pack': {}, 'info': {}}, 'logs': {'refs': {'remotes': {'origin': {}}, 'heads': {}}}}, '.github': {'ISSUE_TEMPLATE': {}, 'workflows': {}}, 'docs': {'source': {'_static': {'images': {}}}}, 'examples': {}, 'images': {}, 'plugins': {'sqlfluff-plugin-example': {'test': {'rules': {'test_cases': {}}}, 'src': {'example': {}}}, 'sqlfluff-templater-dbt': {'sqlfluff_templater_dbt': {}}}, 'src': {'sqlfluff': {'api': {}, 'cli': {}, 'core': {'dialects': {}, 'linter': {}, 'parser': {'grammar': {}, 'segments': {}}, 'plugin': {}, 'rules': {'analysis': {}}, 'templaters': {}}, 'dialects': {}, 'rules': {}, 'testing': {}}, 'sqlfluff.egg-info': {}}, 'test': {'api': {}, 'cli': {}, 'core': {'parser': {}, 'rules': {}, 'templaters': {}}, 'dialects': {}, 'fixtures': {'cli': {}, 'config': {'inheritance_a': {'nested': {}}, 'inheritance_b': {'nested': {}}, 'toml': {}}, 'dialects': {'ansi': {}, 'bigquery': {}, 'exasol': {}, 'hive': {}, 'mysql': {}, 'snowflake': {}, 'sqlite': {}, 'teradata': {}, 'tsql': {}, 'postgres': {}}, 'lexer': {}, 'linter': {'autofix': {'ansi': {'001_long_line': {}, '002_indentation': {}, '003_long_line': {}, '004_indentation': {}, '005_function_spacing': {}, '006_indentation': {}, '007_with_clause': {}, '008_with_clause': {}, '009_keyword_capitalisation': {}, '010_CTEs_and_newlines': {}, '011_indentation': {}, '012_templating': {}, '013_order_by_explicit': {}, '014_looping_interaction_between_l008_and_l030': {}, '015_jinja_leading_whitespace': {}, '016_index_error_with_jinja_if': {}, '016_index_error_with_jinja_if2': {}, '019_trailing_comma_to_leading': {}, '020_L008_trailing_comma': {}, '021_fix_respects_noqa': {}, '008_looping_rules_l003_l016_l019': {}, '016_no_fix_in_template_loops': {}, '017_lintresult_fixes_cannot_span_block_boundaries': {}, '018_l003_indent_templated_code': {}}, 'bigquery': {'001_templating': {}, '002_templating': {}, '003_templating': {}, '004_templating': {}, '005_unnest_spacing': {}}, 'snowflake': {'001_semi_structured': {}}}, 'diffquality': {}, 'sqlfluffignore': {'path_a': {}, 'path_b': {}}}, 'rules': {'custom': {'bad_rule_name': {}}, 'std_rule_cases': {}}, 'templater': {'jinja_a': {}, 'jinja_b': {}, 'jinja_d_roundtrip': {}, 'jinja_e': {}, 'jinja_f': {}, 'jinja_g_macros': {'macros': {}}, 'jinja_h_macros': {'macros': {}}, 'jinja_i_raw': {}, 'jinja_j_libraries': {'libs': {}}, 'jinja_k_config_override_path_macros': {'macros': {}}, 'jinja_l_metas': {}, 'jinja_c_dbt': {}}, 'dbt': {'dbt_project': {'macros': {}, 'models': {'depends_on_ephemeral': {}, 'my_new_project': {}}, 'tests': {}}, 'error_models': {}}}, 'rules': {}}, 'benchmarks': {'bench_002': {}}}, '': {}}, 'editor': {}, 'cwd': '/', 'issue': 'TSQL - L031 incorrectly triggers "Avoid using aliases in join condition" when no join present\n## Expected Behaviour\r\n\r\nBoth of these queries should pass, the only difference is the addition of a table alias \'a\':\r\n\r\n1/ no alias\r\n\r\n```\r\nSELECT [hello]\r\nFROM\r\n    mytable\r\n```\r\n\r\n2/ same query with alias\r\n\r\n```\r\nSELECT a.[hello]\r\nFROM\r\n    mytable AS a\r\n```\r\n\r\n## Observed Behaviour\r\n\r\n1/ passes\r\n2/ fails with: L031: Avoid using aliases in join condition.\r\n\r\nBut there is no join condition :-)\r\n\r\n## Steps to Reproduce\r\n\r\nLint queries above\r\n\r\n## Dialect\r\n\r\nTSQL\r\n\r\n## Version\r\n\r\nsqlfluff 0.6.9\r\nPython 3.6.9\r\n\r\n## Configuration\r\n\r\nN/A\n'}}, {'role': 'user', 'content': '"OCI runtime exec failed: exec failed: unable to start container process: exec: \\"create_file\\": executable file not found in $PATH: unknown\\r\\n"', 'agent': 'primary'}, {'role': 'assistant', 'content': '<THOUGHT>\nTo start, I should create a script to reproduce the issue described in the problem statement. This will allow me to verify that I can replicate the bug before attempting to fix it.\n</THOUGHT>\n\n<COMMAND>\ncreate_file reproduce_issue.py\n</COMMAND>', 'thought': '\nTo start, I should create a script to reproduce the issue described in the problem statement. This will allow me to verify that I can replicate the bug before attempting to fix it.\n', 'action': '\ncreate_file reproduce_issue.py\n', 'agent': 'primary', 'state': {'file_tree': {'sqlfluff__sqlfluff': {'.git': {'branches': {}, 'hooks': {}, 'info': {}, 'refs': {'heads': {}, 'tags': {}, 'remotes': {'origin': {}}}, 'objects': {'pack': {}, 'info': {}}, 'logs': {'refs': {'remotes': {'origin': {}}, 'heads': {}}}}, '.github': {'ISSUE_TEMPLATE': {}, 'workflows': {}}, 'docs': {'source': {'_static': {'images': {}}}}, 'examples': {}, 'images': {}, 'plugins': {'sqlfluff-plugin-example': {'test': {'rules': {'test_cases': {}}}, 'src': {'example': {}}}, 'sqlfluff-templater-dbt': {'sqlfluff_templater_dbt': {}}}, 'src': {'sqlfluff': {'api': {}, 'cli': {}, 'core': {'dialects': {}, 'linter': {}, 'parser': {'grammar': {}, 'segments': {}}, 'plugin': {}, 'rules': {'analysis': {}}, 'templaters': {}}, 'dialects': {}, 'rules': {}, 'testing': {}}, 'sqlfluff.egg-info': {}}, 'test': {'api': {}, 'cli': {}, 'core': {'parser': {}, 'rules': {}, 'templaters': {}}, 'dialects': {}, 'fixtures': {'cli': {}, 'config': {'inheritance_a': {'nested': {}}, 'inheritance_b': {'nested': {}}, 'toml': {}}, 'dialects': {'ansi': {}, 'bigquery': {}, 'exasol': {}, 'hive': {}, 'mysql': {}, 'snowflake': {}, 'sqlite': {}, 'teradata': {}, 'tsql': {}, 'postgres': {}}, 'lexer': {}, 'linter': {'autofix': {'ansi': {'001_long_line': {}, '002_indentation': {}, '003_long_line': {}, '004_indentation': {}, '005_function_spacing': {}, '006_indentation': {}, '007_with_clause': {}, '008_with_clause': {}, '009_keyword_capitalisation': {}, '010_CTEs_and_newlines': {}, '011_indentation': {}, '012_templating': {}, '013_order_by_explicit': {}, '014_looping_interaction_between_l008_and_l030': {}, '015_jinja_leading_whitespace': {}, '016_index_error_with_jinja_if': {}, '016_index_error_with_jinja_if2': {}, '019_trailing_comma_to_leading': {}, '020_L008_trailing_comma': {}, '021_fix_respects_noqa': {}, '008_looping_rules_l003_l016_l019': {}, '016_no_fix_in_template_loops': {}, '017_lintresult_fixes_cannot_span_block_boundaries': {}, '018_l003_indent_templated_code': {}}, 'bigquery': {'001_templating': {}, '002_templating': {}, '003_templating': {}, '004_templating': {}, '005_unnest_spacing': {}}, 'snowflake': {'001_semi_structured': {}}}, 'diffquality': {}, 'sqlfluffignore': {'path_a': {}, 'path_b': {}}}, 'rules': {'custom': {'bad_rule_name': {}}, 'std_rule_cases': {}}, 'templater': {'jinja_a': {}, 'jinja_b': {}, 'jinja_d_roundtrip': {}, 'jinja_e': {}, 'jinja_f': {}, 'jinja_g_macros': {'macros': {}}, 'jinja_h_macros': {'macros': {}}, 'jinja_i_raw': {}, 'jinja_j_libraries': {'libs': {}}, 'jinja_k_config_override_path_macros': {'macros': {}}, 'jinja_l_metas': {}, 'jinja_c_dbt': {}}, 'dbt': {'dbt_project': {'macros': {}, 'models': {'depends_on_ephemeral': {}, 'my_new_project': {}}, 'tests': {}}, 'error_models': {}}}, 'rules': {}}, 'benchmarks': {'bench_002': {}}}, '': {}}, 'editor': {}, 'cwd': '/', 'issue': 'TSQL - L031 incorrectly triggers "Avoid using aliases in join condition" when no join present\n## Expected Behaviour\r\n\r\nBoth of these queries should pass, the only difference is the addition of a table alias \'a\':\r\n\r\n1/ no alias\r\n\r\n```\r\nSELECT [hello]\r\nFROM\r\n    mytable\r\n```\r\n\r\n2/ same query with alias\r\n\r\n```\r\nSELECT a.[hello]\r\nFROM\r\n    mytable AS a\r\n```\r\n\r\n## Observed Behaviour\r\n\r\n1/ passes\r\n2/ fails with: L031: Avoid using aliases in join condition.\r\n\r\nBut there is no join condition :-)\r\n\r\n## Steps to Reproduce\r\n\r\nLint queries above\r\n\r\n## Dialect\r\n\r\nTSQL\r\n\r\n## Version\r\n\r\nsqlfluff 0.6.9\r\nPython 3.6.9\r\n\r\n## Configuration\r\n\r\nN/A\n'}}, {'role': 'user', 'content': '"OCI runtime exec failed: exec failed: unable to start container process: exec: \\"create_file\\": executable file not found in $PATH: unknown\\r\\n"', 'agent': 'primary'}]

  print(history_to_bash_history(history))