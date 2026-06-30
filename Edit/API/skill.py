from imports import *


class EditAPI:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Editing API")

        VAR.target = Help.selectAPI() if not VAR.target else VAR.target
        code = cli.read(f"{project}/Apis/{VAR.target}")

        if code.strip() == "":
            return ""

        prompt = AISI.prompt(message, skill)
        prompt = prompt.replace("{{name}}", VAR.target).replace("{{ApiCode}}", code)
        files = AISI.FILES(prompt)

        if VAR.target not in files:
            return ""

        path = f"{project}/Apis/{VAR.target}".replace("\\", "/").replace("../", "")
        Patch.add(path)
        cli.write(path, files[VAR.target])

        return files[VAR.target]

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
