<?php

// [SECURITY]
class Storage
{
    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Params

    private static $root = '';
    private static $chunkSize = 1048576; // 1MB chunks
    private static $cipher = 'aes-256-gcm';
    private static $maxFileSize = 5242880; // 5MB max for internal content

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Load

    public static function init($folder = '')
    {
        self::$root = $folder;
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Main

    /** (AI-USE) - Checks if file and its content is legit mime type, encrypts using user storage key and stores with unique name - returns uploaded file ID or false;
     * $file_id = Storage::upload($user, $_FILES['file']['name'], $_FILES['file']);
     */
    public static function upload(int $user, string $filename, $file)
    {
        if (empty($user) || !isset($file['tmp_name'])) return false;

        $mime = self::validateFile($file['tmp_name']);
        if (!$mime) return false;

        $in = fopen($file['tmp_name'], 'rb');

        return self::createStream($user, $filename, $in, $mime);
    }

    /** (AI-USE) - Creates encrypted file - Creates file in storage with unique name, stores original filename database, returns created file ID or false;
     * $file_id = Storage::create($user, 'items/item.txt', $base64);
     */
    public static function create(int $user, string $filename, $content)
    {
        if (empty($user) || empty($filename)) return false;
        if (!is_string($content)) return false;
        if (strlen($content) > self::$maxFileSize) return false;

        $mime = self::getMimeType($filename);
        if (empty($mime)) return false;

        $stream = fopen('php://temp', 'r+');
        fwrite($stream, $content);
        rewind($stream);

        return self::createStream($user, $filename, $stream, $mime);
    }

    /** (AI-USE) - Returns decrypted file content or "";
     * $content = Storage::content($file_id);
     */
    public static function content(int $id)
    {
        if ($id <= 0) return '';
        if (empty(App::user())) return '';

        $rows = DB::query([
            'SELECT * FROM user_files WHERE id = :id LIMIT 1'
        ], ['id' => $id]);

        if (empty($rows) || !isset($rows[0])) return '';

        $file = $rows[0];
        if (!is_file($file['path'])) return '';

        $key = self::userKey($file['user']);
        $fp = fopen($file['path'], 'rb');

        if (!$fp) return '';

        $content = self::decryptToString($fp, $key);
        fclose($fp);

        return $content;
    }

    /** (AI-USE) - Deletes file by ID from storage and database - returns true or false;
     * $result = Storage::delete($file_id);
     */
    public static function delete(int $id)
    {
        if ($id <= 0) return false;
        if (empty(App::user())) return false;

        $rows = DB::query([
            'SELECT * FROM user_files WHERE id = :id LIMIT 1'
        ], ['id' => $id]);

        if (empty($rows) || !isset($rows[0])) return false;

        $file = $rows[0];
        if (!empty($file['path']) && is_file($file['path']))
        {
            @unlink($file['path']);
        }

        DB::delete('user_files', 'id = :id', [
            'id' => $id
        ]);

        return true;
    }

    /** (AI-USE) - Returns file storage URL path (e.g. /FILE/token...) or "";
     * // Returned URL path file token is valid just for once to deliver storage resource safely;
     * $url = Storage::url($file_id);
     */
    public static function url(int $id)
    {
        $rows = DB::query([
            'SELECT * FROM user_files WHERE id = :id LIMIT 1'
        ], ['id' => $id]);

        if (empty($rows)) return '';
        if (!isset($rows[0]['token'])) return '';
        if (empty($rows[0]['token'])) return '';

        return '/FILE/' . urlencode($rows[0]['token']);
    }

    /** (AI-USE) - Downloads file using id or using file token;
     * Storage::download($file_id);
     * // or
     * Storage::download(0, $file_token);
     */
    public static function download(int $id = 0, string $token = '')
    {
        if (empty($id) && empty($token)) return false;
        if (empty(App::user())) return false;

        $file = null;
        if ($id > 0)
        {
            $rows = DB::query([
                'SELECT * FROM user_files WHERE id = :id LIMIT 1'
            ], ['id' => $id]);

            if (!isset($rows[0]) || empty($rows[0])) return;
            $file = $rows[0];
        }
        elseif (!empty($token))
        {
            $rows = DB::query([
                'SELECT * FROM user_files WHERE token = :token LIMIT 1'
            ], ['token' => $token]);

            if (!isset($rows[0]) || empty($rows[0])) return;
            $file = $rows[0];
        }
        else
        {
            return false;
        }

        DB::update('user_files', [
            'token' => App::rand(32)
        ], [
            'id = :id',
        ], [
            'id' => $file['id'],
        ]);

        header('Content-Description: File Transfer');
        header('Content-Type: application/octet-stream');
        header('Content-Disposition: attachment; filename="' . self::sanitizeFileName($file['filename']) . '"');
        header('Content-Transfer-Encoding: binary');
        header('Cache-Control: no-store, no-cache, must-revalidate');
        header('Pragma: no-cache');

        $fp = fopen($file['path'], 'rb');
        self::decryptStream($fp, self::userKey($file['user']));
        fclose($fp);

        exit;
    }

    /** (AI-USE) - Deletes user storage from file system and from database - returns true or false;
     * $result = Storage::destroy($user);
     */
    public static function destroy(int $user)
    {
        $dir = self::userDir($user);

        if (is_dir($dir))
        {
            foreach (glob($dir . '/*') as $f) unlink($f);
            rmdir($dir);
        }

        DB::delete('user_files', 'user = :user', ['user' => $user]);
        DB::delete('user_keys', 'user = :user AND name = "storage"', ['user' => $user]);

        return true;
    }

    public static function deliver(string $token = '')
    {
        if (empty($token)) exit;
        if (empty(App::user())) exit;

        $file = DB::query([
            'SELECT * FROM user_files WHERE token = :token LIMIT 1'
        ], ['token' => $token]);

        if (!isset($file[0]) || empty($file[0])) exit;

        DB::update('user_files', [
            'token' => App::rand(32)
        ], [
            'id = :id',
        ], [
            'id' => $file[0]['id'],
        ]);

        $key = self::userKey($file[0]['user']);
        header('Content-Type: ' . $file[0]['mime']);
        header('Content-Disposition: inline; filename="' . self::sanitizeFileName($file[0]['filename']) . '"');

        $fp = fopen($file[0]['path'], 'rb');
        self::decryptStream($fp, $key);
        fclose($fp);

        exit;
    }

    public static function path($path)
    {
        return App::path('.system/storage/' . $path);
    }

    public static function userDir($user)
    {
        $dir = self::$root . '/' . hash('sha256', self::userKey($user));
        if (!is_dir($dir)) mkdir($dir, 0700, true);

        return $dir;
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Helpers

    private static function createStream($user, $filename, $input, $mime = 'application/octet-stream')
    {
        $key = self::userKey($user);
        $dir = self::userDir($user);

        $name = App::rand(7);
        $path = $dir . '/' . $name;

        $out = fopen($path, 'wb');

        self::encryptStream($input, $out, $key);

        fclose($input);
        fclose($out);

        return DB::insert('user_files', [
            'user' => $user,
            'filename' => $filename,
            'mime' => $mime,
            'path' => $path,
            'token' => App::rand(32)
        ]);
    }

    private static function userKey($user)
    {
        $row = DB::query([
            'SELECT * FROM user_keys',
            'WHERE user = :user AND name = :name LIMIT 1'
        ], ['user' => $user, 'name' => 'storage']);

        if ($row) return hash('sha256', $row[0]['value'] . App::env('PROJECT_KEY'));

        $key = App::rand(32);
        DB::insert('user_keys', [
            'name' => 'storage',
            'user' => $user,
            'value' => $key
        ]);

        return hash('sha256', $key . App::env('PROJECT_KEY'));
    }

    private static function sanitizeFileName(string $filename)
    {
        $filename = basename($filename);
        $filename = str_replace(["\r", "\n"], '', $filename);
        $filename = preg_replace('/[^\p{L}\p{N}_\-. ]+/u', '_', $filename);
        $filename = trim($filename);
        $filename = ltrim($filename, '-_');

        if ($filename === '') return 'file';

        return $filename;
    }

    private static function validateMagicBytes($path, $mime)
    {
        $fh = fopen($path, 'rb');
        $bytes = fread($fh, 12);
        fclose($fh);

        $signatures = [
            'image/png' => "\x89PNG",
            'image/jpeg' => "\xFF\xD8\xFF",
            'image/gif' => "GIF8",
            'application/pdf' => "%PDF",
            'video/mp4' => "ftyp"
        ];

        if (!isset($signatures[$mime])) return true;

        return strpos($bytes, $signatures[$mime]) !== false;
    }

    private static function validateContent($path, $mime)
    {
        switch ($mime)
        {
            case 'image/png':
            case 'image/jpeg':
            case 'image/gif':
                $info = @getimagesize($path);
                return $info !== false && in_array($info[2], [IMAGETYPE_PNG, IMAGETYPE_JPEG, IMAGETYPE_GIF]);
            case 'application/pdf':
                $content = file_get_contents($path, false, null, 0, 1024);
                if (strpos($content, '%PDF-') !== 0) return false;
                $size = filesize($path);
                $end = file_get_contents($path, false, null, max(0, $size - 1024), 1024);
                return strpos($end, '%%EOF') !== false;
            case 'video/mp4':
                $fh = fopen($path, 'rb');
                $bytes = fread($fh, 12);
                fclose($fh);
                return strpos($bytes, 'ftyp') !== false;
            case 'text/plain':
                $content = file_get_contents($path, false, null, 0, 512);
                return !preg_match('/\x00/', $content) && mb_check_encoding($content, 'UTF-8');
            default:
                return true;
        }
    }

    private static function validateFile($path)
    {
        $mime = self::getMimeType($path);
        if (empty($mime)) return false;

        if (!self::validateMagicBytes($path, $mime)) return false;
        if (!self::validateContent($path, $mime)) return false;

        return $mime;
    }

    private static function encryptStream($input, $output, $key)
    {
        $key = hex2bin($key);

        while (!feof($input))
        {
            $plain = fread($input, self::$chunkSize);
            if ($plain === false) break;

            $iv = random_bytes(12);
            $tag = '';

            $cipher = openssl_encrypt(
                $plain,
                self::$cipher,
                $key,
                OPENSSL_RAW_DATA,
                $iv,
                $tag
            );

            $chunk = pack('N', strlen($iv . $tag . $cipher)) . $iv . $tag . $cipher;
            fwrite($output, $chunk);
        }
    }

    private static function decryptStream($input, $key)
    {
        $key = hex2bin($key);

        while (!feof($input))
        {
            $lenData = fread($input, 4);
            if (!$lenData) break;

            $len = unpack('N', $lenData)[1];
            $chunk = fread($input, $len);

            $iv = substr($chunk, 0, 12);
            $tag = substr($chunk, 12, 16);
            $cipher = substr($chunk, 28);

            $plain = openssl_decrypt(
                $cipher,
                self::$cipher,
                $key,
                OPENSSL_RAW_DATA,
                $iv,
                $tag
            );

            if ($plain === false) continue;

            echo $plain;
            flush();
        }
    }

    private static function decryptToString($input, $key)
    {
        $key = hex2bin($key);
        $content = '';

        while (!feof($input))
        {
            $lenData = fread($input, 4);
            if (!$lenData || strlen($lenData) !== 4) break;

            $len = unpack('N', $lenData)[1];
            $chunk = fread($input, $len);

            if (strlen($chunk) !== $len) break;

            $iv = substr($chunk, 0, 12);
            $tag = substr($chunk, 12, 16);
            $cipher = substr($chunk, 28);

            $plain = openssl_decrypt(
                $cipher,
                self::$cipher,
                $key,
                OPENSSL_RAW_DATA,
                $iv,
                $tag
            );

            if ($plain === false) return false;

            $content .= $plain;
        }

        return $content;
    }

    private static function getMimeType($filename = '')
    {
        if (empty($filename)) return '';

        $extension = strtolower(pathinfo($filename, PATHINFO_EXTENSION));
        if (empty($extension)) return '';

        $mimeTypes = [
            'txt'  => 'text/plain',
            'html' => 'text/html',
            'htm'  => 'text/html',
            'css'  => 'text/css',
            'js'   => 'application/javascript',
            'json' => 'application/json',
            'xml'  => 'application/xml',
            'jpg'  => 'image/jpeg',
            'jpeg' => 'image/jpeg',
            'png'  => 'image/png',
            'gif'  => 'image/gif',
            'webp' => 'image/webp',
            'svg'  => 'image/svg+xml',
            'pdf'  => 'application/pdf',
            'zip'  => 'application/zip',
            'rar'  => 'application/vnd.rar',
            'mp3'  => 'audio/mpeg',
            'mp4'  => 'video/mp4',
            'csv'  => 'text/csv',
            'doc'  => 'application/msword',
            'docx' => 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls'  => 'application/vnd.ms-excel',
            'xlsx' => 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'ppt'  => 'application/vnd.ms-powerpoint',
            'pptx' => 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        ];

        return $mimeTypes[$extension] ?? '';
    }
}
