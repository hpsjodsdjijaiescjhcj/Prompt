-- TaskForge MySQL bootstrap schema
-- Compatible with MySQL 8+

CREATE DATABASE IF NOT EXISTS `taskforge`
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE `taskforge`;

CREATE TABLE IF NOT EXISTS `workflow_sessions` (
  `session_id` VARCHAR(64) NOT NULL,
  `state` VARCHAR(32) NOT NULL,
  `payload` LONGTEXT NOT NULL,
  `created_at` VARCHAR(64) NOT NULL,
  `updated_at` VARCHAR(64) NOT NULL,
  PRIMARY KEY (`session_id`),
  KEY `idx_workflow_state` (`state`),
  KEY `idx_workflow_updated_at` (`updated_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `analyze_history` (
  `id` VARCHAR(64) NOT NULL,
  `payload` LONGTEXT NOT NULL,
  `created_at` VARCHAR(64) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_history_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
