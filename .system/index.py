from imports import *


class index:
    ####################################################################################// Load
    def __init__(self, app="", cwd="", args=[]):
        self.app, self.cwd, self.args = app, cwd, args
        # ...
        cli.dev = "-trace" in args
        self.stopped = False

        Help(app, cwd, args)
        pass

    def __exit__(self):
        if not self.stopped:
            self.stop()
            DB.close()
        pass

    ####################################################################################// Main
    def new(self, cmd=""):  # Create new project
        if Help.getEnv("PROJECT_LOCAL").strip() != "":
            return "Project already exists"

        frame = os.path.join(self.app, ".system/frame")
        if not os.path.exists(frame):
            return f"Frame directory '{frame}' does not exist!"

        replacers = {
            "date_time": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "project_dir": self.cwd.replace("\\", "/"),
            "app_key": secrets.token_urlsafe(21),
        }

        values = {}
        for root, dirs, files in os.walk(frame):
            rel_path = os.path.relpath(root, frame)
            target_dir = os.path.join(self.cwd, rel_path)
            os.makedirs(target_dir, exist_ok=True)

            for file_name in files:
                src_file = os.path.join(root, file_name)
                dest_file = os.path.join(target_dir, file_name)

                try:
                    with open(src_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    is_text = True
                except UnicodeDecodeError:
                    is_text = False

                if is_text:
                    keys = re.findall(r"\{\{(.*?)\}\}", content)
                    for key in keys:
                        if key not in values:
                            values[key] = cli.input(self.__textify(key), True)
                    for key, val in values.items():
                        content = content.replace(f"{{{{{key}}}}}", val)
                    for replacer in replacers:
                        content = content.replace(f"<{replacer}>", replacers[replacer])
                    cli.write(dest_file, content)
                else:
                    shutil.copy2(src_file, dest_file)

        config = os.path.join(self.cwd, ".env")
        if os.path.exists(config):
            content = cli.read(config)
            content = content.replace("<database_pass>", cli.input("Database pass"))
            content = content.replace(
                "<ai_model>",
                AISI.models(True),
            )
            content = content.replace("<ai_key>", cli.input("API Key", True))
            cli.write(config, content)

        if not self.__hasKeyFile():
            cli.selection("You should add AI key file!", ["Done", "Later"], True)
        if self.__hasKeyFile():
            self.__refineIdea()

        self.__git()
        Help.createShortcut(values["project_name"])
        cli.command(f"code {self.cwd}/.md", False, True)

        if cli.selection("Want to start development?", ["Yes", "No"], True) == "Yes":
            return self.start()

        return "Project created"

    def start(self, cmd=""):  # Start project development
        domain = Help.getEnv("PROJECT_LOCAL").strip()
        if not domain:
            return "Project not verified!"

        if not self.__hasKeyFile():
            return "AI key file not found!"

        hint = "_".join(domain.split(".")[:-1]).lower().strip()
        if not Localhost.start("phpshift_" + hint, domain, True, self.app, self.cwd):
            cli.error("Localhost failed")
            return False

        self.__init(hint)
        self.__continue()
        self.__crons()

        task = ""
        option = ""

        while True:
            skip = ["Render"]
            if self.__hasUnits():
                skip.append("Create.Project")
                skip.append("More.RefineIdea")
            else:
                skip.append("Create.Translation")
                skip.append("Create.SEO")
                skip.append("Create.README")
                skip.append("Edit.SEO")
                skip.append("Edit.Project")
            if not self.__hasApis():
                skip.append("Edit.API")
                pass
            if not self.__hasCrons():
                skip.append("Edit.Cron")
                pass
            if not self.__hasPages():
                skip.append("Edit.Page")
                pass

            if not option:
                option = AISI.skills(False, skip)

            if not option:
                self.stop()
                DB.close()
                sys.exit()

            if task:
                task += ".\n" + self.__message("Adjust")
            else:
                task = self.__message("Describe", True)
                if task == ".":
                    option = ""
                    task = ""
                    continue
                DB.reserve()

            Patch.new()
            VAR.target = ""
            VAR.styling = ""

            cli.setLoading("Working")
            if not AISI.run(task, option):
                cli.endLoading()
                cli.trace("Could not complete the task")
                Patch.rollback()
                DB.rollback()
                option = ""
                task = ""
                continue

            cli.endLoading()
            confirm = cli.selection(
                "Want to keep changes?", ["Yes", "Redo", "No"], True
            )

            if confirm == "Yes":
                Patch.confirm()
                DB.clear()
                self.__commit()
            elif confirm == "Redo":
                Patch.rollback()
                DB.rollback()
                continue
            elif confirm == "No":
                Patch.rollback()
                DB.rollback()

            option = ""
            task = ""
        pass

    def stop(self, cmd=""):  # Stop localhost if didn't by itself
        domain = Help.getEnv("PROJECT_LOCAL").strip()
        if not domain:
            return "Project not verified!"

        cli.setLoading("Please wait")
        hint = "_".join(domain.split(".")[:-1]).lower().strip()
        Localhost.stop("phpshift_" + hint, domain, self.app, self.cwd)
        self.stopped = True
        cli.endLoading()

        return "Localhost stopped"

    ####################################################################################// Helpers
    def __init(self, hint=""):
        if not hint:
            hint = "phpshift_test"

        Patch(self.cwd + "/.system")

        db_host = Help.getEnv("DB_HOST")
        db_user = Help.getEnv("DB_USER")
        db_pass = Help.getEnv("DB_PASS")
        DB.config(db_host, db_user, db_pass)

        db_name = Help.getEnv("DB_NAME")
        db_check = db_name.replace("[", "").replace("]", "").strip()
        while DB.exists(db_check) and db_name[:1] == "[":
            option = cli.selection(
                f"Database '{db_check}' already exists",
                ["Clear", "Keep", "Change"],
                True,
            )
            if option == "Clear":
                DB.reset(db_check)
                Help.setEnv("DB_NAME", db_check)
                db_name = db_check
            if option == "Keep":
                Help.setEnv("DB_NAME", db_check)
                db_name = db_check
            elif option == "Change":
                new_name = ""
                taken = 0
                while not new_name or DB.exists(new_name):
                    if taken > 0:
                        cli.error(f"Database '{new_name}' is taken")
                        time.sleep(3)
                        cli.unline()
                    new_name = cli.input("Database name", True).strip()
                    taken += 1
                Help.setEnv("DB_NAME", new_name)
                db_name = new_name

        if "[" in db_name:
            db_name = db_name.replace("[", "").replace("]", "").strip()
            Help.setEnv("DB_NAME", db_name)

        DB(
            db_host,
            db_name,
            db_user,
            db_pass,
            self.cwd + "/.system",
        )

        DB.new(db_name)

        AISI.init(
            self.app,
            f"{self.app}/.system/collectors.py",
            Help.getEnv("PHPSHIFT_AIMODEL"),
            Help.getEnv("PHPSHIFT_AIKEY"),
        )

        pass

    def __continue(self):
        if not Patch.exists():
            return False

        if cli.selection("Want to keep changes?", ["Yes", "No"], True) != "Yes":
            Patch.rollback()
            DB.rollback()
            return False

        Patch.confirm()
        self.__commit()

        return True

    def __crons(self):
        crons = [x for x in os.listdir(f"{self.cwd}/Crons") if x != "x.placeholder"]
        if len(crons) <= 0:
            return False

        if cli.selection("Want to start corn jobs?", ["Yes", "No"], True) != "Yes":
            return False

        thread = threading.Thread(target=self.__runCrons, daemon=True)
        thread.start()

        return True

    def __textify(self, text):
        text = text.replace("_", " ")

        return text.capitalize()

    def __hasApis(self):
        apis = os.listdir(self.cwd + "/Apis")

        if "x.placeholder" in apis and len(apis) == 1:
            del apis[0]

        return len(apis) > 0

    def __hasCrons(self):
        crons = os.listdir(self.cwd + "/Crons")

        if "x.placeholder" in crons and len(crons) == 1:
            del crons[0]

        return len(crons) > 0
        return len(apis) > 0

    def __hasPages(self):
        pages = os.listdir(self.cwd + "/Pages")

        if "public.phpshift" in pages and len(pages) == 1:
            del pages[0]

        return len(pages) > 0

    def __hasUnits(self):
        return self.__hasApis() or self.__hasCrons() or self.__hasPages()

    def __message(self, hint="", must=False):
        message = cli.input(hint, must)
        if message == ".md":
            message = f"{self.cwd}/.md"

        if (
            isinstance(message, str)
            and os.path.isfile(message)
            and os.path.exists(message)
        ):
            cli.trace("Loading file: " + message)
            message = cli.read(message)

        return message

    def __commit(self):
        if not os.path.exists(self.cwd + "/.git"):
            return False

        if cli.selection("Want to commit changes?", ["Yes", "No"], True) == "No":
            return False

        commit = cli.input("Label", True)
        cli.info("Adding commit ...")
        cli.command("git add .", True, True, self.cwd)
        cli.command('git commit -m "' + commit + '"', True, True, self.cwd)
        cli.unline()

        if cli.selection("Want to push commits?", ["Yes", "No"], True) == "No":
            return False

        cli.info("Pushing commits ...")
        cli.command("git push", True, True, self.cwd)

        return True

    def __git(self):
        if os.path.exists(self.cwd + "/.git"):
            return False

        if cli.selection("Want to init Git?", ["Yes", "No"], True) == "No":
            return False

        username = cli.input("Git user.name", True)
        usermail = cli.input("Git user.email", True)

        cli.setLoading("Initializing Git")

        path = f"{self.app}/.system/sources/gitignore"
        if cli.isFile(path):
            shutil.copyfile(path, f"{self.cwd}/.gitignore")

        cli.command("git init", True, True, self.cwd)
        cli.command(f"git config  user.name '{username}'", True, True, self.cwd)
        cli.command(f"git config  user.email '{usermail}'", True, True, self.cwd)
        cli.command("git add .", True, True, self.cwd)
        cli.command('git commit -m "+ Frame"', True, True, self.cwd)

        cli.endLoading()

        return True

    def __refineIdea(self):
        if not os.path.exists(self.cwd + "/.md"):
            return False

        if cli.selection("Want to refine your idea?", ["Yes", "No"], True) == "No":
            return False

        AISI.init(
            self.app,
            f"{self.app}/.system/collectors.py",
            Help.getEnv("PHPSHIFT_AIMODEL"),
            Help.getEnv("PHPSHIFT_AIKEY"),
        )

        message = cli.input("Describe the project shortly", True)
        AISI.run(message, "More.RefineIdea")

        cli.endLoading()
        cli.command(f"code {self.cwd}/.md", False, True)

        if cli.selection("Want to keep this plan?", ["Yes", "No"], True) == "No":
            Patch.rollback()
            return False

        return True

    def __hasKeyFile(self):
        model = Help.getEnv("PHPSHIFT_AIMODEL")
        if not model:
            return False

        if model.split("/")[0] not in ["vertex"]:
            return True

        key = Help.getEnv("PHPSHIFT_AIKEY")
        if not os.path.exists(f"{self.cwd}/{key}"):
            return False

        return True

    def __runCrons(self):
        while True:
            now = time.time()
            next_minute = (now // 60 + 1) * 60
            time.sleep(next_minute - now)
            subprocess.run(
                f"php {self.cwd}/cron -auto",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
