from imports import *


class MoreRefineIdea:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Refining idea")

        name = Help.getEnv("PROJECT_NAME", "")
        if not name:
            return ""

        prompt = AISI.prompt(f"{name} - {message}.", skill)
        prompt = prompt.replace("{{name}}", name).replace("{{description}}", message)

        code = AISI.FILES(prompt)
        if "project.md" not in code:
            return ""

        path = project + "/.md"
        Patch.add(path)
        cli.write(path, code["project.md"])

        return code["project.md"]

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
