<?php

class Cron
{
    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Params

    private static $pendingExpression = null;
    private $cronsDir;
    private $now;

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Load

    public function __construct(string $cronsDir)
    {
        if (!is_dir($cronsDir)) App::log('cron', 'Invalid crons folder: ' . $cronsDir);

        $this->cronsDir = rtrim($cronsDir, '/\\');
        $this->now = new \DateTimeImmutable(
            (new \DateTime())->format('Y-m-d H:i') . ':00'
        );
    }

    public function init($args = [])
    {
        $files = glob($this->cronsDir . '/*.php');
        if (empty($files)) return;

        foreach ($files as $file)
        {
            $this->processFile($file, $args);
        }
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Main

    public static function check(string $expression)
    {
        self::$pendingExpression = $expression;
    }

    public function isDue(string $expression)
    {
        $fields = preg_split('/\s+/', trim($expression));

        if (count($fields) !== 5)
        {
            App::log('cron', "ERROR  Invalid cron expression (need 5 fields): {$expression}");
            return false;
        }

        [$minExpr, $hourExpr, $domExpr, $monExpr, $dowExpr] = $fields;

        $minute  = (int) $this->now->format('i');   // 0–59
        $hour    = (int) $this->now->format('G');   // 0–23
        $dom     = (int) $this->now->format('j');   // 1–31
        $month   = (int) $this->now->format('n');   // 1–12
        $dow     = (int) $this->now->format('w');   // 0 (Sun) – 6 (Sat)

        return $this->fieldMatches($minExpr,  $minute,  0, 59)
            && $this->fieldMatches($hourExpr, $hour,    0, 23)
            && $this->fieldMatches($domExpr,  $dom,     1, 31)
            && $this->fieldMatches($monExpr,  $month,   1, 12)
            && $this->fieldMatches($dowExpr,  $dow,     0,  6);
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Helpers

    private function processFile(string $file, array $args)
    {
        self::$pendingExpression = null;

        $className = $this->detectClassName($file);
        if ($className === null)
        {
            App::log('cron', "SKIP  {$file} - no class definition found.");
            return;
        }

        if (self::$pendingExpression === null)
        {
            App::log('cron', "SKIP  {$file} - schedule() was not called.");
            return;
        }

        $expression = self::$pendingExpression;
        if (!$this->isDue($expression))
        {
            App::log('cron', "WAIT  [{$expression}]  {$className}");
            return;
        }

        $this->execute($className, $expression, $args);
    }

    private function detectClassName(string $file)
    {
        require_once $file;
        $className = 'Cron' . ucfirst(str_replace(['.php', '.'], '', basename($file)));
        if (!class_exists($className, false)) return null;

        return $className;
    }

    private function execute(string $class, string $expression, array $args)
    {
        if (!class_exists($class, false))
        {
            App::log('cron', "ERROR [{$expression}]  class {$class} not found after require.");
            return;
        }

        $start = Date::utc('now', 'Y-m-d H:i:s');
        App::log('api', "RUN [{$class}] " . $start);

        try
        {
            $obj = new $class();
            $result = $obj->init($args);
            $end = Date::utc('now', 'Y-m-d H:i:s');

            if ($result !== null)
            {
                $ts1 = (float) DateTime::createFromFormat('Y-m-d H:i:s', $start)->format('U.u');
                $ts2 = (float) DateTime::createFromFormat('Y-m-d H:i:s', $end)->format('U.u');

                $result['time'] = (($ts2 - $ts1) * 1000) . ' ms';
                App::log('cron', "DONE [{$expression}]  {$end} → " . json_encode($result));
            }
        }
        catch (\Throwable $e)
        {
            $end = Date::utc('now', 'Y-m-d H:i:s');
            App::log('api', "FAIL  [{$expression}]  {$end} → {$e->getMessage()}");
        }
    }

    private function fieldMatches(string $expr, int $value, int $min, int $max)
    {
        if (str_contains($expr, ','))
        {
            foreach (explode(',', $expr) as $part)
            {
                if ($this->fieldMatches(trim($part), $value, $min, $max)) return true;
            }

            return false;
        }

        if (str_contains($expr, '/'))
        {
            [$rangeExpr, $stepStr] = explode('/', $expr, 2);
            $step = (int) $stepStr;

            if ($step <= 0) return false;

            if ($rangeExpr === '*')
            {
                $rangeMin = $min;
                $rangeMax = $max;
            }
            elseif (str_contains($rangeExpr, '-'))
            {
                [$lo, $hi]  = explode('-', $rangeExpr, 2);
                $rangeMin   = (int) $lo;
                $rangeMax   = (int) $hi;
            }
            else
            {
                $rangeMin = (int) $rangeExpr;
                $rangeMax = $max;
            }

            if ($value < $rangeMin || $value > $rangeMax) return false;

            return (($value - $rangeMin) % $step) === 0;
        }

        if (str_contains($expr, '-'))
        {
            [$lo, $hi] = explode('-', $expr, 2);
            return $value >= (int) $lo && $value <= (int) $hi;
        }

        if ($expr === '*') return true;

        return (int) $expr === $value;
    }
}
