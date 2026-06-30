from imports import *


class EditAccess:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Editing Access File")

        code = cli.read(f"{project}/.access")
        if code.strip() == "":
            return ""

        prompt = AISI.prompt(message, skill)
        prompt = prompt.replace("{{AccessCode}}", code)
        files = AISI.FILES(prompt)

        print(files)

        if "access.php" not in files:
            return ""

        path = f"{project}/.access".replace("\\", "/").replace("../", "")
        Patch.add(path)
        cli.write(path, files["access.php"])

        return files["access.php"]

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
