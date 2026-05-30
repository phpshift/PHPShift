from imports import *


class MoreCreateDesktopIcon:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Creating Desktop Icon")

        Help.createShortcut(Help.getEnv("PROJECT_NAME"))

        return True

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
