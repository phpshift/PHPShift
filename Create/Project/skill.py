from imports import *


class CreateProject:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Creating the project")

        prompt = AISI.prompt(message, skill)
        pages = AISI.FILES(prompt)
        if not pages:
            return {}

        if "config.json" not in pages:
            return {}

        config = json.loads(pages.get("config.json", "{}"))
        VAR.styling = config.get("landing-page", "").strip()
        if not VAR.styling:
            return {}

        cli.trace("Configuring landing page")

        Help.setEnv("PROJECT_LANDING", VAR.styling)
        cli.command(f"code {project}/.env", False, True)

        if "db.sql" in pages and pages["db.sql"].strip() != "":
            sql_file = project + "/db.sql"
            cli.write(sql_file, pages["db.sql"])
            cli.command("code " + sql_file, False, True)
            if cli.selection("Confirm to update database", ["Go", "No"], True) == "Go":
                cli.trace("Updating database")
                DB.reset()
                DB.new(DB.name())
                DB.submit(pages["db.sql"])
            os.remove(sql_file)

        for each in pages:
            if each in ["config.json"]:
                continue

            parts = each.split(".")
            if len(parts) != 3:
                cli.trace(f"Skipping '{each}'")
                continue

            group, page, extension = parts
            if (
                not group
                or not page
                or page in ["README", "readme"]
                or extension != "md"
            ):
                cli.trace(f"Skipping '{group}.{page}'")
                continue

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

        if "README.md" in pages and pages["README.md"].strip() != "":
            Patch.add(project + "/README.md")
            cli.write(project + "/README.md", pages["README.md"])

        AISI.run("", "Create.SEO")

        default = f"{project}/Pages/public.phpshift"
        if cli.isFolder(default):
            Patch.add(default)
            shutil.rmtree(default)

        lng_en = f"{project}/Space/lng.en.json"
        if cli.isFile(lng_en):
            Patch.add(lng_en)
            os.remove(lng_en)

        lng_ka = f"{project}/Space/lng.ka.json"
        if cli.isFile(lng_ka):
            Patch.add(lng_ka)
            os.remove(lng_ka)

        Help.updateSitemap()
        VAR.styling = ""

        return pages

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
