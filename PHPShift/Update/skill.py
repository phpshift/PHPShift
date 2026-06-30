from imports import *


class PHPShiftUpdate:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Updating phpshift module")

        cli.command("pip install --upgrade phpshift", True, True, project)

        return True
