from imports import *


class MoreEmptyDatabaseTables:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Emptying Database Tables")

        DB.empty()

        return True

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
