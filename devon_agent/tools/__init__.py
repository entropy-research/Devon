import re

# def parse_command(ctx, command: str) -> tuple:
#     """
#     Parses a command string into its function name and arguments.

#     Args:
#         command (str): The command string to parse.

#     Returns:
#         tuple: A tuple containing the function name (str) and a list of arguments (list).
#     """
#     parts = command.split(None, 1)
#     fn_name = parts[0]
#     args = []

#     if len(parts) > 1:
#         arg_string = parts[1]

#         line_0 = command.splitlines()[1]

#         if "<<<" in line_0 and ">>>" in arg_string:
#             # Handle multiline arguments
#             before_multiline, multiline_arg = arg_string.split("<<<", 1)
#             multiline_arg, after_multiline = multiline_arg.split(">>>", 1)

#             if before_multiline:
#                 temp_pre = re.findall(r'(?:[^\s"]+|"[^"]*")+', before_multiline)
#                 args.extend([arg.strip('"').strip("'") for arg in temp_pre])

#             args.append(multiline_arg.strip())

#             if after_multiline:
#                 args.extend(
#                     [arg.strip('"').strip("'") for arg in after_multiline.split()]
#                 )
#         else:
#             # Handle single line arguments
#             temp_pre = re.findall(r'(?:[^\s"]+|"[^"]*")+', arg_string)
#             args = [arg.strip('"').strip("'") for arg in temp_pre]

#     return fn_name, args

def parse_command(command: str) -> tuple:
    """
    Parses a command string into its function name and arguments.

    Args:
        command (str): The command string to parse.

    Returns:
        tuple: A tuple containing the function name (str) and a list of arguments (list).
    """
    if "<<<" in command:
        parts = command.split("<<<", 1)
        before_multiline = parts[0].strip()
        multiline_arg = parts[1].strip()

        if ">>>" not in multiline_arg:
            raise ValueError("No closing fence (>>>) found for multiline argument.")

        multiline_arg, _ = multiline_arg.split(">>>", 1)
        multiline_arg = multiline_arg.strip()

        fn_name, *args = re.findall(r'(?:[^\s"]+|"[^"]*")+', before_multiline)
        args.append(multiline_arg)
    else:
        fn_name, *args = re.findall(r'(?:[^\s"]+|"[^"]*")+', command)

    args = [arg.strip('"').strip("'") for arg in args]
    return fn_name, args

def parse_commands(commands: str) -> list:
    """
    Parses a string containing multiple commands into a list of tuples.

    Args:
        commands (str): The string containing multiple commands to parse.

    Returns:
        list: A list of tuples, where each tuple contains the function name (str) and a list of arguments (list).
    """
    command_list = []
    commands = commands.strip()

    while commands:
        if "<<<" in commands.split("\n", 1)[0]:
            if ">>>" not in commands:
                raise ValueError(f"Error parsing command: {commands}, No '>>>' closing fence found")
            
            pre_command, _, post_command = commands.partition("<<<")
            command, _, remainder = post_command.partition(">>>")
            command = pre_command.strip() + " <<< " + command.strip() + " >>>"
        else:
            command, _, remainder = commands.partition("\n")

        command = command.strip()
        if command:
            command_list.append(command)

        commands = remainder.strip()

    parsed_commands = []
    for command in command_list:
        try:
            fn_name, args = parse_command(command)
            parsed_commands.append((fn_name, args))
        except ValueError as e:
            raise ValueError(f"Error parsing command: {command}. {str(e)}")

    return parsed_commands
