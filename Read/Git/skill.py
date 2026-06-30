from imports import *
import os

class ReadGit:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Converting request to Git command...")

        prompt_content_for_command = AISI.prompt(message, skill)
        command_files = AISI.FILES(prompt_content_for_command)
        git_command = command_files.get("command.sh", "").strip()

        if not cli.confirmation(f'Confirm to execute "{git_command}" command'):
            return False

        if not git_command:
            return cli.error("Failed to generate a Git command. Please try rephrasing your request.")

        if not git_command.startswith("git"):
             git_command = "git " + git_command.lstrip()

        cli.trace(f"Generated Git command: {git_command}")
        cli.setLoading("Executing Git command...")

        try:
            git_output = cli.command(git_command, True, True, project, True)
        except Exception as e:
            return cli.error(f"Error executing Git command: {e}\nOutput captured: {git_output if 'git_output' in locals() else 'No output available.'}")

        cli.trace(f"Git command output:\n{git_output}")
        cli.setLoading("Summarizing Git command output...")

        summary_instruction_prompt = (
            "You are a skilled technical writer. "
            "Analyze the following Git command output and create a concise, informative summary in Markdown format. "
            "Highlight key details, success/failure indicators, and any relevant information. "
            "Output should be a single file named 'summary.md'.\n\n"
            "--- Git Command Output ---\n"
            f"{git_output}\n"
            "-------------------------"
        )

        summary_files = AISI.FILES(summary_instruction_prompt)
        summary_content = summary_files.get("summary.md", "").strip()

        if not summary_content:
            return cli.error("Failed to generate summary from Git command output.")

        summary_path = os.path.join(project, "summary.md")
        Patch.add(path=summary_path)
        cli.write(file=summary_path, content=summary_content)
        cli.setLoading("Opening summary in editor...")
        cli.command(f"code \"{summary_path}\"", False, True)

        return summary_content