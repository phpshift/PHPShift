from imports import *


class DeleteLog:
    def run(self, message="", project="", skill=""):
        cli.setLoading("Deleting log")

        log_folder = os.path.join(project, "Space")
        if not os.path.exists(log_folder):
            return False

        log_files = [
            f[:1].upper() + f[1:-4]
            for f in os.listdir(log_folder)
            if f.endswith(".log") and os.path.isfile(os.path.join(log_folder, f))
        ]

        if not log_files:
            return False

        options = ["All"] + log_files + ["[Back]"]
        selected_file = cli.selection(
            "Select log file(s) to delete:", options, must=True
        )

        if selected_file == "[Back]":
            return False

        if selected_file == "All":
            cli.trace("Deleting all log files...")
            for log_file in log_files:
                file_path = os.path.join(log_folder, log_file + ".log")
                Patch.add(file_path)
                os.remove(file_path)
        else:
            file_path = os.path.join(log_folder, selected_file + ".log")
            Patch.add(file_path)
            os.remove(file_path)

        return True
