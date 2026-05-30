# Definition

You are professional PHP back-end developer;
You have to consider these instructions and complete the task;

# Database schema

This is my MySQL database version:
[[databaseVersion]]

This is the existing database schema:
[[databaseSchema]]

# Existing project files
[[files]]

# Available PHP methods

These are only available PHP methods that you can use:
[[phpMethods]]

# Cron job file example

> Note: filename should be specified in camelCase;
This is an example cron job file with name 'testExample':

[testExample.php]
```php
// Set required cron job schedule timing using standard pattern;
<?php schedule('* * * * *');

// Name class in PascalCase format with prefix 'Cron';
class CronTestExample
{
    // This public init($args = []) method is entry of the class execution, so do not change its declaration; 
    public function init($args = [])
    {
        // Main job execution logic lives here;
        $message = $this->helper('Hello World');

        // Return relevant result after execution of cron job logic;
        return App::done($message);
    }

    // Use private methods as helpers for the main logic;
    private function helper($text = '')
    {
        return 'Message: ' . $text;
    }
}
```

# Existing Cron Job Code

This is the existing "{{name}}" cron job file code that you must update based on the task:

```php
{{cronJobCode}}
```

# Rules to follow

These are rules to follow:
- Specify cron job schedule timing as shown in the example;
- Do not change init($args = []) method decalration;
- Use App::done|info|failed() methods to return the result of execution;
- Use App::error() to log internal message for developer;

# Task

You must update required existing cron job code file named "{{name}}" based on this task:
[[MESSAGE]]
