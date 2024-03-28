class ReasoningPrompts:
    system="""
You are a diligent senior software engineer.
Your job is to take user requirements and describe high level changes required to implement the requirements.
Also mention files that need to be modified, deleted and created seperatly. Your plan will be given to a junior engineering bot to implement.
If file is already present in the code base, you must not create it again.
You will be given relevant code files.
Input format
<REQUIREMENT>
use requirement goes here
</REQUIREMENT>
<FILE_TREE>
file tree from root directory here...
</FILE_TREE>
<CODE>
code files go here ....
</CODE>

Output format
<SCRATCHPAD>
Think step by step here: What needs to change, where is it located, how does it need to change.

If a file already exists you do not need to create it.
</SCRATCHPAD>
<PLAN>
Your plan
</PLAN>
<FILES>
<CREATE>
files to create... (Do not create files that already exist in the code base)
</CREATE>
<MODIFY>
files to modify...
</MODIFY>
<DELETE>
files to delete...
</DELETE>
<FILES/>"""

    def user_msg(goal, code, file_tree):
        return f"<REQUIREMENT>\n{goal}\n</REQUIREMENT>\n<FILE_TREE>{file_tree}\n</FILE_TREE>\n<CODE>\n{code}\n</CODE>"

    def parse_msg(output):
        plan = output.split("<PLAN>")[1].split("</PLAN>")[0]

        files = output.split("<FILES>")[1].split("</FILES>")

        create = None
        modify = None
        delete = None

        files_to_edit = []

        if "<CREATE>" in output:
            create = output.split("<CREATE>")[1].split("</CREATE>")[0].splitlines()
            files_to_edit += create
        if "<MODIFY>" in output:
            modify = output.split("<MODIFY>")[1].split("</MODIFY>")[0].splitlines()
            files_to_edit += modify
        if "<DELETE>" in output:
            delete = output.split("<DELETE>")[1].split("</DELETE>")[0].splitlines()
            files_to_edit += delete

        return plan, create, modify, delete, files_to_edit