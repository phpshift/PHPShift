from imports import *


class DB:
    ####################################################################################// Params
    _engine = None
    _Session = None
    _session = None
    _host = ""
    _database = ""
    _user = ""
    _pass = ""
    _storage = ""

    ####################################################################################// Load
    def __init__(self, host, database, user, password, storage="", driver="pymysql"):
        try:
            conn_str = f"mysql+{driver}://{user}:{password}@{host}/{database}"
            DB._engine = create_engine(conn_str, echo=False, future=True)
            DB._Session = sessionmaker(bind=DB._engine, future=True)
            DB._session = DB._Session()
        except Exception as e:
            cli.error(f"Database connection error: {e}")
            sys.exit()

        DB._host = host
        DB._database = database
        DB._user = user
        DB._pass = password
        DB._storage = storage
        pass

    def config(host, user, password):
        DB._host = host
        DB._user = user
        DB._pass = password
        pass

    ####################################################################################// Main
    def new(name):
        cli.trace("Running database setup")
        file = os.path.dirname(os.path.dirname(__file__)) + f"/sources/setup.sql"
        sql = cli.read(file)
        sql = sql.replace("{{DB_NAME}}", name).strip()

        engine = create_engine(f"mysql+pymysql://{DB._user}:{DB._pass}@{DB._host}/")
        with engine.connect() as conn:
            for statement in sql.split(";"):
                stmt = statement.strip()
                if stmt:
                    conn.execute(text(stmt))
            conn.commit()
        engine.dispose()
        pass

    def insert(table, data):
        try:
            cols = ", ".join(data.keys())
            vals = ", ".join([f":{k}" for k in data.keys()])
            sql = f"INSERT INTO {table} ({cols}) VALUES ({vals})"
            cli.trace(f"Inserting row in '{table}' table")

            with DB._engine.begin() as conn:
                result = conn.execute(text(sql), data)
                return result.lastrowid if result.lastrowid else False
        except Exception as e:
            cli.error(f"Insert error: {e}")
            return False
        return False

    def update(table, data, where, params=None):
        try:
            set_clause = ", ".join([f"{k}=:{k}" for k in data.keys()])
            combined_params = {**data, **(params or {})}
            sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
            cli.trace(f"Updating row in '{table}' table")

            with DB._engine.begin() as conn:
                conn.execute(text(sql), combined_params)
            return True
        except Exception as e:
            cli.error(f"Update error: {e}")
            return False
        return False

    def delete(table, where, params=None):
        try:
            sql = f"DELETE FROM {table} WHERE {where}"
            cli.trace(f"Deleting row from '{table}' table")

            with DB._engine.begin() as conn:
                conn.execute(text(sql), params or {})
            return True
        except Exception as e:
            cli.error(f"Delete error: {e}")
            return False
        return False

    def query(statement, params=None):
        try:
            cli.trace(f"Running database query")
            with DB._engine.connect() as conn:
                result = conn.execute(text(statement), params or {})
                return [dict(row) for row in result.mappings().all()]
        except Exception as e:
            cli.error(f"Query error: {e}")
            return []

    def submit(sql, params=None):
        try:
            statements = [s.strip() for s in sql.split(";") if s.strip()]
            cli.trace(f"Submitting database code")

            with DB._engine.begin() as conn:
                for stmt in statements:
                    conn.execute(text(stmt), params or {})
            return True
        except Exception as e:
            cli.error(f"Submit error: {e}")
            return False
        return False

    def empty():
        try:
            cli.trace("Fetching database tables")
            with DB._engine.connect() as conn:
                result = conn.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result.fetchall()]

            if not tables:
                cli.error("No tables found")
                return False

            keep = cli.selections("Select tables to keep", tables)
            if keep is None:
                keep = []

            if isinstance(keep, str):
                keep = [keep]

            cli.trace("Clearing database tables")
            with DB._engine.begin() as conn:
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                for table in tables:
                    if table not in keep:
                        cli.trace(f"Clearing '{table}' table")
                        conn.execute(text(f"TRUNCATE TABLE `{table}`"))

                conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            return True

        except Exception as e:
            cli.error(f"Empty error: {e}")
            return False
        return False

    def schema():
        try:
            cli.trace(f"Extracting database schema")
            with DB._engine.connect() as conn:
                tables = conn.execute(text("SHOW TABLES")).fetchall()
                ddl = []

                for (table,) in tables:
                    result = conn.execute(text(f"SHOW CREATE TABLE {table}"))
                    row = result.fetchone()
                    ddl.append(row[1] + ";\n")

                return "\n".join(ddl)

        except Exception as e:
            cli.error(f"Schema error: {e}")
            return ""
        return ""

    def version():
        try:
            cli.trace(f"Extracting database version")
            with DB._engine.connect() as conn:
                result = conn.execute(text("SHOW VARIABLES LIKE 'version';"))
                row = result.fetchone()
                if row:
                    return str(row[1])
                return ""
        except Exception as e:
            cli.error(f"Version error: {e}")
            return ""
        return ""

    def reserve(name="backup"):
        try:
            path = DB._storage + f"/{name}.sql"
            cmd = [
                "C:/xampp/mysql/bin/mysqldump.exe",
                "-h",
                DB._host,
                "-u",
                DB._user,
                DB._database,
            ]

            if DB._pass:
                cmd.append(f"-p{DB._pass}")

            cli.trace(f"Reserving database backup")
            with open(path, "w", encoding="utf-8") as f:
                subprocess.run(cmd, stdout=f, check=True)
                cli.trace(f"Backup created: {path}")
            return True
        except Exception as e:
            cli.error(f"Backup error: {e}")
            return False
        return False

    def clear(name="backup"):
        path = DB._storage + f"/{name}.sql"
        if not os.path.exists(path):
            return False
        cli.trace(f"Deleting database backup")
        os.remove(path)
        return True

    def rollback(name="backup", delete=True):
        path = DB._storage + f"/{name}.sql"
        if not os.path.exists(path):
            return False

        try:
            cmd = [
                "C:/xampp/mysql/bin/mysql.exe",
                "-h",
                DB._host,
                "-u",
                DB._user,
                DB._database,
            ]

            if DB._pass:
                cmd.append(f"-p{DB._pass}")

            DB.reset()
            cli.trace(f"Rolling back the database")
            with open(path, "r", encoding="utf-8") as f:
                subprocess.run(cmd, stdin=f, check=True)
            cli.trace("Database restored from backup")

            if delete:
                cli.trace(f"Deleting database backup")
                os.remove(path)

            return True
        except Exception as e:
            cli.error(f"Rollback error: {e}")
            return False
        return False

    def reset(name=""):
        if not name:
            name = DB._database
        if not name:
            cli.error("Invalid database name to reset")
            return False

        try:
            cli.trace(f"Resetting the database")
            engine = create_engine(f"mysql+pymysql://{DB._user}:{DB._pass}@{DB._host}/")
            with engine.begin() as conn:
                conn.execute(text(f"DROP DATABASE IF EXISTS `{name}`"))
                conn.execute(
                    text(
                        f"CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
                    )
                )
            engine.dispose()
            return True
        except Exception as e:
            cli.error(f"Reset error: {e}")
            return False
        return False

    def close():
        if DB._engine == None:
            return False

        cli.trace("Closing database connection")
        DB._session.close()
        DB._engine.dispose()
        DB._engine = None
        DB._Session = None
        DB._session = None

        return True

    def name():
        return DB._database

    def exists(name=""):
        if not name:
            name = DB._database
        if not name:
            cli.error("Invalid database name to check")
            return False

        try:
            engine = create_engine(f"mysql+pymysql://{DB._user}:{DB._pass}@{DB._host}/")
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db"
                    ),
                    {"db": name},
                ).fetchone()
            engine.dispose()
            return result is not None

        except Exception as e:
            cli.error(f"Exists check error: {e}")
            return False
        return False

    ####################################################################################// Helpers
