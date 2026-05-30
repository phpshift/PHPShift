from imports import *


class Patch:
    ####################################################################################// Params
    spot = ""

    ####################################################################################// Load
    def __init__(self, spot):
        Patch.spot = spot
        cli.trace("Creating patch spot")
        os.makedirs(Patch.spot, exist_ok=True)
        pass

    ####################################################################################// Main
    def exists():
        cli.trace("Checking patch file")
        return os.path.exists(Patch._patch_file())

    def new():
        patch_file = Patch._patch_file()
        if os.path.exists(patch_file):
            return False

        meta = {"created": datetime.now().isoformat(), "files": []}
        cli.trace("Creating new patch")

        cli.write(patch_file, json.dumps(meta, indent=4))

        return True

    def add(path):
        patch_file = Patch._patch_file()
        if not os.path.exists(patch_file):
            return False

        meta = json.loads(cli.read(patch_file))
        existed = os.path.exists(path)
        entry = {
            "original_path": path,
            "existed": existed,
            "type": None,
            "backup": None,
        }

        cli.trace("Adding patch item")
        if existed:
            if os.path.isfile(path):
                entry["type"] = "file"
                with open(path, "rb") as f:
                    entry["backup"] = base64.b64encode(f.read()).decode()
            elif os.path.isdir(path):
                entry["type"] = "dir"
                entry["backup"] = Patch._serialize_dir(path)
            else:
                return False
        else:
            entry["type"] = "new"

        meta["files"].append(entry)
        cli.write(patch_file, json.dumps(meta, indent=4))

        return True

    def rollback():
        patch_file = Patch._patch_file()
        if not os.path.exists(patch_file):
            return False

        cli.trace("Rolling back the patch")
        meta = json.loads(cli.read(patch_file))
        for item in reversed(meta["files"]):
            path = item["original_path"]

            if not item["existed"]:
                if os.path.isfile(path):
                    os.remove(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                continue

            if item["type"] == "file":
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    f.write(base64.b64decode(item["backup"]))
            elif item["type"] == "dir":
                Patch._restore_dir(path, item["backup"])

        cli.trace("Deleting patch file")
        os.remove(patch_file)

        return True

    def confirm():
        patch_file = Patch._patch_file()
        if not os.path.exists(patch_file):
            return False

        cli.trace("Deleting patch file")
        os.remove(patch_file)

        return True

    ####################################################################################// Helpers
    def _patch_file():
        return os.path.join(Patch.spot, f"patch.json")

    def _serialize_dir(path):
        data = {}

        for root, dirs, files in os.walk(path):
            rel_root = os.path.relpath(root, path)

            for f in files:
                full = os.path.join(root, f)

                with open(full, "rb") as fh:
                    encoded = base64.b64encode(fh.read()).decode()

                data[os.path.join(rel_root, f)] = encoded

        return data

    def _restore_dir(path, data):
        if os.path.exists(path):
            shutil.rmtree(path)

        for rel, encoded in data.items():

            full = os.path.join(path, rel)

            os.makedirs(os.path.dirname(full), exist_ok=True)

            with open(full, "wb") as f:
                f.write(base64.b64decode(encoded))

        return True
