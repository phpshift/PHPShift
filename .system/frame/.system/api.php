<?php

class Api
{
    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Params

    public static $on;
    public static $type;
    public static $method;
    public static $folder;
    public static $user;

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Load

    public static function init($folder = '', $get = [], $post = [], $json = [])
    {
        self::$folder = App::path(rtrim($folder, '/\\'));
        self::$user = 0;

        if (!is_dir(self::$folder)) self::error('Invalid apis folder', self::$folder);
        if (!self::isAPI()) return false;

        $version = self::apiVersion();
        if (empty($version)) self::error('Undefined API version.', $version);

        $api = self::requestedAPI();
        if (empty($api)) self::error('Undefined API.', $api);

        $file = self::$folder . "/{$version}.{$api}.php";
        if (!file_exists($file)) self::error('Invalid API file.', "{$version}.{$api}");

        require_once $file;

        $class = 'Api' . ucfirst($api);
        if (!class_exists($class, false)) self::error('Invalid API class.', $class);

        $function = 'init';
        if (!method_exists($class, $function)) self::error('Invalid API function.', $function);

        $method = $_SERVER['REQUEST_METHOD'];
        if ($method !== self::$method) self::error('Invalid API method.', "{$version}.{$api} - {$method}");

        if (self::$type == 'public' && !isset($get['token']) && !isset($json['system_key']) && !isset($json['api_key']))
        {
            self::checkPublic();
        }
        elseif (self::$type == 'callback' && isset($get['token']) && !isset($json['system_key']) && !isset($json['api_key']))
        {
            self::checkCallbackResponse($api, $get['token']);
        }
        elseif (self::$type == 'systemApi' && !isset($get['token']) && isset($json['system_key']) && !isset($json['api_key']))
        {
            self::checkSystemApi($api, $json['system_key']);
        }
        elseif (self::$type == 'userApi' && !isset($get['token']) && !isset($json['system_key']) && isset($json['api_key']))
        {
            self::checkUserApi($api, $json['api_key']);
        }
        else
        {
            self::error('Invalid API type.', self::$type);
        }

        self::execute($class, $json, $post, $get);
        exit;
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Main

    public static function setCategory($name = '', $method = '')
    {
        self::$type = $name;
        self::$method = $method;
    }

    /** (AI-USE) - Registers API endpoint access, returns array of ['id'] and ['token'] values;
     * // Available categories ($category):
     * // callback - For receiving and processing callbacks from 3rd party services (one-time access);
     * // systemApi - For building external project monitoring systems (access until expiration);
     * // userApi - For letting users get api keys for project offered API services (access until expiration);
     * // userWebhook - For letting users set own URL endpoints to push event notifications from project to their URL hooks (access until expiration);
     * $api = API::register($user, 'Testing', 'userWebhook', 'test', 3600, 'https://example.com/endpoint');
     * // $user - 0 if it is a systemApi, or user ID;
     * // $expires - unit is seconds;
     * // $hook - only when registering userWebhook;
     */
    public static function register(int $user = 0, string $label = '', string $category = '', string $name = '', int $expires = 0, string $hook = '')
    {
        if (empty($label) || empty($category) || empty($name) || empty($expires)) return false;
        if (!preg_match('/^[a-zA-Z0-9]+$/', $name))
        {
            self::error('Invalid API name format. Only alphanumeric characters are allowed.', $name);
            return false;
        }

        if ($category === 'userWebhook' && !empty($hook))
        {
            if (!self::validateWebhookUrl($hook))
            {
                self::error('Invalid or unsafe webhook URL', $hook);
                return false;
            }
        }

        $rand = App::rand(43);
        $id = DB::insert('api', [
            'user' => $user,
            'label' => $label,
            'type' => $category,
            'name' => $name,
            'token' => $rand,
            'hook' => $hook,
            'expires' => Date::utc('now', 'U') + $expires,
            'created' => Date::utc('now', 'Y-m-d H:i:s'),
        ]);

        return [
            'id' => $id,
            'token' => $rand,
        ];
    }

    /** (AI-USE) - Deletes registered API endpoint access, returns true or false;
     * $result = API::remove($id);
     */
    public static function remove(int $id = 0)
    {
        if (empty($id)) return false;

        return DB::delete('api', ['id = :id'], ['id' => $id]);
    }

    /** (AI-USE) - Used to dispatch user registered webhooks, executes API class and posts data to specified URL hook, returns false or true;
     * // Used only for APIs registered with 'userWebhook' category;
     * $result = API::dispatch($user, 'test', 1);
     * // $user - 0 if it is a systemApi, or user ID;
     */
    public static function dispatch(int $user, string $name = '', int $version = 1)
    {
        if (empty($version)) self::error('Undefined API version.', $version);
        if (empty($name)) self::error('Undefined API.', $name);

        $safeName = basename($name);
        $file = self::$folder . "/v{$version}.{$safeName}.php";
        if (!file_exists($file)) self::error('Invalid API dispatch file.', "v{$version}.{$name}.php");

        require_once $file;

        $class = 'Api' . ucfirst($name);
        if (!class_exists($class, false)) self::error('Invalid API dispatch class.', $class);

        $function = 'init';
        if (!method_exists($class, $function)) self::error('Invalid API dispatch method.', $function);

        $hooks = DB::query('SELECT id, hook, expires from api where user = :user and type = "userWebhook" and name = :name', [
            'user' => $user,
            'name' => $name,
        ]);

        if (empty($hooks)) return false;

        $payload = ['name'    => $name, 'version' => $version];

        foreach ($hooks as $x)
        {
            if ($x['expires'] < Date::utc('now', 'U'))
            {
                DB::delete('api', ['id = :id'], ['id' => $x['id']]);
                self::error('User webhook API expired.', $class);
                continue;
            }

            $ips = self::getWebhookIps($x['hook']);
            if (App::env('PRODUCTION', 1))
            {
                if (empty($ips))
                {
                    App::log('api', "BLOCKED unsafe webhook URL for [{$class}]: {$x['hook']}");
                    DB::delete('api', ['id = :id'], ['id' => $x['id']]);
                    continue;
                }

                foreach ($ips as $ip)
                {
                    if (!self::isValidPublicIp($ip))
                    {
                        App::log('api', "BLOCKED unsafe webhook URL for [{$class}]: {$x['hook']}");
                        DB::delete('api', ['id = :id'], ['id' => $x['id']]);
                        continue 2;
                    }
                }
            }

            try
            {
                $data = json_encode(array_merge($payload, self::execute($class, [], [], [], true)));
                $ch = curl_init($x['hook']);

                $curlOptions = [
                    CURLOPT_POST => true,
                    CURLOPT_POSTFIELDS => $data,
                    CURLOPT_HTTPHEADER => [
                        'Content-Type: application/json',
                        'Content-Length: ' . strlen($data),
                    ],
                    CURLOPT_TIMEOUT => 5,
                    CURLOPT_FOLLOWLOCATION => false,
                    CURLOPT_MAXREDIRS => 0,
                    CURLOPT_CONNECTTIMEOUT => 2,
                ];

                $host = parse_url($x['hook'], PHP_URL_HOST);
                $port = parse_url($x['hook'], PHP_URL_PORT) ?: 443;
                if (!filter_var($host, FILTER_VALIDATE_IP))
                {
                    $resolve = [];
                    foreach ($ips as $ip)
                    {
                        $resolve[] = "{$host}:{$port}:{$ip}";
                    }
                    if (!empty($resolve))
                    {
                        $curlOptions[CURLOPT_RESOLVE] = $resolve;
                    }
                }

                curl_setopt_array($ch, $curlOptions);

                curl_exec($ch);
                $error = curl_error($ch);
                $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);

                curl_close($ch);
            }
            catch (\Throwable $e)
            {
                $end = Date::utc('now', 'Y-m-d H:i:s');
                App::log('api', "FAIL  [{$class}]  {$end} → {$e->getMessage()}");
            }
        }

        return true;
    }

