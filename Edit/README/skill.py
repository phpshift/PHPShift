from imports import *


class EditREADME:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Creating README")

        code = cli.read(f"{project}/README.md")
        if code.strip() == "":
            return ""

        prompt = AISI.prompt(message, skill)
        prompt = prompt.replace("{{ReadmeCode}}", code)
        files = AISI.FILES(prompt)

        if "README.md" not in files:
            return ""

        Patch.add(f"{project}/README.md")
        cli.write(f"{project}/README.md", files["README.md"])
        Help.updateSitemap()

        return files["README.md"]

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
