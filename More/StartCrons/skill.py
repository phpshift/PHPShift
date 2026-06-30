from imports import *


class MoreStartCrons:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Starting cron jobs")

        Help.startCrons()

        return True

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