    /** (AI-USE) - Removes expired API records;
     * $result = API::cleanUp();
     */
    public static function cleanUp()
    {
        return DB::delete('api', 'expires < :current', ['current' => Date::utc('now', 'U')]);
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Categories

    private static function checkPublic()
    {
        return true;
    }

    private static function checkCallbackResponse($api = '', $key = '')
    {
        if (empty($api)) self::error('Invalid callback API name.', $api);
        if (empty($key)) self::error('Invalid callback API key.', $key);

        $records = DB::query([
            'SELECT * FROM api WHERE type = "callback" and name = :name and token = :token order by created desc'
        ], ['name' => $api, 'token' => $key]);

        if (empty($records)) self::error('Callback API not found.', $key);

        DB::delete('api', [
            'id in (:ids)',
        ], [
            'ids' => array_column($records, 'id'),
        ]);

        return true;
    }

    private static function checkUserApi($api = '', $key = '')
    {
        if (empty($api)) self::error('Invalid user API name.', $api);
        if (empty($key)) self::error('Invalid user API token.', $key);

        $records = DB::query([
            'SELECT * FROM api WHERE type = "userApi" and name = :name and token = :token order by created desc'
        ], ['name' => $api, 'token' => $key]);

        if (empty($records)) self::error('User API not found.', $key);

        $id = $records[0]['id'];

        if ($records[0]['expires'] < Date::utc('now', 'U'))
        {
            DB::delete('api', ['id = :id'], ['id' => $id]);
            self::error('User API expired.', $key);
        }

        if (count($records) > 1) DB::delete('api', ['token = :token and id != :id'], ['token' => $key, 'id' => $id]);

        self::$user = $records[0]['user'];

        return true;
    }

    private static function checkSystemApi($api = '', $key = '')
    {
        if (empty($api)) self::error('Invalid system API name.', $api);
        if (empty($key)) self::error('Invalid system API token.', $key);

        $records = DB::query([
            'SELECT * FROM api WHERE type = "systemApi" and name = :name and token = :token order by created desc'
        ], ['name' => $api, 'token' => $key]);

        if (empty($records)) self::error('System API not found.', $key);

        $id = $records[0]['id'];

        if ($records[0]['expires'] < Date::utc('now', 'U'))
        {
            DB::delete('api', ['id = :id'], ['id' => $id]);
            self::error('System API expired.', $key);
        }

        if (count($records) > 1) DB::delete('api', ['token = :token and id != :id'], ['token' => $key, 'id' => $id]);

        return true;
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Helpers

    private static function validateWebhookUrl(string $url = '')
    {
        if (empty($url)) return false;

        $parsed = parse_url($url);
        if ($parsed === false || empty($parsed['scheme']) || empty($parsed['host'])) return false;
        if (!App::env('PRODUCTION', 1)) return true;

        $scheme = strtolower($parsed['scheme']);
        if ($scheme !== 'https') return false;

        $hostname = $parsed['host'];
        $ips = self::getWebhookIps($hostname);
        if (empty($ips)) return false;

        foreach ($ips as $ip)
        {
            if (!self::isValidPublicIp($ip)) return false;
        }

        return true;
    }

    private static function getWebhookIps(string $urlOrHost = '')
    {
        if (empty($urlOrHost)) return [];
        if (strpos($urlOrHost, '://') !== false)
        {
            $parsedHost = parse_url($urlOrHost, PHP_URL_HOST);
            if (!empty($parsedHost)) $urlOrHost = $parsedHost;
        }
        if (filter_var($urlOrHost, FILTER_VALIDATE_IP)) return [$urlOrHost];

        $seen = [];
        $queue = [$urlOrHost];
        $ips = [];

        while (!empty($queue))
        {
            $current = array_shift($queue);
            if (isset($seen[$current])) continue;
            $seen[$current] = true;

            $records = @dns_get_record($current, DNS_A + DNS_AAAA + DNS_CNAME);
            if ($records === false) continue;

            foreach ($records as $record)
            {
                if (!empty($record['type']) && $record['type'] === 'CNAME' && !empty($record['target']))
                {
                    if (!isset($seen[$record['target']]))
                    {
                        $queue[] = $record['target'];
                    }
                    continue;
                }

                if (!empty($record['type']) && $record['type'] === 'A' && !empty($record['ip']))
                {
                    $ips[] = $record['ip'];
                }

                if (!empty($record['type']) && $record['type'] === 'AAAA' && !empty($record['ipv6']))
                {
                    $ips[] = $record['ipv6'];
                }
            }
        }

        return array_values(array_unique($ips));
    }

    private static function isValidPublicIp(string $ip = '')
    {
        if (empty($ip)) return false;
        if (!filter_var($ip, FILTER_VALIDATE_IP)) return false;
        if (!filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_PRIV_RANGE)) return false;
        if (!filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_NO_RES_RANGE)) return false;

        return true;
    }

