<?php

// [SECURITY]
class DB
{
    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Params

    private static $charset = 'utf8mb4';
    private static $pdo = null;
    private static $config = null;

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Load

    public static function init($host = '', $database = '', $user = '', $pass = '')
    {
        self::$config = (object)[];
        self::$config->host = $host;
        self::$config->database = $database;
        self::$config->user = $user;
        self::$config->pass = $pass;
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Main

    /** (AI-USE) - Prepares statement, binds data column values and inserts new row in database - returns record id or false;
     * $id = DB::insert('users', [
     *     'name' => 'John',
     *     'email' => 'john@mail.com'
     * ]);
     */
    public static function insert(string $table = '', array $data = [])
    {
        if (!$table || empty($data)) return false;

        try
        {
            $pdo = self::connect();
            $quotedTable = self::quoteIdentifier($table);
            $columns = array_keys($data);
            $quotedColumns = array_map([self::class, 'quoteIdentifier'], $columns);
            $fields = implode(', ', $quotedColumns);
            $placeholders = ':' . implode(', :', $columns);
            $sql = "INSERT INTO {$quotedTable} ($fields) VALUES ($placeholders)";
            $stmt = $pdo->prepare($sql);

            foreach ($data as $key => $value)
            {
                $stmt->bindValue(":$key", $value);
            }

            if ($stmt->execute()) return $pdo->lastInsertId();

            return false;
        }
        catch (Exception $e)
        {
            App::error($e->getMessage() . ' (' . $e->getFile() . ':' . $e->getLine() . ')');
            exit;
        }
    }

    /** (AI-USE) - Deletes record where sql line conditions met - returns true or false;
     * $result = DB::delete(
     *     'users',
     *     ['id = :id', 'status = 1'],
     *     ['id' => 5]
     * );
     */
    public static function delete(string $table = '', string|array $where = [], array $where_vars = [])
    {
        if (!$table || empty($where)) return false;

        try
        {
            $pdo = self::connect();
            $quotedTable = self::quoteIdentifier($table);
            $sql = "DELETE FROM {$quotedTable} WHERE " . self::buildSQL($where, ' and ');
            $vars = self::prepareVars($sql, $where_vars);
            $stmt = $pdo->prepare($sql);

            foreach ($vars as $key => $value)
            {
                $stmt->bindValue(":$key", $value);
            }

            return $stmt->execute();
        }
        catch (Exception $e)
        {
            App::error($e->getMessage() . ' (' . $e->getFile() . ':' . $e->getLine() . ')');
            exit;
        }
    }

    /** (AI-USE) - Updates record columns where sql line conditions met - returns true or false;
     * $result = DB::update(
     *     'users',
     *     ['name' => 'Mike'],
     *     ['id = :id', 'status = 1'],
     *     ['id' => 5]
     * );
     */
    public static function update(string $table = '', array $data = [], string|array $where = [], array $where_vars = [])
    {
        if (!$table || empty($data) || empty($where)) return false;

        try
        {
            $pdo = self::connect();
            $quotedTable = self::quoteIdentifier($table);
            $setParts = [];

            foreach ($data as $column => $value)
            {
                $quotedColumn = self::quoteIdentifier($column);
                $setParts[] = "{$quotedColumn} = :set_$column";
            }

            $setSQL = implode(', ', $setParts);
            $whereSQL = self::buildSQL($where, ' and ');
            $sql = "UPDATE {$quotedTable} SET $setSQL WHERE $whereSQL";
            $vars = self::prepareVars($sql, $where_vars);
            $stmt = $pdo->prepare($sql);

            foreach ($data as $column => $value)
            {
                $stmt->bindValue(":set_$column", $value);
            }

            foreach ($vars as $key => $value)
            {
                $stmt->bindValue(":$key", $value);
            }

            return $stmt->execute();
        }
        catch (Exception $e)
        {
            App::error($e->getMessage() . ' (' . $e->getFile() . ':' . $e->getLine() . ')');
            exit;
        }
    }

    /** (AI-USE) - Takes sql lines, queries the database - returns array of records;
     * $rows = DB::query([
     *     'SELECT',
     *     '*',
     *     'FROM users',
     *     'WHERE',
     *     'id = :id',
     *     'and role in (:roles)',
     *     'and status = 1',
     * ], [
     *     'id' => 5,
     *     'roles' => ['admin', 'user'],
     * ]);
     */
    public static function query(string|array $statement = [], array $statement_vars = [])
    {
        if (empty($statement)) return [];

        try
        {
            $pdo = self::connect();
            $sql = self::buildSQL($statement);
            $vars = self::prepareVars($sql, $statement_vars);
            $stmt = $pdo->prepare($sql);

            foreach ($vars as $key => $value)
            {
                $stmt->bindValue(":$key", $value);
            }

            $stmt->execute();

            return $stmt->fetchAll();
        }
        catch (Exception $e)
        {
            App::error($e->getMessage() . ' (' . $e->getFile() . ':' . $e->getLine() . ')');
            exit;
        }
    }

    /** (AI-USE) - Takes sql lines, submits custom sql code - returns true if completed or false;
     * $result = DB::submit([
     *     'CREATE TABLE test (',
     *     'id INT AUTO_INCREMENT PRIMARY KEY,',
     *     'name VARCHAR(100)',
     *     ')'
     * ]);
     */
    public static function submit(string|array $sql = [], array $sql_vars = [])
    {
        if (empty($sql)) return false;

        try
        {
            $pdo = self::connect();
            $statement = self::buildSQL($sql);
            $vars = self::prepareVars($statement, $sql_vars);
            $stmt = $pdo->prepare($statement);

            foreach ($vars as $key => $value)
            {
                $stmt->bindValue(":$key", $value);
            }

            return $stmt->execute();
        }
        catch (Exception $e)
        {
            App::error($e->getMessage() . ' (' . $e->getFile() . ':' . $e->getLine() . ')');
            exit;
        }
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Helpers

    private static function connect()
    {
        if (self::$pdo === null)
        {
            try
            {
                self::$pdo = new PDO("mysql:host=" . self::$config->host . ";dbname=" . self::$config->database . ";charset=" . self::$charset, self::$config->user, self::$config->pass, [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    PDO::ATTR_EMULATE_PREPARES => false,
                ]);
            }
            catch (PDOException $e)
            {
                App::error($e->getMessage() . ' (' . $e->getFile() . ':' . $e->getLine() . ')');
                exit;
            }
        }

        return self::$pdo;
    }

    private static function buildSQL($lines = [], $delimiter = ' ')
    {
        if (!is_array($lines) && trim($lines) == '') return '';

        return trim(implode($delimiter, (array)$lines));
    }

    private static function quoteIdentifier(string $identifier)
    {
        if (!preg_match('/^[a-zA-Z0-9_]+$/', $identifier))
        {
            App::error('Invalid SQL identifier: ' . $identifier);
            exit;
        }

        return "`{$identifier}`";
    }

    private static function prepareVars(&$sql = '', $vars = [])
    {
        $collect = [];
        foreach ($vars as $key => $value)
        {
            if (is_array($value))
            {
                $placeholders = [];
                foreach ($value as $i => $v)
                {
                    $newKey = "{$key}_{$i}";
                    $placeholders[] = ":{$newKey}";
                    $collect[$newKey] = $v;
                }

                $sql = str_replace(":{$key}", implode(', ', $placeholders), $sql);
            }
            else
            {
                preg_match_all("/:{$key}\b/", $sql, $matches);
                $count = count($matches[0]);
                if ($count > 1)
                {
                    for ($i = 0; $i < $count; $i++)
                    {
                        $newKey = "{$key}_{$i}";
                        $sql = preg_replace(
                            "/:{$key}\b/",
                            ":{$newKey}",
                            $sql,
                            1
                        );
                        $collect[$newKey] = $value;
                    }
                }
                else
                {
                    $collect[$key] = $value;
                }
            }
        }

        return $collect;
    }
}
