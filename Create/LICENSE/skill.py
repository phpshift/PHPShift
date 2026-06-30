from imports import *


class CreateLICENSE:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Creating LICENSE")

        return Help.installLicense(project, True)

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
