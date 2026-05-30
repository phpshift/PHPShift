from imports import *


class CreateTranslation:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Creating new language")

        VAR.target = Help.selectPage() if not VAR.target else VAR.target
        folder = f"{project}/Pages/{VAR.target}"

        if not VAR.target:
            return False

        prompt = AISI.prompt(message, skill)
        files = AISI.run(prompt, "Edit.Page")

        patched = []
        collect = {}
        for file in os.listdir(folder):
            if not file.startswith("lng.") and not file.endswith(".json"):
                continue

            lng = file.replace("lng.", "").replace(".json", "").strip()
            if not lng:
                continue

            base_data = {}
            base = f"{project}/Space/lng.{lng}.json"
            if cli.isFile(base):
                base_data = json.loads(cli.read(base))

            new = f"{folder}/{file}"
            new_data = json.loads(cli.read(new))

            for key in new_data:
                if key in base_data:
                    continue
                base_data[key] = new_data[key]
                if lng not in collect:
                    collect[lng] = {}
                collect[lng][key] = new_data[key]
                pass

            if base not in patched:
                Patch.add(base)
                patched.append(base)

            cli.write(base, json.dumps(base_data, indent=4, ensure_ascii=False))
            os.remove(new)
            pass

        return collect

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
