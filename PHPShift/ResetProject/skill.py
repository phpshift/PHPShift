from imports import *
import shutil


class PHPShiftResetProject:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Resetting Project")

        if not project:
            cli.error("Project path missing")
            return False


        keep_files = {
            os.path.normpath("Space/seo.html"),
            os.path.normpath(".assets/robots.txt"),
            os.path.normpath(".assets/sitemap.xml"),
        }

        for path in Path(project).iterdir():
            if path.name in [
                ".env",
                ".md",
                ".git",
                ".vscode",
                # "",
            ]:
                continue

            rel_path = os.path.normpath(os.path.relpath(path, project))
            if rel_path in keep_files:
                continue

            if path.is_dir():
                if not self.__remove_path(path, project, keep_files):
                    return False
            else:
                path.unlink()

        frame_dir = os.path.join(Help.app, ".system/frame")
        if not self.__copyFrameDir(frame_dir, project):
            return False

        gitignore_file = os.path.join(Help.app, ".system/sources/gitignore")
        if not self.__copyGitignore(gitignore_file, project):
            return False

        if not self.__patchEnv(project):
            return False

        DB.reset(DB.name())

        return True

    def __remove_path(self, path, project, keep_files):
        try:
            for child in sorted(path.iterdir(), reverse=True):
                rel_child = os.path.normpath(os.path.relpath(child, project))
                if rel_child in keep_files:
                    continue

                if child.is_dir():
                    if not self.__remove_path(child, project, keep_files):
                        return False
                    if child.exists() and not any(child.iterdir()):
                        child.rmdir()
                else:
                    child.unlink()

            if path.exists() and not any(path.iterdir()):
                path.rmdir()
        except Exception as e:
            cli.error(f"Cannot remove path {path}: {e}")
            return False

        return True

    ####################################################################################// Helpers

    def __copyFrameDir(self, frame_dir="", project=""):
        if not os.path.isdir(frame_dir):
            cli.error(f"Frame directory not found: {frame_dir}")
            return False

        try:
            for root, _, files in os.walk(frame_dir):
                rel_root = os.path.relpath(root, frame_dir)
                dest_root = (
                    project if rel_root == "." else os.path.join(project, rel_root)
                )
                os.makedirs(dest_root, exist_ok=True)

                for name in files:
                    if name in [".env", ".md", "robots.txt", "sitemap.xml", "seo.html"]:
                        continue

                    src = os.path.join(root, name)
                    dst = os.path.join(dest_root, name)
                    shutil.copy2(src, dst)
        except Exception as e:
            cli.error(f"Cannot copy frame directory: {e}")
            return False

        cli.trace("Frame directory copied")
        return True

    def __copyGitignore(self, gitignore_file="", project=""):
        if not os.path.isfile(gitignore_file):
            cli.error(f".gitignore source not found: {gitignore_file}")
            return False

        destination = os.path.join(project, ".gitignore")
        try:
            shutil.copy2(gitignore_file, destination)
        except Exception as e:
            cli.error(f"Cannot copy .gitignore: {e}")
            return False

        cli.trace(".gitignore copied")
        return True

    def __patchEnv(self, project=""):
        env_path = os.path.join(project, ".env")
        if not os.path.exists(env_path):
            cli.trace(".env not found; skipping patch")
            return True

        try:
            with open(env_path, "r", encoding="utf-8") as f:
                raw = f.read()
        except Exception as e:
            cli.error(f"Cannot read .env: {e}")
            return False

        lines = raw.splitlines(keepends=True)
        output_lines = []
        project_section_found = False

        for line in lines:
            stripped = line.rstrip("\r\n")
            if "############## Project" in stripped:
                output_lines.append(line)
                project_section_found = True
                break
            if re.match(r"^\s*PROJECT_LANDING\s*=", stripped):
                output_lines.append('PROJECT_LANDING="public/phpshift"\n')
                cli.trace("Updated PROJECT_LANDING to public/phpshift")
                continue
            output_lines.append(line)
        if not project_section_found:
            cli.trace(
                "'############## Project' marker not found; no truncation applied"
            )
        try:
            with open(env_path, "w", encoding="utf-8", newline="") as f:
                f.writelines(output_lines)
        except Exception as e:
            cli.error(f"Cannot write .env: {e}")
            return False

        cli.trace(".env patched successfully")
        return True
