from imports import *


class PHPShiftExportProject:
    # Keys whose values are preserved as-is in example.env
    ENV_KEEP_KEYS = {
        "PROJECT_NAME",
        "PROJECT_AUTHOR",
        "PROJECT_LOCAL",
        "PROJECT_PRODUCTION",
        "PROJECT_LANDING",
    }

    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Exporting Project")

        sql_file = os.path.join(project, "project.sql")
        zip_file = os.path.join(project, "project.zip")
        example_env_file = os.path.join(project, "example.env")

        # Step 1: Export database schema and write project.sql to project root (not archived)
        cli.trace("Extracting database schema")
        schema = DB.schema()
        if not schema:
            cli.error("Could not export database schema")
            return False

        cli.write(sql_file, schema)
        cli.trace(f"Schema saved: {sql_file}")

        # Step 2: Generate example.env from .env (values blanked except whitelisted keys)
        cli.trace("Generating example.env")
        self.__generateExampleEnv(project, example_env_file)

        # Step 3: Collect ignored patterns from .gitignore
        ignored = self.__loadGitignore(project)

        # Step 4: Archive project files into project.zip
        cli.trace("Creating project archive")
        try:
            import zipfile as zf

            with zf.ZipFile(zip_file, "w", zf.ZIP_DEFLATED) as archive:
                for root, dirs, files in os.walk(project):
                    # Filter out ignored directories in-place so os.walk skips them
                    dirs[:] = [
                        d
                        for d in dirs
                        if not self.__isIgnored(
                            os.path.relpath(os.path.join(root, d), project),
                            ignored,
                            is_dir=True,
                        )
                        and d not in [".git"]
                    ]

                    for file_name in files:
                        abs_path = os.path.join(root, file_name)
                        rel_path = os.path.relpath(abs_path, project)

                        # Always include example.env in archive
                        is_example_env = os.path.normpath(rel_path) == os.path.normpath(
                            "example.env"
                        )

                        # Never include project.sql in the archive (stays in project root only)
                        is_sql = os.path.normpath(rel_path) == os.path.normpath(
                            "project.sql"
                        )
                        if is_sql:
                            cli.trace(f"Skipping from archive (project root only): {rel_path}")
                            continue

                        if not is_example_env and self.__isIgnored(rel_path, ignored):
                            cli.trace(f"Skipping ignored file: {rel_path}")
                            continue

                        archive.write(abs_path, rel_path)
                        cli.trace(f"Added: {rel_path}")

        except Exception as e:
            cli.error(f"Archive error: {e}")
            # Clean up generated files on failure
            if os.path.exists(example_env_file):
                os.remove(example_env_file)
            return False

        # Step 5: Clean up the temporary example.env (it is now inside the archive)
        cli.trace("Cleaning up example.env")
        if os.path.exists(example_env_file):
            os.remove(example_env_file)

        cli.endLoading()
        return zip_file

    ####################################################################################// Helpers
    def __generateExampleEnv(self, project="", dest=""):
        """
        Read .env from project root, blank out values for keys not in ENV_KEEP_KEYS,
        and write the result to dest (example.env).
        Returns True on success, False if .env does not exist.
        """
        env_path = os.path.join(project, ".env")
        if not os.path.exists(env_path):
            cli.trace(".env not found; skipping example.env generation")
            return False

        output_lines = []
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.rstrip("\n").rstrip("\r")

                # Preserve blank lines and comments as-is
                if not stripped.strip() or stripped.strip().startswith("#"):
                    output_lines.append(stripped)
                    continue

                # Try to parse KEY=VALUE (or KEY="VALUE")
                if "=" in stripped:
                    key, _, value = stripped.partition("=")
                    key_clean = key.strip()
                    if key_clean in self.ENV_KEEP_KEYS:
                        # Keep the original line unchanged
                        output_lines.append(stripped)
                    else:
                        # Blank out the value: KEY=""
                        output_lines.append(f'{key_clean}=""')
                else:
                    output_lines.append(stripped)

        cli.write(dest, "\n".join(output_lines))
        cli.trace(f"example.env generated: {dest}")
        return True

    def __loadGitignore(self, project=""):
        """Parse .gitignore and return a list of pattern strings (order preserved, negations included)."""
        patterns = []
        gitignore = os.path.join(project, ".gitignore")
        if not os.path.exists(gitignore):
            return patterns

        with open(gitignore, "r", encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n").rstrip("\r")
                # Skip blank lines and comments
                if not line.strip() or line.strip().startswith("#"):
                    continue
                patterns.append(line.strip())

        return patterns

    def __isIgnored(self, rel_path="", patterns=[], is_dir=False):
        """
        Return True if rel_path is ignored according to .gitignore patterns.

        Patterns are evaluated in order; a negation pattern (!pattern) un-ignores
        a path that was previously matched by an earlier pattern.
        """
        rel_path = rel_path.replace("\\", "/")
        basename = os.path.basename(rel_path)

        ignored = False

        for pattern in patterns:
            is_negation = pattern.startswith("!")
            effective_pattern = pattern[1:] if is_negation else pattern

            if self.__matchPattern(rel_path, basename, effective_pattern, is_dir):
                ignored = not is_negation  # negation un-ignores, normal pattern ignores

        return ignored

    def __matchPattern(self, rel_path, basename, pattern, is_dir):
        """Return True if rel_path/basename matches the given gitignore pattern."""
        # Directory-only pattern (trailing slash)
        if pattern.endswith("/"):
            dir_pattern = pattern.rstrip("/")
            if is_dir and (
                fnmatch.fnmatch(basename, dir_pattern)
                or fnmatch.fnmatch(rel_path, dir_pattern)
                or fnmatch.fnmatch(rel_path, dir_pattern + "/*")
            ):
                return True
            return False

        # Pattern with a slash — match relative path
        if "/" in pattern:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            if fnmatch.fnmatch(rel_path, pattern.lstrip("/")):
                return True
        else:
            # Simple pattern — match basename or any path component
            if fnmatch.fnmatch(basename, pattern):
                return True
            if fnmatch.fnmatch(rel_path, pattern):
                return True

        return False
