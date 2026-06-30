from imports import *

class ReadLog:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Scanning and analyzing log files")

        log_dir = f"{project}/.system/"
        if not os.path.exists(log_dir):
            cli.trace(f"Log directory not found: {log_dir}")
            return False

        log_files_raw = [f for f in os.listdir(log_dir) if f.endswith(".log")]
        if not log_files_raw:
            cli.trace("No log files with '.log' extension found in .system/ directory.")
            return False

        log_options_map = {f.replace(".log", "").capitalize(): f for f in log_files_raw}
        display_options = sorted(log_options_map.keys())
        display_options.append("[Back]")
        selected_display_name = cli.selection("Select a log file to analyze:", display_options, must=True)

        if selected_display_name == "[Back]":
            cli.trace("Log analysis cancelled by user.")
            return False

        original_filename = log_options_map[selected_display_name]
        full_log_file_path = os.path.join(log_dir, original_filename)
        VAR.log_file_path = full_log_file_path

        prompt = AISI.prompt(message, skill)
        Patch.add(path=f"{project}/summary.md")
        files = AISI.FILES(prompt)
        
        summary_content = files.get("summary.md")
        if not summary_content:
            cli.trace("AI failed to generate summary.md content.")
            del VAR.log_file_path
            return False

        cli.write(f"{project}/summary.md", summary_content)
        cli.command(f"code {project}/summary.md", False, True)
        cli.trace(f"Log summary successfully saved to {project}/summary.md")

        del VAR.log_file_path

        return summary_content
