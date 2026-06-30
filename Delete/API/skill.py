from imports import *


class DeleteAPI:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Deleting API")

        apis_dir = f"{project}/Apis"
        api_files_map = {}
        options = []

        if not os.path.exists(apis_dir):
            cli.trace(f"Directory not found: {apis_dir}")
            return False

        found_api_files = [
            f for f in os.listdir(apis_dir) if f.endswith(".php") and f[:2] != "x."
        ]
        if not found_api_files:
            cli.trace("No API files detected.")
            return AISI.REPLY(
                AISI.prompt("No API files were found in your project to delete.", skill)
            )

        options.append("All")
        for filename in sorted(found_api_files):
            file_path = os.path.join(apis_dir, filename)
            filename_no_ext = os.path.splitext(filename)[0]
            display_name = ""
            version_prefix = ""
            parts = filename_no_ext.split(".", 1)

            if len(parts) > 1 and re.match(r"v\d+", parts[0]):  # e.g., 'v1', 'v2'
                version_prefix = parts[0]
                api_name_camel = parts[1]
            else:
                api_name_camel = filename_no_ext

            display_name = re.sub(r"(?<!^)(?=[A-Z])", " ", api_name_camel).title()
            if version_prefix:
                option_text = f"{display_name} - {version_prefix.upper()}"
            else:
                option_text = display_name

            original_option_text = option_text
            counter = 1
            while option_text in api_files_map:
                option_text = f"{original_option_text} ({counter})"
                counter += 1

            options.append(option_text)
            api_files_map[option_text] = file_path

        options.append("[Back]")
        selected_option = cli.selection("Select API to delete:", options, must=True)

        if selected_option == "[Back]":
            cli.trace("Deletion cancelled by user.")
            return False

        if selected_option == "All":
            cli.trace("Deleting all API files...")
            for filename in found_api_files:
                file_to_delete = os.path.join(apis_dir, filename)
                if os.path.exists(file_to_delete):
                    Patch.add(path=file_to_delete)
                    os.remove(file_to_delete)
                    cli.trace(f"Deleted: {file_to_delete}")
            cli.trace("All API files deleted.")

            return True
        else:
            file_to_delete = api_files_map.get(selected_option)
            if file_to_delete and os.path.exists(file_to_delete):
                cli.trace(f"Deleting: {file_to_delete}")
                Patch.add(path=file_to_delete)
                os.remove(file_to_delete)
                cli.trace(f"Deleted: {file_to_delete}")

                return True
            else:
                cli.trace(f"Error: Could not find API file for '{selected_option}'")
                return False

        return True
