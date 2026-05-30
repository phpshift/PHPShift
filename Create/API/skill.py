from imports import *


class CreateAPI:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Creating API")

        prompt = AISI.prompt(message, skill)
        files = AISI.FILES(prompt)

        for file in files:
            path = f"{project}/Apis/{file}".replace("\\", "/").replace("../", "")
            Patch.add(path)
            cli.write(path, files[file].strip())

        return files

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
