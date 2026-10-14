-- Campus Lost & Found database schema for app.py
-- Import this into a NEW/EMPTY MySQL-compatible database.
-- Back up existing data before running schema changes on an existing database.

CREATE TABLE IF NOT EXISTS `USER` (
    user_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS STUDENT (
    student_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    PRN VARCHAR(40) NOT NULL,
    dept VARCHAR(100) NOT NULL,
    PRIMARY KEY (student_id),
    UNIQUE KEY uq_student_user (user_id),
    UNIQUE KEY uq_student_prn (PRN),
    CONSTRAINT fk_student_user FOREIGN KEY (user_id) REFERENCES `USER` (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ADMIN (
    admin_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    PRIMARY KEY (admin_id),
    UNIQUE KEY uq_admin_user (user_id),
    CONSTRAINT fk_admin_user FOREIGN KEY (user_id) REFERENCES `USER` (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS CATEGORY (
    category_id INT NOT NULL AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (category_id),
    UNIQUE KEY uq_category_name (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS LOCATION (
    location_id INT NOT NULL AUTO_INCREMENT,
    location_name VARCHAR(150) NOT NULL,
    PRIMARY KEY (location_id),
    UNIQUE KEY uq_location_name (location_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS LOST_ITEM (
    lost_item_id INT NOT NULL AUTO_INCREMENT,
    student_id INT NOT NULL,
    category_id INT NOT NULL,
    location_id INT NOT NULL,
    description TEXT NOT NULL,
    date_reported DATE NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Open',
    PRIMARY KEY (lost_item_id),
    KEY idx_lost_student (student_id),
    KEY idx_lost_category_location (category_id, location_id),
    CONSTRAINT fk_lost_student FOREIGN KEY (student_id) REFERENCES STUDENT (student_id),
    CONSTRAINT fk_lost_category FOREIGN KEY (category_id) REFERENCES CATEGORY (category_id),
    CONSTRAINT fk_lost_location FOREIGN KEY (location_id) REFERENCES LOCATION (location_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS FOUND_ITEM (
    found_item_id INT NOT NULL AUTO_INCREMENT,
    student_id INT NOT NULL,
    category_id INT NOT NULL,
    location_id INT NOT NULL,
    description TEXT NOT NULL,
    date_reported DATE NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Available',
    PRIMARY KEY (found_item_id),
    KEY idx_found_student (student_id),
    KEY idx_found_category_location (category_id, location_id),
    CONSTRAINT fk_found_student FOREIGN KEY (student_id) REFERENCES STUDENT (student_id),
    CONSTRAINT fk_found_category FOREIGN KEY (category_id) REFERENCES CATEGORY (category_id),
    CONSTRAINT fk_found_location FOREIGN KEY (location_id) REFERENCES LOCATION (location_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `MATCH` (
    match_id INT NOT NULL AUTO_INCREMENT,
    lost_item_id INT NOT NULL,
    found_item_id INT NOT NULL,
    match_score INT NOT NULL DEFAULT 0,
    match_status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (match_id),
    UNIQUE KEY uq_match_pair (lost_item_id, found_item_id),
    CONSTRAINT fk_match_lost FOREIGN KEY (lost_item_id) REFERENCES LOST_ITEM (lost_item_id),
    CONSTRAINT fk_match_found FOREIGN KEY (found_item_id) REFERENCES FOUND_ITEM (found_item_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS CLAIM (
    claim_id INT NOT NULL AUTO_INCREMENT,
    student_id INT NOT NULL,
    found_item_id INT NOT NULL,
    match_id INT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'Pending',
    admin_id INT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    authorized_at DATETIME NULL,
    PRIMARY KEY (claim_id),
    KEY idx_claim_student (student_id),
    KEY idx_claim_found_status (found_item_id, status),
    CONSTRAINT fk_claim_student FOREIGN KEY (student_id) REFERENCES STUDENT (student_id),
    CONSTRAINT fk_claim_found FOREIGN KEY (found_item_id) REFERENCES FOUND_ITEM (found_item_id),
    CONSTRAINT fk_claim_match FOREIGN KEY (match_id) REFERENCES `MATCH` (match_id) ON DELETE SET NULL,
    CONSTRAINT fk_claim_admin FOREIGN KEY (admin_id) REFERENCES ADMIN (admin_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS NOTIFICATION (
    notification_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (notification_id),
    KEY idx_notification_user_read (user_id, is_read),
    CONSTRAINT fk_notification_user FOREIGN KEY (user_id) REFERENCES `USER` (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO CATEGORY (category_name) VALUES
('Electronics'), ('ID Card'), ('Books'), ('Clothing'), ('Keys'), ('Bag'), ('Bottle'), ('Other');

INSERT IGNORE INTO LOCATION (location_name) VALUES
('Library'), ('Canteen'), ('Classroom'), ('Laboratory'), ('Auditorium'), ('Sports Ground'), ('Parking Area'), ('Other');
