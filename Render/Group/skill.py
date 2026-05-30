from imports import *


class RenderGroup:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Rendering the group")

        name = "public"
        description = "public - means that only visitors can access the page"

        if isinstance(message, dict) and "description" in message:
            name = message["name"]
            description = message["description"]

        prompt = AISI.prompt(f"{name} - {description}.", skill)
        prompt = prompt.replace("{{name}}", name).replace(
            "{{description}}", description
        )

        code = AISI.FILES(prompt)
        if "function.php" not in code:
            return ""

        method = code["function.php"].replace("<?php", "").strip()
        self.__addGroupMethod(project, method)

        Help.updateSitemap()

        return method

    ####################################################################################// Helpers
    def __addGroupMethod(self, project, method):
        file = os.path.join(project, ".access")
        if not os.path.exists(file):
            return False

        content = cli.read(file)
        pos = content.rfind("}")

        if pos == -1:
            return False

        method = method.strip()
        method = textwrap.dedent(method).strip("\n")
        lines = method.split("\n")
        formatted = "\n".join("    " + line if line else "" for line in lines)
        insertion = "\n" + formatted + "\n"
        new_content = content[:pos] + insertion + content[pos:]

        Patch.add(file)
        cli.write(file, new_content)

        return True
