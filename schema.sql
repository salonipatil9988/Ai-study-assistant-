CREATE DATABASE IF NOT EXISTS study_assistant
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE study_assistant;

CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(80) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS notes (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NULL,
    title VARCHAR(255) NOT NULL,
    subject VARCHAR(120) NULL,
    content TEXT NOT NULL,
    ai_summary TEXT NULL,
    ai_confuser TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_notes_user_id (user_id),
    CONSTRAINT fk_notes_user_id_users
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS pyq_analyses (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NULL,
    subject_name VARCHAR(255) NOT NULL,
    exam_name VARCHAR(255) NULL,
    academic_level VARCHAR(255) NULL,
    year_range VARCHAR(100) NULL,
    question_count INT NOT NULL DEFAULT 0,
    raw_pyqs TEXT NOT NULL,
    repeated_topics TEXT NOT NULL,
    exam_strategy TEXT NOT NULL,
    trend_summary TEXT NULL,
    confidence_note TEXT NULL,
    topics_json JSON NOT NULL,
    practice_questions JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_pyq_analyses_user_id (user_id),
    CONSTRAINT fk_pyq_analyses_user_id_users
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS chat_threads (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(160) NOT NULL DEFAULT 'New study session',
    context_note_ids JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_chat_threads_user_id (user_id),
    KEY ix_chat_threads_updated_at (updated_at),
    CONSTRAINT fk_chat_threads_user_id_users
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS chat_messages (
    id INT NOT NULL AUTO_INCREMENT,
    thread_id INT NOT NULL,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    sources_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_chat_messages_thread_id (thread_id),
    CONSTRAINT fk_chat_messages_thread_id_chat_threads
        FOREIGN KEY (thread_id) REFERENCES chat_threads (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
