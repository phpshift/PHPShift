<?php

class Cache
{
    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX// Params

    private static $base = '';

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX// Load

    public static function init($base = '')
    {
        $base = App::path($base);
        if (empty($base) || !file_exists($base))
        {
            App::error('Invalid MEMO base');
            exit;
        }

        self::$base = $base;
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX// Main

    /** (AI-USE) - Creates cache data by name, returns stored data or null;
     * // Set system level cache data;
     * Cache::set('system', 'metrics', ['size' => 16]);
     * // Set user level cache data;
     * Cache::set($user, 'metrics', ['size' => 16]);
     */
    public static function set(string|int $user, string $name = '', mixed $data = null)
    {
        if (empty($name) || is_null($data)) return null;

        $base = self::$base;
        if ($user != 'system') $base = Storage::userDir($user);

        $given = self::buildData($data);
        $json = json_encode((array)$given);
        $safe_name = basename($name);
        $cache_file = $base . '/' . $safe_name . '.cache';
        $content = App::encrypt($json, App::env('PROJECT_KEY'));

        file_put_contents($cache_file, $content);

        return $data;
    }

    /** (AI-USE) - Adds data to cache by name, returns updated data or null;
     * // Add system level cache data item;
     * Cache::add('system', 'metrics', 'size', '24');
     * // Add user level cache data item;
     * Cache::add($user, 'metrics', 'size', '24');
     */
    public static function add(string|int $user, string $name = '', string $key = '', mixed $value = null)
    {
        $data = self::get($user, $name);

        if (is_array($data)) $data[$key] = $value;
        elseif (is_object($data)) $data->$key = $value;
        else
        {
            settype($data, 'array');
            $data[$key] = $value;
        }

        return self::set($user, $name, $data);
    }

    /** (AI-USE) - Cuts data from cache by name and key, returns updated data or null;
     * // Cut system level cache data item;
     * Cache::cut('system', 'metrics', 'size');
     * // Cut user level cache data item;
     * Cache::cut($user, 'metrics', 'size');
     */
    public static function cut(string|int $user, string $name = '', string $key = '')
    {
        $data = self::get($user, $name);

        if (is_array($data) && isset($data[$key])) unset($data[$key]);
        if (is_object($data) && isset($data->$key)) unset($data->$key);

        return self::set($user, $name, $data);
    }

    /** (AI-USE) - Returns cache data by name;
     * // Get system level cache data;
     * Cache::get('system', 'metrics');
     * // Get user level cache data;
     * Cache::get($user, 'metrics');
     */
    public static function get(string|int $user, string $name = '')
    {
        if (empty($name)) return null;

        $base = self::$base;
        if ($user != 'system') $base = Storage::userDir($user);

        $safe_name = basename($name);
        $cache_file = $base . '/' . $safe_name . '.cache';
        if (!file_exists($cache_file)) return null;

        $content = file_get_contents($cache_file);
        $json = App::decrypt($content, App::env('PROJECT_KEY'));
        $data = json_decode($json, true);

        return self::parseData($data);
    }

    /** (AI-USE) - Deletes cache data by name;
     * // Delete system level cache data;
     * Cache::get('system', 'metrics');
     * // Delete user level cache data;
     * Cache::get($user, 'metrics');
     */
    public static function del(string|int $user, string $name = '')
    {
        if (empty($name)) return false;

        $base = self::$base;
        if ($user != 'system') $base = Storage::userDir($user);

        $safe_name = basename($name);
        $cache_file = $base . '/' . $safe_name . '.cache';
        if (!file_exists($cache_file)) return true;

        unlink($cache_file);

        return true;
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX// Helpers

    private static function buildData($value = null, $key = null)
    {
        if (!is_array($value) && !is_object($value))
        {
            return [
                'type' => gettype($value),
                'key' => $key,
                'value' => $value
            ];
        }

        $collect = [
            'type' => gettype($value),
            'key' => $key,
            'value' => []
        ];

        foreach ($value as $k => $v)
        {
            if (is_array($v) || is_object($v))
            {
                $collect['value'][] = self::buildData($v, $k);
                continue;
            }

            $collect['value'][] = [
                'type' => gettype($v),
                'key' => $k,
                'value' => $v
            ];
        }

        return $collect;
    }

    private static function parseData($data = null)
    {
        if (is_null($data)) return null;

        $type = $data['type'];
        $key = $data['key'];
        $value = $data['value'];

        if ($type != 'array' && $type != 'object')
        {
            settype($value, $type);
            return $value;
        }

        $collect = [];
        foreach ($value as $k => $v)
        {
            $ty = $v['type'];
            $ke = $v['key'];
            $va = $v['value'];

            if ($ty == 'array' || $ty == 'object')
            {
                $collect[$ke] = self::parseData($v);
                continue;
            }

            settype($va, $ty);
            $collect[$ke] = $va;
        }

        settype($collect, $type);
        return $collect;
    }
}
