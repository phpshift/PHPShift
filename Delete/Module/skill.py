from imports import *


class DeleteModule:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Deleting Module")

        space_dir = f"{project}/Space"
        module_files_map = {}
        options = []

        if not os.path.exists(space_dir):
            cli.trace(f"Directory not found: {space_dir}")
            return False

        found_module_files = [
            f for f in os.listdir(space_dir) if f.endswith(".php") and f[:2] != "x."
        ]

        if not found_module_files:
            cli.trace("No module files detected.")
            return AISI.REPLY(
                AISI.prompt(
                    "No module files were found in your project to delete.", skill
                )
            )

        options.append("All")
        for filename in sorted(found_module_files):
            file_path = os.path.join(space_dir, filename)
            filename_no_ext = os.path.splitext(filename)[0]
            display_name = ""
            version_prefix = ""
            parts = filename_no_ext.split(".", 1)

            if len(parts) > 1 and re.match(r"v\d+", parts[0]):  # e.g., 'v1', 'v2'
                version_prefix = parts[0]
                module_name_camel = parts[1]
            else:
                module_name_camel = filename_no_ext

            display_name = re.sub(r"(?<!^)(?=[A-Z])", " ", module_name_camel).title()
            if version_prefix:
                option_text = f"{display_name} - {version_prefix.upper()}"
            else:
                option_text = display_name

            original_option_text = option_text
            counter = 1
            while option_text in module_files_map:
                option_text = f"{original_option_text} ({counter})"
                counter += 1

            options.append(option_text)
            module_files_map[option_text] = file_path

        options.append("[Back]")
        selected_option = cli.selection("Select module to delete:", options, must=True)

        if selected_option == "[Back]":
            cli.trace("Deletion cancelled by user.")
            return False

        if selected_option == "All":
            cli.trace("Deleting all module files...")
            for filename in found_module_files:
                file_to_delete = os.path.join(space_dir, filename)
                if os.path.exists(file_to_delete):
                    Patch.add(path=file_to_delete)
                    os.remove(file_to_delete)
                    cli.trace(f"Deleted: {file_to_delete}")
            cli.trace("All module files deleted.")

            return True
        else:
            file_to_delete = module_files_map.get(selected_option)
            if file_to_delete and os.path.exists(file_to_delete):
                cli.trace(f"Deleting: {file_to_delete}")
                Patch.add(path=file_to_delete)
                os.remove(file_to_delete)
                cli.trace(f"Deleted: {file_to_delete}")

                return True
            else:
                cli.trace(f"Error: Could not find module file for '{selected_option}'")
                return False

        return True
