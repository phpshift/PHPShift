from imports import *


class DeleteTranslation:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Deleting translation files")

        translation_dir = f"{project}/Space"
        pattern = os.path.join(translation_dir, "lng.*.json")
        translation_files = glob.glob(pattern)

        if not translation_files:
            return ""

        options = ["All"]
        for filepath in translation_files:
            filename = os.path.basename(filepath)
            lang_code = filename.replace("lng.", "").replace(".json", "").upper()
            options.append(lang_code)
        options.append("[Back]")

        selected_option = cli.selection(
            "Select a translation to delete:", options, must=True
        )

        if selected_option == "[Back]":
            return False

        if selected_option == "All":
            for filepath in translation_files:
                Patch.add(path=filepath)
                os.remove(filepath)
            return True
        else:
            filename_to_delete = f"lng.{selected_option.lower()}.json"
            filepath_to_delete = os.path.join(translation_dir, filename_to_delete)
            if os.path.exists(filepath_to_delete):
                Patch.add(path=filepath_to_delete)
                os.remove(filepath_to_delete)
                return True
            else:
                cli.trace(
                    f"Error: File not found for selected option '{selected_option}'"
                )
                return False
