from imports import *


class CreatePage:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Creating the page")

        prompt = AISI.prompt(message, skill)
        code = AISI.FILES(prompt)
        if not code:
            return {}

        config = json.loads(code.get("config.json", "{}"))
        page_group = config.get("page-group", "group")
        page_name = config.get("page-name", "page")

        Help.codeEditor(page_group, page_name, code)
        Help.updateSitemap()

        return code

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
