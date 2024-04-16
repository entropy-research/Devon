import os

from devon.swebenchenv.environment.unified_diff.udiff import apply_context_diff, parse_multi_file_diffs


def test_diff():

    cases = ["case0","case1","case3"]

    current_file = __file__
    current_dir = os.path.dirname(current_file)

    for case in cases:

        file_content = open(current_dir + f"/files/{case}.py").read()
        file_diff = open(current_dir + f"/diffs/{case}").read()
        excepted = open(current_dir + f"/expected/{case}.py").read()

        # apply fuction
        diffs = parse_multi_file_diffs(file_diff)
        
        assert len(diffs) == 1

        result = apply_context_diff(file_content, diffs[0])

        #  write to file
        with open(current_dir + f"/results/{case}.py", "w") as f:
            f.write(result)

        assert result == excepted






