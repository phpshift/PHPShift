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

# PHP module file example

> Note: filename should be specified in camelCase;
> This is an example global PHP module class file with name 'testExample':

[testExample.php]
```php
<?php

// Name class in PascalCase format with prefix 'Module';
class ModuleTestExample
{
    public $arg1 = '';
    public $arg2 = '';

    public function __construct($arg1 = '', $arg2 = '')
    {
        $this->arg1 = $arg1;
        $this->arg2 = $arg2;
    }

    public static function static($name = "")
    {
        die($name);
    }

    public function public($name = "")
    {
        die($this->arg1 . ' - ' . $name . ' - ' . $this->arg2);
    }
}

```

# Existing module code

This is the existing "{{name}}" module file code that you must update based on the task:

```php
{{ModuleCode}}
```

# Required files

1. "db.sql" - (if needed) Ready to execute in MySQL database;
2. "{{name}}.php" - (mandatory) Updated PHP class module file;

# Rules to follow

These are rules to follow:

- The single PHP module should be dedicated for single purpose, and should handle single service requirements;
- Build required PHP module class file (or files) that handles task requirements, and the configuration file;

# Task

You must return required files:
[[MESSAGE]]
