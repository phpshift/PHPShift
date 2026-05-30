from imports import *


class MoreInstallComposerPlugin:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Installing Composer Plugin")

        prompt = AISI.prompt(message, skill)
        code = AISI.FILES(prompt)
        if "response.json" not in code:
            return ""

        response = json.loads(code.get("response.json", "{}"))
        plugin = response.get("plugin", "")
        if not plugin:
            return ""

        if cli.selection(f"Confirm to install Composer({plugin})", ["Go", "No"], True) == "Go":
            Patch.add(f"{project}/.system/vendor")
            Patch.add(f"{project}/.system/composer.json")
            Patch.add(f"{project}/.system/composer.lock")
            cli.command("composer require " + plugin, True, True, project + "/.system")

        return plugin

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
