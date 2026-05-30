from imports import *


class CreateSEO:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Creating SEO")

        prompt = AISI.prompt(message, skill)
        files = AISI.FILES(prompt)
        if "seo.html" not in files:
            return ""

        Patch.add(f"{project}/Space/seo.html")
        cli.write(f"{project}/Space/seo.html", files["seo.html"])
        Help.updateSitemap()

        return files["seo.html"]

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
