# 🏥 Public Health Clinic Records System

A comprehensive desktop-based healthcare management application developed using Python, CustomTkinter, and MySQL.

The Public Health Clinic Records System is designed to streamline clinic operations by providing healthcare providers with an efficient platform for managing patients, staff, appointments, diagnoses, prescriptions, medications, billing, and reporting.

---

## 📖 Table of Contents

- Overview
- Features
- Technology Stack
- System Modules
- Database Design
- Installation Guide
- Configuration
- Running the Application
- Project Structure
- Security Considerations
- Future Enhancements
- Academic Information
- Author
- License

---

# 📋 Overview

Managing healthcare records manually can be time-consuming and prone to errors. This system digitizes clinic operations by centralizing patient information, appointment scheduling, medication tracking, billing, and reporting into a single platform.

The application supports multiple clinics, healthcare staff, and patient records while maintaining data consistency through a relational MySQL database.

This project was developed as part of a database systems course and supports the United Nations Sustainable Development Goal:

**SDG 3: Good Health and Well-Being**

---

# ✨ Features

## Dashboard

The dashboard provides a real-time overview of clinic activities.

### Dashboard Statistics

- Total Patients
- Total Staff
- Total Clinics
- Total Appointments
- Monthly Revenue
- Outstanding Balances
- Medication Inventory Summary

### Dashboard Benefits

- Quick operational overview
- Improved decision making
- Easy monitoring of clinic performance

---

## Patient Management

Manage all patient-related information.

### Capabilities

- Register new patients
- Update patient details
- Delete patient records
- Search patient information
- View patient medical history
- Store emergency contacts

### Patient Information

- Full Name
- Date of Birth
- Gender
- Address
- Phone Number
- Email Address
- Emergency Contact

---

## Staff Management

Manage clinic personnel.

### Capabilities

- Add new staff
- Update staff records
- Assign staff to clinics
- Remove staff members
- Track employee information

### Staff Information

- Name
- Position
- Contact Information
- Hire Date
- Assigned Clinic

---

## Clinic Management

Manage healthcare facilities.

### Capabilities

- Add clinics
- Update clinic information
- Track clinic performance
- Assign staff to clinics

### Clinic Information

- Clinic Name
- Location
- Contact Information
- Operating Hours

---

## Appointment Management

Efficient scheduling and tracking of appointments.

### Capabilities

- Schedule appointments
- Reschedule appointments
- Cancel appointments
- Mark appointments as completed
- Search appointment history

### Appointment Status

- Scheduled
- Completed
- Cancelled
- No Show

---

## Diagnosis Management

Maintain medical diagnosis records.

### Capabilities

- Record diagnoses
- Update diagnosis information
- View diagnosis history
- Track severity levels

### Diagnosis Information

- Diagnosis Name
- Description
- Severity Level
- Diagnosis Date

---

## Medication Management

Track medications available in the clinic.

### Capabilities

- Add medications
- Update medication stock
- Remove medications
- Monitor inventory levels

### Medication Information

- Medication Name
- Quantity Available
- Unit Price
- Reorder Level

---

## Prescription Management

Manage patient prescriptions.

### Capabilities

- Create prescriptions
- Link medications to patients
- Track prescription history
- Manage treatment duration

### Prescription Information

- Prescription Date
- Medication
- Dosage
- Frequency
- Duration

---

## Billing Management

Track patient billing and payments.

### Capabilities

- Create bills
- Record payments
- View outstanding balances
- Generate financial summaries

### Billing Information

- Bill Amount
- Payment Amount
- Outstanding Balance
- Payment Status

### Payment Status

- Paid
- Partially Paid
- Unpaid

---

## Reporting Module

Generate clinic reports for analysis and decision-making.

### Available Reports

- Revenue by Clinic
- Outstanding Balances
- Common Diagnoses
- Appointment Statistics
- Medication Inventory Report
- Patient Activity Report

---

# 🛠 Technology Stack

## Programming Language

- Python 3.x

## User Interface

- CustomTkinter
- Tkinter
- ttk Widgets

## Database

- MySQL
- MariaDB

## Database Connector

- mysql-connector-python

## Development Tools

- XAMPP
- VS Code
- Git
- GitHub

---

# 🗄 Database Design

The system uses a relational database structure.

## Main Tables

### Clinic

Stores clinic information.

### Staff

Stores employee information.

### Patient

Stores patient records.

### Appointment

Stores scheduled appointments.

### Diagnosis

Stores patient diagnoses.

### Medication

Stores available medications.

### Prescription

Stores prescriptions issued to patients.

### Bill

Stores billing and payment information.

---

## Database Relationships

### One-to-Many Relationships

Clinic → Staff

Clinic → Patient

Patient → Appointment

Patient → Diagnosis

Patient → Bill

Diagnosis → Prescription

Medication → Prescription

### Integrity Constraints

- Primary Keys
- Foreign Keys
- NOT NULL Constraints
- CHECK Constraints
- Default Values
- Cascading Updates

---

# 📥 Installation Guide

## Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/public-health-clinic-records.git
```

```bash
cd public-health-clinic-records
```

---

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install customtkinter mysql-connector-python
```

---

## Step 3: Start Database Server

Open XAMPP Control Panel and start:

- Apache
- MySQL

---

## Step 4: Import Database

Import:

```sql
public_health_clinic_db.sql
```

into phpMyAdmin.

---

## Step 5: Configure Database Connection

Update database credentials in:

```python
db.py
```

Example:

```python
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "public_health_clinic_db"
DB_PORT = 3306
```

---

## Step 6: Run Application

```bash
python main.py
```

---

# 📂 Project Structure

```text
public-health-clinic-records/
│
├── main.py
├── db.py
├── requirements.txt
├── README.md
├── LICENSE
│
├── database/
│   └── public_health_clinic_db.sql
│
├── exports/
│
├── logs/
│
├── assets/
│   ├── images/
│   └── icons/
│
└── modules/
    ├── patients.py
    ├── staff.py
    ├── clinics.py
    ├── appointments.py
    ├── diagnoses.py
    ├── prescriptions.py
    ├── medications.py
    ├── billing.py
    └── reports.py
```

---

# 🔒 Security Considerations

This project was developed primarily for educational and academic purposes.

For production deployment, the following enhancements are recommended:

- User Authentication
- Password Hashing
- Role-Based Access Control
- Data Encryption
- Secure Backups
- Audit Logs
- Session Management
- Multi-Factor Authentication

---

# 🚀 Future Enhancements

Potential improvements include:

- Online Appointment Booking
- SMS Notifications
- Email Notifications
- Electronic Medical Records (EMR)
- Laboratory Module
- Pharmacy Module
- Doctor Portal
- Patient Portal
- Cloud Deployment
- Mobile Application

---

# 🎓 Academic Information

## Course

COMP 102 – Introduction to Database

## Project Title

Public Health Clinic Records System

## Sustainable Development Goal

SDG 3 – Good Health and Well-Being

## Institution

Limkokwing University of Creative Technology

---

# 👨‍💻 Author

Michael Tucker - Maria Williams - Andrew Bai Conteh

Software Engineering Student

Sierra Leone

---

# 🤝 Contributing

Contributions are welcome.

To contribute:

1. Fork the repository
2. Create a new branch
3. Commit changes
4. Push changes
5. Submit a Pull Request

---

# ⭐ Support

If you found this project useful:

- Star the repository
- Share with others
- Provide feedback

---

# 📜 License

This project is licensed under the MIT License.

See the LICENSE file for more information.