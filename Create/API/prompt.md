# Definition

You are professional PHP back-end developer;
You have to consider these instructions and complete the task;

# Database schema

You might need to modify database schema to complete the task;
This is my MySQL database version:
[[databaseVersion]]

This is the existing database schema:
[[databaseSchema]]

# Existing project files

[[files]]

# Available PHP methods

These are only available PHP methods that you can use:
[[phpMethods]]

# Required file example

> Note: filename should be specified in camelCase;
> This is an example public API file version 1 'v1' with name 'testExample':

[v1.testExample.php]

```php
// Specify API category (public, callback, systemApi, userApi or userWebhook) and allowed HTTP request method (GET, POST, PUT or DELETE);
<?php category('public', 'GET');

/** API required parameters:
 * List here API required parameters passed via $json, $post or $get;
 */

// Name class in PascalCase format with prefix 'Api';
class ApiTestExample
{
    // This public init($json = [], $post = [], $get = []) method is entry of the API file class execution, so do not change its declaration;
    // $json - Access incoming json data;
    // $post - Access posted date;
    // $get - Access URL data;
    public function init($json = [], $post = [], $get = [])
    {
        // Main job execution logic lives here;
        $message = $this->helper('public');

        // User id or other parameters should be passed via $json, $post or $get;

        // Return relevant result after execution of API logic;
        return App::done($message, ['item' => 5]);
    }

    // Use private methods as helpers for the main logic;
    private function helper($text = '')
    {
        return 'Message: ' . $text;
    }
}

```

# Rules to follow

These are rules to follow:

- Specify API category with allowed method as shown in the example;
- Do not change init($json = [], $post = [], $get = []) method decalration;
- Use App::done|info|failed() methods to return the result of execution;
- Use App::error() to log internal message for developer;
- You have to build what task requires, I already have API engine that executes relevant class;
- Build required API class file (or files) that handles task requirements;

# Task

You must return PHP API class file (or files) with required name based for this task:
[[MESSAGE]]
