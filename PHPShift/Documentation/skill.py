from imports import *

class PHPShiftDocumentation:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Opening PHP Shift documentation")

        webbrowser.open("https://docs.phpshift.com/?cli")

        return True