from imports import *


class MoreChangeAIModel:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        domain = Help.getEnv("PROJECT_LOCAL").strip()
        if not domain:
            return False

        model = AISI.models(True)
        cli.unline()
        print()
        key = cli.input("API Key", True)

        cli.setLoading("Changing AI model")
        Help.setEnv("PHPSHIFT_AIMODEL", model)
        Help.setEnv("PHPSHIFT_AIKEY", key)
        cli.command(f"code {project}/.env", False, True)

        AISI.init(
            Help.app,
            f"{Help.app}/.system/collectors.py",
            model,
            key,
        )

        return True

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
