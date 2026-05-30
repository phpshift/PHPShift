<?php

// [SECURITY]
class Session
{
    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Load

    public static function init($skip = false)
    {
        if ($skip) return;

        $folder = __DIR__ . '/sessions';
        if (!is_dir($folder)) mkdir($folder, 0700, true);
        else chmod($folder, 0700);

        session_name('session');
        ini_set('session.save_path', $folder);
        ini_set('session.use_strict_mode', 1);
        ini_set('session.use_cookies', 1);
        ini_set('session.use_only_cookies', 1);
        ini_set('session.cookie_httponly', 1);
        ini_set('session.cookie_secure', App::env('PRODUCTION'));
        ini_set('session.cookie_samesite', 'Strict');
        ini_set('session.gc_maxlifetime', 3600); // 1 hour
        ini_set('session.gc_probability', 1);
        ini_set('session.gc_divisor', 1);

        $cookieDomain = App::env('PRODUCTION') ? App::env('PROJECT_PRODUCTION') : trim(App::env('PROJECT_LOCAL', ''));
        if ($cookieDomain !== '' && filter_var($cookieDomain, FILTER_VALIDATE_DOMAIN, FILTER_FLAG_HOSTNAME) === false && filter_var($cookieDomain, FILTER_VALIDATE_IP) === false) $cookieDomain = '';

        $cookieParams = [
            'lifetime' => 3600,
            'path' => '/',
            'secure' => App::env('PRODUCTION') ? true : false,
            'httponly' => true,
            'samesite' => 'Strict'
        ];

        if ($cookieDomain !== '') $cookieParams['domain'] = $cookieDomain;

        session_set_cookie_params($cookieParams);

        self::start();
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Main

    public static function exists()
    {
        return isset($_SESSION['session']);
    }

    public static function start()
    {
        if (session_status() == PHP_SESSION_NONE) session_start();

        if (!self::has('system_session_time')) self::set('system_session_time', time());

        if (time() - self::get('system_session_time') >= 1800) // 30 minutes
        {
            self::renew();
            self::set('system_session_time', time());
        }

        return true;
    }

    public static function renew()
    {
        session_regenerate_id(true);
    }

    /** (AI-USE) - Check if session has a specific item;
     * Session::has('item');
     */
    public static function has(string $name = '')
    {
        $data = self::decrypt();

        return isset($data[$name]);
    }

    /** (AI-USE) - Set a session item with a specific value;
     * Session::set('item', 1);
     */
    public static function set(string $name = '', mixed $value = null)
    {
        $data = self::decrypt();
        $data[$name] = $value;

        return self::encrypt($data);
    }

    /** (AI-USE) - Get a session item, or default if not set;
     * Session::get('item', 0);
     */
    public static function get(string $name = '', mixed $default = null)
    {
        $data = self::decrypt();

        return $data[$name] ?? $default;
    }

    /** (AI-USE) - Remove a specific item from session;
     * Session::del('item');
     */
    public static function del(string $name = '')
    {
        if (!self::has($name)) return false;

        $data = self::decrypt();
        unset($data[$name]);

        return self::encrypt($data);
    }

    public static function destroy()
    {
        if (session_status() != PHP_SESSION_NONE)
        {
            session_unset();
            session_destroy();
        }
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Helpers

    private static function encrypt($data = [])
    {
        $_SESSION['session'] = App::encrypt(json_encode($data), App::env('PROJECT_KEY'));
        return true;
    }

    private static function decrypt()
    {
        if (!isset($_SESSION['session'])) return [];
        return json_decode(App::decrypt($_SESSION['session'], App::env('PROJECT_KEY')), true);
    }
}
