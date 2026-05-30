<?php

// [SECURITY]
class Request
{
    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Params

    private static $config = [];
    private static $prev_csrf = '';

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Load

    public static function init($skip = false)
    {
        if ($skip) return;

        self::$prev_csrf = self::csrf();
        self::$config = [
            'block_requests' => getenv('LOCK_TIME'), // Seconds
            'csrf_protection' => true,
            'rate_limit' => true,
            'rate_period' => getenv('IDR_PERIOD'), // Seconds
            'rate_amount' => getenv('IDR_AMOUNT'), // Requests
            'ip_rate_period' => getenv('IPR_PERIOD'), // Seconds
            'ip_rate_amount' => getenv('IPR_AMOUNT'), // Requests
            'allowed_origins' => array_diff(array_map('trim', explode(',', App::env('ALLOWED', ''))), ['']),
            'allowed_methods' => ['GET', 'POST', 'PUT', 'DELETE'], // Methods
            'content_length_limit' => getenv('CONTENT_LENGTH'), // Size MB
            'https_only' => App::env('PRODUCTION', 0) ? true : false,
        ];

        self::blockRequests();
        self::enforceHTTPS();
        self::validateRequestMethod();
        self::checkContentLength();
        self::handleCORS();
        self::csrfProtection();
        self::rateLimitIP();
        self::rateLimitVisitor();
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Main

    public static function identifier()
    {
        return hash('sha256', implode('', [
            $_SERVER['REMOTE_ADDR'],
            $_SERVER['HTTP_USER_AGENT'] ?? '',
            $_SERVER['HTTP_ACCEPT'],
            $_SERVER['HTTP_ACCEPT_LANGUAGE'] ?? '',
            $_SERVER['HTTP_ACCEPT_ENCODING'] ?? '',
            $_SERVER['HTTP_CONNECTION'] ?? '',
            $_SERVER['HTTP_HOST'],
            // $_SERVER['HTTPS'],
        ]));
    }

    public static function csrf()
    {
        return Session::get('system_csrf_token', '');
    }

    public static function csrfPrev()
    {
        return Session::set('system_csrf_token', self::$prev_csrf);
    }

    public static function lock($message = '', $status = 400, $lock = false)
    {
        if (empty($message)) $message = 'Undefined';

        App::danger($message . ' (' . self::identifier() . ')');
        if ($lock) Session::set('system_blocked', time());

        http_response_code($status);
        exit;
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Helpers

    private static function blockRequests()
    {
        if (self::$config['block_requests'] <= 0) return;

        $blocked = Session::get('system_blocked', 0);
        if ($blocked > 0 && time() - $blocked < self::$config['block_requests'])
        {
            http_response_code(400);
            exit;
        }
    }

    /**
     * Forces HTTPS connection
     */
    private static function enforceHTTPS()
    {
        if (self::$config['https_only'] && empty($_SERVER['HTTPS']))
        {
            App::danger('Invalid HTTP protocol: not HTTPS');
            header("Location: https://" . $_SERVER['HTTP_HOST'] . $_SERVER['REQUEST_URI']);
            exit;
        }
    }

    /**
     * Validates allowed HTTP methods
     */
    private static function validateRequestMethod()
    {
        header('Access-Control-Allow-Methods: ' . implode(', ', self::$config['allowed_methods']));

        $override_headers = ['X-HTTP-Method-Override', 'X-Method-Override', 'X-Original-Method'];
        $headers = getallheaders();

        foreach ($override_headers as $header_name)
        {
            if (isset($headers[$header_name]))
            {
                App::danger('HTTP method override attempt detected: ' . $header_name . ' = ' . $headers[$header_name]);
                self::lock('HTTP method override not allowed', 405, true);
            }
        }

        if (!in_array($_SERVER['REQUEST_METHOD'], self::$config['allowed_methods']))
        {
            self::lock('Request method not allowed: ' . $_SERVER['REQUEST_METHOD'], 405, true);
        }
    }

    /**
     * Limits incoming request payload size
     */
    private static function checkContentLength()
    {
        if (!empty($_SERVER['CONTENT_LENGTH']) && $_SERVER['CONTENT_LENGTH'] > self::$config['content_length_limit'] * 1048576)
        {
            self::lock('Payload too large: ' . $_SERVER['CONTENT_LENGTH'], 413, true);
        }
    }

    private static function isValidOrigin($origin = '')
    {
        $parsed = parse_url($origin);

        if (!$parsed || !isset($parsed['scheme']) || !isset($parsed['host'])) return false;
        if (App::env('PRODUCTION') && $parsed['scheme'] !== 'https') return false;
        if (App::env('PRODUCTION') && in_array($parsed['host'], ['localhost', '127.0.0.1', '::1'])) return false;

        return true;
    }

    private static function handleCORS()
    {
        if (empty($_SERVER['HTTP_ORIGIN'])) return;

        if (!self::isValidOrigin($_SERVER['HTTP_ORIGIN'])) self::lock('Invalid origin: ' . $_SERVER['HTTP_ORIGIN'], 403, true);

        self::$config['allowed_origins'][] = self::origin();

        if (in_array($_SERVER['HTTP_ORIGIN'], self::$config['allowed_origins']))
        {
            header("Access-Control-Allow-Origin: " . $_SERVER['HTTP_ORIGIN']);
            header("Access-Control-Allow-Credentials: true");
        }
        else
        {
            self::lock('CORS blocked: ' . $_SERVER['HTTP_ORIGIN'], 403, true);
        }
    }

    /**
     * Protects against CSRF attacks using token validation
     */
    private static function csrfProtection()
    {
        if (!self::$config['csrf_protection']) return;
        if ($_SERVER['REQUEST_METHOD'] == 'GET') return;

        $csrf = Session::get('system_csrf_token', '');
        $headers = getallheaders();
        $token = $headers['X-System'] ?? '';

        Session::set('system_csrf_token', App::rand(32));

        if (!hash_equals($csrf, $token)) self::lock('Invalid CSRF token.', 403, true);
    }

    /**
     * Applies IP-based rate limiting
     */
    private static function rateLimitIP()
    {
        if (!self::$config['rate_limit']) return;

        $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
        $ip_key = 'rate_ip_' . md5($ip);
        $ip_rate = Cache::get('system', $ip_key) ?? ['count' => 0, 'time' => time()];

        if (time() - $ip_rate['time'] < self::$config['ip_rate_period'])
        {
            $ip_rate['count']++;
        }
        else
        {
            $ip_rate['count'] = 1;
            $ip_rate['time'] = time();
        }

        if ($ip_rate['count'] > self::$config['ip_rate_amount'])
        {
            Cache::set('system', $ip_key, $ip_rate);
            self::lock('Too many requests from IP.', 429, true);
        }
        else
        {
            Cache::set('system', $ip_key, $ip_rate);
        }
    }

    /**
     * Applies basic identifier-based rate limiting
     */
    private static function rateLimitVisitor()
    {
        if (!self::$config['rate_limit']) return;

        $key = self::identifier();
        $rate = Session::get($key, ['count' => 0, 'time' => time()]);

        if (time() - $rate['time'] < self::$config['rate_period'])
        {
            $rate['count']++;
        }
        else
        {
            $rate['count'] = 1;
            $rate['time'] = time();
        }

        if ($rate['count'] > self::$config['rate_amount'])
        {
            Session::set($key, $rate);
            self::lock('Too many requests.', 429, true);
        }
        else
        {
            Session::set($key, $rate);
        }
    }

    private static function origin()
    {
        if (App::env('PRODUCTION'))
        {
            return 'https://' . App::env('PROJECT_PRODUCTION');
        }

        return 'http://' . App::env('PROJECT_LOCAL');
    }
}
