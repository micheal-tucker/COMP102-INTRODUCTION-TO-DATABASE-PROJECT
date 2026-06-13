# Public Health Clinic Records System

A desktop records system for a public health clinic database project. The app uses CustomTkinter for the interface and the XAMPP MySQL/MariaDB service for persistent clinic, patient, appointment, diagnosis, prescription, medication, and billing records.

## Features

- Professional dashboard with patient, staff, clinic, appointment, revenue, and outstanding balance metrics
- Searchable data views for patients, staff, clinics, appointments, diagnoses, prescriptions, medications, and billing
- Joined records that show useful names and clinic details instead of raw foreign keys
- Sortable table columns and CSV export for visible records
- Patient registration form with validation
- Patient visit history view
- Appointment scheduling and status updates
- Medication restocking workflow
- Bill payment recording with automatic payment-status updates
- Reports page for clinic revenue, common diagnoses, and outstanding balances
- Connection pooling for more reliable XAMPP database access
- Context-managed database cursors with automatic cleanup, commits, and rollbacks
- Central `execute()` helper for `INSERT`, `UPDATE`, and `DELETE` statements
- Application logging to `clinic_system.log`
- Environment-based database configuration with XAMPP-friendly defaults
- SQL schema with sample data, constraints, joins, aggregates, and privilege examples

## Setup

1. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

2. Start XAMPP and turn on the **MySQL** service.

3. Import the database schema with phpMyAdmin:

   - Open `http://localhost/phpmyadmin`
   - Choose the **Import** tab
   - Select `schema.sql`
   - Click **Import**

4. Run the application:

   ```powershell
   python main.py
   ```

## XAMPP Database Configuration

The app works with the default XAMPP database setup:

- Host: `localhost`
- Port: `3306`
- User: `root`
- Password: empty
- Database: `public_health_clinic_db`

You can override these with environment variables:

- `CLINIC_DB_HOST`
- `CLINIC_DB_PORT`
- `CLINIC_DB_USER`
- `CLINIC_DB_PASSWORD`
- `CLINIC_DB_NAME`
- `CLINIC_DB_POOL_NAME`
- `CLINIC_DB_POOL_SIZE`
- `CLINIC_DB_CONNECTION_TIMEOUT`

## Logging

The app writes operational logs to `clinic_system.log` in the project folder by default. You can override logging with:

- `CLINIC_LOG_FILE`
- `CLINIC_LOG_LEVEL`
