from imports import *


class CreateREADME:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Creating README")

        prompt = AISI.prompt(message, skill)
        files = AISI.FILES(prompt)
        if "README.md" not in files:
            return ""

        Patch.add(f"{project}/README.md")
        cli.write(f"{project}/README.md", files["README.md"])
        Help.updateSitemap()

        return files["README.md"]

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
