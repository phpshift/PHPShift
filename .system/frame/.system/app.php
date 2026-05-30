<?php

class Pages
{
    /** (AI-USE) - Returns real path of given page file/folder, used to reach page level items;
     * Pages::path('private.items/list.json');
     */
    public static function path(string $path)
    {
        return App::path('Pages/' . $path);
    }
}

class Space
{
    /** (AI-USE) - Returns real path of given space file/folder, used to reach system level global items;
     * Space::path('items.json');
     */
    public static function path(string $path)
    {
        return App::path('Space/' . $path);
    }
}

function category($name = '', $method = '')
{
    API::setCategory($name, $method);
}

class App
{
    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Params

    private static $blank = false;
    private static $cron = false;
    private static $group = '';
    private static $page = '';
    private static $action = '';
    private static $post = [];
    private static $get = [];
    private static $files = [];
    private static $lngs = [];
    private static $nonce = '';
    private static $croner = null;

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Load

    public function __construct()
    {
        $this->init();
        self::$cron = php_sapi_name() == 'cli';
        self::$nonce = App::rand(23);

        try
        {
            require_once 'session.php';
            Session::init(self::$cron);

            require_once 'cache.php';
            Cache::init('.system/cache');

            require_once 'request.php';
            Request::init(self::$cron);

            require_once 'date.php';
            Date::init();

            require_once 'database.php';
            DB::init(App::env('DB_HOST'), App::env('DB_NAME'), App::env('DB_USER'), App::env('DB_PASS'));

            require_once 'storage.php';
            Storage::init(__DIR__ . '/storage');

            if (self::$cron) return;

            $url = $this->url();
            $request = $this->request();

            require_once 'api.php';
            API::init('Apis', $request['get'], $request['post'], $request['json']);

            if (isset($url['segments'][0]) && $url['segments'][0] == 'FILE' && count($url['segments']) == 2 && isset($url['segments'][1]) && !empty($url['segments'][1]))
            {
                Storage::deliver($url['segments'][1]);
                exit;
            }

            self::$page = isset($url['segments'][0]) ? $this->normalizePageSegment($url['segments'][0]) : '';
            self::$group = $this->detectGroup();

            $default = explode('/', self::env('PROJECT_LANDING'));
            if (empty(self::$group))
            {
                self::$page = isset($default[1]) ? $this->normalizePageSegment($default[1]) : '';
                self::$group = $this->detectGroup();
            }

            $this->validateGroup();

            self::$post = $request['post'];
            self::$get = $request['get'];
            self::$files = $request['files'];
            self::$blank = $this->detectBlank();
            self::$action = $this->detectAction();
            self::$lngs = $this->loadTranslations();

            if (!self::$blank && empty(self::$action)) $this->registerPageActions();
            if (self::$blank || !empty(self::$action)) return $this->executeAction();

            header("Content-Security-Policy: base-uri 'self'; object-src 'none'; font-src 'self' https://cdnjs.cloudflare.com; connect-src 'self'; worker-src 'self'; frame-src 'self'; form-action 'self'; script-src 'self' 'nonce-" . self::$nonce . "'; script-src-attr 'unsafe-inline'; style-src 'self' 'nonce-" . self::$nonce . "' https://cdnjs.cloudflare.com; style-src-attr 'unsafe-inline';");

            $html = $this->getContent("Space/seo.html", self::$nonce);
            $html .= '<script nonce="' . self::$nonce . '">App.translations = ' . json_encode(self::$lngs) . '; App.system = "' . Request::csrf() . '"; </script>';
            $html .= $this->getContent('Pages/' . self::$group . '.' . self::$page . '/style.css', self::$nonce);
            $html .= $this->getContent('Pages/' . self::$group . '.' . self::$page . '/page.html', self::$nonce);
            $html .= $this->getContent('Pages/' . self::$group . '.' . self::$page . '/script.js', self::$nonce);
            $html .= '<script nonce="' . self::$nonce . '">$(window).on("load", function() {App.loaded()});</script>';

            echo $html;
        }
        catch (Throwable $e)
        {
            self::error($e->getMessage() . ' (' . $e->getFile() . ':' . $e->getLine() . ')');
            exit;
        }
    }

