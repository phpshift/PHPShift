from imports import *


class DeleteSEO:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Deleting SEO")

        app = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        base = app + "/.system/frame/Space/seo.html"
        if not cli.isFile(base):
            cli.trace("SEO base file not found")
            return False

        file = project + "/Space/seo.html"
        if not cli.isFile(file):
            cli.trace("SEO file not found")
            return False

        Patch.add(file)
        cli.write(file, cli.read(base))

        return True
