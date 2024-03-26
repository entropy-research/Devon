import os
from openai import OpenAI
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
import xml.etree.ElementTree as ET
from typing import Callable, Dict, Any, List, get_type_hints
import json
import inspect

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    function: Callable

    @classmethod
    def from_function(cls, function: Callable, name: str, description: str):
        parameters = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        type_hints = get_type_hints(function)
        signature = inspect.signature(function)

        for param_name, param in signature.parameters.items():
            param_type = type_hints.get(param_name, Any)
            param_description = ""
            param_required = True

            if isinstance(param.default, FieldInfo):
                param_description = param.default.description
                param_required = param.default.default == ...

            if param_type == int:
                param_type_name = "integer"
            elif param_type == str:
                param_type_name = "string"
            else:
                param_type_name = param_type.__name__

            parameters["properties"][param_name] = {
                "type": param_type_name,
                "description": param_description,
            }

            if param_required:
                parameters["required"].append(param_name)

        return cls(name=name, description=description, parameters=parameters, function=function)

    def to_dict(self):
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

#     def to_xml(self):
#         parameters_xml = ""
#         for param_name, param_info in self.parameters["properties"].items():
#             parameter_xml = f"""
#         <parameter>
#             <name>{param_name}</name>
#             <type>{param_info["type"]}</type>
#             <description>{param_info["description"]}</description>
#         </parameter>"""
#             parameters_xml += parameter_xml

#         return f"""
# <tool_description>
#     <tool_name>{self.name}</tool_name>
#     <description>{self.description}</description>
#     <parameters>{parameters_xml}
#     </parameters>
# </tool_description>"""

# def parse_function_calls(xml_string: str) -> List[Dict[str, Any]]:
#     root = ET.fromstring(xml_string)
#     function_calls = []

#     for invoke_element in root.findall(".//invoke"):
#         tool_name = invoke_element.find("tool_name").text
#         parameters = {}

#         params_element = invoke_element.find("parameters")
#         if params_element is not None:
#             for param_element in params_element:
#                 param_name = param_element.tag
#                 param_value = param_element.text
#                 parameters[param_name] = param_value

#         function_call = {
#             "tool_name": tool_name,
#             "parameters": parameters
#         }
#         function_calls.append(function_call)

#     return function_calls

class Toolbox:
    def __init__(self):
        self.tools: List[Tool] = []

    def add_tool(self, tool: Tool):
        self.tools.append(tool)

    def get_tool(self, name: str) -> Tool:
        for tool in self.tools:
            if tool.name == name:
                return tool
        raise ValueError(f"Tool with name '{name}' not found.")

    def get_all_tools(self) -> List[Dict[str, Any]]:
        return [tool.to_dict() for tool in self.tools]

    def execute_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, Any]]:
        results = []
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            tool = self.get_tool(function_name)
            function_to_call = tool.function
            function_args = json.loads(tool_call.function.arguments)

            # Get the default values for optional parameters
            signature = inspect.signature(function_to_call)
            default_values = {
                param.name: param.default.default
                for param in signature.parameters.values()
                if isinstance(param.default, FieldInfo) and param.default.default != ...
            }

            # Update the function arguments with default values if not provided
            for param_name, default_value in default_values.items():
                if param_name not in function_args:
                    function_args[param_name] = default_value

            function_response = function_to_call(**function_args)
            results.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "function",
                    "name": function_name,
                    "content": function_response,
                }
            )
        return results