    // [SECURITY]
    private function init()
    {
        ini_set('expose_php', 'Off');
        ini_set('display_errors', '0');
        ini_set('error_log', __DIR__ . '/error.log');
        set_error_handler(function ($severity, $message, $file, $line)
        {
            throw new ErrorException($message, 0, $severity, $file, $line);
        });
        set_exception_handler(function ($e)
        {
            self::error($e->getMessage());
        });
        register_shutdown_function(function ()
        {
            $error = error_get_last();
            if ($error !== null)
            {
                self::error($error['message']);
            }
        });
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Main

    public static function danger(string $message)
    {
        self::log('danger', $message);
    }

    /** (AI-USE) - Log error for developer;
     * App::error('System failed to load request.');
     */
    public static function error(string $message)
    {
        self::log('error', $message);

        if (self::$cron) return self::cliResponse('error', $message, "");
        if (class_exists('API', false) && API::$on) return self::apiResponse('error', $message, "");
    }

    /** (AI-USE) - Return an error response and notify developer;
     * App::alert('Failed to load request.');
     */
    public static function alert(string $message, mixed $response = null)
    {
        self::log('alert', $message);

        if (self::$cron) return self::cliResponse('alert', $message, $response);
        if (API::$on) return self::apiResponse('alert', $message, $response);

        self::sendResponse(true, $message, $response);
    }

    /** (AI-USE) - Return an error response;
     * App::failed('Failed to load request.');
     */
    public static function failed(string $message, mixed $response = null)
    {
        if (self::$cron) return self::cliResponse('failed', $message, $response);
        if (API::$on) return self::apiResponse('failed', $message, $response);

        self::sendResponse(true, $message, $response);
    }

    /** (AI-USE) - Return an informational response;
     * App::info('Account created.', ['status' => $status]);
     */
    public static function info(string $message, mixed $response = null)
    {
        if (self::$cron) return self::cliResponse('info', $message, $response);
        if (API::$on) return self::apiResponse('info', $message, $response);

        self::sendResponse(false, $message, $response);
    }

    /** (AI-USE) - Return a success response;
     * App::done('Loaded items.', $items);
     */
    public static function done(string $message, mixed $response = null)
    {
        if (self::$cron) return self::cliResponse('done', $message, $response);
        if (API::$on) return self::apiResponse('done', $message, $response);

        self::sendResponse(false, $message, $response);
    }

    /** (AI-USE) - Return HTML, used in rare cases (used for controled HTML output, unsafe for dynamic user inputs);
     * App::html('Loaded component.', $html);
     */
    public static function html(string $message, string $html = '')
    {
        if (self::$cron) return self::cliResponse('html', $message, $html);
        if (API::$on) return self::apiResponse('html', $message, $html);

        self::sendResponse(false, $message, $html, false);
    }

    /** (AI-USE) - Redirect directly to page name, no page category needed;
     * App::redirect('landing');
     */
    public static function redirect(string $page)
    {
        if (empty($page)) return false;
        if (self::$blank) exit;

        header("Location: /" . $page);
        exit;
    }

    /** (AI-USE) - Checks session to get web authorized user id - returns user's id if authorized, or 0;
     * // Used only for pages or user APIs, not for Cron jobs;
     * $user = App::user();
     */
    public static function user()
    {
        if (API::$user > 0) return API::$user;
        if (!Session::has('system_user_id')) return 0;

        $user = (int)Session::get('system_user_id', 0);
        if ($user <= 0) return 0;

        return $user;
    }

    /** (AI-USE) - Registers authorized user id in session - returns true;
     * $result = App::login($user);
     */
    public static function login(int $user)
    {
        Session::renew();
        Session::set('system_user_id', (int)$user);

        return true;
    }

    /** (AI-USE) - Deletes authorized user session - returns true;
     * $result = App::logout();
     */
    public static function logout()
    {
        Session::destroy();

        return true;
    }

    /** (AI-USE) - Retrieves environment variable from project's configuration - returns environment variable value, or default value;
     * // If you ever will need environment variable in code, do not create '.env' file - just call it using App::env('...');
     * $value = App::env('ENV_VARIABLE', 1);
     */
    public static function env(string $name = '', string|int|float $default = '')
    {
        if (!$name) return $default;
        if (isset($_SERVER[$name])) return $_SERVER[$name];

        $value = getenv($name);
        if ($value !== false) return $value;

        $env = parse_ini_file(__DIR__ . '/../.env', false, INI_SCANNER_RAW);
        foreach ($env as $key => $value)
        {
            putenv("$key=$value");
        }

        if (isset($env[$name])) return $env[$name];

        return $default;
    }

    public static function encrypt($text = '', $key = '')
    {
        $encryptionKey = base64_decode($key);
        $iv = openssl_random_pseudo_bytes(openssl_cipher_iv_length('aes-256-gcm'));
        $encrypted = openssl_encrypt($text, 'aes-256-gcm', $encryptionKey, 0, $iv, $tag);
        return $encrypted . ':' . base64_encode($iv) . ':' . base64_encode($tag);
    }

    public static function decrypt($text = '', $key = '')
    {
        set_error_handler(function ($errno, $errstr)
        {
            throw new Exception("OpenSSL Error: $errstr");
            die('Adct');
        });

        $encryptionKey = base64_decode($key);
        $ex = explode(':', $text, 3);
        if (count((array)$ex) < 3)
        {
            restore_error_handler();
            return '';
        }

        list($encryptedData, $iv, $tag) = $ex;

        $result = null;
        try
        {
            $result = openssl_decrypt($encryptedData, 'aes-256-gcm', $encryptionKey, 0, base64_decode($iv), base64_decode($tag));
            restore_error_handler();
        }
        catch (Exception $e)
        {
            self::error($e->getMessage() . ' (' . $e->getFile() . ':' . $e->getLine() . ')');
            exit;
        }

        return $result;
    }

    public static function path($path)
    {
        return __DIR__ . '/../' . $path;
    }

    public static function lng($key = '', $text = '')
    {
        if (empty($key) || empty($text)) return $text;

        $lng = isset($_COOKIE['translate']) ? $_COOKIE['translate'] : 'en';

        if (!isset(self::$lngs[$lng])) $lng = 'en';
        if ($lng == 'en') return $text;
        if (isset(self::$lngs[$lng][$key])) return self::$lngs[$lng][$key];

        return $text;
    }

    public static function runCrons($args = [])
    {
        self::$croner = $args;

        require_once 'cron.php';

        $runner = new Cron(__DIR__ . '/../Crons');
        $runner->init($args);

        exit;
    }

    public static function checkCron($expression = '')
    {
        if (is_null(self::$croner)) return;
        if (!empty($expression)) Cron::check($expression);
    }

    public static function log($type = '', $message = '')
    {
        $type = self::sanitizeLogType($type);
        $message = self::sanitizeLogMessage($message);

        $timestamp = gmdate('Y-m-d H:i:s');
        file_put_contents(__DIR__ . "/{$type}.log", "[{$timestamp}] {$message}" . PHP_EOL, FILE_APPEND);
    }

    private static function sanitizeLogType($type = '')
    {
        $type = preg_replace('/[^a-z0-9_.-]+/i', '', (string)$type);
        return empty($type) ? 'app' : $type;
    }

    private static function sanitizeLogMessage($message = '')
    {
        $message = (string)$message;
        $message = preg_replace('/[\x00-\x1F\x7F]+/', ' ', $message);
        return trim($message);
    }

    public static function rand($length = 5, $uppercase = false)
    {
        $rand = substr(bin2hex(random_bytes(16)), 0, $length);
        if ($uppercase) return strtoupper($rand);

        return $rand;
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Helpers

    private function loadTranslations()
    {
        $folder = self::path('Space');
        $collect = [];
        foreach (scandir($folder) as $file)
        {
            if (!str_starts_with($file, "lng.") || !str_ends_with($file, ".json")) continue;
            $data = json_decode(file_get_contents($folder . '/' . $file), true);
            $collect[str_replace(["lng.", ".json"], "", $file)] = $this->escapeTranslations($data);
        }

        return $collect;
    }

    private function escapeTranslations($data)
    {
        if (is_array($data))
        {
            $escaped = [];
            foreach ($data as $key => $value)
            {
                $escaped[$key] = $this->escapeTranslations($value);
            }
            return $escaped;
        }

        if (is_string($data))
        {
            return htmlspecialchars($data, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
        }

        return $data;
    }

    private static function sanitizeResponseData($data)
    {
        if (is_array($data))
        {
            $sanitized = [];
            foreach ($data as $key => $value)
            {
                $sanitized[$key] = self::sanitizeResponseData($value);
            }
            return $sanitized;
        }

        if (is_object($data))
        {
            $sanitized = new stdClass();
            foreach ($data as $key => $value)
            {
                $sanitized->{$key} = self::sanitizeResponseData($value);
            }
            return $sanitized;
        }

        if (is_string($data))
        {
            return htmlspecialchars($data, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
        }

        return $data;
    }

    private static function sendResponse($error, $message, $response, $sanitize = true)
    {
        header('Content-Type: application/json');
        echo json_encode([
            'system' => Request::csrf(),
            'error' => $error,
            'message' => $message,
            'response' => $sanitize ? self::sanitizeResponseData($response) : $response
        ]);
        exit;
    }

    private static function apiResponse($type, $message, $data)
    {
        if (!empty($data)) $data = self::sanitizeResponseData($data);

        $result = [$type => $message];

        if (is_string($data)) $data = trim($data);
        if ($data === 0 || $data === '0') $result['data'] = $data;
        else if (!empty($data)) $result['data'] = $data;

        return $result;
    }

    private static function cliResponse($type, $message, $data)
    {
        if (!empty($data)) $data = self::sanitizeResponseData($data);

        $result = [$type => $message];

        if (is_string($data)) $data = trim($data);
        if ($data === 0 || $data === '0') $result['data'] = $data;
        else if (!empty($data)) $result['data'] = $data;

        print_r($result);

        return $result;
    }

    private function url()
    {
        $schema = (
            (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ||
            ($_SERVER['SERVER_PORT'] ?? 80) == 443
        ) ? 'https' : 'http';

        $host = $_SERVER['HTTP_HOST'] ?? 'localhost';
        $host = preg_replace('/[^a-zA-Z0-9\.\-:]/', '', $host);
        $uri = $_SERVER['REQUEST_URI'] ?? '/';
        $uri = filter_var($uri, FILTER_SANITIZE_URL);
        $url = $schema . '://' . $host . $uri;
        $parts = parse_url($url);
        $segments = [];

        if (!empty($parts['path']))
        {
            $segments = array_values(
                array_filter(explode('/', trim($parts['path'], '/')))
            );
        }

        return [
            'url' => $url,
            'schema' => $parts['schema'] ?? '',
            'host' => $parts['host'] ?? '',
            'path' => $parts['path'] ?? '',
            'segments' => $segments
        ];
    }

    private function request()
    {
        static $data = null;
        if ($data !== null) return $data;

        $cleanArray = function (array $source)
        {
            $clean = [];
            foreach ($source as $key => $value)
            {
                $safeKey = preg_replace('/[^a-zA-Z0-9_\-]/', '', $key);
                if ($safeKey === '') continue;

                if (is_array($value))
                {
                    $clean[$safeKey] = array_map(function ($v)
                    {
                        return $this->cleanRequestValue($v);
                    }, $value);
                }
                else
                {
                    $clean[$safeKey] = $this->cleanRequestValue($value);
                }
            }
            return $clean;
        };

        $cleanFiles = function (array $files)
        {
            $clean = [];
            foreach ($files as $key => $file)
            {
                $safeKey = preg_replace('/[^a-zA-Z0-9_\-]/', '', $key);
                if ($safeKey === '') continue;

                if (is_array($file['name']))
                {
                    $clean[$safeKey] = [
                        'name' => array_map([$this, 'cleanFileName'], $file['name']),
                        'type' => $file['type'],
                        'tmp_name' => $file['tmp_name'],
                        'error' => $file['error'],
                        'size' => $file['size']
                    ];
                }
                else
                {
                    $clean[$safeKey] = [
                        'name' => $this->cleanFileName($file['name']),
                        'type' => $file['type'],
                        'tmp_name' => $file['tmp_name'],
                        'error' => $file['error'],
                        'size' => $file['size']
                    ];
                }
            }
            return $clean;
        };

        $raw = file_get_contents('php://input');
        $jsonData = [];

        if (!empty($raw) && !str_starts_with($raw, 'system-call='))
        {
            $decoded = json_decode($raw, true);
            if (json_last_error() !== JSON_ERROR_NONE)
            {
                header('Content-Type: application/json', true, 400);
                self::sendResponse(true, 'Invalid JSON request body', []);
            }

            if (is_array($decoded)) $jsonData = $decoded;
        }

        return [
            'get' => $cleanArray($_GET),
            'post' => $cleanArray($_POST),
            'json' => $cleanArray($jsonData),
            'files' => $cleanFiles($_FILES),
        ];
    }

    private function cleanRequestValue($value)
    {
        if (empty($value)) return '';

        $value = str_replace("\0", '', $value);
        $value = trim($value);
        $value = strip_tags($value);
        $value = preg_replace('/[\x00-\x1F\x7F]/u', '', $value);

        return $value;
    }

    private function cleanFileName(string $name)
    {
        $name = basename($name);
        $name = preg_replace('/[^a-zA-Z0-9_\.\-]/', '_', $name);

        return $name;
    }

    private function normalizePageSegment(string $segment)
    {
        $segment = basename(trim($segment));
        if (preg_match('/^[a-zA-Z0-9_-]+$/', $segment)) return $segment;

        return '';
    }

    private function detectGroup()
    {
        if (empty(self::$page)) return '';

        $folder = __DIR__ . '/../Pages';
        $items = array_diff(scandir($folder), [
            '.',
            '..',
            // '',
        ]);

        $detected = "";
        foreach ($items as $x)
        {
            [$group, $page] = explode('.', $x);

            $path = "{$folder}/{$group}." . self::$page . '/code.php';
            if (!file_exists($path) || !is_readable($path)) continue;

            require_once $path;
            if (!class_exists('Page' . ucfirst(self::$page), false)) continue;

            $detected = $group;
            break;
        }

        return $detected;
    }

    private function getContent($file = '', $nonce = '')
    {
        if (empty($file)) return '';

        $file = __DIR__ . '/../' . $file;
        if (!is_file($file) || !file_exists($file) || !is_readable($file)) return '';

        $type = pathinfo($file, PATHINFO_EXTENSION);
        if ($type == 'html')
        {
            $content = file_get_contents($file);
            // Add nonce to inline scripts and styles
            $content = preg_replace('/<script([^>]*?)>/', '<script$1 nonce="' . $nonce . '">', $content);
            $content = preg_replace('/<style([^>]*?)>/', '<style$1 nonce="' . $nonce . '">', $content);
            return PHP_EOL . $content . PHP_EOL;
        }
        if ($type == 'css') return '<style nonce="' . $nonce . '">' . PHP_EOL . file_get_contents($file) . PHP_EOL . '</style>';
        if ($type == 'js') return '<script nonce="' . $nonce . '">' . PHP_EOL . file_get_contents($file) . PHP_EOL . '</script>';

        return file_get_contents($file);
    }

    private function detectBlank()
    {
        $file = __DIR__ . '/../Pages/' . self::$group . '.' . self::$page . '/page.html';
        if (file_exists($file) && is_readable($file)) return false;

        return true;
    }

    private function detectAction()
    {
        if (!isset(self::$post['system-call'])) return '';

        $call = trim(self::$post['system-call']);
        if (empty($call)) return '';
        if (!preg_match('/^[a-zA-Z0-9_]+$/', $call)) return '';
        if (!$this->isActionAllowed($call)) return '';
        if (!method_exists('Page' . ucfirst(self::$page), $call)) return '';

        return $call;
    }

    private function isActionAllowed($action = '')
    {
        if (!preg_match('/^[a-zA-Z0-9_]+$/', $action)) return false;

        $allowed = Session::get('system_page_actions', []);
        return in_array($action, $allowed, true);
    }

    private function registerPageActions()
    {
        $actions = $this->extractPageActions();
        Session::set('system_page_actions', $actions);

        return $actions;
    }

    private function extractPageActions()
    {
        $class = 'Page' . ucfirst(self::$page);
        if (!class_exists($class, false)) return [];

        $reflection = new ReflectionClass($class);
        $methods = [];
        foreach ($reflection->getMethods(ReflectionMethod::IS_PUBLIC) as $method)
        {
            if ($method->isConstructor() || $method->isStatic()) continue;
            if ($method->getDeclaringClass()->getName() !== $class) continue;

            $name = $method->getName();
            if (strpos($name, '__') === 0) continue;

            $methods[] = $name;
        }

        return array_values($methods);
    }

    private function executeAction()
    {
        if (empty(self::$page) || empty(self::$action)) die;

        $class = 'Page' . ucfirst(self::$page);
        $method = self::$action;

        if (!preg_match('/^[a-zA-Z0-9_]+$/', $method) || !$this->isActionAllowed($method)) die;
        if (file_exists(__DIR__ . '/vendor/autoload.php')) require_once __DIR__ . '/vendor/autoload.php';

        $object = new $class();
        $object->$method(self::$post, self::$get, self::$files);

        die;
    }

    private function validateGroup()
    {
        $group = self::$group;
        if (empty($group)) return '';

        require_once '../.access';
        if (!class_exists('Access', false)) return '';
        if (!method_exists('Access', $group)) return $group;
        if (!Access::$group(self::$post, self::$get, self::$files)) return '';

        return self::$group;
    }
}

$app = new App();
