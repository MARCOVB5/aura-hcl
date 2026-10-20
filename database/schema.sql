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

CREATE TABLE pathology_type (
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
  address_country     VARCHAR(64)  NULL,
  CONSTRAINT ck_person_name CHECK (name_given IS NULL OR name_family IS NOT NULL)
) ENGINE=InnoDB;

CREATE TABLE person_telecom (
  id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  person_id BIGINT UNSIGNED NOT NULL,
  system    ENUM('phone','fax','email','pager','url','sms','other') NOT NULL,
  value     VARCHAR(255) NOT NULL,
  CONSTRAINT fk_telecom_person FOREIGN KEY (person_id)
    REFERENCES person(id) ON DELETE CASCADE,
  UNIQUE KEY uq_telecom (person_id, system, value)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Staff & Departments
-- ------------------------------------------------------------
CREATE TABLE organization (
  id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(255) NOT NULL,
  active     BOOLEAN NOT NULL DEFAULT TRUE,
  part_of_id BIGINT UNSIGNED NULL,
  CONSTRAINT fk_org_part_of FOREIGN KEY (part_of_id) REFERENCES organization(id)
) ENGINE=InnoDB;

CREATE TABLE practitioner (
  id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  person_id BIGINT UNSIGNED NOT NULL,
  active    BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT fk_practitioner_person FOREIGN KEY (person_id) REFERENCES person(id),
  UNIQUE KEY uq_practitioner_person (person_id)
) ENGINE=InnoDB;

CREATE TABLE practitioner_identifier (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  system          VARCHAR(255) NULL,
  value           VARCHAR(128) NOT NULL,
  CONSTRAINT fk_prac_ident FOREIGN KEY (practitioner_id)
    REFERENCES practitioner(id) ON DELETE CASCADE,
  UNIQUE KEY uq_prac_ident (system, value)
) ENGINE=InnoDB;

CREATE TABLE practitioner_role (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  organization_id BIGINT UNSIGNED NOT NULL,
  active          BOOLEAN NOT NULL DEFAULT TRUE,
  period_start    DATETIME NULL,
  period_end      DATETIME NULL,
  specialty       VARCHAR(128) NULL,
  practitioner_category   ENUM('PHYSICIAN','PARAMEDICAL') NOT NULL,
  practitioner_profession ENUM('PHYSICIAN','NURSE','CARE_ASSISTANT',
                               'PHYSIOTHERAPIST','OTHER') NOT NULL,
  CONSTRAINT fk_role_practitioner FOREIGN KEY (practitioner_id) REFERENCES practitioner(id),
  CONSTRAINT fk_role_organization FOREIGN KEY (organization_id) REFERENCES organization(id),
  CONSTRAINT ck_role_period CHECK (period_end IS NULL OR period_start IS NULL
                                   OR period_end >= period_start),
  CONSTRAINT ck_role_category CHECK ((practitioner_category = 'PHYSICIAN')
                                     = (practitioner_profession = 'PHYSICIAN'))
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
  active        BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT fk_user_person FOREIGN KEY (person_id) REFERENCES person(id),
  UNIQUE KEY uq_user_person (person_id)
) ENGINE=InnoDB;

CREATE TABLE user_account_role (
  user_account_id BIGINT UNSIGNED NOT NULL,
  app_role_id     BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (user_account_id, app_role_id),
  CONSTRAINT fk_uar_user FOREIGN KEY (user_account_id)
    REFERENCES user_account(id) ON DELETE CASCADE,
  CONSTRAINT fk_uar_role FOREIGN KEY (app_role_id) REFERENCES app_role(id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Patient & Stay
-- ------------------------------------------------------------
CREATE TABLE patient (
  id                    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  person_id             BIGINT UNSIGNED NOT NULL,
  ipp                   VARCHAR(32) NULL,
  identification_status ENUM('IDENTIFIED','PROVISIONAL','UNKNOWN') NOT NULL,
  active                BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT fk_patient_person FOREIGN KEY (person_id) REFERENCES person(id),
  UNIQUE KEY uq_patient_person (person_id),
  UNIQUE KEY uq_patient_ipp (ipp),
  CONSTRAINT ck_patient_ipp CHECK (ipp IS NULL OR TRIM(ipp) <> '')
) ENGINE=InnoDB;

CREATE TABLE patient_general_practitioner (
  patient_id      BIGINT UNSIGNED NOT NULL,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (patient_id, practitioner_id),
  CONSTRAINT fk_pgp_patient FOREIGN KEY (patient_id)
    REFERENCES patient(id) ON DELETE CASCADE,
  CONSTRAINT fk_pgp_practitioner FOREIGN KEY (practitioner_id) REFERENCES practitioner(id)
) ENGINE=InnoDB;

CREATE TABLE related_person (
  id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  person_id    BIGINT UNSIGNED NOT NULL,
  patient_id   BIGINT UNSIGNED NOT NULL,
  relationship VARCHAR(64) NULL,
  active       BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT fk_rp_person  FOREIGN KEY (person_id)  REFERENCES person(id),
  CONSTRAINT fk_rp_patient FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE allergen (
  id       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  code     VARCHAR(32)  NOT NULL UNIQUE,
  name     VARCHAR(255) NOT NULL,
  category ENUM('food','medication','environment','biologic') NULL
) ENGINE=InnoDB;

CREATE TABLE pathology (
  id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  patient_id          BIGINT UNSIGNED NOT NULL,
  pathology_type_code VARCHAR(32)  NOT NULL,
  allergen_id         BIGINT UNSIGNED NULL,
  name                VARCHAR(255) NULL,
  active              BOOLEAN NOT NULL DEFAULT TRUE,
  note                TEXT NULL,
  UNIQUE KEY uq_patho_allergen (patient_id, allergen_id),
  CONSTRAINT fk_patho_patient  FOREIGN KEY (patient_id) REFERENCES patient(id),
  CONSTRAINT fk_patho_type     FOREIGN KEY (pathology_type_code) REFERENCES pathology_type(code),
  CONSTRAINT fk_patho_allergen FOREIGN KEY (allergen_id) REFERENCES allergen(id),
  CONSTRAINT ck_patho_allergen CHECK ((pathology_type_code = 'ALLERGY') = (allergen_id IS NOT NULL)),
  CONSTRAINT ck_patho_name     CHECK (allergen_id IS NOT NULL OR name IS NOT NULL)
) ENGINE=InnoDB;

CREATE TABLE location (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  organization_id BIGINT UNSIGNED NOT NULL,
  code            VARCHAR(32)  NOT NULL,
  name            VARCHAR(128) NOT NULL,
  type            ENUM('ROOM','BED','BOX') NOT NULL,
  UNIQUE KEY uq_location_code (organization_id, code),
  CONSTRAINT fk_loc_organization FOREIGN KEY (organization_id) REFERENCES organization(id)
) ENGINE=InnoDB;

CREATE TABLE encounter (
  id                      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  stay_number             VARCHAR(32) NOT NULL,
  patient_id              BIGINT UNSIGNED NOT NULL,
  status                  ENUM('planned','arrived','triaged','in-progress','onleave',
                               'finished','cancelled','entered-in-error','unknown') NOT NULL,
  encounter_type_code     VARCHAR(32) NOT NULL,
  admission_date          DATETIME NOT NULL,
  expected_discharge_date DATETIME NULL,
  actual_discharge_date   DATETIME NULL,
  reason                  VARCHAR(255) NULL,
  service_provider_id     BIGINT UNSIGNED NULL,
  UNIQUE KEY uq_encounter_stay_number (stay_number),
  UNIQUE KEY uq_encounter_patient (id, patient_id),
  CONSTRAINT fk_enc_patient  FOREIGN KEY (patient_id) REFERENCES patient(id),
  CONSTRAINT fk_enc_type     FOREIGN KEY (encounter_type_code) REFERENCES encounter_type(code),
  CONSTRAINT fk_enc_provider FOREIGN KEY (service_provider_id) REFERENCES organization(id),
  CONSTRAINT ck_enc_stay_number CHECK (TRIM(stay_number) <> ''),
  CONSTRAINT ck_enc_expected_discharge CHECK (expected_discharge_date IS NULL
                                              OR expected_discharge_date >= admission_date),
  CONSTRAINT ck_enc_actual_discharge   CHECK (actual_discharge_date IS NULL
                                              OR actual_discharge_date >= admission_date)
) ENGINE=InnoDB;

CREATE TABLE hospitalization (
  encounter_id            BIGINT UNSIGNED PRIMARY KEY,
  admission_status        ENUM('IN_PROGRESS','COMPLETE') NOT NULL DEFAULT 'IN_PROGRESS',
  assessment_completed_at DATETIME NULL,
  CONSTRAINT fk_hosp_encounter FOREIGN KEY (encounter_id)
    REFERENCES encounter(id) ON DELETE CASCADE,
  CONSTRAINT ck_hosp_assessment CHECK (assessment_completed_at IS NULL
                                       OR admission_status = 'COMPLETE')
) ENGINE=InnoDB;

CREATE TABLE encounter_participant (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  encounter_id    BIGINT UNSIGNED NOT NULL,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  type            VARCHAR(64) NULL,
  period_start    DATETIME NULL,
  period_end      DATETIME NULL,
  CONSTRAINT fk_ep_encounter FOREIGN KEY (encounter_id)
    REFERENCES encounter(id) ON DELETE CASCADE,
  CONSTRAINT fk_ep_practitioner FOREIGN KEY (practitioner_id) REFERENCES practitioner(id),
  CONSTRAINT ck_ep_period CHECK (period_end IS NULL OR period_start IS NULL
                                 OR period_end >= period_start)
) ENGINE=InnoDB;

CREATE TABLE encounter_location (
  id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  encounter_id BIGINT UNSIGNED NOT NULL,
  location_id  BIGINT UNSIGNED NOT NULL,
  period_start DATETIME NOT NULL,
  period_end   DATETIME NULL,
  KEY ix_el_location (location_id, period_start),
  CONSTRAINT fk_el_encounter FOREIGN KEY (encounter_id)
    REFERENCES encounter(id) ON DELETE CASCADE,
  CONSTRAINT fk_el_location  FOREIGN KEY (location_id) REFERENCES location(id),
  CONSTRAINT ck_el_period CHECK (period_end IS NULL OR period_end >= period_start)
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
  UNIQUE KEY uq_vs_patient (id, patient_id),
  KEY ix_vs_latest (patient_id, effective_at),
  CONSTRAINT fk_vs_patient   FOREIGN KEY (patient_id) REFERENCES patient(id),
  CONSTRAINT fk_vs_encounter FOREIGN KEY (encounter_id, patient_id)
    REFERENCES encounter(id, patient_id),
  CONSTRAINT fk_vs_recorder  FOREIGN KEY (recorded_by_id) REFERENCES practitioner(id),
  CONSTRAINT ck_vs_not_empty CHECK (weight_kg IS NOT NULL OR height_cm IS NOT NULL),
  CONSTRAINT ck_vs_weight    CHECK (weight_kg IS NULL OR weight_kg BETWEEN 0.2 AND 650),
  CONSTRAINT ck_vs_height    CHECK (height_cm IS NULL OR height_cm BETWEEN 20 AND 280),
  CONSTRAINT ck_vs_method    CHECK ((weight_kg IS NULL) = (weight_method IS NULL))
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
  dosage_form_code VARCHAR(32)  NULL,
  CONSTRAINT fk_med_dosage_form FOREIGN KEY (dosage_form_code) REFERENCES dosage_form(code)
) ENGINE=InnoDB;

CREATE TABLE evaluation (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  patient_id      BIGINT UNSIGNED NOT NULL,
  encounter_id    BIGINT UNSIGNED NOT NULL,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  status          ENUM('in-progress','completed','entered-in-error') NOT NULL DEFAULT 'in-progress',
  effective_at    DATETIME NOT NULL,
  summary         TEXT NULL,
  UNIQUE KEY uq_eval_patient (id, patient_id),
  CONSTRAINT fk_eval_patient      FOREIGN KEY (patient_id) REFERENCES patient(id),
  CONSTRAINT fk_eval_encounter    FOREIGN KEY (encounter_id, patient_id)
    REFERENCES encounter(id, patient_id),
  CONSTRAINT fk_eval_practitioner FOREIGN KEY (practitioner_id) REFERENCES practitioner(id)
) ENGINE=InnoDB;

CREATE TABLE care_plan (
  id                BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  patient_id        BIGINT UNSIGNED NOT NULL,
  encounter_id      BIGINT UNSIGNED NULL,
  evaluation_id     BIGINT UNSIGNED NULL,
  author_id         BIGINT UNSIGNED NOT NULL,
  validator_id      BIGINT UNSIGNED NULL,
  status            ENUM('draft','active','on-hold','revoked','completed',
                         'entered-in-error','unknown') NOT NULL,
  validation_status ENUM('PENDING','VALIDATED') NOT NULL DEFAULT 'PENDING',
  urgent            BOOLEAN NOT NULL DEFAULT FALSE,
  title             VARCHAR(255) NULL,
  description       TEXT NULL,
  created           DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  validated_at      DATETIME NULL,
  UNIQUE KEY uq_cp_patient (id, patient_id),
  UNIQUE KEY uq_cp_author  (id, author_id),
  CONSTRAINT fk_cp_patient   FOREIGN KEY (patient_id) REFERENCES patient(id),
  CONSTRAINT fk_cp_encounter FOREIGN KEY (encounter_id, patient_id)
    REFERENCES encounter(id, patient_id),
  CONSTRAINT fk_cp_evaluation FOREIGN KEY (evaluation_id, patient_id)
    REFERENCES evaluation(id, patient_id),
  CONSTRAINT fk_cp_author    FOREIGN KEY (author_id) REFERENCES practitioner(id),
  CONSTRAINT fk_cp_validator FOREIGN KEY (validator_id) REFERENCES user_account(id),
  CONSTRAINT ck_cp_validation CHECK (validation_status <> 'VALIDATED'
                                     OR (validator_id IS NOT NULL AND validated_at IS NOT NULL)),
  CONSTRAINT ck_cp_urgent CHECK (NOT (status = 'active' AND validation_status = 'PENDING')
                                 OR urgent),
  CONSTRAINT ck_cp_evaluation CHECK (urgent OR evaluation_id IS NOT NULL)
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
  timing_period_unit  ENUM('s','min','h','d','wk','mo','a') NULL,
  UNIQUE KEY uq_req_patient (id, patient_id),
  UNIQUE KEY uq_req_type    (id, request_type),
  CONSTRAINT fk_req_patient   FOREIGN KEY (patient_id) REFERENCES patient(id),
  CONSTRAINT fk_req_encounter FOREIGN KEY (encounter_id, patient_id)
    REFERENCES encounter(id, patient_id),
  CONSTRAINT fk_req_requester FOREIGN KEY (requester_id) REFERENCES practitioner(id),
  CONSTRAINT fk_req_cp_patient FOREIGN KEY (care_plan_id, patient_id)
    REFERENCES care_plan(id, patient_id),
  CONSTRAINT fk_req_cp_author  FOREIGN KEY (care_plan_id, requester_id)
    REFERENCES care_plan(id, author_id),
  CONSTRAINT ck_req_recurrence CHECK (timing_frequency IS NULL OR
      (timing_frequency > 0 AND timing_bounds_start IS NOT NULL
       AND timing_period > 0 AND timing_period_unit IS NOT NULL)),
  CONSTRAINT ck_req_bounds CHECK (timing_bounds_end IS NULL OR timing_bounds_start IS NULL
                                  OR timing_bounds_end >= timing_bounds_start)
) ENGINE=InnoDB;

CREATE TABLE request_timing_event (
  request_id UUID NOT NULL,
  event_at   DATETIME NOT NULL,
  PRIMARY KEY (request_id, event_at),
  CONSTRAINT fk_rte_request FOREIGN KEY (request_id) REFERENCES request(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE request_timing_time_of_day (
  request_id  UUID NOT NULL,
  time_of_day TIME NOT NULL,
  PRIMARY KEY (request_id, time_of_day),
  CONSTRAINT fk_rtt_request FOREIGN KEY (request_id) REFERENCES request(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE service_request (
  request_id             UUID NOT NULL PRIMARY KEY,
  request_type           ENUM('SERVICE','MEDICATION') NOT NULL DEFAULT 'SERVICE'
                         CHECK (request_type = 'SERVICE'),
  activity_definition_id BIGINT UNSIGNED NOT NULL,
  parameters             TEXT NULL,
  CONSTRAINT fk_sr_request FOREIGN KEY (request_id, request_type)
    REFERENCES request(id, request_type) ON DELETE CASCADE,
  CONSTRAINT fk_sr_activity FOREIGN KEY (activity_definition_id)
    REFERENCES activity_definition(id)
) ENGINE=InnoDB;

CREATE TABLE medication_request (
  request_id               UUID NOT NULL PRIMARY KEY,
  request_type             ENUM('SERVICE','MEDICATION') NOT NULL DEFAULT 'MEDICATION'
                           CHECK (request_type = 'MEDICATION'),
  medication_definition_id BIGINT UNSIGNED NOT NULL,
  dose_value               DECIMAL(12,4) NULL,
  dose_unit                VARCHAR(32) NULL,
  administration_route_code VARCHAR(32) NULL,
  dosage_text              TEXT NULL,
  weight_vital_signs_id    BIGINT UNSIGNED NULL,
  CONSTRAINT fk_mr_weight FOREIGN KEY (weight_vital_signs_id) REFERENCES vital_signs(id),
  CONSTRAINT fk_mr_request FOREIGN KEY (request_id, request_type)
    REFERENCES request(id, request_type) ON DELETE CASCADE,
  CONSTRAINT fk_mr_medication FOREIGN KEY (medication_definition_id)
    REFERENCES medication_definition(id),
  CONSTRAINT fk_mr_route FOREIGN KEY (administration_route_code)
    REFERENCES administration_route(code),
  CONSTRAINT ck_mr_dose CHECK ((dose_value IS NULL) = (dose_unit IS NULL))
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
  UNIQUE KEY uq_appt_patient (id, patient_id),
  KEY ix_appt_agenda (patient_id, scheduled_at),
  CONSTRAINT fk_appt_patient   FOREIGN KEY (patient_id) REFERENCES patient(id),
  CONSTRAINT fk_appt_encounter FOREIGN KEY (encounter_id, patient_id)
    REFERENCES encounter(id, patient_id),
  CONSTRAINT fk_appt_request   FOREIGN KEY (request_id, patient_id)
    REFERENCES request(id, patient_id),
  CONSTRAINT fk_appt_activity  FOREIGN KEY (activity_definition_id)
    REFERENCES activity_definition(id),
  CONSTRAINT fk_appt_practitioner FOREIGN KEY (assigned_practitioner_id)
    REFERENCES practitioner(id)
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
  note                   TEXT NULL,
  UNIQUE KEY uq_proc_appointment (appointment_id),
  CONSTRAINT fk_proc_patient   FOREIGN KEY (patient_id) REFERENCES patient(id),
  CONSTRAINT fk_proc_encounter FOREIGN KEY (encounter_id, patient_id)
    REFERENCES encounter(id, patient_id),
  CONSTRAINT fk_proc_request   FOREIGN KEY (request_id, patient_id)
    REFERENCES request(id, patient_id),
  CONSTRAINT fk_proc_appt      FOREIGN KEY (appointment_id, patient_id)
    REFERENCES appointment(id, patient_id),
  CONSTRAINT fk_proc_activity  FOREIGN KEY (activity_definition_id)
    REFERENCES activity_definition(id),
  CONSTRAINT ck_proc_period CHECK (performed_end IS NULL OR performed_start IS NULL
                                   OR performed_end >= performed_start)
) ENGINE=InnoDB;

CREATE TABLE procedure_performer (
  procedure_id    BIGINT UNSIGNED NOT NULL,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (procedure_id, practitioner_id),
  CONSTRAINT fk_pp_procedure FOREIGN KEY (procedure_id)
    REFERENCES clinical_procedure(id) ON DELETE CASCADE,
  CONSTRAINT fk_pp_practitioner FOREIGN KEY (practitioner_id) REFERENCES practitioner(id)
) ENGINE=InnoDB;

-- ============================================================
-- Triggers for cross-table invariants
-- ============================================================
DELIMITER //

CREATE PROCEDURE chk_patient_identified(IN p_person BIGINT UNSIGNED, IN p_status VARCHAR(16))
BEGIN
  IF p_status = 'IDENTIFIED' AND
     (SELECT name_family FROM person WHERE id = p_person) IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C3: identified patient must have a name';
  END IF;
END//
CREATE TRIGGER trg_patient_bi BEFORE INSERT ON patient FOR EACH ROW
  CALL chk_patient_identified(NEW.person_id, NEW.identification_status)//
CREATE TRIGGER trg_patient_bu BEFORE UPDATE ON patient FOR EACH ROW
  CALL chk_patient_identified(NEW.person_id, NEW.identification_status)//

CREATE PROCEDURE chk_location_free(IN p_id BIGINT UNSIGNED, IN p_enc BIGINT UNSIGNED,
                                   IN p_loc BIGINT UNSIGNED, IN p_start DATETIME, IN p_end DATETIME)
BEGIN
  IF (SELECT type FROM location WHERE id = p_loc) IN ('BED','BOX')
     AND EXISTS (SELECT 1 FROM encounter_location el
                 WHERE el.location_id = p_loc
                   AND el.id <> COALESCE(p_id, 0)
                   AND el.period_start < COALESCE(p_end, '9999-12-31')
                   AND COALESCE(el.period_end, '9999-12-31') > p_start) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C7: bed/box already occupied';
  END IF;
  IF EXISTS (SELECT 1 FROM encounter_location el
              WHERE el.encounter_id = p_enc
                AND el.id <> COALESCE(p_id, 0)
                AND el.period_start < COALESCE(p_end, '9999-12-31')
                AND COALESCE(el.period_end, '9999-12-31') > p_start) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'patient already has a location for this period';
  END IF;
END//
CREATE TRIGGER trg_el_bi BEFORE INSERT ON encounter_location FOR EACH ROW
  CALL chk_location_free(NULL, NEW.encounter_id, NEW.location_id, NEW.period_start, NEW.period_end)//
CREATE TRIGGER trg_el_bu BEFORE UPDATE ON encounter_location FOR EACH ROW
  CALL chk_location_free(NEW.id, NEW.encounter_id, NEW.location_id, NEW.period_start, NEW.period_end)//

CREATE PROCEDURE chk_appt_service_type(IN p_req UUID, IN p_act BIGINT UNSIGNED)
BEGIN
  DECLARE v_code BIGINT UNSIGNED;
  IF p_req IS NOT NULL THEN
    SELECT activity_definition_id INTO v_code FROM service_request WHERE request_id = p_req;
    IF v_code IS NOT NULL AND NOT (p_act <=> v_code) THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C18: serviceType must equal basedOn.code';
    END IF;
  END IF;
END//
CREATE TRIGGER trg_appt_bi BEFORE INSERT ON appointment FOR EACH ROW
  CALL chk_appt_service_type(NEW.request_id, NEW.activity_definition_id)//
CREATE TRIGGER trg_appt_bu BEFORE UPDATE ON appointment FOR EACH ROW
  CALL chk_appt_service_type(NEW.request_id, NEW.activity_definition_id)//

CREATE PROCEDURE chk_proc_fulfills(IN p_appt UUID, IN p_req UUID, IN p_act BIGINT UNSIGNED)
BEGIN
  DECLARE v_req UUID;
  DECLARE v_act BIGINT UNSIGNED;
  IF p_appt IS NOT NULL THEN
    SELECT request_id, activity_definition_id INTO v_req, v_act
      FROM appointment WHERE id = p_appt;
    IF (v_act IS NOT NULL AND v_act <> p_act)
       OR (v_req IS NOT NULL AND NOT (v_req <=> p_req)) THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C21: procedure inconsistent with fulfilled appointment';
    END IF;
  END IF;
END//
CREATE TRIGGER trg_proc_bi BEFORE INSERT ON clinical_procedure FOR EACH ROW
  CALL chk_proc_fulfills(NEW.appointment_id, NEW.request_id, NEW.activity_definition_id)//
CREATE TRIGGER trg_proc_bu BEFORE UPDATE ON clinical_procedure FOR EACH ROW
  CALL chk_proc_fulfills(NEW.appointment_id, NEW.request_id, NEW.activity_definition_id)//

CREATE TRIGGER trg_cp_bu BEFORE UPDATE ON care_plan FOR EACH ROW
BEGIN
  IF NEW.validation_status = 'VALIDATED'
     AND NOT EXISTS (SELECT 1 FROM request WHERE care_plan_id = NEW.id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C11: validated care plan needs activities';
  END IF;
END//
CREATE TRIGGER trg_cp_bi BEFORE INSERT ON care_plan FOR EACH ROW
BEGIN
  IF NEW.validation_status = 'VALIDATED' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C11: insert PENDING, then validate';
  END IF;
END//

CREATE PROCEDURE chk_mr_weight(IN p_req UUID, IN p_vs BIGINT UNSIGNED)
BEGIN
  IF p_vs IS NOT NULL AND NOT EXISTS (
       SELECT 1 FROM vital_signs v JOIN request r ON r.id = p_req
        WHERE v.id = p_vs AND v.patient_id = r.patient_id
          AND v.weight_kg IS NOT NULL AND v.status <> 'entered-in-error'
          AND v.effective_at <= r.authored_on) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'weightUsed must be a valid prior weight of the same patient';
  END IF;
END//
CREATE TRIGGER trg_mr_bi BEFORE INSERT ON medication_request FOR EACH ROW
  CALL chk_mr_weight(NEW.request_id, NEW.weight_vital_signs_id)//
CREATE TRIGGER trg_mr_bu BEFORE UPDATE ON medication_request FOR EACH ROW
  CALL chk_mr_weight(NEW.request_id, NEW.weight_vital_signs_id)//

CREATE PROCEDURE chk_admission_weight(IN p_enc BIGINT UNSIGNED, IN p_status VARCHAR(16))
BEGIN
  IF p_status = 'COMPLETE' AND NOT EXISTS (
       SELECT 1 FROM vital_signs
        WHERE encounter_id = p_enc AND weight_kg IS NOT NULL
          AND status <> 'entered-in-error') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C8: admission weight required before COMPLETE';
  END IF;
END//
CREATE TRIGGER trg_hosp_bi BEFORE INSERT ON hospitalization FOR EACH ROW
  CALL chk_admission_weight(NEW.encounter_id, NEW.admission_status)//
CREATE TRIGGER trg_hosp_bu BEFORE UPDATE ON hospitalization FOR EACH ROW
  CALL chk_admission_weight(NEW.encounter_id, NEW.admission_status)//

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

INSERT INTO pathology_type (code, label) VALUES
  ('ALLERGY', 'Allergy'), ('MEDICAL', 'Medical condition'),
  ('SURGICAL', 'Surgical history'), ('OBSTETRIC', 'Obstetric history');

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
