import os

from devon.swebenchenv.environment.unified_diff.udiff import apply_context_diff, apply_multi_file_context_diff, parse_multi_file_diffs


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

        # apply fuction
        # diffs = parse_multi_file_diffs(file_diff)
        
        # assert len(diffs) == 1

        result = apply_multi_file_context_diff(file_content, file_diff)

        result_code = result["success"][0][1]

        #  write to files
        with open(current_dir + f"/results/{case}.py", "w") as f:
            f.write(result_code)

        assert result_code == excepted






