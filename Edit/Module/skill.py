from imports import *


class EditModule:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Editing Module")

        VAR.target = Help.selectModule() if not VAR.target else VAR.target
        code = cli.read(f"{project}/Space/{VAR.target}")

        if code.strip() == "":
            return ""

        prompt = AISI.prompt(message, skill)
        prompt = prompt.replace("{{name}}", VAR.target).replace("{{ModuleCode}}", code)
        files = AISI.FILES(prompt)

        if VAR.target not in files:
            return ""

        path = f"{project}/Space/{VAR.target}".replace("\\", "/").replace("../", "")
        Patch.add(path)
        cli.write(path, files[VAR.target])

        for file in files:
            if file.endswith(".sql"):
                path2 = f"{project}/Space/{file}".replace("\\", "/").replace("../", "")
                cli.write(path2, files[file])
                Help.executeDatabaseFile(path2)

        return files[VAR.target]

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
