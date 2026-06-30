from imports import *


class EditLICENSE:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Editing LICENSE")

        return Help.installLicense(project, True)

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