    private static function error($message = '', $unit = '')
    {
        App::log('api', "ERROR [{$unit}] {$message}");
        exit;
    }

    private static function execute($class = '', $json = [], $post = [], $get = [], $return = false)
    {
        if (empty($class)) self::error('Invalid class name.', $class);

        $start = Date::utc('now', 'Y-m-d H:i:s');
        App::log('api', "RUN [{$class}] " . $start);

        try
        {
            self::$on = true;

            $obj = new $class();
            $result = $obj->init($json, $post, $get);
            $end = Date::utc('now', 'Y-m-d H:i:s');

            if ($result !== null)
            {
                $ts1 = (float) DateTime::createFromFormat('Y-m-d H:i:s', $start)->format('U.u');
                $ts2 = (float) DateTime::createFromFormat('Y-m-d H:i:s', $end)->format('U.u');

                $result['time'] = (($ts2 - $ts1) * 1000) . ' ms';
                App::log('api', "DONE [{$class}]  {$end} → " . $result['time']);

                if ($return) return $result;

                header('Content-Type: application/json');
                echo json_encode($result);
                exit;
            }
        }
        catch (\Throwable $e)
        {
            $end = Date::utc('now', 'Y-m-d H:i:s');
            App::log('api', "FAIL  [{$class}]  {$end} → {$e->getMessage()}");
        }
    }

    private static function isAPI()
    {
        return preg_match('#^/API/#', $_SERVER['REQUEST_URI']);
    }

    private static function apiVersion()
    {
        preg_match('#^/API/(v[0-9]+)/#', $_SERVER['REQUEST_URI'], $m);
        return $m[1] ?? '';
    }

    private static function requestedAPI()
    {
        preg_match('#^/API/v[0-9]+/([^/?]+)#', $_SERVER['REQUEST_URI'], $m);
        return $m[1] ?? '';
    }
}
