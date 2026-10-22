-- ============================================================
-- Hospital information system - MariaDB schema
-- ============================================================

DROP DATABASE IF EXISTS si_hospitalier;
CREATE DATABASE si_hospitalier CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE si_hospitalier;

-- ------------------------------------------------------------
-- Reference tables (enums without a known value list)
-- ------------------------------------------------------------
CREATE TABLE encounter_type (
  code  VARCHAR(32)  PRIMARY KEY,
  label VARCHAR(128) NOT NULL,
  is_inpatient BOOLEAN NOT NULL DEFAULT FALSE
) ENGINE=InnoDB;

CREATE TABLE administration_route (
  code  VARCHAR(32)  PRIMARY KEY,
  label VARCHAR(128) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE dosage_form (
  code  VARCHAR(32)  PRIMARY KEY,
  label VARCHAR(128) NOT NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Person (+ telecom [0..*])
-- ------------------------------------------------------------
CREATE TABLE person (
  id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name_family         VARCHAR(128) NULL,
  name_given          VARCHAR(128) NULL,
  gender              ENUM('male','female','other','unknown') NULL,
  birth_date          DATE NULL,
  address_line        VARCHAR(255) NULL,
  address_city        VARCHAR(128) NULL,
  address_postal_code VARCHAR(16)  NULL,
  address_country     VARCHAR(64)  NULL
) ENGINE=InnoDB;

CREATE TABLE person_telecom (
  id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  person_id BIGINT UNSIGNED NOT NULL,
  system    ENUM('phone','fax','email','pager','url','sms','other') NOT NULL,
  value     VARCHAR(255) NOT NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Staff & Departments
-- ------------------------------------------------------------
CREATE TABLE organization (
  id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(255) NOT NULL,
  active     BOOLEAN NOT NULL DEFAULT TRUE,
  part_of_id BIGINT UNSIGNED NULL
) ENGINE=InnoDB;

CREATE TABLE practitioner (
  id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  person_id BIGINT UNSIGNED NOT NULL,
  active    BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE practitioner_identifier (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  system          VARCHAR(255) NULL,
  value           VARCHAR(128) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE practitioner_role (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  organization_id BIGINT UNSIGNED NOT NULL,
  active          BOOLEAN NOT NULL DEFAULT TRUE,
  period_start    DATETIME NULL,
  period_end      DATETIME NULL,
  specialty       VARCHAR(128) NULL,
  practitioner_category   ENUM('PHYSICIAN','PARAMEDICAL','OTHER') NOT NULL,
  practitioner_profession ENUM('PHYSICIAN','NURSE','CARE_ASSISTANT',
                               'PHYSIOTHERAPIST','OTHER') NOT NULL
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Application access
-- ------------------------------------------------------------
CREATE TABLE app_role (
  id    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  code  VARCHAR(32)  NOT NULL UNIQUE,
  label VARCHAR(128) NOT NULL
) ENGINE=InnoDB;

CREATE TABLE user_account (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  person_id     BIGINT UNSIGNED NOT NULL,
  login         VARCHAR(64)  NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  active        BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE user_account_role (
  user_account_id BIGINT UNSIGNED NOT NULL,
  app_role_id     BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (user_account_id, app_role_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Patient & Stay
-- ------------------------------------------------------------
CREATE TABLE patient (
  id                    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  person_id             BIGINT UNSIGNED NOT NULL,
  ipp                   VARCHAR(32) NOT NULL,
  identification_status ENUM('IDENTIFIED','PROVISIONAL','UNKNOWN') NOT NULL,
  active                BOOLEAN NOT NULL DEFAULT TRUE,
  allergies             TEXT NULL,
  UNIQUE KEY uq_patient_ipp (ipp)
) ENGINE=InnoDB;

CREATE TABLE patient_general_practitioner (
  patient_id      BIGINT UNSIGNED NOT NULL,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (patient_id, practitioner_id)
) ENGINE=InnoDB;

CREATE TABLE related_person (
  id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  person_id    BIGINT UNSIGNED NOT NULL,
  patient_id   BIGINT UNSIGNED NOT NULL,
  relationship VARCHAR(64) NULL,
  active       BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

CREATE TABLE location (
  id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(32)  NOT NULL UNIQUE,
  name VARCHAR(128) NOT NULL,
  type ENUM('ROOM','BED','BOX') NOT NULL
) ENGINE=InnoDB;

CREATE TABLE encounter (
  id                      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  stay_number             VARCHAR(32) NOT NULL,
  patient_id              BIGINT UNSIGNED NOT NULL,
  status                  ENUM('planned','arrived','triaged','in-progress','onleave',
                               'finished','cancelled','entered-in-error','unknown') NOT NULL,
  encounter_type_code     ENUM('INPATIENT','OUTPATIENT','EMERGENCY') NOT NULL DEFAULT 'INPATIENT',
  admission_date          DATETIME NOT NULL,
  expected_discharge_date DATETIME NULL,
  actual_discharge_date   DATETIME NULL,
  reason                  VARCHAR(255) NULL,
  current_location_id     BIGINT UNSIGNED NULL,
  service_provider_id     BIGINT UNSIGNED NULL,
  UNIQUE KEY uq_encounter_stay_number (stay_number)
) ENGINE=InnoDB;

CREATE TABLE hospitalization (
  encounter_id            BIGINT UNSIGNED PRIMARY KEY,
  admission_status        ENUM('IN_PROGRESS','COMPLETE') NOT NULL DEFAULT 'IN_PROGRESS',
  assessment_completed_at DATETIME NULL
) ENGINE=InnoDB;

CREATE TABLE encounter_participant (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  encounter_id    BIGINT UNSIGNED NOT NULL,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  type            VARCHAR(64) NULL,
  period_start    DATETIME NULL,
  period_end      DATETIME NULL
) ENGINE=InnoDB;

CREATE TABLE vital_signs (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  patient_id      BIGINT UNSIGNED NOT NULL,
  encounter_id    BIGINT UNSIGNED NULL,
  recorded_by_id  BIGINT UNSIGNED NULL,
  effective_at    DATETIME NOT NULL,
  status          ENUM('final','amended','entered-in-error') NOT NULL DEFAULT 'final',
  weight_kg       DECIMAL(5,2) NULL,
  weight_method   ENUM('MEASURED','DECLARED','ESTIMATED') NULL,
  height_cm       DECIMAL(5,1) NULL,
  bmi             DECIMAL(5,2) AS (weight_kg / POWER(height_cm / 100, 2)) VIRTUAL,
  note            VARCHAR(255) NULL,
  KEY ix_vs_latest (patient_id, effective_at)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Care planning & Agenda
-- ------------------------------------------------------------
CREATE TABLE activity_definition (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  code        VARCHAR(32)  NOT NULL UNIQUE,
  name        VARCHAR(255) NOT NULL,
  description TEXT NULL
) ENGINE=InnoDB;

CREATE TABLE medication_definition (
  id               BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  code             VARCHAR(32)  NOT NULL UNIQUE,
  molecule         VARCHAR(255) NOT NULL,
  brand_name       VARCHAR(255) NULL,
  dosage_form_code VARCHAR(32)  NULL
) ENGINE=InnoDB;

CREATE TABLE care_plan (
  id                BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  patient_id        BIGINT UNSIGNED NOT NULL,
  encounter_id      BIGINT UNSIGNED NULL,
  author_id         BIGINT UNSIGNED NOT NULL,
  validator_id      BIGINT UNSIGNED NULL,
  status            ENUM('draft','active','on-hold','revoked','completed',
                         'entered-in-error','unknown') NOT NULL,
  validation_status ENUM('PENDING','VALIDATED') NOT NULL DEFAULT 'PENDING',
  urgent            BOOLEAN NOT NULL DEFAULT FALSE,
  title             VARCHAR(255) NULL,
  description       TEXT NULL,
  created           DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  validated_at      DATETIME NULL
) ENGINE=InnoDB;

CREATE TABLE request (
  id           UUID NOT NULL DEFAULT UUID() PRIMARY KEY,
  request_type ENUM('SERVICE','MEDICATION') NOT NULL,
  patient_id   BIGINT UNSIGNED NOT NULL,
  encounter_id BIGINT UNSIGNED NULL,
  requester_id BIGINT UNSIGNED NOT NULL,
  care_plan_id BIGINT UNSIGNED NULL,
  status       ENUM('draft','active','on-hold','revoked','completed',
                    'entered-in-error','unknown') NOT NULL,
  priority     ENUM('routine','urgent','asap','stat') NOT NULL DEFAULT 'routine',
  authored_on  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  note         TEXT NULL,
  timing_bounds_start DATETIME NULL,
  timing_bounds_end   DATETIME NULL,
  timing_frequency    INT UNSIGNED NULL,
  timing_period       DECIMAL(10,3) NULL,
  timing_period_unit  ENUM('s','min','h','d','wk','mo','a') NULL
) ENGINE=InnoDB;

CREATE TABLE request_timing_event (
  request_id UUID NOT NULL,
  event_at   DATETIME NOT NULL,
  PRIMARY KEY (request_id, event_at)
) ENGINE=InnoDB;

CREATE TABLE request_timing_time_of_day (
  request_id  UUID NOT NULL,
  time_of_day TIME NOT NULL,
  PRIMARY KEY (request_id, time_of_day)
) ENGINE=InnoDB;

CREATE TABLE service_request (
  request_id             UUID NOT NULL PRIMARY KEY,
  request_type           ENUM('SERVICE','MEDICATION') NOT NULL DEFAULT 'SERVICE',
  activity_definition_id BIGINT UNSIGNED NOT NULL,
  parameters             TEXT NULL
) ENGINE=InnoDB;

CREATE TABLE medication_request (
  request_id               UUID NOT NULL PRIMARY KEY,
  request_type             ENUM('SERVICE','MEDICATION') NOT NULL DEFAULT 'MEDICATION',
  medication_definition_id BIGINT UNSIGNED NOT NULL,
  dose_value               DECIMAL(12,4) NULL,
  dose_unit                VARCHAR(32) NULL,
  administration_route_code VARCHAR(32) NULL,
  dosage_text              TEXT NULL,
  weight_vital_signs_id    BIGINT UNSIGNED NULL
) ENGINE=InnoDB;

CREATE TABLE appointment (
  id                       UUID NOT NULL DEFAULT UUID() PRIMARY KEY,
  patient_id               BIGINT UNSIGNED NOT NULL,
  encounter_id             BIGINT UNSIGNED NULL,
  request_id               UUID NULL,
  activity_definition_id   BIGINT UNSIGNED NULL,
  assigned_practitioner_id BIGINT UNSIGNED NULL,
  scheduled_at             DATETIME NOT NULL,
  created                  DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  status                   ENUM('PLANNED','CANCELLED','DONE') NOT NULL DEFAULT 'PLANNED',
  parameters               TEXT NULL,
  KEY ix_appt_agenda (patient_id, scheduled_at)
) ENGINE=InnoDB;

CREATE TABLE clinical_procedure (
  id                     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  patient_id             BIGINT UNSIGNED NOT NULL,
  encounter_id           BIGINT UNSIGNED NULL,
  request_id             UUID NULL,
  appointment_id         UUID NULL,
  activity_definition_id BIGINT UNSIGNED NOT NULL,
  status                 ENUM('preparation','in-progress','not-done','on-hold',
                              'stopped','completed','entered-in-error','unknown') NOT NULL,
  performed_start        DATETIME NULL,
  performed_end          DATETIME NULL,
  note                   TEXT NULL
) ENGINE=InnoDB;

CREATE TABLE procedure_performer (
  procedure_id    BIGINT UNSIGNED NOT NULL,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (procedure_id, practitioner_id)
) ENGINE=InnoDB;

DELIMITER //

CREATE PROCEDURE get_daily_schedule(IN p_patient BIGINT UNSIGNED, IN p_day DATE)
BEGIN
  SELECT a.*
    FROM appointment a
   WHERE a.patient_id = p_patient
     AND a.scheduled_at >= p_day
     AND a.scheduled_at <  p_day + INTERVAL 1 DAY
     AND a.status <> 'CANCELLED'
   ORDER BY a.scheduled_at;
END//

DELIMITER ;

-- ============================================================
-- Seed data for reference tables (EXAMPLES - to be validated)
-- ============================================================
INSERT INTO encounter_type (code, label, is_inpatient) VALUES
  ('INPATIENT',   'Full hospitalization', TRUE),
  ('DAY_HOSPITAL','Day hospitalization',  FALSE),
  ('EMERGENCY',   'Emergency',            FALSE),
  ('OUTPATIENT',  'Outpatient visit',     FALSE);

INSERT INTO administration_route (code, label) VALUES
  ('PO', 'Oral'), ('IV', 'Intravenous'), ('IM', 'Intramuscular'),
  ('SC', 'Subcutaneous'), ('TOP', 'Topical'), ('INH', 'Inhalation');

INSERT INTO dosage_form (code, label) VALUES
  ('TAB', 'Tablet'), ('CAP', 'Capsule'), ('SOL_INJ', 'Solution for injection'),
  ('SYR', 'Syrup'), ('CREAM', 'Cream'), ('PATCH', 'Transdermal patch');

INSERT INTO app_role (code, label) VALUES
  ('ADMIN', 'Administrator'), ('PHYSICIAN', 'Physician'),
  ('NURSE', 'Nurse'), ('ADMISSION_CLERK', 'Admission clerk');

-- ============================================================
-- Latest valid weight and height per patient
-- ============================================================
CREATE VIEW v_patient_latest_measures AS
SELECT p.id AS patient_id,
       (SELECT v.weight_kg FROM vital_signs v
         WHERE v.patient_id = p.id AND v.weight_kg IS NOT NULL
           AND v.status <> 'entered-in-error'
         ORDER BY v.effective_at DESC LIMIT 1) AS weight_kg,
       (SELECT v.effective_at FROM vital_signs v
         WHERE v.patient_id = p.id AND v.weight_kg IS NOT NULL
           AND v.status <> 'entered-in-error'
         ORDER BY v.effective_at DESC LIMIT 1) AS weight_at,
       (SELECT v.height_cm FROM vital_signs v
         WHERE v.patient_id = p.id AND v.height_cm IS NOT NULL
           AND v.status <> 'entered-in-error'
         ORDER BY v.effective_at DESC LIMIT 1) AS height_cm,
       (SELECT v.effective_at FROM vital_signs v
         WHERE v.patient_id = p.id AND v.height_cm IS NOT NULL
           AND v.status <> 'entered-in-error'
         ORDER BY v.effective_at DESC LIMIT 1) AS height_at
  FROM patient p;
