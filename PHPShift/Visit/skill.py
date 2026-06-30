from imports import *


class PHPShiftVisit:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Opening PHPShift website")

        webbrowser.open("https://phpshift.com/?cli")

        return True
