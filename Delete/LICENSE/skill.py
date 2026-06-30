from imports import *


class DeleteLICENSE:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Deleting LICENSE file")

        file = os.path.join(project, "LICENSE")
        if not cli.isFile(file):
            cli.trace(f"LICENSE not found at {file}")
            return False

        Patch.add(file)
        os.remove(file)

        return True
