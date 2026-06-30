from imports import *


class MoreCreateNewSkill:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Generating new skill")

        category = cli.input("Category").strip()
        if not category:
            return False

        cli.unline()
        print()

        name = cli.input("Name").strip()
        if not name:
            return False

        skill = f"{category}.{name}".replace(" ", "")
        AISI.generate(skill, message)

        return True

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
