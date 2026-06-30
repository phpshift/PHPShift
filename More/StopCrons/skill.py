from imports import *


class MoreStopCrons:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Stopping cron jobs")

        Help.stopCrons()

        return True

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
