-- ============================================================
--  COMP 102 – Introduction to Database | Final Project
--  Option A: Public Health Clinic Records System
--  SDG 3: Good Health and Well-being
--  Limkokwing University of Creative Technology – Sierra Leone
-- ============================================================

-- ============================================================
-- SECTION 1: DATABASE CREATION
-- ============================================================

DROP DATABASE IF EXISTS public_health_clinic_db;
CREATE DATABASE public_health_clinic_db;
USE public_health_clinic_db;

-- ============================================================
-- SECTION 2: TABLE CREATION WITH CONSTRAINTS
-- ============================================================

-- 2.1 Clinic Table
CREATE TABLE Clinic (
    clinic_id       INT             NOT NULL AUTO_INCREMENT,
    clinic_name     VARCHAR(100)    NOT NULL,
    location        VARCHAR(150)    NOT NULL,
    district        VARCHAR(50)     NOT NULL,
    phone           VARCHAR(20)     NOT NULL,
    email           VARCHAR(100)    DEFAULT NULL,
    established_date DATE           DEFAULT NULL,
    PRIMARY KEY (clinic_id)
);

-- 2.2 Staff Table
CREATE TABLE Staff (
    staff_id        INT             NOT NULL AUTO_INCREMENT,
    clinic_id       INT             NOT NULL,
    first_name      VARCHAR(50)     NOT NULL,
    last_name       VARCHAR(50)     NOT NULL,
    role            VARCHAR(50)     NOT NULL,  -- e.g., Doctor, Nurse, Receptionist
    gender          ENUM('Male','Female','Other') NOT NULL,
    phone           VARCHAR(20)     NOT NULL,
    email           VARCHAR(100)    DEFAULT NULL,
    hire_date       DATE            NOT NULL,
    PRIMARY KEY (staff_id),
    CONSTRAINT fk_staff_clinic FOREIGN KEY (clinic_id) REFERENCES Clinic(clinic_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 2.3 Patient Table
CREATE TABLE Patient (
    patient_id      INT             NOT NULL AUTO_INCREMENT,
    first_name      VARCHAR(50)     NOT NULL,
    last_name       VARCHAR(50)     NOT NULL,
    date_of_birth   DATE            NOT NULL,
    gender          ENUM('Male','Female','Other') NOT NULL,
    address         VARCHAR(200)    NOT NULL,
    phone           VARCHAR(20)     NOT NULL,
    blood_type      VARCHAR(5)      DEFAULT NULL,
    registration_date DATE          NOT NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (patient_id)
);

-- 2.4 Appointment Table
CREATE TABLE Appointment (
    appointment_id  INT             NOT NULL AUTO_INCREMENT,
    patient_id      INT             NOT NULL,
    staff_id        INT             NOT NULL,
    clinic_id       INT             NOT NULL,
    appointment_date DATE           NOT NULL,
    appointment_time TIME           NOT NULL,
    reason          VARCHAR(200)    NOT NULL,
    status          ENUM('Scheduled','Completed','Cancelled') NOT NULL DEFAULT 'Scheduled',
    PRIMARY KEY (appointment_id),
    CONSTRAINT fk_appt_patient  FOREIGN KEY (patient_id)  REFERENCES Patient(patient_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_appt_staff    FOREIGN KEY (staff_id)    REFERENCES Staff(staff_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_appt_clinic   FOREIGN KEY (clinic_id)   REFERENCES Clinic(clinic_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 2.5 Diagnosis Table
CREATE TABLE Diagnosis (
    diagnosis_id    INT             NOT NULL AUTO_INCREMENT,
    appointment_id  INT             NOT NULL,
    diagnosis_code  VARCHAR(20)     NOT NULL,  -- ICD-10 style code
    description     VARCHAR(300)    NOT NULL,
    severity        ENUM('Mild','Moderate','Severe') NOT NULL DEFAULT 'Mild',
    diagnosed_date  DATE            NOT NULL,
    PRIMARY KEY (diagnosis_id),
    CONSTRAINT fk_diag_appointment FOREIGN KEY (appointment_id) REFERENCES Appointment(appointment_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 2.6 Medication Table
CREATE TABLE Medication (
    medication_id   INT             NOT NULL AUTO_INCREMENT,
    medication_name VARCHAR(100)    NOT NULL,
    description     VARCHAR(200)    DEFAULT NULL,
    unit            VARCHAR(30)     NOT NULL,   -- e.g., mg, ml, tablet
    stock_quantity  INT             NOT NULL DEFAULT 0,
    PRIMARY KEY (medication_id)
);

-- 2.7 Prescription Table
CREATE TABLE Prescription (
    prescription_id INT             NOT NULL AUTO_INCREMENT,
    diagnosis_id    INT             NOT NULL,
    medication_id   INT             NOT NULL,
    dosage          VARCHAR(100)    NOT NULL,
    frequency       VARCHAR(100)    NOT NULL,   -- e.g., twice daily
    duration_days   INT             NOT NULL,
    prescribed_date DATE            NOT NULL,
    PRIMARY KEY (prescription_id),
    CONSTRAINT fk_pres_diagnosis  FOREIGN KEY (diagnosis_id)  REFERENCES Diagnosis(diagnosis_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_pres_medication FOREIGN KEY (medication_id) REFERENCES Medication(medication_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 2.8 Bill Table
CREATE TABLE Bill (
    bill_id         INT             NOT NULL AUTO_INCREMENT,
    patient_id      INT             NOT NULL,
    appointment_id  INT             NOT NULL,
    total_amount    DECIMAL(10,2)   NOT NULL DEFAULT 0.00,
    amount_paid     DECIMAL(10,2)   NOT NULL DEFAULT 0.00,
    bill_date       DATE            NOT NULL,
    payment_status  ENUM('Unpaid','Partial','Paid') NOT NULL DEFAULT 'Unpaid',
    PRIMARY KEY (bill_id),
    CONSTRAINT fk_bill_patient     FOREIGN KEY (patient_id)     REFERENCES Patient(patient_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_bill_appointment FOREIGN KEY (appointment_id) REFERENCES Appointment(appointment_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- ============================================================
-- SECTION 3: SAMPLE DATA INSERTION
-- ============================================================

-- 3.1 Insert Clinics
INSERT INTO Clinic (clinic_name, location, district, phone, email, established_date) VALUES
('Connaught Community Clinic',   'Siaka Stevens Street, Freetown',  'Western Area Urban',   '+232-76-100001', 'connaught@health.gov.sl',  '2005-03-15'),
('Kissy Public Health Clinic',   'Kissy Road, Freetown',            'Western Area Urban',   '+232-76-100002', 'kissy@health.gov.sl',       '2008-07-20'),
('Bo District Health Clinic',    'Dambara Road, Bo',                'Bo District',          '+232-76-100003', 'bo.clinic@health.gov.sl',   '2010-01-10'),
('Makeni General Clinic',        'Rogbonko Road, Makeni',           'Bombali District',     '+232-76-100004', 'makeni@health.gov.sl',      '2012-05-05'),
('Kenema Health Post',           'Hangha Road, Kenema',             'Kenema District',      '+232-76-100005', 'kenema@health.gov.sl',      '2015-09-01');

-- 3.2 Insert Staff
INSERT INTO Staff (clinic_id, first_name, last_name, role, gender, phone, email, hire_date) VALUES
(1, 'Mohamed',   'Kamara',    'Doctor',       'Male',   '+232-77-200001', 'mkamara@health.sl',   '2010-06-01'),
(1, 'Aminata',   'Conteh',    'Nurse',        'Female', '+232-77-200002', 'aconteh@health.sl',   '2012-03-15'),
(1, 'Ibrahim',   'Sesay',     'Receptionist', 'Male',   '+232-77-200003', 'isesay@health.sl',    '2015-01-10'),
(2, 'Fatmata',   'Koroma',    'Doctor',       'Female', '+232-77-200004', 'fkoroma@health.sl',   '2009-08-20'),
(2, 'Samuel',    'Bangura',   'Nurse',        'Male',   '+232-77-200005', 'sbangura@health.sl',  '2013-11-01'),
(3, 'Mariama',   'Turay',     'Doctor',       'Female', '+232-77-200006', 'mturay@health.sl',    '2011-04-15'),
(4, 'Abdul',     'Jalloh',    'Nurse',        'Male',   '+232-77-200007', 'ajalloh@health.sl',   '2016-02-28'),
(5, 'Patricia',  'Mansaray',  'Doctor',       'Female', '+232-77-200008', 'pmansaray@health.sl', '2018-07-01');

-- 3.3 Insert Patients
INSERT INTO Patient (first_name, last_name, date_of_birth, gender, address, phone, blood_type, registration_date) VALUES
('Adama',      'Fofanah',   '1990-04-12', 'Female', '14 Wellington Street, Freetown',   '+232-78-300001', 'O+',  '2023-01-10'),
('Sorie',      'Kamara',    '1985-09-25', 'Male',   '7 Circular Road, Freetown',        '+232-78-300002', 'A+',  '2023-02-14'),
('Hawa',       'Bangura',   '2000-06-30', 'Female', '22 Sanders Street, Freetown',      '+232-78-300003', 'B+',  '2023-03-05'),
('Thomas',     'Koroma',    '1978-11-03', 'Male',   '5 Liverpool Street, Freetown',     '+232-78-300004', 'AB+', '2023-04-20'),
('Isata',      'Turay',     '1995-07-17', 'Female', '9 Kroo Bay, Freetown',             '+232-78-300005', 'O-',  '2023-05-11'),
('Alimamy',    'Sesay',     '1970-02-28', 'Male',   '30 Lumley Beach Road, Freetown',   '+232-78-300006', 'A-',  '2023-06-01'),
('Kadiatu',    'Conteh',    '2005-12-15', 'Female', '18 Bo Highway, Bo',                '+232-78-300007', 'B-',  '2024-01-08'),
('Emmanuel',   'Jalloh',    '1988-08-09', 'Male',   '4 Makeni Central, Makeni',         '+232-78-300008', 'O+',  '2024-02-22'),
('Memunatu',   'Mansaray',  '1993-03-21', 'Female', '12 Kenema Town, Kenema',           '+232-78-300009', 'A+',  '2024-03-15'),
('David',      'Fullah',    '1965-10-10', 'Male',   '3 Hill Station, Freetown',         '+232-78-300010', 'AB-', '2024-04-05');

-- 3.4 Insert Appointments
INSERT INTO Appointment (patient_id, staff_id, clinic_id, appointment_date, appointment_time, reason, status) VALUES
(1,  1, 1, '2024-05-01', '08:30:00', 'Fever and headache',              'Completed'),
(2,  1, 1, '2024-05-02', '09:00:00', 'Routine check-up',                'Completed'),
(3,  4, 2, '2024-05-03', '10:00:00', 'Persistent cough',                'Completed'),
(4,  6, 3, '2024-05-04', '11:00:00', 'Diabetes management',             'Completed'),
(5,  1, 1, '2024-05-05', '08:00:00', 'Malaria symptoms',                'Completed'),
(6,  4, 2, '2024-05-06', '09:30:00', 'Hypertension follow-up',          'Completed'),
(7,  6, 3, '2024-05-07', '10:30:00', 'Vaccination',                     'Completed'),
(8,  8, 5, '2024-05-08', '14:00:00', 'Abdominal pain',                  'Completed'),
(9,  8, 5, '2024-05-09', '11:00:00', 'Prenatal visit',                  'Completed'),
(10, 1, 1, '2024-05-10', '15:00:00', 'Joint pain and swelling',         'Completed'),
(1,  4, 2, '2024-06-01', '08:30:00', 'Malaria follow-up',               'Completed'),
(3,  1, 1, '2024-06-05', '09:00:00', 'Respiratory check',               'Scheduled'),
(5,  6, 3, '2024-06-10', '10:00:00', 'Malaria re-test',                 'Scheduled');

-- 3.5 Insert Diagnoses
INSERT INTO Diagnosis (appointment_id, diagnosis_code, description, severity, diagnosed_date) VALUES
(1,  'B54',    'Unspecified malaria',                         'Moderate', '2024-05-01'),
(2,  'Z00.0',  'General adult medical examination',           'Mild',     '2024-05-02'),
(3,  'J06.9',  'Acute upper respiratory infection',           'Mild',     '2024-05-03'),
(4,  'E11.9',  'Type 2 diabetes without complications',       'Moderate', '2024-05-04'),
(5,  'B54',    'Unspecified malaria',                         'Severe',   '2024-05-05'),
(6,  'I10',    'Essential (primary) hypertension',            'Moderate', '2024-05-06'),
(7,  'Z23',    'Encounter for immunisation',                  'Mild',     '2024-05-07'),
(8,  'R10.4',  'Other and unspecified abdominal pain',        'Moderate', '2024-05-08'),
(9,  'Z34.1',  'Supervision of normal second pregnancy',      'Mild',     '2024-05-09'),
(10, 'M05.9',  'Seropositive rheumatoid arthritis, unspecified', 'Severe','2024-05-10'),
(11, 'B54',    'Unspecified malaria – follow-up resolved',    'Mild',     '2024-06-01');

-- 3.6 Insert Medications
INSERT INTO Medication (medication_name, description, unit, stock_quantity) VALUES
('Artemether-Lumefantrine', 'First-line antimalarial (ACT)',       'tablet', 500),
('Amoxicillin',             'Broad-spectrum antibiotic',           'capsule', 300),
('Metformin',               'Oral antidiabetic – biguanide class', 'tablet', 400),
('Amlodipine',              'Calcium channel blocker for BP',      'tablet', 250),
('Paracetamol',             'Analgesic and antipyretic',           'tablet', 1000),
('ORS Sachets',             'Oral Rehydration Salts',              'sachet', 800),
('Ibuprofen',               'NSAID – anti-inflammatory',           'tablet', 600),
('Folic Acid',              'Prenatal supplement',                 'tablet', 350),
('Vitamin C',               'Immune support supplement',           'tablet', 700),
('Hydroxychloroquine',      'DMARD for rheumatoid arthritis',      'tablet', 150);

-- 3.7 Insert Prescriptions
INSERT INTO Prescription (diagnosis_id, medication_id, dosage, frequency, duration_days, prescribed_date) VALUES
(1,  1,  '20mg/120mg',  'Twice daily',          3,  '2024-05-01'),
(1,  5,  '500mg',       'Three times daily',    5,  '2024-05-01'),
(3,  2,  '500mg',       'Three times daily',    7,  '2024-05-03'),
(3,  5,  '500mg',       'As needed',            5,  '2024-05-03'),
(4,  3,  '500mg',       'Twice daily',          30, '2024-05-04'),
(5,  1,  '20mg/120mg',  'Twice daily',          3,  '2024-05-05'),
(5,  6,  '1 sachet',    'After each loose stool', 3,'2024-05-05'),
(6,  4,  '5mg',         'Once daily',           30, '2024-05-06'),
(8,  5,  '500mg',       'Three times daily',    5,  '2024-05-08'),
(8,  7,  '400mg',       'Twice daily',          5,  '2024-05-08'),
(9,  8,  '5mg',         'Once daily',           90, '2024-05-09'),
(10, 10, '200mg',       'Twice daily',          60, '2024-05-10'),
(10, 7,  '400mg',       'Twice daily',          14, '2024-05-10'),
(11, 5,  '500mg',       'As needed',            3,  '2024-06-01');

-- 3.8 Insert Bills
INSERT INTO Bill (patient_id, appointment_id, total_amount, amount_paid, bill_date, payment_status) VALUES
(1,  1,  75000.00,  75000.00,  '2024-05-01', 'Paid'),
(2,  2,  50000.00,  50000.00,  '2024-05-02', 'Paid'),
(3,  3,  60000.00,  30000.00,  '2024-05-03', 'Partial'),
(4,  4,  80000.00,  80000.00,  '2024-05-04', 'Paid'),
(5,  5,  90000.00,  45000.00,  '2024-05-05', 'Partial'),
(6,  6,  70000.00,  0.00,      '2024-05-06', 'Unpaid'),
(7,  7,  30000.00,  30000.00,  '2024-05-07', 'Paid'),
(8,  8,  65000.00,  65000.00,  '2024-05-08', 'Paid'),
(9,  9,  55000.00,  55000.00,  '2024-05-09', 'Paid'),
(10, 10, 120000.00, 60000.00,  '2024-05-10', 'Partial'),
(1,  11, 40000.00,  40000.00,  '2024-06-01', 'Paid');

-- ============================================================
-- SECTION 4: DATA MANIPULATION – UPDATE & DELETE
-- ============================================================

-- 4.1 UPDATE: Change appointment status
UPDATE Appointment
SET status = 'Cancelled'
WHERE appointment_id = 12 AND status = 'Scheduled';

-- 4.2 UPDATE: Record additional payment on a partial bill
UPDATE Bill
SET amount_paid = 60000.00,
    payment_status = 'Paid'
WHERE bill_id = 3 AND payment_status = 'Partial';

-- 4.3 UPDATE: Increase medication stock after delivery
UPDATE Medication
SET stock_quantity = stock_quantity + 200
WHERE medication_name = 'Artemether-Lumefantrine';

-- 4.4 DELETE: Remove a cancelled appointment (safe delete example)
DELETE FROM Appointment
WHERE appointment_id = 12 AND status = 'Cancelled';

-- ============================================================
-- SECTION 5: SQL QUERIES
-- ============================================================

-- 5.1 SELECT – List all patients (basic SELECT)
SELECT patient_id,
       CONCAT(first_name, ' ', last_name) AS full_name,
       date_of_birth,
       gender,
       phone
FROM Patient
ORDER BY last_name, first_name;

-- 5.2 WHERE – Find patients registered in 2024
SELECT patient_id,
       CONCAT(first_name, ' ', last_name) AS full_name,
       registration_date
FROM Patient
WHERE registration_date >= '2024-01-01'
ORDER BY registration_date;

-- 5.3 WHERE – Find all completed appointments at Clinic 1
SELECT a.appointment_id,
       CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
       a.appointment_date,
       a.reason,
       a.status
FROM Appointment a
JOIN Patient p ON a.patient_id = p.patient_id
WHERE a.clinic_id = 1 AND a.status = 'Completed'
ORDER BY a.appointment_date;

-- 5.4 ORDER BY – List all bills sorted by total amount (highest first)
SELECT b.bill_id,
       CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
       b.total_amount,
       b.amount_paid,
       (b.total_amount - b.amount_paid) AS outstanding_balance,
       b.payment_status
FROM Bill b
JOIN Patient p ON b.patient_id = p.patient_id
ORDER BY b.total_amount DESC;

-- 5.5 AGGREGATE – COUNT: Total appointments per clinic
SELECT c.clinic_name,
       COUNT(a.appointment_id) AS total_appointments
FROM Clinic c
LEFT JOIN Appointment a ON c.clinic_id = a.clinic_id
GROUP BY c.clinic_id, c.clinic_name
ORDER BY total_appointments DESC;

-- 5.6 AGGREGATE – SUM: Total revenue collected per clinic
SELECT c.clinic_name,
       SUM(b.total_amount) AS total_billed,
       SUM(b.amount_paid)  AS total_collected,
       SUM(b.total_amount - b.amount_paid) AS total_outstanding
FROM Bill b
JOIN Appointment a ON b.appointment_id = a.appointment_id
JOIN Clinic c      ON a.clinic_id = c.clinic_id
GROUP BY c.clinic_id, c.clinic_name
ORDER BY total_collected DESC;

-- 5.7 AGGREGATE – AVG: Average bill amount per patient
SELECT CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
       COUNT(b.bill_id)        AS number_of_visits,
       SUM(b.total_amount)     AS total_billed,
       AVG(b.total_amount)     AS avg_bill_amount
FROM Patient p
JOIN Bill b ON p.patient_id = b.patient_id
GROUP BY p.patient_id, p.first_name, p.last_name
ORDER BY total_billed DESC;

-- 5.8 REAL-LIFE SCENARIO – Patients with outstanding balances
SELECT CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
       p.phone,
       SUM(b.total_amount - b.amount_paid) AS outstanding_balance,
       b.payment_status
FROM Patient p
JOIN Bill b ON p.patient_id = b.patient_id
WHERE b.payment_status IN ('Unpaid', 'Partial')
GROUP BY p.patient_id, p.first_name, p.last_name, p.phone, b.payment_status
ORDER BY outstanding_balance DESC;

-- 5.9 REAL-LIFE SCENARIO – Most common diagnoses
SELECT d.diagnosis_code,
       d.description,
       COUNT(d.diagnosis_id) AS total_cases,
       SUM(CASE WHEN d.severity = 'Severe'   THEN 1 ELSE 0 END) AS severe_cases,
       SUM(CASE WHEN d.severity = 'Moderate' THEN 1 ELSE 0 END) AS moderate_cases,
       SUM(CASE WHEN d.severity = 'Mild'     THEN 1 ELSE 0 END) AS mild_cases
FROM Diagnosis d
GROUP BY d.diagnosis_code, d.description
ORDER BY total_cases DESC;

-- 5.10 LIMIT – Top 5 most prescribed medications
SELECT m.medication_name,
       m.unit,
       COUNT(pr.prescription_id) AS times_prescribed
FROM Medication m
JOIN Prescription pr ON m.medication_id = pr.medication_id
GROUP BY m.medication_id, m.medication_name, m.unit
ORDER BY times_prescribed DESC
LIMIT 5;

-- 5.11 LIMIT – Last 5 registered patients
SELECT patient_id,
       CONCAT(first_name, ' ', last_name) AS full_name,
       registration_date
FROM Patient
ORDER BY registration_date DESC
LIMIT 5;

-- 5.12 REAL-LIFE SCENARIO – Full patient visit history (JOIN across 4 tables)
SELECT  p.patient_id,
        CONCAT(p.first_name, ' ', p.last_name)   AS patient_name,
        a.appointment_date,
        c.clinic_name,
        d.description                             AS diagnosis,
        d.severity,
        b.total_amount,
        b.payment_status
FROM Patient     p
JOIN Appointment a  ON p.patient_id     = a.patient_id
JOIN Clinic      c  ON a.clinic_id      = c.clinic_id
JOIN Diagnosis   d  ON a.appointment_id = d.appointment_id
JOIN Bill        b  ON a.appointment_id = b.appointment_id
ORDER BY p.patient_id, a.appointment_date;

-- ============================================================
-- SECTION 6: USER MANAGEMENT
-- ============================================================

-- Create a user account for each group member
-- (Adjust usernames/passwords to match your actual group members)

CREATE USER IF NOT EXISTS 'student_alice'@'localhost'   IDENTIFIED BY 'Alice@Clinic2024';
CREATE USER IF NOT EXISTS 'student_bob'@'localhost'     IDENTIFIED BY 'Bob@Clinic2024';
CREATE USER IF NOT EXISTS 'student_carol'@'localhost'   IDENTIFIED BY 'Carol@Clinic2024';
CREATE USER IF NOT EXISTS 'student_david'@'localhost'   IDENTIFIED BY 'David@Clinic2024';

-- Grant SELECT privilege (read-only analyst role)
GRANT SELECT ON public_health_clinic_db.* TO 'student_alice'@'localhost';

-- Grant SELECT and INSERT (data entry role)
GRANT SELECT, INSERT ON public_health_clinic_db.* TO 'student_bob'@'localhost';

-- Grant SELECT, INSERT, UPDATE (data management role)
GRANT SELECT, INSERT, UPDATE ON public_health_clinic_db.* TO 'student_carol'@'localhost';

-- Grant ALL privileges (admin/developer role)
GRANT ALL PRIVILEGES ON public_health_clinic_db.* TO 'student_david'@'localhost';

-- Change a password example
ALTER USER 'student_alice'@'localhost' IDENTIFIED BY 'Alice@NewPass2025';

-- Apply privilege changes immediately
FLUSH PRIVILEGES;

-- Verify users and their privileges (run individually to inspect)
-- SHOW GRANTS FOR 'student_alice'@'localhost';
-- SHOW GRANTS FOR 'student_bob'@'localhost';
-- SELECT user, host FROM mysql.user WHERE user LIKE 'student_%';

-- ============================================================
-- END OF SCRIPT
-- ============================================================