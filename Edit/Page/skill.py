from imports import *


class EditPage:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Editing the page")

        VAR.target = Help.selectPage() if not VAR.target else VAR.target
        parts = VAR.target.split(".")

        if len(parts) != 2:
            VAR.target = ""
            return False

        prompt = AISI.prompt(message, skill)
        code = AISI.FILES(prompt)

        if not code:
            VAR.target = ""
            return False

        Help.codeEditor(parts[0], parts[1], code)
        Help.updateSitemap()
        VAR.target = ""

        return code

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
