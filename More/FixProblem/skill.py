from imports import *


class MoreFixProblem:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Analyzing the problem")

        # Build project file tree
        file_tree = self.__buildFileTree(project)
        if not file_tree:
            cli.trace("No project files found")
            return {}

        # Fetch PHPShift documentation
        cli.setLoading("Loading documentation")
        docs = self.__fetchDocs()

        # Use AI to pick relevant resource files based on user message
        cli.setLoading("Picking relevant files")
        picked_paths = self.__pickRelevantFiles(message, file_tree, project)
        if not picked_paths:
            cli.trace("No relevant files selected by AI")
            return {}

        # Read the contents of the picked files
        resource_contents = self.__readFileContents(picked_paths, project)

        # Build prompt and call AI to generate fixed files
        cli.setLoading("Fixing the problem")
        prompt = AISI.prompt(message, skill)
        prompt = prompt.replace("{{fileTree}}", file_tree)
        prompt = prompt.replace("{{resourceContents}}", resource_contents)
        prompt = prompt.replace("{{documentation}}", docs)

        fixed = AISI.FILES(prompt)
        if not fixed:
            cli.trace("AI did not return any fixed files")
            return {}

        # Replace current project files with generated fixes
        for filename, content in fixed.items():
            if not filename or not content.strip():
                cli.trace(f"Skipping empty file '{filename}'")
                continue

            path = os.path.join(project, filename).replace("\\", "/").replace("../", "")
            if not os.path.exists(os.path.dirname(path)):
                cli.trace(f"Skipping '{filename}' - parent directory does not exist")
                continue

            cli.trace(f"Fixing '{filename}'")
            Patch.add(path)
            cli.write(path, content)

        return fixed

    ####################################################################################// Helpers
    def __buildFileTree(self, project=""):
        """Walk the project directory and return a YAML-formatted file tree."""
        if not project or not os.path.exists(project):
            return ""

        skip_dirs = {".git", ".system", "vendor", "node_modules"}
        lines = []

        for root, dirs, files in os.walk(project):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            rel_root = os.path.relpath(root, project).replace("\\", "/")
            prefix = "" if rel_root == "." else rel_root + "/"

            for filename in sorted(files):
                if filename.startswith("x.") or filename.startswith("."):
                    continue
                lines.append(prefix + filename)

        return "\n".join(lines)

    def __pickRelevantFiles(self, message="", file_tree="", project=""):
        """Ask AI to select the most relevant files for the given problem."""
        pick_prompt = (
            "You are a code analysis assistant.\n"
            "The user has reported a problem:\n\n"
            f"{message}\n\n"
            "Here is the project file tree:\n"
            f"```yaml\n{file_tree}\n```\n\n"
            "Based on the problem description, list ONLY the file paths that are most likely relevant to finding and fixing this problem.\n"
            "Return each file path on its own line, relative to the project root (e.g. Pages/public.home/code.php).\n"
            "Do NOT include any explanation, headers or extra text — only the file paths, one per line."
        )

        response = AISI.REPLY(pick_prompt)
        if not response:
            return []

        paths = []
        for line in response.strip().splitlines():
            line = line.strip().lstrip("-").strip()
            if line:
                paths.append(line)

        return paths

    def __readFileContents(self, paths=[], project=""):
        """Read and format the contents of the given file paths."""
        extension_map = {
            ".html": "html", ".htm": "html", ".css": "css", ".js": "js",
            ".php": "php", ".py": "python", ".json": "json", ".xml": "xml",
            ".txt": "text", ".md": "markdown", ".ts": "ts", ".sql": "sql",
            ".sh": "bash", ".env": "env",
        }

        output = []
        for rel_path in paths:
            abs_path = os.path.join(project, rel_path)
            if not os.path.isfile(abs_path):
                cli.trace(f"File not found: {rel_path}")
                continue

            _, ext = os.path.splitext(rel_path)
            lang = extension_map.get(ext.lower(), "")
            content = cli.read(abs_path)
            output.append(f"{rel_path}\n```{lang}\n{content}\n```")

        return "\n\n".join(output)

    def __fetchDocs(self):
        """Fetch PHPShift documentation from the official docs website."""
        try:
            cli.trace("Fetching PHPShift documentation")
            docs = Help.webExtract(
                "https://docs.phpshift.com",
                "div.docipygroup"
            )
            return docs
        except Exception as e:
            cli.trace(f"Could not fetch documentation: {e}")
            return ""
