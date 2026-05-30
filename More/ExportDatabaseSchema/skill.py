from imports import *


class MoreExportDatabaseSchema:
    ####################################################################################// Load
    def run(self, message="", project="", skill=""):
        cli.setLoading("Exporting Database Schema")

        schema = DB.schema()
        name = Help.getEnv("DB_NAME", "database")
        file = f"{project}/{name}.sql"

        Patch.add(file)
        cli.write(file, schema)

        return schema

    ####################################################################################// Helpers
    # def __helperExample(self, skill="")
