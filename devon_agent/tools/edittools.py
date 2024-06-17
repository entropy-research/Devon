import os

from devon_agent.tool import Tool, ToolContext
from devon_agent.tools.utils import (check_lint, check_lint_entry_in_list,
                                     make_abs_path, read_file, write_file)
from devon_agent.udiff import (Hallucination, apply_file_context_diffs,
                               extract_all_diffs, log_failed_diff,
                               log_successful_diff)

# from devon_agent.vgit import commit_files, simple_stash_and_commit_changes, stash_and_commit_changes


def apply_diff(ctx, multi_file_diffs):
    """
    Applies the given diffs to the codebase.
    """

    results = []

    for file_diff in multi_file_diffs:
        src_file = file_diff.src_file
        tgt_file = file_diff.tgt_file

        # diff_logger.debug(src_file + " " + tgt_file)
        if not (src_file or tgt_file):
            raise Hallucination(
                "Could not apply changes, missing source or target file."
            )

        # diff_logger.debug("Applying diff to: %s, %s", src_file, tgt_file)

        # Ensure src_file and tgt_file are valid paths, if not, make them absolute paths from file_tree_root
        src_file_abs = make_abs_path(ctx, src_file)
        tgt_file_abs = make_abs_path(ctx, tgt_file)

        src_file_exists = (
            ctx["environment"]
            .execute(f"test -e {src_file_abs} && echo 'exists'")[0]
            .strip()
            == "exists"
        )

        # diff_logger.debug("Applying diff to: %s, %s", src_file_abs, tgt_file_abs)
        cwd = ctx["environment"].get_cwd().strip()

        if tgt_file_abs.startswith(cwd):
            tgt_file_abs = make_abs_path(ctx, tgt_file_abs)
        else:
            tgt_file_abs = make_abs_path(ctx, os.path.join(cwd, tgt_file_abs))

        if src_file_abs.startswith(cwd):
            src_file_abs = make_abs_path(ctx, src_file_abs)
        else:
            src_file_abs = make_abs_path(ctx, os.path.join(cwd, src_file_abs))

        if not src_file_exists:
            raise Exception(
                f"Failed to write diff with source file: {src_file}, {src_file_abs} not open"
            )

        # Modifying an existing file
        src_content = read_file(ctx, file_path=src_file_abs)
        # diff_logger.debug("source content: %s", src_content)

        file_diff.src_file = src_file_abs
        file_diff.tgt_file = tgt_file_abs

        apply_result = apply_file_context_diffs(src_content, [file_diff])
        results.append(apply_result)

    return results


def real_write_diff(ctx, diff):
    """
    Writes the given diff to the codebase.
    """

    diff_code = diff

    all_diffs, _ = extract_all_diffs(diff_code)
    results = apply_diff(ctx, all_diffs)
    failures = []
    successes = []
    for result in results:
        if len(result["fail"]) > 0:
            failures.extend(result["fail"])
            for failure in result["fail"]:
                log_failed_diff(
                    diff=diff_code,
                    file_content=failure[2],
                    src_file=failure[0],
                    tgt_file=failure[0],
                )
        if len(result["success"]) > 0:
            successes.extend(result["success"])
            for success in result["success"]:
                log_successful_diff(
                    diff=diff_code,
                    file_content=success[2],
                    src_file=success[0],
                    tgt_file=success[0],
                )

    if len(failures) == 0 and len(successes) > 0:
        file_paths = []
        diff_results = []
        for result in successes:
            # This will overwrite if the tgt files are the same, but doesnt really matter in this case because its usually only one diff

            target_path = result[0]

            if target_path.endswith(".py"):
                try:
                    compile(result[1], "<string>", "exec")
                    before_results = check_lint(
                        ctx, read_file(ctx, target_path), target_path
                    )
                except Exception as e:
                    return "Error applying diff: \n" + repr(e)

            write_file(ctx, file_path=target_path, content=result[1])
            file_paths.append(target_path)

            if target_path.endswith(".py"):
                after_results = check_lint(ctx, result[1], target_path)

                diff_results = [
                    x
                    for x in after_results
                    if not check_lint_entry_in_list(x, before_results)
                ]

        paths = ", ".join(file_paths)

        if diff_results:
            lint_error_message = ""
            for rst in diff_results:
                lint_error_message += f"{rst['type']}: {rst['message']} on line {rst['line']} column {rst['column']}. Line {result[1].splitlines()[int(rst['line'])-1]} \n"

            return f"Successfully edited file(s): {paths} : Please review the new contents of the files. Your change introduced the following linting errors. Please address them before you submit. \n{lint_error_message}"

        return f"Successfully edited file(s): {paths}: Please review the new contents of the files."

    return "\n".join(["Failed to edit file"] + [f[1].args[0] for f in failures])


class EditFileTool(Tool):
    @property
    def name(self):
        return "edit_file"

    @property
    def supported_formats(self):
        return ["docstring", "manpage"]

    def setup(self, ctx):
        pass

    def cleanup(self, ctx):
        pass

    def documentation(self, format="docstring"):
        match format:
            case "docstring":
                return self.function.__doc__
            case "manpage":
                return """NAME
            edit_file - apply a diff to files in the file system

    SYNOPSIS
            edit_file [DIFF]

    DESCRIPTION
            The edit_file command takes a target DIFF and applies it to files that are open
            in the file system. Someone will edit and double check your work.

            The DIFF argument is a diff string to be applied to specific files. It is similar
            to calling `diff --git "diff string"` where "diff string" is the argument you
            would pass to the edit_file command.

            You ALWAYS need to provide a source AND target file represented with `---` and `+++` even if the source is empty.

            ALWAYS make sure that the code STARTS on its own line.

    RETURN VALUE
            The edit_file command returns a dictionary of all the files that were changed.

    EXAMPLES
            To apply a diff string to open files in the file system:

                    edit_file <<<
                    --- file1.txt
                    +++ file1.txt
                    @@ -1,5 +1,5 @@
                    Line 1
                    -Line 2
                    +Line Two
                    Line 3
                    Line 4
                    Line 5>>>"""

            case _:
                raise ValueError(f"Invalid format: {format}")

    def function(self, ctx: ToolContext, *args, **kwargs) -> str:
        """
        command_name: edit_file
        description: Applies a unified diff to files in the file system
        signature: edit_file [DIFF]
        example: `edit_file <<<
        --- file1.txt
        +++ file1.txt
        @@ -1,5 +1,5 @@
        Line 1
        -Line 2
        +Line Two
        Line 3
        Line 4
        Line 5
        >>>`
        """
        # extract diff
        # apply diff
        # lint
        # write files

        return real_write_diff(ctx, ctx["raw_command"])


def save_edit_file(ctx, response):
    """
    save_edit_file - post func for edit_file
    """
    # vgit
    # if "Successfully edited file(s)" in response:
    #     files = response.split(":")[1].split(", ")
    #     commit = commit_files(ctx["environment"],files, "Deleted file(s) " + " ".join(files))
    #     if commit:
    #         ctx["session"].event_log.append({
    #             "type": "GitEvent",
    #             "content" : {
    #                 "type" : "commit",
    #                 "commit" : commit,
    #                 "files" : files,
    #             }
    #         })
    return response
