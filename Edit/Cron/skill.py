from imports import *


class EditCron:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Editing cron job")

        VAR.target = Help.selectCron() if not VAR.target else VAR.target
        code = cli.read(f"{project}/Crons/{VAR.target}")

        if code.strip() == "":
            return ""

        prompt = AISI.prompt(message, skill)
        prompt = prompt.replace("{{name}}", VAR.target).replace("{{cronJobCode}}", code)
        files = AISI.FILES(prompt)

        if VAR.target not in files:
            return ""

        path = f"{project}/Crons/{VAR.target}".replace("\\", "/").replace("../", "")
        Patch.add(path)
        cli.write(path, files[VAR.target])

        return files[VAR.target]

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
