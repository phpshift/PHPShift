from imports import *


class DeleteCron:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Deleting cron")

        cron_dir = f"{project}/Crons"

        if not os.path.exists(cron_dir):
            cli.trace(f"Crons directory not found at {cron_dir}.")
            return False

        cron_files = [f for f in os.listdir(cron_dir) if f.endswith(".php")]

        if not cron_files:
            cli.trace("No cron files found to delete.")
            return False

        display_options = ["All"]
        file_map = {}

        for filename in sorted(cron_files):
            display_name = self.__format_filename_to_option(filename)
            display_options.append(display_name)
            file_map[display_name] = filename

        display_options.append("[Back]")

        choice = cli.selection("Select cron to delete:", display_options, True)

        if choice == "[Back]":
            cli.trace("Deletion cancelled by user.")
            return False

        if choice == "All":
            cli.unline()
            print()

            if not cli.confirmation("Are you sure you want to delete ALL cron files?"):
                cli.trace("Deletion of all cron files cancelled.")
                return False

            deleted_count = 0
            for filename in cron_files:
                file_path = os.path.join(cron_dir, filename)
                Patch.add(path=file_path)
                os.remove(file_path)
                deleted_count += 1
            return True
        else:
            cli.unline()
            print()

            selected_filename = file_map[choice]
            file_path = os.path.join(cron_dir, selected_filename)

            if not cli.confirmation(
                f"Are you sure you want to delete '{selected_filename}'?"
            ):
                cli.trace(f"Deletion of '{selected_filename}' cancelled.")
                return False

            Patch.add(path=file_path)
            os.remove(file_path)
            return True

    ####################################################################################// Helpers
    def __format_filename_to_option(self, filename):
        name_without_ext = filename.replace(".php", "")
        # Add space before capital letters and capitalize the first letter of the whole string
        formatted_name = re.sub(r"([A-Z])", r" \1", name_without_ext).strip()
        return formatted_name.capitalize()
