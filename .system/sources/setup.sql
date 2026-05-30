CREATE DATABASE IF NOT EXISTS `{{DB_NAME}}` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

USE `{{DB_NAME}}`;

CREATE TABLE IF NOT EXISTS `user_files` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `user` int(11) NOT NULL,
    `filename` varchar(255) NOT NULL,
    `mime` varchar(100) NOT NULL,
    `path` text NOT NULL,
    `token` varchar(128) NOT NULL,
    `created` DATETIME NULL DEFAULT NULL,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `user_keys` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `name` varchar(50) NOT NULL,
    `user` int(11) NOT NULL,
    `value` varchar(128) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `api` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `user` int(11) NOT NULL,
    `label` VARCHAR(100) NOT NULL,
    `type` VARCHAR(50) NOT NULL,
    `name` VARCHAR(50) NOT NULL,
    `token` VARCHAR(100) NOT NULL,
    `hook` VARCHAR(500) NOT NULL,
    `expires` INT NOT NULL,
    `created` DATETIME NULL DEFAULT NULL,
    PRIMARY KEY (`id`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci;
