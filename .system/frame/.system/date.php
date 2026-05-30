<?php

// [SECURITY]
class Date
{
    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Load

    public static function init()
    {
        date_default_timezone_set('UTC');
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Main

    /** (AI-USE) - Get formatted UTC datetime, returns datetime string;
     * // Project's default timezone is set to 'UTC';
     * $event_date = Date::utc('now', 'Y-m-d H:i:s');
     */
    public static function utc(string $datetime, string $format)
    {
        $date = new DateTime($datetime);
        return $date->format($format);
    }

    /** (AI-USE) - Convert a UTC datetime string to a specific timezone and format it;
     * $display_datetime = Date::get('2026-04-21 12:00:00', 'Y-m-d H:i', 'Europe/Berlin');
     */
    public static function get(string $datetime, string $format, string $timezone)
    {
        $date = new DateTime($datetime, new DateTimeZone('UTC'));
        $date->setTimezone(new DateTimeZone($timezone));
        return $date->format($format);
    }

    //XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX> Helpers
}
