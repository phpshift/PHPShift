from imports import *


class Collectors:

    def databaseVersion(self, message="", project="", skill=""):
        cli.trace("Loading database version")

        return AISI.format("", DB.version(), "Version not detected.")

    def databaseSchema(self, message="", project="", skill=""):
        cli.trace("Loading database schema")

        return AISI.format("", DB.schema(), "Schema not provided.")

    def files(self, message="", project="", skill=""):
        cli.trace("Loading project files")

        files = []
        dirs = [
            f"{project}/Apis",
            f"{project}/Crons",
            f"{project}/Pages",
        ]

        for dir in dirs:
            for root, _, filenames in os.walk(dir):
                if filename[:2] == "x.":
                    continue
                for filename in filenames:
                    path = f"{root}/{filename}".replace(project + "/", "")
                    files.append(path.replace("\\", "/"))

        return AISI.format("yaml", "\n".join(files), "No files detected.")

    def styling(self, message="", project="", skill=""):
        cli.trace("Loading styling example")

        pages = os.listdir(f"{project}/Pages")
        if "public.phpshift" in pages:
            pages.remove("public.phpshift")

        if "x.placeholder" in pages:
            pages.remove("x.placeholder")

        styling = ""
        page = (
            cli.selection("Select styling example", pages)
            if not VAR.styling
            else VAR.styling
        )

        if page:
            styling = cli.read(f"{project}/Pages/{page}/style.css")

        return AISI.format("css", styling, "Styling not provided.")

    def phpMethods(self, message="", project="", skill=""):
        cli.trace("Loading PHP methods")

        collection = ""
        for root, dirs, files in os.walk(project + "/.system"):
            dirs[:] = [d for d in dirs if d != "vendor"]
            for file in files:
                if file.endswith(".php"):
                    class_name = ""
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        docblock = ""
                        in_docblock = False
                        for i, line in enumerate(lines):
                            if line.startswith("class "):
                                class_name = line.replace("class ", "").strip()
                            line = line.strip()
                            if line.startswith("/** (AI-USE)"):
                                in_docblock = True
                                docblock += line.replace("/** (AI-USE)", "{{METHOD}}")
                            elif in_docblock and line.startswith("*/"):
                                in_docblock = False
                            elif in_docblock:
                                docblock += "\n" + line[2:]
                            elif line.startswith("public static function "):
                                if docblock:
                                    method_declaration = line.replace(
                                        "public static function ", f"{class_name}::"
                                    )
                                    collection += (
                                        "\n\n// "
                                        + docblock.replace(
                                            "{{METHOD}}", method_declaration.strip()
                                        ).strip()
                                    )
                                    docblock = ""

        return AISI.format("php", collection.strip(), "No methods detected.")

    def jsMethods(self, message="", project="", skill=""):
        cli.trace("Loading JavaScript methods")

        collection = ""
        for root, dirs, files in os.walk(project + "/.assets"):
            dirs[:] = [d for d in dirs if d != "vendor"]
            for file in files:
                if file.endswith(".js"):
                    class_name = ""
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        docblock = ""
                        in_docblock = False
                        for i, line in enumerate(lines):
                            if line.startswith("var ") and " = {" in line:
                                class_name = (
                                    line.replace("var ", "").replace(" = {", "").strip()
                                )
                            line = line.strip()
                            if line.startswith("/** (AI-USE)"):
                                in_docblock = True
                                docblock += line.replace("/** (AI-USE)", "{{METHOD}}")
                            elif in_docblock and line.startswith("*/"):
                                in_docblock = False
                            elif in_docblock:
                                docblock += "\n" + line[2:]
                            elif ": function (" in line:
                                if docblock:
                                    method_declaration = (
                                        f"{class_name}."
                                        + line.replace(": function ", "")
                                    ).strip()[:-1]

                                    collection += (
                                        "\n\n// "
                                        + docblock.replace(
                                            "{{METHOD}}", method_declaration.strip()
                                        ).strip()
                                    )
                                    docblock = ""

        return AISI.format("js", collection.strip(), "No methods detected.")

    def codeBase(self, message="", project="", skill=""):
        cli.trace("Loading page codebase")

        if not VAR.target:
            return ""

        folder = f"{project}/Pages/{VAR.target}"
        if not os.path.exists(folder):
            return ""

        extension_map = {
            ".html": "html",
            ".htm": "html",
            ".css": "css",
            ".js": "js",
            ".php": "php",
            ".py": "python",
            ".json": "json",
            ".xml": "xml",
            ".txt": "text",
            ".md": "markdown",
            ".ts": "ts",
            ".jsx": "jsx",
            ".tsx": "tsx",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cs": "csharp",
            ".rb": "ruby",
            ".go": "go",
            ".sh": "bash",
        }

        output = []
        files = sorted(
            f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))
        )

        for index, filename in enumerate(files, start=1):
            if filename[:2] == "x.":
                continue
            file_path = os.path.join(folder, filename)
            _, ext = os.path.splitext(filename)
            language = extension_map.get(ext.lower(), "")
            content = cli.read(file_path)
            block = f"{index}. {filename}\n" f"```{language}\n" f"{content}\n" f"```\n"
            output.append(block)

        return AISI.format("", "\n".join(output).strip(), "Codebase not found.")

    def pages(self, message="", project="", skill=""):
        cli.trace("Loading pages")

        n = 1
        pages = []
        for page in os.listdir(f"{project}/Pages"):
            content = cli.read(f"{project}/Pages/{page}/readme.md").strip()
            if not content:
                continue
            pages.append(f"{n}. {page}\n\n```md\n{content}\n```")
            n += 1

        return AISI.format("", "\n\n".join(pages), "Pages not found.")

    def projectPages(self, message="", project="", skill=""):
        cli.trace("Loading project pages")

        collect = []
        for page in os.listdir(f"{project}/Pages"):
            if page[:2] == "x.":
                continue
            collect.append(page.replace(".", "/"))

        return AISI.format("yaml", "\n".join(collect), "Pages not found.")

    def aboutProject(self, message="", project="", skill=""):
        cli.trace("Loading project information")

        about = cli.read(f"{project}/README.md").strip()

        if not about:
            cli.trace("Loading page infos")
            for page in os.listdir(f"{project}/Pages"):
                info = cli.read(f"{project}/Pages/{page}/readme.md").strip()
                if not info:
                    continue
                about += f"{info}\n\n"

        return AISI.format("md", about.strip(), "Information not found.")

    def seo(self, message="", project="", skill=""):
        cli.trace("Loading SEO code")

        code = cli.read(f"{project}/Space/seo.html").strip()
        if not code:
            code = cli.read(__file__ + "/frame/Space/seo.html").strip()

        return AISI.format("html", code.strip(), "SEO code not found.")

    def frameworkStructure(self, message="", project="", skill=""):
        cli.trace("Loading framework structure")

        folder = os.path.join(os.path.dirname(__file__), "frame")
        include = [
            ".assets/*",
            ".system/*",
            "Apis/*",
            "Crons/*",
            "Pages/*",
            "Space/*",
            ".access",
            ".env",
            ".htaccess",
            "cron",
        ]

        structure = ""
        for root, dirs, files in os.walk(folder):
            rel_path = os.path.relpath(root, folder).replace("\\", "/")
            if any(fnmatch.fnmatch(os.path.join(rel_path, file), pattern) for pattern in include for file in files):
                structure += f"/{rel_path}:\n"
                for file in files:
                    if any(fnmatch.fnmatch(os.path.join(rel_path, file), pattern) for pattern in include):
                        structure += f"  - {file}\n"

        for item in include:
            if cli.isFile(f"{folder}/{item}"):
                structure += f"/{item}\n"

        return AISI.format("yaml", structure.strip(), "Framework structure is empty.")

    def frameworkCodebase(self, message="", project="", skill=""):
        cli.trace("Loading framework codebase")

        folder = os.path.join(os.path.dirname(__file__), "frame")
        include = [
            ".assets/script.js",
            ".system/*.php",
            "cron",
            ".access",
            ".htaccess",
        ]

        codebase = ""
        for pattern in include:
            for filepath in glob.glob(os.path.join(folder, pattern)):
                basename = filepath.replace(folder + "\\", "").replace("\\", "/")
                ext = basename.split(".")[-1]
                if ext in ["cron", "access"]:
                    ext = "php"
                with open(filepath, 'r') as file:
                    content = file.read().replace("//XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX>", "//>")
                # content = "Content of " + basename
                code_snippet = f"\n/{basename}\n```{ext}\n\n{content}\n\n```\n"
                codebase += code_snippet

        return AISI.format("", "\n" + codebase.strip(), "Codebase not found.")

    def frameworkSolvedIssues(self, message="", project="", skill=""):
        cli.trace("Loading framework solved issues")

        folder = os.path.dirname(os.path.dirname(__file__))
        file = os.path.join(folder, skill.replace(".", "/"), "solved.md")

        return AISI.format("md", cli.read(file).strip(), "Solved issues not found.")

    # def ___(self, message="", project="", skill=""):
    #     cli.trace("Loading ___")
    #     return AISI.format("txt", "...", "___ not found.")
