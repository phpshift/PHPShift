from imports import *


class DeletePage:
    def run(self, message="", project="", skill=""):
        cli.setLoading("Deleting page")

        pages_dir = f"{project}/Pages"
        all_pages = [
            f
            for f in os.listdir(pages_dir)
            if os.path.isdir(os.path.join(pages_dir, f)) and not f.startswith("x.")
        ]

        if not all_pages:
            return False

        # Prepare selection options
        options_map = {}
        display_options = []
        display_options.append("All")
        options_map["All"] = "All"  # Special key for deleting all

        for page_folder in sorted(all_pages):
            parts = page_folder.split(".")
            display_name = (
                f"{' '.join(p.capitalize() for p in parts[1:])} - {parts[0].capitalize()}"
                if len(parts) > 1
                else page_folder.capitalize()
            )
            display_options.append(display_name)
            options_map[display_name] = page_folder

        display_options.append("[Back]")
        options_map["[Back]"] = "[Back]"
        selected_display_name = cli.selection(
            "Select page(s) to delete", display_options, True
        )

        selected_folder_name = options_map.get(selected_display_name)
        if selected_folder_name == "[Back]" or not selected_folder_name:
            return False

        if selected_folder_name == "All":
            cli.unline()
            print()

            if cli.confirmation(
                "Are you sure you want to delete ALL pages?"
            ):
                for page_folder in all_pages:
                    path_to_delete = os.path.join(pages_dir, page_folder)
                    try:
                        Patch.add(path=path_to_delete)
                        shutil.rmtree(path_to_delete)
                        cli.trace(f"Deleted folder: {page_folder}")
                    except Exception as e:
                        cli.trace(f"Failed to delete {page_folder}: {e}")
                        return False
                return True
            else:
                cli.trace("Deletion of all pages cancelled.")
                return False
        else:
            cli.unline()
            print()

            path_to_delete = os.path.join(pages_dir, selected_folder_name)
            if cli.confirmation(
                f"Are you sure you want to delete the page '{selected_folder_name}'?"
            ):
                try:
                    Patch.add(path=path_to_delete)
                    shutil.rmtree(path_to_delete)
                    return True
                except Exception as e:
                    cli.trace(f"Failed to delete page '{selected_folder_name}': {e}")
                    return False
            else:
                cli.trace(f"Deletion of page '{selected_folder_name}' cancelled.")
                return False

        return True
