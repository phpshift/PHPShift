from imports import *


class EditProject:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Editing the project")

        prompt = AISI.prompt(message, skill)
        pages = AISI.FILES(prompt)
        if not pages:
            return {}

        for each in pages:
            parts = each.split(".")
            if len(parts) != 3:
                cli.trace(f"Skipping '{each}'")
                continue
            group, page, extension = parts
            if (
                not group
                or not page
                or page in ["README", "readme", "strategy"]
                or extension != "md"
            ):
                cli.trace(f"Skipping '{group}.{page}'")
                continue
            if not os.path.exists(project + f"/Pages/{group}.{page}/code.php"):
                cli.trace(f"Creating '{group}.{page}'")
                AISI.run(
                    {
                        "group": group,
                        "page": page,
                        "description": "Create new page, here is the description:\n\n"
                        + pages[each],
                        "internal": True,
                    },
                    "Render.Page",
                )
            else:
                cli.trace(f"Editing '{group}.{page}'")
                VAR.target = f"{group}.{page}"
                AISI.run(
                    "Edit code, here is the description:\n\n" + pages[each],
                    "Edit.Page",
                )
                VAR.target = ""
            time.sleep(1)

        if "db.sql" in pages and pages["db.sql"].strip() != "":
            sql_file = os.path.join(project, "db.sql")
            cli.write(sql_file, pages["db.sql"])
            cli.command("code " + sql_file, False, True)
            if cli.selection("Confirm to update database", ["Go", "No"], True) == "Go":
                cli.trace("Updating database")
                DB.submit(pages["db.sql"])
            os.remove(sql_file)

        if "README.md" in pages and pages["README.md"].strip() != "":
            Patch.add(project + "/README.md")
            cli.write(project + "/README.md", pages["README.md"])

        Help.updateSitemap()

        return pages

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
