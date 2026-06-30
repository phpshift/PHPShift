from imports import *


class CreateProject:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Creating the project")

        prompt = AISI.prompt(message, skill)
        files = AISI.FILES(prompt)
        if not files:
            return {}

        if "config.json" not in files:
            return {}

        config = json.loads(files.get("config.json", "{}"))
        VAR.styling = config.get("landing-page", "").strip()
        if not VAR.styling:
            return {}

        cli.trace("Configuring landing page")

        Help.setEnv("PROJECT_LANDING", VAR.styling)
        cli.command(f"code {project}/.env", False, True)

        if "db.sql" in files and files["db.sql"].strip() != "":
            sql_file = project + "/db.sql"
            cli.write(sql_file, files["db.sql"])
            cli.command("code " + sql_file, False, True)
            if cli.selection("Confirm to update database", ["Go", "No"], True) == "Go":
                cli.trace("Updating database")
                DB.reset()
                DB.new(DB.name())
                DB.submit(files["db.sql"])
            os.remove(sql_file)

        for each in files:
            if each in ["config.json"]:
                continue

            parts = each.split("/")
            if parts[-1].endswith(".md"):
                parts[-1] = parts[-1].replace(".md", "")

            if parts[-1] in ["README", "readme"]:
                continue

            if each.startswith("page/"):
                unit, group, page = parts
                cli.trace(f"Creating {unit} '{group}.{page}'")
                AISI.run(
                    {
                        "group": group,
                        "page": page,
                        "description": "Create new page, here is the description:\n\n"
                        + files[each],
                        "internal": True,
                    },
                    "Render.Page",
                )
                pass

            if each.startswith("api/"):
                unit, api = parts
                cli.trace(f"Creating {unit} '{api}'")
                AISI.run(
                    "Create new API, here is the description:\n\n" + files[each],
                    "Create.API",
                )
                pass

            if each.startswith("cron/"):
                unit, cron = parts
                cli.trace(f"Creating {unit} '{cron}'")
                AISI.run(
                    "Create new cron job, here is the description:\n\n" + files[each],
                    "Create.Cron",
                )
                pass

        if "README.md" in files and files["README.md"].strip() != "":
            Patch.add(project + "/README.md")
            cli.write(project + "/README.md", files["README.md"])

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

        return files

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
