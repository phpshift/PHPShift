from imports import *


class RenderPage:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Rendering the page")

        group = "public"
        page = "page"
        internal = False

        if isinstance(message, dict) and "description" in message:
            group = message["group"]
            page = message["page"]
            internal = message["internal"]
            message = message["description"]

        prompt = AISI.prompt(message, skill)
        code = AISI.FILES(prompt)
        if not code:
            return False

        Help.codeEditor(group, page, code, internal)
        Help.updateSitemap()

        return prompt

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
