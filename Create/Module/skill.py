from imports import *


class CreateModule:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Creating Module")

        prompt = AISI.prompt(message, skill)
        files = AISI.FILES(prompt)

        phps = {}
        for file in files:
            if file in ["config.json", "readme.md"]:
                continue
            path = f"{project}/Space/{file}".replace("\\", "/").replace("../", "")
            Patch.add(path)
            cli.write(path, files[file].strip())
            if file.endswith(".sql"):
                Help.executeDatabaseFile(path)
            else:
                Help.extractEnvVars(files[file], True)
                phps[file] = files[file]

        config = json.loads(files.get("config.json", "{}"))
        plugins = config.get("composer-plugins", [])
        Help.installComposerModules(plugins)

        return phps

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
