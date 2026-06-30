from imports import *


class DeleteREADME:
    def run(self, message="", project="", skill=""):
        cli.setLoading("Deleting README file")

        readme_path = os.path.join(project, "README.md")
        if not cli.isFile(readme_path):
            cli.trace(f"README.md not found at {readme_path}")
            return False

        Patch.add(readme_path)
        os.remove(readme_path)

        return True
