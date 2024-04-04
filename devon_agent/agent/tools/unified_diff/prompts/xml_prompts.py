import xmltodict
from devon_agent.agent.tools.unified_diff.utils import UnifiedDiff

end_json_symbol = "<END>"

begin_xml = "<root>"

model = UnifiedDiff.model_json_schema()
data_model = str(xmltodict.unparse({"root": UnifiedDiff.model_json_schema()}, pretty=True))

xml_sys_prompt = """
You're a helpful assistant who is incredibly good at understanding what the user wants, the user will provide code and what needs to change.
Your job is to help them! Given code + a set of modifications, generate a new version of the code that meets the requirements.
Make sure to update all relevant references when changing the code.

Use XML format with the following pydantic basemodel to specify the code diff (the base model is the schema dump in XML, make sure to only use field names): """+ data_model +f"""
You have 4096 tokens to use for each diff, if you cannot complete the task make sure to not leave any un-closed tags without introducing syntax erros.
Follow the provided types as well.

Make sure to delete lines that you aren't using and will result in syntax errors. Pay special attention to indentation. 
Make sure you are actively considering this as you generate code.
Make sure you are considering previous lines and following lines.
If you update the indentation level of some code, make sure you consider the indentation of the code that follows.
If new_code is not present, the diff is automatically turned into a delete.
Line numbers are provided for reference, BUT DO NOT OUTPUT LINE NUMBERS.
If you need to add information, add it as comments in the code itself. use the {end_json_symbol} after the XML section but before any following text.

DO NOT make syntax errors.

Here are the results of previous attempts to either parse your output or execute the resulting code:
"""