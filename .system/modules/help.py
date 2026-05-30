from imports import *


class Help:
    ####################################################################################// Params
    app = ""
    cwd = ""
    args = []
    config = {}

    ####################################################################################// Load
    def __init__(self, app="", cwd="", args=[]):
        Help.app, Help.cwd, Help.args = app, cwd, args
        pass

    ####################################################################################// Main
    def codeEditor(page_group, page_name, page_code={}, internal=False):
        if not os.path.exists(Help.cwd):
            return False
        if not page_group:
            page_group = "public"
        if not page_group:
            page_group = "page"
        if len(page_code) == 0:
            return False

        config = json.loads(page_code.get("config.json", "{}"))
        page_path = f"{Help.cwd}/Pages/{page_group}.{page_name}"
        page_exists = os.path.exists(os.path.join(page_path, "code.php"))

        Patch.add(page_path)
        cli.trace("Creating page folder")
        os.makedirs(page_path, exist_ok=True)

        for filename, content in page_code.items():
            if filename in [
                "config.json",
                # "",
            ]:
                continue
            file_path = os.path.join(page_path, filename)
            Patch.add(file_path)
            cli.trace(f"Injecting page file '{filename}'")
            cli.write(file_path, content)

        if (
            not page_exists
            and "page.html" in page_code
            and page_code["page.html"].strip() != ""
        ):
            if not Help.groupMethodExists(page_group):
                desc = config.get(
                    "group-description",
                    f"means that only {page_group} users can access the page",
                )
                AISI.run(
                    {
                        "name": page_group,
                        "description": f"I need method '{page_group}' - {desc}",
                    },
                    "Render.Group",
                )

        if "db.sql" in page_code and page_code["db.sql"].strip() != "":
            sql_file = os.path.join(page_path, "db.sql")
            if not internal and os.path.exists(sql_file):
                cli.command("code " + sql_file, False, True)
                if (
                    cli.selection("Confirm to update database", ["Go", "No"], True)
                    == "Go"
                ):
                    cli.trace("Updating database")
                    DB.submit(page_code["db.sql"])
            cli.trace("Deleting SQL file")
            os.remove(sql_file)

        if "code.php" in page_code and page_code["code.php"].strip() != "":
            envars = Help.extractEnvVars(page_code["code.php"])
            if len(envars) > 0:
                for envar in envars:
                    cli.trace(f"Adding environment variable '{envar}'")
                    Help.addEnv(envar, "")

        plugins = config.get("composer-plugins", [])
        existing_plugins = list(
            json.loads(cli.read(f"{Help.cwd}/.system/composer.json") or "{}")
            .get("require", {})
            .keys()
        )

        if len(plugins) > 0:
            for plugin in plugins:
                plugin = plugin.strip()
                if plugin in existing_plugins:
                    continue
                if (
                    cli.selection(
                        f"Confirm to install Composer({plugin})", ["Go", "No"], True
                    )
                    == "Go"
                ):
                    Patch.add(os.path.join(Help.cwd + "/.system", "composer.json"))
                    Patch.add(os.path.join(Help.cwd + "/.system", "composer.lock"))
                    Patch.add(os.path.join(Help.cwd + "/.system", "vendor"))

                    cli.setLoading("Installing composer plugin")
                    cli.trace(f"Installing composer plugin '{plugin}'")
                    cli.command(
                        "composer require " + plugin, True, True, Help.cwd + "/.system"
                    )

        return True

    def groupMethodExists(name):
        file = os.path.join(Help.cwd, ".access")
        if not os.path.exists(file):
            return False

        content = cli.read(file)
        pattern = rf"public\s+static\s+function\s+{re.escape(name)}\s*\("

        return re.search(pattern, content) is not None

    def extractEnvVars(content):
        pattern = r"""App::env\(\s*      # App::env(
                      ['"]                # opening quote
                      ([^'"]+)            # capture variable name
                      ['"]                # closing quote
                   """
        matches = re.findall(pattern, content, re.VERBOSE)

        return sorted(set(matches))

    def selectCron():
        if not Help.cwd:
            return ""

        crons = []
        for cron in os.listdir(f"{Help.cwd}/Crons"):
            if cron in ["x.placeholder"]:
                continue
            crons.append(cron[:-4])
        crons.append("[Back]")

        cron = cli.selection("Select cron job", crons, True)
        if cron == "[Back]":
            return ""

        return cron + ".php"

    def selectPage():
        if not Help.cwd:
            return ""

        pages = os.listdir(f"{Help.cwd}/Pages")
        if "public.phpshift" in pages:
            pages.remove("public.phpshift")
        pages.append("[Back]")

        page = cli.selection("Select page", pages, True)
        if page == "[Back]":
            return ""

        return page

    def updateSitemap():
        base = os.path.dirname(os.path.dirname(__file__)) + "/frame/.assets/sitemap.xml"
        if not os.path.exists(base):
            return False

        date_time = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        content = cli.read(base).replace("<date_time>", date_time)

        file = f"{Help.cwd}/.assets/sitemap.xml"
        Patch.add(file)
        cli.write(file, content)

        return True

    def addEnv(name, value):
        if not name:
            return False

        file_path = os.path.join(Help.cwd, ".env")
        if not os.path.exists(file_path):
            return False

        content = cli.read(file_path)
        if content is None:
            return False

        if re.search(rf"^\s*{re.escape(name)}=", content, re.MULTILINE):
            cli.trace(f"Variable '{name}' already exists. Skipping.")
            return True

        new_line = f'{name}="{value}"'
        lines = content.splitlines()
        hint = "#################################################################################### Project"

        try:
            section_index = next(
                i for i, line in enumerate(lines) if line.strip() == hint
            )
        except StopIteration:
            updated_content = f"{hint}\n{new_line}\n\n{content}"
        else:
            insert_index = section_index + 1
            while insert_index < len(lines) and re.match(
                r"{}\s*=".format(name), lines[insert_index]
            ):
                insert_index += 1
            lines.insert(insert_index, new_line)
            updated_content = "\n".join(lines) + "\n"

        Patch.add(file_path)
        if not cli.write(file_path, updated_content):
            return False

        cli.trace(f"Variable '{name}' added successfully.")
        cli.command(f"code {Help.cwd}/.env", False, True)

        return True

    def getEnv(name="", default=""):
        if not name.strip():
            cli.error("Invalid environment variable name")
            return default

        file = Help.cwd + "/.env"
        if not os.path.exists(file):
            cli.trace("Could not find the configuration")
            return default

        if name in Help.config:
            return Help.config[name]

        with open(file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    Help.config[key.strip()] = value.replace('"', "")

        if name in Help.config:
            return Help.config[name]

        return default

    def setEnv(name="", value=""):
        if not name.strip():
            cli.error("Invalid environment variable name")
            return False

        file = f"{Help.cwd}/.env"
        if not cli.isFile(file):
            cli.error("Invalid environment file")
            return False

        var = f'{name}="{value}"'
        content = re.sub(rf'{name}=".*?"', var, cli.read(file))

        Patch.add(file)
        cli.write(file, content)

        return True

    def createShortcut(name=""):
        if not name:
            return False

        path = f"{Help.cwd}/.vscode/vs.code-workspace"
        if not cli.isFile(path) or not name:
            return False

        desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
        shortcut_path = os.path.join(desktop, f"{name}.lnk")

        target_file = f"{Help.cwd}/.vscode/vs.code-workspace"
        icon_path = f"{Help.cwd}/.vscode/logo.ico"

        Patch.add(shortcut_path)

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = target_file
        shortcut.WorkingDirectory = os.path.dirname(target_file)
        shortcut.IconLocation = icon_path
        shortcut.save()

        return True