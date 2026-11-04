-- ============================================================
-- Hospital information system - MariaDB schema 
-- Based on FHIR R4, simplified. 
--   * Allergies are represented as strings in pathology (with a type ALLERGY)
--   * Locations are free text, with a full history per encounter
--     (encounter_location).
--   * Care type ("type de soin") is a string on ServiceRequest, Appointment
--     and Procedure; -
--   * Patient.ipp is optional (unknown in emergencies); Request.encounter is mandatory.
--   * Patient "sous X" (UNKNOWN) must have a description.
--   * Application access = (username, password);
-- 
-- ============================================================

DROP DATABASE IF EXISTS si_hospitalier;
CREATE DATABASE si_hospitalier CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE si_hospitalier;

-- ------------------------------------------------------------
-- Reference tables 
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
-- Person (+ telecom (contact_info) [0..*])
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
-- Staff
-- ------------------------------------------------------------
CREATE TABLE practitioner (
  id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  person_id  BIGINT UNSIGNED NOT NULL,
  active     BOOLEAN NOT NULL DEFAULT TRUE,
  profession VARCHAR(64) NULL,              -- free text (e.g. "Médecin", "Infirmier")
  specialty  VARCHAR(128) NULL,
  CONSTRAINT fk_practitioner_person FOREIGN KEY (person_id) REFERENCES person(id),
  UNIQUE KEY uq_practitioner_person (person_id)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Application login/auth access
-- ------------------------------------------------------------
CREATE TABLE app_user (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  username        VARCHAR(64)  NOT NULL,
  password_hash   VARCHAR(255) NOT NULL,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  UNIQUE KEY uq_user_username     (username),
  UNIQUE KEY uq_user_practitioner (practitioner_id),
  CONSTRAINT fk_user_practitioner FOREIGN KEY (practitioner_id)
    REFERENCES practitioner(id) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Patient & Stay
-- ------------------------------------------------------------
CREATE TABLE patient (
  id                    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  person_id             BIGINT UNSIGNED NOT NULL,
  ipp                   VARCHAR(32) NULL,      -- may be unknown (e.g. emergency)
  identification_status ENUM('IDENTIFIED','PROVISIONAL','UNKNOWN') NOT NULL,
  active                BOOLEAN NOT NULL DEFAULT TRUE,
  description           TEXT NULL,             -- mandatory for a patient "sous X" (UNKNOWN)
  CONSTRAINT fk_patient_person FOREIGN KEY (person_id) REFERENCES person(id),
  UNIQUE KEY uq_patient_person (person_id),
  UNIQUE KEY uq_patient_ipp (ipp),
  CONSTRAINT ck_patient_ipp CHECK (ipp IS NULL OR TRIM(ipp) <> ''),
  CONSTRAINT ck_patient_sous_x CHECK (identification_status <> 'UNKNOWN'
                                      OR TRIM(COALESCE(description, '')) <> '')
) ENGINE=InnoDB;

-- Medical / surgical - history and allergies, all represented as strings.
-- No ALLERGY rows = allergies not documented (ATTENTION!!!!!!!!!!!!!!!!!!!(how many more !?) : IT DOESNT MEAN "no allergy").
CREATE TABLE pathology (
  id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  patient_id          BIGINT UNSIGNED NOT NULL,
  pathology_type_code VARCHAR(32)  NOT NULL,
  name                VARCHAR(255) NOT NULL,
  active              BOOLEAN NOT NULL DEFAULT TRUE,
  note                TEXT NULL,
  KEY ix_patho_patient_type (patient_id, pathology_type_code),
  CONSTRAINT fk_patho_patient FOREIGN KEY (patient_id) REFERENCES patient(id),
  CONSTRAINT fk_patho_type    FOREIGN KEY (pathology_type_code) REFERENCES pathology_type(code),
  CONSTRAINT ck_patho_name    CHECK (TRIM(name) <> '')
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
  UNIQUE KEY uq_encounter_stay_number (stay_number),
  UNIQUE KEY uq_encounter_patient (id, patient_id),
  CONSTRAINT fk_enc_patient  FOREIGN KEY (patient_id) REFERENCES patient(id),
  CONSTRAINT fk_enc_type     FOREIGN KEY (encounter_type_code) REFERENCES encounter_type(code),
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

-- location history of a stay: one row per place, the current one has no period_end
CREATE TABLE encounter_location (
  id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  encounter_id BIGINT UNSIGNED NOT NULL,
  location     VARCHAR(128) NOT NULL,
  period_start DATETIME NOT NULL,
  period_end   DATETIME NULL,
  KEY ix_el_encounter (encounter_id, period_start),
  CONSTRAINT fk_el_encounter FOREIGN KEY (encounter_id)
    REFERENCES encounter(id) ON DELETE CASCADE,
  CONSTRAINT ck_el_location CHECK (TRIM(location) <> ''),
  CONSTRAINT ck_el_period   CHECK (period_end IS NULL OR period_end >= period_start)
) ENGINE=InnoDB;

CREATE TABLE vital_signs (
  id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  patient_id   BIGINT UNSIGNED NOT NULL,
  encounter_id BIGINT UNSIGNED NULL,
  effective_at DATETIME NOT NULL,
  weight_kg    DECIMAL(5,2) NULL,
  height_cm    DECIMAL(5,1) NULL,
  KEY ix_vs_latest (patient_id, effective_at),
  CONSTRAINT fk_vs_patient   FOREIGN KEY (patient_id) REFERENCES patient(id),
  CONSTRAINT fk_vs_encounter FOREIGN KEY (encounter_id, patient_id)
    REFERENCES encounter(id, patient_id),
  CONSTRAINT ck_vs_not_empty CHECK (weight_kg IS NOT NULL OR height_cm IS NOT NULL),
  CONSTRAINT ck_vs_weight    CHECK (weight_kg IS NULL OR weight_kg BETWEEN 0.2 AND 650),
  CONSTRAINT ck_vs_height    CHECK (height_cm IS NULL OR height_cm BETWEEN 20 AND 280)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Care planning & Agenda
-- ------------------------------------------------------------
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
  CONSTRAINT fk_cp_validator FOREIGN KEY (validator_id) REFERENCES app_user(id),
  CONSTRAINT ck_cp_validation CHECK (validation_status <> 'VALIDATED'
                                     OR (validator_id IS NOT NULL AND validated_at IS NOT NULL)),
  CONSTRAINT ck_cp_urgent CHECK (NOT (status = 'active' AND validation_status = 'PENDING')
                                 OR urgent),
  CONSTRAINT ck_cp_evaluation CHECK (urgent OR evaluation_id IS NOT NULL)
) ENGINE=InnoDB;

CREATE TABLE request (
  id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  request_type ENUM('SERVICE','MEDICATION') NOT NULL,
  patient_id   BIGINT UNSIGNED NOT NULL,
  encounter_id BIGINT UNSIGNED NOT NULL,     -- every request belongs to a stay (séjour)
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
  validator_id        BIGINT UNSIGNED NULL,
  validated_at        DATETIME NULL,
  UNIQUE KEY uq_req_patient   (id, patient_id),
  UNIQUE KEY uq_req_type      (id, request_type),
  UNIQUE KEY uq_req_encounter (id, encounter_id),
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
  CONSTRAINT fk_req_validator FOREIGN KEY (validator_id) REFERENCES app_user(id),
  CONSTRAINT ck_req_bounds CHECK (timing_bounds_end IS NULL OR timing_bounds_start IS NULL
                                  OR timing_bounds_end >= timing_bounds_start),
  CONSTRAINT ck_req_validation CHECK ((validator_id IS NULL) = (validated_at IS NULL)
                                      AND (care_plan_id IS NULL OR validator_id IS NULL))
) ENGINE=InnoDB;

CREATE TABLE request_timing_event (
  request_id BIGINT UNSIGNED NOT NULL,
  event_at   DATETIME NOT NULL,
  PRIMARY KEY (request_id, event_at),
  CONSTRAINT fk_rte_request FOREIGN KEY (request_id) REFERENCES request(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE request_timing_time_of_day (
  request_id  BIGINT UNSIGNED NOT NULL,
  time_of_day TIME NOT NULL,
  PRIMARY KEY (request_id, time_of_day),
  CONSTRAINT fk_rtt_request FOREIGN KEY (request_id) REFERENCES request(id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE service_request (
  request_id   BIGINT UNSIGNED NOT NULL PRIMARY KEY,
  request_type ENUM('SERVICE','MEDICATION') NOT NULL DEFAULT 'SERVICE'
               CHECK (request_type = 'SERVICE'),
  care_type    VARCHAR(128) NOT NULL,
  parameters   TEXT NULL,
  CONSTRAINT fk_sr_request FOREIGN KEY (request_id, request_type)
    REFERENCES request(id, request_type) ON DELETE CASCADE,
  CONSTRAINT ck_sr_care_type CHECK (TRIM(care_type) <> '')
) ENGINE=InnoDB;

CREATE TABLE medication_request (
  request_id               BIGINT UNSIGNED NOT NULL PRIMARY KEY,
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

-- an appointment is always created from a request (ServiceRequest / MedicationRequest)
CREATE TABLE appointment (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  patient_id      BIGINT UNSIGNED NOT NULL,
  encounter_id    BIGINT UNSIGNED NOT NULL,
  request_id      BIGINT UNSIGNED NOT NULL,
  service_type    VARCHAR(128) NULL,
  time_constraint ENUM('WEAK','STRONG') NOT NULL,
  scheduled_start DATETIME NOT NULL,
  scheduled_end   DATETIME NULL,
  created         DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
  status          ENUM('PLANNED','CANCELLED','DONE') NOT NULL DEFAULT 'PLANNED',
  parameters      TEXT NULL,
  UNIQUE KEY uq_appt_patient (id, patient_id),
  KEY ix_appt_agenda (patient_id, scheduled_start),
  CONSTRAINT fk_appt_patient   FOREIGN KEY (patient_id) REFERENCES patient(id),
  CONSTRAINT fk_appt_encounter FOREIGN KEY (encounter_id, patient_id)
    REFERENCES encounter(id, patient_id),
  CONSTRAINT fk_appt_request   FOREIGN KEY (request_id, patient_id)
    REFERENCES request(id, patient_id),
  CONSTRAINT fk_appt_req_encounter FOREIGN KEY (request_id, encounter_id)
    REFERENCES request(id, encounter_id),
  CONSTRAINT ck_appt_service_type CHECK (service_type IS NULL OR TRIM(service_type) <> ''),
  CONSTRAINT ck_appt_time CHECK (
    (time_constraint = 'STRONG' AND scheduled_end IS NULL)
    OR (time_constraint = 'WEAK' AND scheduled_end IS NOT NULL
        AND scheduled_end > scheduled_start))
) ENGINE=InnoDB;

CREATE TABLE appointment_assigned_practitioner (
  appointment_id  BIGINT UNSIGNED NOT NULL,
  practitioner_id BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY (appointment_id, practitioner_id),
  CONSTRAINT fk_aap_appointment FOREIGN KEY (appointment_id)
    REFERENCES appointment(id) ON DELETE CASCADE,
  CONSTRAINT fk_aap_practitioner FOREIGN KEY (practitioner_id) REFERENCES practitioner(id)
) ENGINE=InnoDB;

-- care_type: free text, filled automatically from the appointment / ServiceRequest.
-- May stay NULL only for a medication dose (so if based on a MedicationRequest).
-- performer [1..*]: required once status is in-progress/on-hold/stopped/completed,
-- so insert in 'preparation', add performers, then you can move the status forward.
CREATE TABLE clinical_procedure (
  id                     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  patient_id             BIGINT UNSIGNED NOT NULL,
  encounter_id           BIGINT UNSIGNED NOT NULL,
  request_id             BIGINT UNSIGNED NOT NULL,
  appointment_id         BIGINT UNSIGNED NULL,
  care_type              VARCHAR(128) NULL,
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
  CONSTRAINT fk_proc_req_encounter FOREIGN KEY (request_id, encounter_id)
    REFERENCES request(id, encounter_id),
  CONSTRAINT fk_proc_appt      FOREIGN KEY (appointment_id, patient_id)
    REFERENCES appointment(id, patient_id),
  CONSTRAINT ck_proc_care_type CHECK (care_type IS NULL OR TRIM(care_type) <> ''),
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
-- Triggers  
-- ============================================================
DELIMITER //
-- Most are taken from the HL7 standard tho, 
-- ---------- C3: an identified patient must have a family name ----------
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
CREATE TRIGGER trg_person_bu BEFORE UPDATE ON person FOR EACH ROW
BEGIN
  IF NEW.name_family IS NULL AND EXISTS (
       SELECT 1 FROM patient WHERE person_id = NEW.id
                               AND identification_status = 'IDENTIFIED') THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C3: identified patient must have a name';
  END IF;
END//

-- ---------- Location history: no overlapping periods within one encounter ----------
CREATE PROCEDURE chk_encounter_location(IN p_id BIGINT UNSIGNED, IN p_enc BIGINT UNSIGNED,
                                        IN p_start DATETIME, IN p_end DATETIME)
BEGIN
  IF EXISTS (SELECT 1 FROM encounter_location el
              WHERE el.encounter_id = p_enc
                AND el.id <> COALESCE(p_id, 0)
                AND el.period_start < COALESCE(p_end, '9999-12-31')
                AND COALESCE(el.period_end, '9999-12-31') > p_start) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'patient already has a location for this period (close the previous one first)';
  END IF;
END//
CREATE TRIGGER trg_el_bi BEFORE INSERT ON encounter_location FOR EACH ROW
  CALL chk_encounter_location(NULL, NEW.encounter_id, NEW.period_start, NEW.period_end)//
CREATE TRIGGER trg_el_bu BEFORE UPDATE ON encounter_location FOR EACH ROW
  CALL chk_encounter_location(NEW.id, NEW.encounter_id, NEW.period_start, NEW.period_end)//

-- ---------- C18: appointment service type = ServiceRequest care type ----------
CREATE FUNCTION fn_service_care_type(p_req BIGINT UNSIGNED) RETURNS VARCHAR(128)
  READS SQL DATA
BEGIN
  RETURN (SELECT care_type FROM service_request WHERE request_id = p_req);
END//

CREATE PROCEDURE resolve_appt_service_type(IN p_req BIGINT UNSIGNED, IN p_type VARCHAR(128),
                                           OUT p_out VARCHAR(128))
BEGIN
  DECLARE v_type VARCHAR(128) DEFAULT fn_service_care_type(p_req);
  SET p_out = COALESCE(p_type, v_type);
  IF v_type IS NOT NULL AND p_out <> v_type THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C18: serviceType must equal basedOn care type';
  END IF;
END//
CREATE TRIGGER trg_appt_bi BEFORE INSERT ON appointment FOR EACH ROW
BEGIN
  DECLARE v VARCHAR(128);
  CALL resolve_appt_service_type(NEW.request_id, NEW.service_type, v);
  SET NEW.service_type = v;
END//
CREATE TRIGGER trg_appt_bu BEFORE UPDATE ON appointment FOR EACH ROW
BEGIN
  DECLARE v VARCHAR(128);
  CALL resolve_appt_service_type(NEW.request_id, NEW.service_type, v);
  SET NEW.service_type = v;
END//

-- ---------- C21 + Procedure care type + performer [1..*] ----------
CREATE PROCEDURE resolve_proc(IN p_id BIGINT UNSIGNED, IN p_appt BIGINT UNSIGNED, IN p_req BIGINT UNSIGNED,
                              IN p_type VARCHAR(128), IN p_status VARCHAR(32),
                              OUT p_out VARCHAR(128))
BEGIN
  DECLARE v_appt_req  BIGINT UNSIGNED;
  DECLARE v_appt_type VARCHAR(128);
  DECLARE v_req_type  VARCHAR(128) DEFAULT fn_service_care_type(p_req);

  IF p_appt IS NOT NULL THEN
    SELECT request_id, service_type INTO v_appt_req, v_appt_type
      FROM appointment WHERE id = p_appt;
    IF v_appt_req IS NOT NULL AND NOT (v_appt_req <=> p_req) THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C21: procedure basedOn differs from fulfilled appointment';
    END IF;
  END IF;

  SET p_out = COALESCE(p_type, v_appt_type, v_req_type);

  IF (v_appt_type IS NOT NULL AND p_out <> v_appt_type)
     OR (v_req_type IS NOT NULL AND p_out <> v_req_type) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C21: procedure care type differs from appointment/request';
  END IF;

  IF p_out IS NULL AND NOT EXISTS (SELECT 1 FROM medication_request
                                    WHERE request_id = p_req) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'procedure needs a care type unless it is a medication dose';
  END IF;

  IF p_status IN ('in-progress','on-hold','stopped','completed')
     AND NOT EXISTS (SELECT 1 FROM procedure_performer
                      WHERE procedure_id = COALESCE(p_id, 0)) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'performer 1..*: add performers before moving past preparation';
  END IF;
END//
CREATE TRIGGER trg_proc_bi BEFORE INSERT ON clinical_procedure FOR EACH ROW
BEGIN
  DECLARE v VARCHAR(128);
  CALL resolve_proc(NULL, NEW.appointment_id, NEW.request_id, NEW.care_type, NEW.status, v);
  SET NEW.care_type = v;
END//
CREATE TRIGGER trg_proc_bu BEFORE UPDATE ON clinical_procedure FOR EACH ROW
BEGIN
  DECLARE v VARCHAR(128);
  CALL resolve_proc(NEW.id, NEW.appointment_id, NEW.request_id, NEW.care_type, NEW.status, v);
  SET NEW.care_type = v;
END//
CREATE TRIGGER trg_pp_bd BEFORE DELETE ON procedure_performer FOR EACH ROW
BEGIN
  IF (SELECT status FROM clinical_procedure WHERE id = OLD.procedure_id)
       IN ('in-progress','on-hold','stopped','completed')
     AND (SELECT COUNT(*) FROM procedure_performer
           WHERE procedure_id = OLD.procedure_id) = 1 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'performer 1..*: cannot remove the last performer';
  END IF;
END//

-- ---------- C11: a validated care plan keeps at least one activity ----------
CREATE TRIGGER trg_cp_bi BEFORE INSERT ON care_plan FOR EACH ROW
BEGIN
  IF NEW.validation_status = 'VALIDATED' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C11: insert PENDING, then validate';
  END IF;
END//
CREATE TRIGGER trg_cp_bu BEFORE UPDATE ON care_plan FOR EACH ROW
BEGIN
  IF NEW.validation_status = 'VALIDATED'
     AND NOT EXISTS (SELECT 1 FROM request WHERE care_plan_id = NEW.id) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C11: validated care plan needs activities';
  END IF;
END//
CREATE PROCEDURE chk_cp_keeps_activity(IN p_cp BIGINT UNSIGNED, IN p_req BIGINT UNSIGNED)
BEGIN
  IF p_cp IS NOT NULL
     AND (SELECT validation_status FROM care_plan WHERE id = p_cp) = 'VALIDATED'
     AND NOT EXISTS (SELECT 1 FROM request
                      WHERE care_plan_id = p_cp AND id <> p_req) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C11: cannot remove the last activity of a validated care plan';
  END IF;
END//
CREATE TRIGGER trg_req_bd BEFORE DELETE ON request FOR EACH ROW
  CALL chk_cp_keeps_activity(OLD.care_plan_id, OLD.id)//
CREATE TRIGGER trg_req_bu BEFORE UPDATE ON request FOR EACH ROW
BEGIN
  IF NOT (OLD.care_plan_id <=> NEW.care_plan_id) THEN
    CALL chk_cp_keeps_activity(OLD.care_plan_id, OLD.id);
  END IF;
END//

-- ---------- weightUsed: a valid prior weight of the same patient ----------
CREATE PROCEDURE chk_mr_weight(IN p_req BIGINT UNSIGNED, IN p_vs BIGINT UNSIGNED)
BEGIN
  IF p_vs IS NOT NULL AND NOT EXISTS (
       SELECT 1 FROM vital_signs v JOIN request r ON r.id = p_req
        WHERE v.id = p_vs AND v.patient_id = r.patient_id
          AND v.weight_kg IS NOT NULL
          AND v.effective_at <= r.authored_on) THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'weightUsed must be a valid prior weight of the same patient';
  END IF;
END//
CREATE TRIGGER trg_mr_bi BEFORE INSERT ON medication_request FOR EACH ROW
  CALL chk_mr_weight(NEW.request_id, NEW.weight_vital_signs_id)//
CREATE TRIGGER trg_mr_bu BEFORE UPDATE ON medication_request FOR EACH ROW
  CALL chk_mr_weight(NEW.request_id, NEW.weight_vital_signs_id)//

-- ---------- C8: admission weight required before COMPLETE ----------
CREATE PROCEDURE chk_admission_weight(IN p_enc BIGINT UNSIGNED, IN p_status VARCHAR(16))
BEGIN
  IF p_status = 'COMPLETE' AND NOT EXISTS (
       SELECT 1 FROM vital_signs
        WHERE encounter_id = p_enc AND weight_kg IS NOT NULL) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'C8: admission weight required before COMPLETE';
  END IF;
END//
CREATE TRIGGER trg_hosp_bi BEFORE INSERT ON hospitalization FOR EACH ROW
  CALL chk_admission_weight(NEW.encounter_id, NEW.admission_status)//
CREATE TRIGGER trg_hosp_bu BEFORE UPDATE ON hospitalization FOR EACH ROW
  CALL chk_admission_weight(NEW.encounter_id, NEW.admission_status)//

-- ---------- Patient.getDailySchedule(day) ----------
CREATE PROCEDURE get_daily_schedule(IN p_patient BIGINT UNSIGNED, IN p_day DATE)
BEGIN
  SELECT a.*
    FROM appointment a
   WHERE a.patient_id = p_patient
     AND a.scheduled_start >= p_day
     AND a.scheduled_start <  p_day + INTERVAL 1 DAY
     AND a.status <> 'CANCELLED'
   ORDER BY a.scheduled_start;
END//

DELIMITER ;

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

-- ============================================================
-- Views
-- ============================================================
-- Latest valid weight and height per patient
CREATE VIEW v_patient_latest_measures AS
SELECT p.id AS patient_id,
       (SELECT v.weight_kg FROM vital_signs v
         WHERE v.patient_id = p.id AND v.weight_kg IS NOT NULL
         ORDER BY v.effective_at DESC LIMIT 1) AS weight_kg,
       (SELECT v.effective_at FROM vital_signs v
         WHERE v.patient_id = p.id AND v.weight_kg IS NOT NULL
         ORDER BY v.effective_at DESC LIMIT 1) AS weight_at,
       (SELECT v.height_cm FROM vital_signs v
         WHERE v.patient_id = p.id AND v.height_cm IS NOT NULL
         ORDER BY v.effective_at DESC LIMIT 1) AS height_cm,
       (SELECT v.effective_at FROM vital_signs v
         WHERE v.patient_id = p.id AND v.height_cm IS NOT NULL
         ORDER BY v.effective_at DESC LIMIT 1) AS height_at
  FROM patient p;

-- Patient.allergies as one string (diagram v3.2); NULL = not documented
CREATE VIEW v_patient_allergies AS
SELECT p.id AS patient_id,
       (SELECT GROUP_CONCAT(pa.name ORDER BY pa.name SEPARATOR ', ')
          FROM pathology pa
         WHERE pa.patient_id = p.id AND pa.pathology_type_code = 'ALLERGY'
           AND pa.active) AS allergies
  FROM patient p;

-- Current location of each encounter 
CREATE VIEW v_encounter_current_location AS
SELECT el.encounter_id, el.location, el.period_start
  FROM encounter_location el
 WHERE el.period_end IS NULL;
