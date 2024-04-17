import os

from flaky import flaky

from anthropic import Anthropic
from devon.swebenchenv.environment.unified_diff.prompts.udiff_prompts import UnifiedDiffPrompts

from devon.swebenchenv.environment.unified_diff.udiff import apply_context_diff, apply_multi_file_context_diff, create_recover_prompt, extract_all_diffs, parse_multi_file_diffs
from devon_agent.agent.clients.client import ClaudeHaiku, ClaudeSonnet, Message


def test_diff():

    cases = ["case0","case1","case2"]
    # cases = ["case2"]

    current_file = __file__
    current_dir = os.path.dirname(current_file)

    for case in cases:

        print(case)

        file_content = open(current_dir + f"/files/{case}.py").read()
        file_diff = open(current_dir + f"/diffs/{case}").read()
        excepted = open(current_dir + f"/expected/{case}.py").read()

        result, total_changed = apply_multi_file_context_diff(file_content, file_diff, None)

        result_code = result["success"][0][1]

        #  write to files
        with open(current_dir + f"/results/{case}.py", "w") as f:
            f.write(result_code)

        assert result_code == excepted


# def test_repair_apply():

#     api_key=os.environ.get("ANTHROPIC_API_KEY")
#     anthrpoic_client = Anthropic(api_key=api_key)
#     diff_model = ClaudeSonnet(client=anthrpoic_client, system_message=UnifiedDiffPrompts.main_system_v2, max_tokens=4096)

#     diff_case = "case4"
#     file_case = "case1"
#     current_file = __file__
#     current_dir = os.path.dirname(current_file)

#     file_content = open(current_dir + f"/files/{file_case}.py").read()
#     file_diff = open(current_dir + f"/diffs/{diff_case}").read()

#     print(file_diff)

#     original_change_count = None
#     original_diff = file_diff

#     attempts = 0
#     fixed = False
#     while not fixed and attempts < 5:

#         res = apply_multi_file_context_diff(file_content, file_diff)

#         failures = []
#         successes = []
#         if len(res["fail"]) > 0:
#             failures.extend(res["fail"])
#         if len(res["success"]) > 0:
#             successes.extend(res["success"])

#         if len(failures) == 0:
#             fixed = True
#             break
#         else:
#             attempts += 1

#             msg = create_recover_prompt({failures[0][0].tgt_file:file_content}, file_diff, failures)

#             file_diff = diff_model.chat([
#                 Message(
#                     role="user",
#                     content=msg
#                 )
#             ])

#     #TODO: assert changed line count is the same

#     assert(fixed == True)

def execute_repair(diff_case, file_case):
    api_key=os.environ.get("ANTHROPIC_API_KEY")
    anthrpoic_client = Anthropic(api_key=api_key)
    diff_model = ClaudeSonnet(client=anthrpoic_client, system_message=UnifiedDiffPrompts.main_system_v3, max_tokens=4096, temperature=0.0)

    current_file = __file__
    current_dir = os.path.dirname(current_file)

    file_content = open(current_dir + f"/files/{file_case}.py").read()
    file_diff = open(current_dir + f"/diffs/{diff_case}").read()

    print(file_diff)

    original_change_count = None
    original_diff = file_diff

    attempts = 0
    fixed = False
    while not fixed and attempts < 5:

        res, total_changed = apply_multi_file_context_diff(file_content, file_diff, original_change_count)

        if original_change_count is None:
            original_change_count = total_changed

        failures = []
        successes = []
        if len(res["fail"]) > 0:
            failures.extend(res["fail"])
        if len(res["success"]) > 0:
            successes.extend(res["success"])

        if len(failures) == 0:
            fixed = True
            break
        else:
            print("\n\n*********\n")
            print("\n".join([f[1].args[0] for f in failures]))
            print("\n*********\n\n")
            attempts += 1

            try:
                msg = create_recover_prompt({failures[0][0].tgt_file:file_content}, original_diff, file_diff, failures)
            except:
                msg = create_recover_prompt({"":file_content}, original_diff, file_diff, failures)

            file_diff = diff_model.chat([
                Message(
                    role="user",
                    content=msg
                )
            ])

    #TODO: assert changed line count is the same

    assert(fixed == True)
    print("\nPASSED: ", diff_case, "\n")

# @flaky(max_runs=3, min_passes=2)
def test_repair_apply1():
    execute_repair("case4", "case1")

def test_repair_apply2():
    execute_repair("case5", "case5")

# def test_repair_apply2():

#     api_key=os.environ.get("ANTHROPIC_API_KEY")
#     anthrpoic_client = Anthropic(api_key=api_key)
#     diff_model = ClaudeSonnet(client=anthrpoic_client, system_message=UnifiedDiffPrompts.main_system_v3, max_tokens=4096, temperature=0.2)

#     diff_case = "case5"
#     file_case = "case5"
#     current_file = __file__
#     current_dir = os.path.dirname(current_file)

#     file_content = open(current_dir + f"/files/{file_case}.py").read()
#     file_diff = open(current_dir + f"/diffs/{diff_case}").read()

#     print(file_diff)

#     original_change_count = None
#     original_diff = file_diff

#     attempts = 0
#     fixed = False
#     while not fixed and attempts < 6:

#         res, total_changed = apply_multi_file_context_diff(file_content, file_diff, original_change_count)

#         if original_change_count is None:
#             original_change_count = total_changed

#         failures = []
#         successes = []
#         if len(res["fail"]) > 0:
#             failures.extend(res["fail"])
#         if len(res["success"]) > 0:
#             successes.extend(res["success"])

#         if len(failures) == 0:
#             fixed = True
#             break
#         else:
#             attempts += 1

#             try:
#                 msg = create_recover_prompt({failures[0][0].tgt_file:file_content}, original_diff, file_diff, failures)
#             except:
#                 msg = create_recover_prompt({"":file_content}, original_diff, file_diff, failures)

#             file_diff = diff_model.chat([
#                 Message(
#                     role="user",
#                     content=msg
#                 )
#             ])

#     #TODO: assert changed line count is the same

#     assert(fixed == True)