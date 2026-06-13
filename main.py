import csv
import logging
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
import mysql.connector

from db import DatabaseConfig, execute, fetch_all, fetch_one


APP_TITLE = "Public Health Clinic Records"
CARD_BG = "#111827"
PANEL_BG = "#0f172a"
PANEL_ALT = "#172033"
TEXT_MUTED = "#94a3b8"
TEXT_PRIMARY = "#f8fafc"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
logger = logging.getLogger("clinic_records.main")


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ClinicSystem(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1280x760")
        self.minsize(1080, 640)
        self.configure(fg_color=PANEL_BG)

        self.nav_buttons = {}
        self.current_rows = []
        self.current_visible_rows = []
        self.current_columns = []
        self.current_headings = []
        self.current_tree = None
        self.current_count_label = None
        self.current_search_entry = None
        self.current_filter_var = None
        self.current_filter_column_index = None
        self.current_sort_column = None
        self.current_sort_reverse = False

        logger.info("Starting %s", APP_TITLE)
        self.create_shell()
        self.show_dashboard()

    def create_shell(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=CARD_BG)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        brand = ctk.CTkLabel(
            self.sidebar,
            text="Clinic Records",
            font=("Segoe UI", 24, "bold"),
            text_color=TEXT_PRIMARY,
        )
        brand.pack(anchor="w", padx=22, pady=(26, 4))

        subtitle = ctk.CTkLabel(
            self.sidebar,
            text="Public health operations",
            font=("Segoe UI", 13),
            text_color=TEXT_MUTED,
        )
        subtitle.pack(anchor="w", padx=22, pady=(0, 22))

        nav_items = [
            ("Dashboard", self.show_dashboard),
            ("Patients", self.show_patients),
            ("Staff", self.show_staff),
            ("Clinics", self.show_clinics),
            ("Appointments", self.show_appointments),
            ("Diagnoses", self.show_diagnoses),
            ("Prescriptions", self.show_prescriptions),
            ("Medications", self.show_medications),
            ("Billing", self.show_bills),
            ("Reports", self.show_reports),
        ]

        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=14)

        for name, command in nav_items:
            button = ctk.CTkButton(
                nav_frame,
                text=name,
                anchor="w",
                height=40,
                corner_radius=8,
                command=lambda item=name, action=command: self.navigate(item, action),
                fg_color="transparent",
                hover_color=PANEL_ALT,
                text_color=TEXT_PRIMARY,
                font=("Segoe UI", 14),
            )
            button.pack(fill="x", pady=3)
            self.nav_buttons[name] = button

        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=14, pady=18)

        db_config = DatabaseConfig()
        db_name = ctk.CTkLabel(
            footer,
            text=f"Database: {db_config.database}",
            font=("Segoe UI", 11),
            text_color=TEXT_MUTED,
            wraplength=210,
            justify="left",
        )
        db_name.pack(anchor="w", padx=8, pady=(0, 10))

        test_button = ctk.CTkButton(
            footer,
            text="Test DB",
            height=38,
            corner_radius=8,
            command=self.test_database_connection,
            fg_color="#0f766e",
            hover_color="#0d9488",
            font=("Segoe UI", 13, "bold"),
        )
        test_button.pack(fill="x", pady=(0, 8))

        exit_button = ctk.CTkButton(
            footer,
            text="Exit",
            height=38,
            corner_radius=8,
            command=self.destroy,
            fg_color="#334155",
            hover_color="#475569",
            font=("Segoe UI", 13, "bold"),
        )
        exit_button.pack(fill="x")

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=PANEL_BG)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def navigate(self, name, command):
        logger.info("Navigating to %s", name)
        self.set_active_nav(name)
        command()

    def test_database_connection(self):
        try:
            result = fetch_one("SELECT 1")
            if result and result[0] == 1:
                logger.info("Database connection test succeeded")
                messagebox.showinfo("Database Connection", "XAMPP database connection is working.")
            else:
                logger.warning("Database connection test returned an unexpected result: %s", result)
                messagebox.showwarning("Database Connection", "The database responded unexpectedly.")
        except mysql.connector.Error as error:
            logger.exception("Database connection test failed")
            messagebox.showerror("Database Connection", str(error))

    def set_active_nav(self, name):
        for button_name, button in self.nav_buttons.items():
            button.configure(
                fg_color=ACCENT if button_name == name else "transparent",
                hover_color=ACCENT_HOVER if button_name == name else PANEL_ALT,
            )

    def clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()
        self.reset_table_state()

    def reset_table_state(self):
        self.current_rows = []
        self.current_visible_rows = []
        self.current_columns = []
        self.current_headings = []
        self.current_tree = None
        self.current_count_label = None
        self.current_search_entry = None
        self.current_filter_var = None
        self.current_filter_column_index = None
        self.current_sort_column = None
        self.current_sort_reverse = False

    def page_header(self, parent, title, subtitle):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(22, 14))
        header.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            header,
            text=title,
            font=("Segoe UI", 28, "bold"),
            text_color=TEXT_PRIMARY,
        )
        title_label.grid(row=0, column=0, sticky="w")

        subtitle_label = ctk.CTkLabel(
            header,
            text=subtitle,
            font=("Segoe UI", 14),
            text_color=TEXT_MUTED,
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

    def create_page_container(self):
        self.clear_content()
        container = ctk.CTkFrame(self.content, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=28, pady=0)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(2, weight=1)
        return container

    def show_dashboard(self):
        self.set_active_nav("Dashboard")
        container = self.create_page_container()
        self.page_header(
            container,
            "Dashboard",
            "Operational snapshot across patients, clinics, appointments, and billing.",
        )

        try:
            metrics = self.get_dashboard_metrics()
            recent_appointments = fetch_all(
                """
                SELECT
                    a.appointment_id,
                    DATE_FORMAT(a.appointment_date, '%d %b %Y'),
                    TIME_FORMAT(a.appointment_time, '%H:%i'),
                    CONCAT(p.first_name, ' ', p.last_name),
                    CONCAT(s.first_name, ' ', s.last_name),
                    c.clinic_name,
                    a.status
                FROM Appointment a
                JOIN Patient p ON a.patient_id = p.patient_id
                JOIN Staff s ON a.staff_id = s.staff_id
                JOIN Clinic c ON a.clinic_id = c.clinic_id
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
                LIMIT 8
                """
            )
        except mysql.connector.Error as error:
            self.show_database_error(container, error)
            return

        cards = ctk.CTkFrame(container, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 18))

        for index, metric in enumerate(metrics):
            cards.grid_columnconfigure(index % 3, weight=1, uniform="metric")
            row = index // 3
            column = index % 3
            self.stat_card(cards, metric["title"], metric["value"], metric["note"], row, column)

        table_panel = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=8)
        table_panel.grid(row=2, column=0, sticky="nsew")
        table_panel.grid_columnconfigure(0, weight=1)
        table_panel.grid_rowconfigure(1, weight=1)

        section_title = ctk.CTkLabel(
            table_panel,
            text="Recent Appointments",
            font=("Segoe UI", 18, "bold"),
            text_color=TEXT_PRIMARY,
        )
        section_title.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 10))

        self.create_tree(
            table_panel,
            [
                ("ID", 70, "center"),
                ("Date", 120, "w"),
                ("Time", 85, "center"),
                ("Patient", 180, "w"),
                ("Staff", 170, "w"),
                ("Clinic", 220, "w"),
                ("Status", 120, "center"),
            ],
            recent_appointments,
            row=1,
            searchable=False,
        )

    def get_dashboard_metrics(self):
        queries = {
            "patients": "SELECT COUNT(*) FROM Patient",
            "staff": "SELECT COUNT(*) FROM Staff",
            "clinics": "SELECT COUNT(*) FROM Clinic",
            "appointments": "SELECT COUNT(*) FROM Appointment",
            "revenue": "SELECT IFNULL(SUM(amount_paid), 0) FROM Bill",
            "outstanding": "SELECT IFNULL(SUM(total_amount - amount_paid), 0) FROM Bill",
        }
        values = {name: fetch_one(query)[0] for name, query in queries.items()}

        return [
            {"title": "Patients", "value": f"{values['patients']:,}", "note": "registered records"},
            {"title": "Staff", "value": f"{values['staff']:,}", "note": "clinic team members"},
            {"title": "Clinics", "value": f"{values['clinics']:,}", "note": "service locations"},
            {"title": "Appointments", "value": f"{values['appointments']:,}", "note": "scheduled or completed"},
            {"title": "Collected", "value": self.money(values["revenue"]), "note": "payments received"},
            {"title": "Outstanding", "value": self.money(values["outstanding"]), "note": "balance to collect"},
        ]

    def stat_card(self, parent, title, value, note, row, column):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=8)
        card.grid(row=row, column=column, sticky="ew", padx=6, pady=6)
        card.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 14, "bold"),
            text_color=TEXT_MUTED,
        )
        title_label.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 0))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Segoe UI", 28, "bold"),
            text_color=TEXT_PRIMARY,
        )
        value_label.grid(row=1, column=0, sticky="w", padx=18, pady=(2, 0))

        note_label = ctk.CTkLabel(
            card,
            text=note,
            font=("Segoe UI", 12),
            text_color=TEXT_MUTED,
        )
        note_label.grid(row=2, column=0, sticky="w", padx=18, pady=(0, 16))

    def show_patients(self):
        self.show_table_page(
            "Patients",
            "Patients",
            "Registered patients with key demographic and contact details.",
            [
                ("ID", 70, "center"),
                ("Name", 220, "w"),
                ("Date of Birth", 130, "w"),
                ("Gender", 100, "center"),
                ("Phone", 145, "w"),
                ("Blood Type", 110, "center"),
                ("Registered", 130, "w"),
            ],
            """
            SELECT
                patient_id,
                CONCAT(first_name, ' ', last_name),
                DATE_FORMAT(date_of_birth, '%d %b %Y'),
                gender,
                phone,
                IFNULL(blood_type, '-'),
                DATE_FORMAT(registration_date, '%d %b %Y')
            FROM Patient
            ORDER BY last_name, first_name
            """,
            actions=[
                ("Register Patient", self.open_patient_form),
                ("Edit Patient", lambda: self.open_selected_record("Edit Patient", self.open_patient_form)),
                ("Visit History", self.open_patient_history),
            ],
        )

    def show_staff(self):
        self.show_table_page(
            "Staff",
            "Staff",
            "Clinic personnel, roles, assigned locations, and contact information.",
            [
                ("ID", 70, "center"),
                ("Name", 210, "w"),
                ("Role", 140, "w"),
                ("Clinic", 240, "w"),
                ("Gender", 100, "center"),
                ("Phone", 145, "w"),
                ("Email", 220, "w"),
                ("Hire Date", 120, "w"),
            ],
            """
            SELECT
                s.staff_id,
                CONCAT(s.first_name, ' ', s.last_name),
                s.role,
                c.clinic_name,
                s.gender,
                s.phone,
                IFNULL(s.email, '-'),
                DATE_FORMAT(s.hire_date, '%d %b %Y')
            FROM Staff s
            JOIN Clinic c ON s.clinic_id = c.clinic_id
            ORDER BY c.clinic_name, s.role, s.last_name
            """,
            actions=[
                ("Add Staff", self.open_staff_form),
                ("Edit Staff", lambda: self.open_selected_record("Edit Staff", self.open_staff_form)),
            ],
        )

    def show_clinics(self):
        self.show_table_page(
            "Clinics",
            "Clinics",
            "Clinic locations with staffing and appointment activity.",
            [
                ("ID", 70, "center"),
                ("Clinic", 240, "w"),
                ("District", 170, "w"),
                ("Location", 260, "w"),
                ("Phone", 145, "w"),
                ("Email", 220, "w"),
                ("Staff", 90, "center"),
                ("Appointments", 120, "center"),
            ],
            """
            SELECT
                c.clinic_id,
                c.clinic_name,
                c.district,
                c.location,
                c.phone,
                IFNULL(c.email, '-'),
                COUNT(DISTINCT s.staff_id),
                COUNT(DISTINCT a.appointment_id)
            FROM Clinic c
            LEFT JOIN Staff s ON c.clinic_id = s.clinic_id
            LEFT JOIN Appointment a ON c.clinic_id = a.clinic_id
            GROUP BY c.clinic_id, c.clinic_name, c.district, c.location, c.phone, c.email
            ORDER BY c.clinic_name
            """,
            actions=[
                ("Add Clinic", self.open_clinic_form),
                ("Edit Clinic", lambda: self.open_selected_record("Edit Clinic", self.open_clinic_form)),
            ],
        )

    def show_appointments(self):
        self.show_table_page(
            "Appointments",
            "Appointments",
            "Visit schedule with patient, staff, clinic, and status details.",
            [
                ("ID", 70, "center"),
                ("Date", 120, "w"),
                ("Time", 85, "center"),
                ("Patient", 190, "w"),
                ("Staff", 185, "w"),
                ("Clinic", 230, "w"),
                ("Status", 120, "center"),
                ("Reason", 280, "w"),
            ],
            """
            SELECT
                a.appointment_id,
                DATE_FORMAT(a.appointment_date, '%d %b %Y'),
                TIME_FORMAT(a.appointment_time, '%H:%i'),
                CONCAT(p.first_name, ' ', p.last_name),
                CONCAT(s.first_name, ' ', s.last_name),
                c.clinic_name,
                a.status,
                a.reason
            FROM Appointment a
            JOIN Patient p ON a.patient_id = p.patient_id
            JOIN Staff s ON a.staff_id = s.staff_id
            JOIN Clinic c ON a.clinic_id = c.clinic_id
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """,
            actions=[
                ("Schedule Appointment", self.open_appointment_form),
                ("Edit Appointment", lambda: self.open_selected_record("Edit Appointment", self.open_appointment_form)),
                ("Mark Completed", lambda: self.update_selected_appointment_status("Completed")),
                ("Cancel", lambda: self.update_selected_appointment_status("Cancelled")),
            ],
            filter_column="Status",
            filter_options=["All", "Scheduled", "Completed", "Cancelled"],
        )

    def show_diagnoses(self):
        self.show_table_page(
            "Diagnoses",
            "Diagnoses",
            "Clinical diagnosis history linked to patient visits.",
            [
                ("ID", 70, "center"),
                ("Date", 120, "w"),
                ("Patient", 200, "w"),
                ("Code", 95, "center"),
                ("Description", 360, "w"),
                ("Severity", 120, "center"),
                ("Visit Status", 120, "center"),
            ],
            """
            SELECT
                d.diagnosis_id,
                DATE_FORMAT(d.diagnosed_date, '%d %b %Y'),
                CONCAT(p.first_name, ' ', p.last_name),
                d.diagnosis_code,
                d.description,
                d.severity,
                a.status
            FROM Diagnosis d
            JOIN Appointment a ON d.appointment_id = a.appointment_id
            JOIN Patient p ON a.patient_id = p.patient_id
            ORDER BY d.diagnosed_date DESC, d.diagnosis_id DESC
            """,
            actions=[
                ("Add Diagnosis", self.open_diagnosis_form),
                ("Edit Diagnosis", lambda: self.open_selected_record("Edit Diagnosis", self.open_diagnosis_form)),
            ],
            filter_column="Severity",
            filter_options=["All", "Mild", "Moderate", "Severe"],
        )

    def show_prescriptions(self):
        self.show_table_page(
            "Prescriptions",
            "Prescriptions",
            "Medication orders with dosage, frequency, and treatment duration.",
            [
                ("ID", 70, "center"),
                ("Date", 120, "w"),
                ("Patient", 200, "w"),
                ("Medication", 240, "w"),
                ("Dosage", 120, "w"),
                ("Frequency", 180, "w"),
                ("Duration", 110, "center"),
            ],
            """
            SELECT
                pr.prescription_id,
                DATE_FORMAT(pr.prescribed_date, '%d %b %Y'),
                CONCAT(p.first_name, ' ', p.last_name),
                m.medication_name,
                pr.dosage,
                pr.frequency,
                CONCAT(pr.duration_days, ' days')
            FROM Prescription pr
            JOIN Diagnosis d ON pr.diagnosis_id = d.diagnosis_id
            JOIN Appointment a ON d.appointment_id = a.appointment_id
            JOIN Patient p ON a.patient_id = p.patient_id
            JOIN Medication m ON pr.medication_id = m.medication_id
            ORDER BY pr.prescribed_date DESC, pr.prescription_id DESC
            """,
            actions=[
                ("Add Prescription", self.open_prescription_form),
                ("Edit Prescription", lambda: self.open_selected_record("Edit Prescription", self.open_prescription_form)),
            ],
        )

    def show_medications(self):
        self.show_table_page(
            "Medications",
            "Medications",
            "Medication inventory with unit type and available stock.",
            [
                ("ID", 70, "center"),
                ("Medication", 260, "w"),
                ("Unit", 110, "center"),
                ("Stock", 100, "center"),
                ("Description", 420, "w"),
            ],
            """
            SELECT
                medication_id,
                medication_name,
                unit,
                stock_quantity,
                IFNULL(description, '-')
            FROM Medication
            ORDER BY medication_name
            """,
            actions=[
                ("Add Medication", self.open_medication_form),
                ("Edit Medication", lambda: self.open_selected_record("Edit Medication", self.open_medication_form)),
                ("Restock", self.open_restock_form),
            ],
        )

    def show_bills(self):
        self.show_table_page(
            "Billing",
            "Billing",
            "Patient billing records with collected and outstanding balances.",
            [
                ("ID", 70, "center"),
                ("Patient", 210, "w"),
                ("Bill Date", 120, "w"),
                ("Total", 130, "e"),
                ("Paid", 130, "e"),
                ("Balance", 130, "e"),
                ("Status", 120, "center"),
            ],
            """
            SELECT
                b.bill_id,
                CONCAT(p.first_name, ' ', p.last_name),
                DATE_FORMAT(b.bill_date, '%d %b %Y'),
                CONCAT('Le ', FORMAT(b.total_amount, 0)),
                CONCAT('Le ', FORMAT(b.amount_paid, 0)),
                CONCAT('Le ', FORMAT(b.total_amount - b.amount_paid, 0)),
                b.payment_status
            FROM Bill b
            JOIN Patient p ON b.patient_id = p.patient_id
            ORDER BY b.bill_date DESC, b.bill_id DESC
            """,
            actions=[
                ("Create Bill", self.open_bill_form),
                ("Edit Bill", lambda: self.open_selected_record("Edit Bill", self.open_bill_form)),
                ("Record Payment", self.open_payment_form),
            ],
            filter_column="Status",
            filter_options=["All", "Unpaid", "Partial", "Paid"],
        )

    def show_reports(self):
        self.set_active_nav("Reports")
        container = self.create_page_container()
        container.grid_rowconfigure(1, weight=1)
        self.page_header(
            container,
            "Reports",
            "Management summaries for revenue collection and clinical activity.",
        )

        try:
            revenue_rows = fetch_all(
                """
                SELECT
                    c.clinic_name,
                    COUNT(DISTINCT a.appointment_id),
                    CONCAT('Le ', FORMAT(IFNULL(SUM(b.total_amount), 0), 0)),
                    CONCAT('Le ', FORMAT(IFNULL(SUM(b.amount_paid), 0), 0)),
                    CONCAT('Le ', FORMAT(IFNULL(SUM(b.total_amount - b.amount_paid), 0), 0))
                FROM Clinic c
                LEFT JOIN Appointment a ON c.clinic_id = a.clinic_id
                LEFT JOIN Bill b ON a.appointment_id = b.appointment_id
                GROUP BY c.clinic_id, c.clinic_name
                ORDER BY IFNULL(SUM(b.amount_paid), 0) DESC
                """
            )
            diagnosis_rows = fetch_all(
                """
                SELECT
                    diagnosis_code,
                    description,
                    COUNT(diagnosis_id),
                    SUM(CASE WHEN severity = 'Severe' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN severity = 'Moderate' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN severity = 'Mild' THEN 1 ELSE 0 END)
                FROM Diagnosis
                GROUP BY diagnosis_code, description
                ORDER BY COUNT(diagnosis_id) DESC, diagnosis_code
                """
            )
            outstanding_rows = fetch_all(
                """
                SELECT
                    CONCAT(p.first_name, ' ', p.last_name),
                    p.phone,
                    CONCAT('Le ', FORMAT(SUM(b.total_amount - b.amount_paid), 0)),
                    GROUP_CONCAT(DISTINCT b.payment_status ORDER BY b.payment_status SEPARATOR ', ')
                FROM Patient p
                JOIN Bill b ON p.patient_id = b.patient_id
                WHERE b.total_amount > b.amount_paid
                GROUP BY p.patient_id, p.first_name, p.last_name, p.phone
                ORDER BY SUM(b.total_amount - b.amount_paid) DESC
                """
            )
        except mysql.connector.Error as error:
            self.show_database_error(container, error)
            return

        reports = ctk.CTkFrame(container, fg_color="transparent")
        reports.grid(row=1, column=0, sticky="nsew")
        reports.grid_columnconfigure((0, 1), weight=1, uniform="report")
        reports.grid_rowconfigure((0, 1), weight=1, uniform="report")

        self.report_panel(
            reports,
            "Revenue by Clinic",
            [
                ("Clinic", 240, "w"),
                ("Visits", 80, "center"),
                ("Billed", 120, "e"),
                ("Collected", 120, "e"),
                ("Outstanding", 130, "e"),
            ],
            revenue_rows,
            0,
            0,
            columnspan=2,
        )
        self.report_panel(
            reports,
            "Common Diagnoses",
            [
                ("Code", 90, "center"),
                ("Description", 320, "w"),
                ("Cases", 80, "center"),
                ("Severe", 80, "center"),
                ("Moderate", 90, "center"),
                ("Mild", 80, "center"),
            ],
            diagnosis_rows,
            1,
            0,
        )
        self.report_panel(
            reports,
            "Outstanding Balances",
            [
                ("Patient", 190, "w"),
                ("Phone", 140, "w"),
                ("Balance", 120, "e"),
                ("Status", 170, "w"),
            ],
            outstanding_rows,
            1,
            1,
        )

    def report_panel(self, parent, title, columns, rows, row, column, columnspan=1):
        panel = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=8)
        panel.grid(row=row, column=column, columnspan=columnspan, sticky="nsew", padx=6, pady=6)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        title_label = ctk.CTkLabel(
            panel,
            text=title,
            font=("Segoe UI", 17, "bold"),
            text_color=TEXT_PRIMARY,
        )
        title_label.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 4))

        self.create_tree(panel, columns, rows, row=1, searchable=False)

    def open_patient_form(self, patient_id=None):
        record = None
        if patient_id is not None:
            try:
                record = fetch_one(
                    """
                    SELECT
                        first_name,
                        last_name,
                        date_of_birth,
                        gender,
                        address,
                        phone,
                        blood_type,
                        registration_date
                    FROM Patient
                    WHERE patient_id = %s
                    """,
                    (patient_id,),
                )
            except mysql.connector.Error as error:
                messagebox.showerror("Edit Patient", str(error))
                return

            if not record:
                messagebox.showerror("Edit Patient", "Patient record was not found.")
                return

        title = "Edit Patient" if patient_id is not None else "Register Patient"
        modal = self.create_modal(title, 580, 640)
        body = self.modal_body(
            modal,
            title,
            "Update patient demographics and contact information."
            if patient_id is not None
            else "Create a new patient record with demographics and contact information.",
        )

        first_name = self.form_entry(body, "First Name", 2, value=record[0] if record else "")
        last_name = self.form_entry(body, "Last Name", 4, value=record[1] if record else "")
        dob = self.form_entry(body, "Date of Birth", 6, "YYYY-MM-DD", self.date_value(record[2]) if record else "")
        gender = self.form_combo(body, "Gender", 8, ["Female", "Male", "Other"])
        if record:
            gender.set(record[3])
        address = self.form_entry(body, "Address", 10, value=record[4] if record else "")
        phone = self.form_entry(body, "Phone", 12, value=record[5] if record else "")
        blood_type = self.form_combo(body, "Blood Type", 14, ["None", "O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"])
        blood_type.set(record[6] if record and record[6] else "None")
        registered = self.form_entry(
            body,
            "Registration Date",
            16,
            "YYYY-MM-DD",
            self.date_value(record[7]) if record else date.today().isoformat(),
        )

        def save_patient():
            try:
                values = {
                    "first_name": first_name.get().strip(),
                    "last_name": last_name.get().strip(),
                    "date_of_birth": self.parse_required_date(dob.get(), "Date of Birth"),
                    "gender": gender.get().strip(),
                    "address": address.get().strip(),
                    "phone": phone.get().strip(),
                    "blood_type": None if blood_type.get() == "None" else blood_type.get().strip(),
                    "registration_date": self.parse_required_date(registered.get(), "Registration Date"),
                }
                required = ["first_name", "last_name", "gender", "address", "phone"]
                missing = [field.replace("_", " ").title() for field in required if not values[field]]
                if missing:
                    raise ValueError(f"Required field missing: {', '.join(missing)}.")

                params = (
                    values["first_name"],
                    values["last_name"],
                    values["date_of_birth"],
                    values["gender"],
                    values["address"],
                    values["phone"],
                    values["blood_type"],
                    values["registration_date"],
                )
                if patient_id is None:
                    result = execute(
                        """
                        INSERT INTO Patient
                            (first_name, last_name, date_of_birth, gender, address, phone, blood_type, registration_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        params,
                    )
                    logger.info("Registered patient id=%s", result["lastrowid"])
                    messagebox.showinfo("Register Patient", "Patient registered successfully.")
                else:
                    result = execute(
                        """
                        UPDATE Patient
                        SET first_name = %s,
                            last_name = %s,
                            date_of_birth = %s,
                            gender = %s,
                            address = %s,
                            phone = %s,
                            blood_type = %s,
                            registration_date = %s
                        WHERE patient_id = %s
                        """,
                        params + (patient_id,),
                    )
                    logger.info("Updated patient id=%s rowcount=%s", patient_id, result["rowcount"])
                    messagebox.showinfo("Edit Patient", "Patient updated successfully.")
                modal.destroy()
                self.show_patients()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror(title, str(error))

        self.action_row(body, 18, "Save Patient", save_patient, modal.destroy)

    def open_patient_history(self):
        patient_id = self.get_selected_id("Visit History")
        if patient_id is None:
            return

        try:
            patient = fetch_one(
                "SELECT CONCAT(first_name, ' ', last_name), phone FROM Patient WHERE patient_id = %s",
                (patient_id,),
            )
            rows = fetch_all(
                """
                SELECT
                    DATE_FORMAT(a.appointment_date, '%d %b %Y'),
                    TIME_FORMAT(a.appointment_time, '%H:%i'),
                    c.clinic_name,
                    CONCAT(s.first_name, ' ', s.last_name),
                    a.status,
                    a.reason,
                    IFNULL(d.description, '-'),
                    IFNULL(d.severity, '-'),
                    IFNULL(CONCAT('Le ', FORMAT(b.total_amount, 0)), '-'),
                    IFNULL(b.payment_status, '-')
                FROM Appointment a
                JOIN Clinic c ON a.clinic_id = c.clinic_id
                JOIN Staff s ON a.staff_id = s.staff_id
                LEFT JOIN Diagnosis d ON a.appointment_id = d.appointment_id
                LEFT JOIN Bill b ON a.appointment_id = b.appointment_id
                WHERE a.patient_id = %s
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
                """,
                (patient_id,),
            )
        except mysql.connector.Error as error:
            messagebox.showerror("Visit History", str(error))
            return

        if not patient:
            messagebox.showerror("Visit History", "Patient record was not found.")
            return

        modal = self.create_modal("Patient Visit History", 1040, 560)
        body = self.modal_body(
            modal,
            patient[0],
            f"Phone: {patient[1]} | Complete appointment, diagnosis, and billing history.",
        )
        body.grid_rowconfigure(2, weight=1)

        panel = ctk.CTkFrame(body, fg_color=CARD_BG, corner_radius=8)
        panel.grid(row=2, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)

        self.create_tree(
            panel,
            [
                ("Date", 120, "w"),
                ("Time", 80, "center"),
                ("Clinic", 220, "w"),
                ("Staff", 170, "w"),
                ("Status", 110, "center"),
                ("Reason", 230, "w"),
                ("Diagnosis", 300, "w"),
                ("Severity", 100, "center"),
                ("Bill", 110, "e"),
                ("Payment", 110, "center"),
            ],
            rows,
            row=0,
            searchable=False,
        )

    def open_clinic_form(self):
        modal = self.create_modal("Add Clinic", 560, 590)
        body = self.modal_body(
            modal,
            "Add Clinic",
            "Create a new clinic location record.",
        )

        clinic_name = self.form_entry(body, "Clinic Name", 2)
        location = self.form_entry(body, "Location", 4)
        district = self.form_entry(body, "District", 6)
        phone = self.form_entry(body, "Phone", 8)
        email = self.form_entry(body, "Email", 10, "Optional")
        established = self.form_entry(body, "Established Date", 12, "Optional YYYY-MM-DD")

        def save_clinic():
            try:
                values = {
                    "clinic_name": clinic_name.get().strip(),
                    "location": location.get().strip(),
                    "district": district.get().strip(),
                    "phone": phone.get().strip(),
                    "email": email.get().strip() or None,
                    "established_date": self.parse_optional_date(established.get(), "Established Date"),
                }
                missing = [
                    field.replace("_", " ").title()
                    for field in ("clinic_name", "location", "district", "phone")
                    if not values[field]
                ]
                if missing:
                    raise ValueError(f"Required field missing: {', '.join(missing)}.")

                result = execute(
                    """
                    INSERT INTO Clinic
                        (clinic_name, location, district, phone, email, established_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        values["clinic_name"],
                        values["location"],
                        values["district"],
                        values["phone"],
                        values["email"],
                        values["established_date"],
                    ),
                )
                logger.info("Created clinic id=%s", result["lastrowid"])
                messagebox.showinfo("Add Clinic", "Clinic added successfully.")
                modal.destroy()
                self.show_clinics()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror("Add Clinic", str(error))

        self.action_row(body, 14, "Save Clinic", save_clinic, modal.destroy)

    def open_staff_form(self):
        try:
            clinics = fetch_all("SELECT clinic_id, clinic_name FROM Clinic ORDER BY clinic_name")
        except mysql.connector.Error as error:
            messagebox.showerror("Add Staff", str(error))
            return

        if not clinics:
            messagebox.showinfo("Add Staff", "Add a clinic before adding staff.")
            return

        modal = self.create_modal("Add Staff", 580, 690)
        body = self.modal_body(
            modal,
            "Add Staff",
            "Create a staff record and assign the staff member to a clinic.",
        )

        clinic = self.form_combo(body, "Clinic", 2, [f"{clinic_id} - {name}" for clinic_id, name in clinics])
        first_name = self.form_entry(body, "First Name", 4)
        last_name = self.form_entry(body, "Last Name", 6)
        role = self.form_entry(body, "Role", 8, "Doctor, Nurse, Receptionist")
        gender = self.form_combo(body, "Gender", 10, ["Female", "Male", "Other"])
        phone = self.form_entry(body, "Phone", 12)
        email = self.form_entry(body, "Email", 14, "Optional")
        hire_date = self.form_entry(body, "Hire Date", 16, "YYYY-MM-DD", date.today().isoformat())

        def save_staff():
            try:
                values = {
                    "clinic_id": self.selected_option_id(clinic.get()),
                    "first_name": first_name.get().strip(),
                    "last_name": last_name.get().strip(),
                    "role": role.get().strip(),
                    "gender": gender.get().strip(),
                    "phone": phone.get().strip(),
                    "email": email.get().strip() or None,
                    "hire_date": self.parse_required_date(hire_date.get(), "Hire Date"),
                }
                missing = [
                    field.replace("_", " ").title()
                    for field in ("first_name", "last_name", "role", "gender", "phone")
                    if not values[field]
                ]
                if missing:
                    raise ValueError(f"Required field missing: {', '.join(missing)}.")

                result = execute(
                    """
                    INSERT INTO Staff
                        (clinic_id, first_name, last_name, role, gender, phone, email, hire_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        values["clinic_id"],
                        values["first_name"],
                        values["last_name"],
                        values["role"],
                        values["gender"],
                        values["phone"],
                        values["email"],
                        values["hire_date"],
                    ),
                )
                logger.info("Created staff id=%s", result["lastrowid"])
                messagebox.showinfo("Add Staff", "Staff member added successfully.")
                modal.destroy()
                self.show_staff()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror("Add Staff", str(error))

        self.action_row(body, 18, "Save Staff", save_staff, modal.destroy)

    def open_diagnosis_form(self):
        try:
            appointments = fetch_all(
                """
                SELECT
                    a.appointment_id,
                    CONCAT(p.first_name, ' ', p.last_name),
                    DATE_FORMAT(a.appointment_date, '%d %b %Y'),
                    a.status
                FROM Appointment a
                JOIN Patient p ON a.patient_id = p.patient_id
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
                """
            )
        except mysql.connector.Error as error:
            messagebox.showerror("Add Diagnosis", str(error))
            return

        if not appointments:
            messagebox.showinfo("Add Diagnosis", "Create an appointment before adding diagnoses.")
            return

        modal = self.create_modal("Add Diagnosis", 620, 590)
        body = self.modal_body(
            modal,
            "Add Diagnosis",
            "Record a diagnosis for an existing appointment.",
        )

        appointment = self.form_combo(
            body,
            "Appointment",
            2,
            [f"{appt_id} - {patient} | {appt_date} | {status}" for appt_id, patient, appt_date, status in appointments],
        )
        code = self.form_entry(body, "Diagnosis Code", 4, "Example: B54")
        description = self.form_entry(body, "Description", 6)
        severity = self.form_combo(body, "Severity", 8, ["Mild", "Moderate", "Severe"])
        diagnosed_date = self.form_entry(body, "Diagnosed Date", 10, "YYYY-MM-DD", date.today().isoformat())

        def save_diagnosis():
            try:
                diagnosis_code = code.get().strip()
                diagnosis_description = description.get().strip()
                if not diagnosis_code or not diagnosis_description:
                    raise ValueError("Diagnosis code and description are required.")

                result = execute(
                    """
                    INSERT INTO Diagnosis
                        (appointment_id, diagnosis_code, description, severity, diagnosed_date)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        self.selected_option_id(appointment.get()),
                        diagnosis_code,
                        diagnosis_description,
                        severity.get(),
                        self.parse_required_date(diagnosed_date.get(), "Diagnosed Date"),
                    ),
                )
                logger.info("Created diagnosis id=%s", result["lastrowid"])
                messagebox.showinfo("Add Diagnosis", "Diagnosis added successfully.")
                modal.destroy()
                self.show_diagnoses()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror("Add Diagnosis", str(error))

        self.action_row(body, 12, "Save Diagnosis", save_diagnosis, modal.destroy)

    def open_prescription_form(self):
        try:
            diagnoses = fetch_all(
                """
                SELECT
                    d.diagnosis_id,
                    d.diagnosis_code,
                    CONCAT(p.first_name, ' ', p.last_name),
                    DATE_FORMAT(d.diagnosed_date, '%d %b %Y')
                FROM Diagnosis d
                JOIN Appointment a ON d.appointment_id = a.appointment_id
                JOIN Patient p ON a.patient_id = p.patient_id
                ORDER BY d.diagnosed_date DESC, d.diagnosis_id DESC
                """
            )
            medications = fetch_all(
                "SELECT medication_id, medication_name FROM Medication ORDER BY medication_name"
            )
        except mysql.connector.Error as error:
            messagebox.showerror("Add Prescription", str(error))
            return

        if not diagnoses:
            messagebox.showinfo("Add Prescription", "Add a diagnosis before adding prescriptions.")
            return
        if not medications:
            messagebox.showinfo("Add Prescription", "Add a medication before adding prescriptions.")
            return

        modal = self.create_modal("Add Prescription", 640, 650)
        body = self.modal_body(
            modal,
            "Add Prescription",
            "Create a prescription linked to a diagnosis and medication.",
        )

        diagnosis = self.form_combo(
            body,
            "Diagnosis",
            2,
            [
                f"{diagnosis_id} - {patient} | {code} | {diagnosis_date}"
                for diagnosis_id, code, patient, diagnosis_date in diagnoses
            ],
        )
        medication = self.form_combo(
            body,
            "Medication",
            4,
            [f"{medication_id} - {name}" for medication_id, name in medications],
        )
        dosage = self.form_entry(body, "Dosage", 6, "Example: 500mg")
        frequency = self.form_entry(body, "Frequency", 8, "Example: Twice daily")
        duration = self.form_entry(body, "Duration Days", 10, "Example: 7")
        prescribed_date = self.form_entry(body, "Prescribed Date", 12, "YYYY-MM-DD", date.today().isoformat())

        def save_prescription():
            try:
                prescription_dosage = dosage.get().strip()
                prescription_frequency = frequency.get().strip()
                if not prescription_dosage or not prescription_frequency:
                    raise ValueError("Dosage and frequency are required.")

                result = execute(
                    """
                    INSERT INTO Prescription
                        (diagnosis_id, medication_id, dosage, frequency, duration_days, prescribed_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.selected_option_id(diagnosis.get()),
                        self.selected_option_id(medication.get()),
                        prescription_dosage,
                        prescription_frequency,
                        self.parse_positive_int(duration.get(), "Duration Days"),
                        self.parse_required_date(prescribed_date.get(), "Prescribed Date"),
                    ),
                )
                logger.info("Created prescription id=%s", result["lastrowid"])
                messagebox.showinfo("Add Prescription", "Prescription added successfully.")
                modal.destroy()
                self.show_prescriptions()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror("Add Prescription", str(error))

        self.action_row(body, 14, "Save Prescription", save_prescription, modal.destroy)

    def open_medication_form(self):
        modal = self.create_modal("Add Medication", 560, 520)
        body = self.modal_body(
            modal,
            "Add Medication",
            "Create a medication inventory record.",
        )

        name = self.form_entry(body, "Medication Name", 2)
        unit = self.form_entry(body, "Unit", 4, "tablet, capsule, ml")
        stock = self.form_entry(body, "Initial Stock", 6, "Example: 100")
        description = self.form_entry(body, "Description", 8, "Optional")

        def save_medication():
            try:
                medication_name = name.get().strip()
                medication_unit = unit.get().strip()
                if not medication_name or not medication_unit:
                    raise ValueError("Medication name and unit are required.")

                result = execute(
                    """
                    INSERT INTO Medication
                        (medication_name, description, unit, stock_quantity)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        medication_name,
                        description.get().strip() or None,
                        medication_unit,
                        self.parse_nonnegative_int(stock.get(), "Initial Stock"),
                    ),
                )
                logger.info("Created medication id=%s", result["lastrowid"])
                messagebox.showinfo("Add Medication", "Medication added successfully.")
                modal.destroy()
                self.show_medications()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror("Add Medication", str(error))

        self.action_row(body, 10, "Save Medication", save_medication, modal.destroy)

    def open_bill_form(self):
        try:
            appointments = fetch_all(
                """
                SELECT
                    a.appointment_id,
                    a.patient_id,
                    CONCAT(p.first_name, ' ', p.last_name),
                    DATE_FORMAT(a.appointment_date, '%d %b %Y'),
                    c.clinic_name
                FROM Appointment a
                JOIN Patient p ON a.patient_id = p.patient_id
                JOIN Clinic c ON a.clinic_id = c.clinic_id
                LEFT JOIN Bill b ON a.appointment_id = b.appointment_id
                WHERE b.bill_id IS NULL
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
                """
            )
        except mysql.connector.Error as error:
            messagebox.showerror("Create Bill", str(error))
            return

        if not appointments:
            messagebox.showinfo("Create Bill", "Every appointment already has a bill.")
            return

        appointment_map = {}
        for appointment_id, patient_id, patient, appointment_date, clinic in appointments:
            label = f"{appointment_id} - {patient} | {appointment_date} | {clinic}"
            appointment_map[label] = (appointment_id, patient_id)

        modal = self.create_modal("Create Bill", 620, 500)
        body = self.modal_body(
            modal,
            "Create Bill",
            "Create a billing record for an appointment that does not already have one.",
        )

        appointment = self.form_combo(body, "Appointment", 2, list(appointment_map.keys()))
        total_amount = self.form_entry(body, "Total Amount", 4, "Example: 75000")
        amount_paid = self.form_entry(body, "Amount Paid", 6, "Example: 0", "0")
        bill_date = self.form_entry(body, "Bill Date", 8, "YYYY-MM-DD", date.today().isoformat())

        def save_bill():
            try:
                total = self.parse_decimal_amount(total_amount.get(), "Total Amount")
                paid = self.parse_decimal_amount(amount_paid.get(), "Amount Paid")
                if total <= 0:
                    raise ValueError("Total amount must be greater than zero.")
                if paid > total:
                    raise ValueError("Amount paid cannot be greater than total amount.")

                payment_status = "Unpaid"
                if paid == total:
                    payment_status = "Paid"
                elif paid > 0:
                    payment_status = "Partial"

                appointment_id, patient_id = appointment_map[appointment.get()]
                result = execute(
                    """
                    INSERT INTO Bill
                        (patient_id, appointment_id, total_amount, amount_paid, bill_date, payment_status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        patient_id,
                        appointment_id,
                        total,
                        paid,
                        self.parse_required_date(bill_date.get(), "Bill Date"),
                        payment_status,
                    ),
                )
                logger.info("Created bill id=%s", result["lastrowid"])
                messagebox.showinfo("Create Bill", "Bill created successfully.")
                modal.destroy()
                self.show_bills()
            except (ValueError, KeyError, mysql.connector.Error) as error:
                messagebox.showerror("Create Bill", str(error))

        self.action_row(body, 10, "Save Bill", save_bill, modal.destroy)

    def open_appointment_form(self):
        try:
            patients = fetch_all(
                "SELECT patient_id, CONCAT(first_name, ' ', last_name) FROM Patient ORDER BY last_name, first_name"
            )
            staff = fetch_all(
                "SELECT staff_id, CONCAT(first_name, ' ', last_name), role FROM Staff ORDER BY last_name, first_name"
            )
            clinics = fetch_all("SELECT clinic_id, clinic_name FROM Clinic ORDER BY clinic_name")
        except mysql.connector.Error as error:
            messagebox.showerror("Schedule Appointment", str(error))
            return

        if not patients or not staff or not clinics:
            messagebox.showinfo("Schedule Appointment", "Patients, staff, and clinics are required first.")
            return

        patient_values = [f"{patient_id} - {name}" for patient_id, name in patients]
        staff_values = [f"{staff_id} - {name} ({role})" for staff_id, name, role in staff]
        clinic_values = [f"{clinic_id} - {name}" for clinic_id, name in clinics]

        modal = self.create_modal("Schedule Appointment", 580, 620)
        body = self.modal_body(
            modal,
            "Schedule Appointment",
            "Create a new clinic visit and assign it to a patient, staff member, and clinic.",
        )

        patient = self.form_combo(body, "Patient", 2, patient_values)
        staff_member = self.form_combo(body, "Staff", 4, staff_values)
        clinic = self.form_combo(body, "Clinic", 6, clinic_values)
        appointment_date = self.form_entry(body, "Appointment Date", 8, "YYYY-MM-DD", date.today().isoformat())
        appointment_time = self.form_entry(body, "Appointment Time", 10, "HH:MM", "09:00")
        reason = self.form_entry(body, "Reason", 12)
        status = self.form_combo(body, "Status", 14, ["Scheduled", "Completed", "Cancelled"])

        def save_appointment():
            try:
                appointment_reason = reason.get().strip()
                if not appointment_reason:
                    raise ValueError("Reason is required.")

                result = execute(
                    """
                    INSERT INTO Appointment
                        (patient_id, staff_id, clinic_id, appointment_date, appointment_time, reason, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.selected_option_id(patient.get()),
                        self.selected_option_id(staff_member.get()),
                        self.selected_option_id(clinic.get()),
                        self.parse_required_date(appointment_date.get(), "Appointment Date"),
                        self.parse_required_time(appointment_time.get(), "Appointment Time"),
                        appointment_reason,
                        status.get(),
                    ),
                )
                logger.info("Scheduled appointment id=%s", result["lastrowid"])
                messagebox.showinfo("Schedule Appointment", "Appointment scheduled successfully.")
                modal.destroy()
                self.show_appointments()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror("Schedule Appointment", str(error))

        self.action_row(body, 16, "Save Appointment", save_appointment, modal.destroy)

    def update_selected_appointment_status(self, status):
        appointment_id = self.get_selected_id("Appointment Status")
        if appointment_id is None:
            return

        if status == "Cancelled" and not messagebox.askyesno(
            "Cancel Appointment",
            "Cancel the selected appointment?",
        ):
            return

        try:
            result = execute(
                "UPDATE Appointment SET status = %s WHERE appointment_id = %s",
                (status, appointment_id),
            )
            logger.info(
                "Updated appointment id=%s to status=%s rowcount=%s",
                appointment_id,
                status,
                result["rowcount"],
            )
            messagebox.showinfo("Appointment Status", f"Appointment marked as {status}.")
            self.show_appointments()
        except mysql.connector.Error as error:
            messagebox.showerror("Appointment Status", str(error))

    def open_restock_form(self):
        selected_id = self.get_selected_id("Restock Medication", silent=True)

        try:
            medications = fetch_all(
                """
                SELECT medication_id, medication_name, stock_quantity
                FROM Medication
                ORDER BY medication_name
                """
            )
        except mysql.connector.Error as error:
            messagebox.showerror("Restock Medication", str(error))
            return

        if not medications:
            messagebox.showinfo("Restock Medication", "No medications are available to restock.")
            return

        values = [f"{medication_id} - {name} (stock: {stock})" for medication_id, name, stock in medications]

        modal = self.create_modal("Restock Medication", 540, 360)
        body = self.modal_body(
            modal,
            "Restock Medication",
            "Add new stock to an existing medication record.",
        )

        medication = self.form_combo(body, "Medication", 2, values)
        if selected_id is not None:
            for value in values:
                if value.startswith(f"{selected_id} - "):
                    medication.set(value)
                    break
        quantity = self.form_entry(body, "Quantity to Add", 4, "Example: 100")

        def save_stock():
            try:
                amount = int(quantity.get().strip())
                if amount <= 0:
                    raise ValueError("Quantity must be greater than zero.")

                result = execute(
                    "UPDATE Medication SET stock_quantity = stock_quantity + %s WHERE medication_id = %s",
                    (amount, self.selected_option_id(medication.get())),
                )
                logger.info(
                    "Restocked medication id=%s quantity=%s rowcount=%s",
                    self.selected_option_id(medication.get()),
                    amount,
                    result["rowcount"],
                )
                messagebox.showinfo("Restock Medication", "Medication stock updated successfully.")
                modal.destroy()
                self.show_medications()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror("Restock Medication", str(error))

        self.action_row(body, 6, "Save Stock", save_stock, modal.destroy)

    def open_payment_form(self):
        selected_id = self.get_selected_id("Record Payment", silent=True)

        try:
            bills = fetch_all(
                """
                SELECT
                    b.bill_id,
                    CONCAT(p.first_name, ' ', p.last_name),
                    b.total_amount,
                    b.amount_paid
                FROM Bill b
                JOIN Patient p ON b.patient_id = p.patient_id
                WHERE b.total_amount > b.amount_paid
                ORDER BY b.bill_date DESC, b.bill_id DESC
                """
            )
        except mysql.connector.Error as error:
            messagebox.showerror("Record Payment", str(error))
            return

        if not bills:
            messagebox.showinfo("Record Payment", "There are no outstanding bills.")
            return

        bill_map = {}
        for bill_id, patient, total, paid in bills:
            balance = float(total) - float(paid)
            label = f"{bill_id} - {patient} | Balance {self.money(balance)}"
            bill_map[label] = (bill_id, float(total), float(paid))

        modal = self.create_modal("Record Payment", 560, 390)
        body = self.modal_body(
            modal,
            "Record Payment",
            "Apply a payment to an unpaid or partially paid bill.",
        )

        bill = self.form_combo(body, "Bill", 2, list(bill_map.keys()))
        if selected_id is not None:
            for value in bill_map:
                if value.startswith(f"{selected_id} - "):
                    bill.set(value)
                    break
        amount = self.form_entry(body, "Payment Amount", 4, "Example: 25000")

        def save_payment():
            try:
                payment = float(amount.get().strip())
                if payment <= 0:
                    raise ValueError("Payment amount must be greater than zero.")

                bill_id, total, paid = bill_map[bill.get()]
                new_paid = min(total, paid + payment)
                payment_status = "Paid" if new_paid >= total else "Partial"

                result = execute(
                    """
                    UPDATE Bill
                    SET amount_paid = %s,
                        payment_status = %s
                    WHERE bill_id = %s
                    """,
                    (new_paid, payment_status, bill_id),
                )
                logger.info(
                    "Recorded payment for bill id=%s amount=%s new_status=%s rowcount=%s",
                    bill_id,
                    payment,
                    payment_status,
                    result["rowcount"],
                )
                messagebox.showinfo("Record Payment", "Payment recorded successfully.")
                modal.destroy()
                self.show_bills()
            except (ValueError, KeyError, mysql.connector.Error) as error:
                messagebox.showerror("Record Payment", str(error))

        self.action_row(body, 6, "Save Payment", save_payment, modal.destroy)

    def show_table_page(
        self,
        nav_name,
        title,
        subtitle,
        columns,
        query,
        actions=None,
        filter_column=None,
        filter_options=None,
    ):
        self.set_active_nav(nav_name)
        container = self.create_page_container()
        self.page_header(container, title, subtitle)

        try:
            rows = fetch_all(query)
        except mysql.connector.Error as error:
            self.show_database_error(container, error)
            return

        self.current_sort_column = None
        self.current_sort_reverse = False
        self.current_filter_column_index = None
        if filter_column:
            headings = [column[0] for column in columns]
            if filter_column in headings:
                self.current_filter_column_index = headings.index(filter_column)

        controls = ctk.CTkFrame(container, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        controls.grid_columnconfigure(0, weight=1)

        search = ctk.CTkEntry(
            controls,
            height=40,
            placeholder_text="Search records",
            border_width=1,
            border_color="#334155",
            fg_color=CARD_BG,
            text_color=TEXT_PRIMARY,
            font=("Segoe UI", 13),
        )
        search.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.current_search_entry = search

        next_column = 1
        if filter_options:
            self.current_filter_var = ctk.StringVar(value=filter_options[0])
            filter_menu = ctk.CTkOptionMenu(
                controls,
                values=filter_options,
                variable=self.current_filter_var,
                width=140,
                height=40,
                fg_color=CARD_BG,
                button_color="#334155",
                button_hover_color="#475569",
                command=lambda _choice: self.filter_rows(),
                font=("Segoe UI", 13),
            )
            filter_menu.grid(row=0, column=next_column, sticky="e", padx=(0, 10))
            next_column += 1
        else:
            self.current_filter_var = None

        for label, callback in actions or []:
            action_button = ctk.CTkButton(
                controls,
                text=label,
                width=145,
                height=40,
                corner_radius=8,
                fg_color="#334155",
                hover_color="#475569",
                command=callback,
                font=("Segoe UI", 13, "bold"),
            )
            action_button.grid(row=0, column=next_column, sticky="e", padx=(0, 10))
            next_column += 1

        refresh = ctk.CTkButton(
            controls,
            text="Refresh",
            width=110,
            height=40,
            corner_radius=8,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=lambda: self.show_table_page(
                nav_name,
                title,
                subtitle,
                columns,
                query,
                actions=actions,
                filter_column=filter_column,
                filter_options=filter_options,
            ),
            font=("Segoe UI", 13, "bold"),
        )
        refresh.grid(row=0, column=next_column, sticky="e", padx=(0, 10))
        next_column += 1

        export = ctk.CTkButton(
            controls,
            text="Export CSV",
            width=120,
            height=40,
            corner_radius=8,
            fg_color="#0f766e",
            hover_color="#0d9488",
            command=self.export_current_rows,
            font=("Segoe UI", 13, "bold"),
        )
        export.grid(row=0, column=next_column, sticky="e")

        table_panel = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=8)
        table_panel.grid(row=2, column=0, sticky="nsew")
        table_panel.grid_columnconfigure(0, weight=1)
        table_panel.grid_rowconfigure(0, weight=1)

        self.create_tree(table_panel, columns, rows, row=0)
        search.bind("<KeyRelease>", lambda _event: self.filter_rows(search.get()))

    def create_tree(self, parent, columns, rows, row, searchable=True):
        self.configure_tree_style()

        table_frame = ctk.CTkFrame(parent, fg_color="transparent")
        table_frame.grid(row=row, column=0, sticky="nsew", padx=14, pady=14)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        column_ids = [f"col_{index}" for index, _column in enumerate(columns)]
        tree = ttk.Treeview(
            table_frame,
            columns=column_ids,
            show="headings",
            style="Professional.Treeview",
        )

        for index, (column_id, (heading, width, anchor)) in enumerate(zip(column_ids, columns)):
            if searchable:
                tree.heading(
                    column_id,
                    text=heading,
                    command=lambda column_index=index: self.sort_rows(column_index),
                )
            else:
                tree.heading(column_id, text=heading)
            tree.column(column_id, width=width, minwidth=70, anchor=anchor, stretch=False)

        vertical_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        horizontal_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical_scroll.set, xscrollcommand=horizontal_scroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")

        count_label = ctk.CTkLabel(
            parent,
            text="",
            font=("Segoe UI", 12),
            text_color=TEXT_MUTED,
        )
        count_label.grid(row=row + 1, column=0, sticky="w", padx=18, pady=(0, 14))

        if searchable:
            self.current_rows = [tuple(self.clean_value(value) for value in row_values) for row_values in rows]
            self.current_columns = column_ids
            self.current_headings = [column[0] for column in columns]
            self.current_tree = tree
            self.current_count_label = count_label
            self.filter_rows()
        else:
            self.populate_tree(tree, rows)
            count_label.configure(text=f"{len(rows)} records")

        return tree

    def configure_tree_style(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure(
            "Professional.Treeview",
            background=CARD_BG,
            foreground=TEXT_PRIMARY,
            fieldbackground=CARD_BG,
            bordercolor="#1f2937",
            borderwidth=0,
            rowheight=32,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Professional.Treeview.Heading",
            background="#1f2937",
            foreground=TEXT_PRIMARY,
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padding=8,
        )
        style.map(
            "Professional.Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", "#ffffff")],
        )

    def sort_rows(self, column_index):
        if self.current_sort_column == column_index:
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            self.current_sort_column = column_index
            self.current_sort_reverse = False
        self.filter_rows()

    def filter_rows(self, term=None):
        if term is None and self.current_search_entry is not None:
            term = self.current_search_entry.get()

        normalized = (term or "").strip().lower()
        if normalized:
            rows = [
                row
                for row in self.current_rows
                if normalized in " ".join(str(value).lower() for value in row)
            ]
        else:
            rows = self.current_rows

        if self.current_filter_var and self.current_filter_column_index is not None:
            selected_filter = self.current_filter_var.get()
            if selected_filter != "All":
                rows = [
                    row
                    for row in rows
                    if str(row[self.current_filter_column_index]).lower() == selected_filter.lower()
                ]

        if self.current_sort_column is not None:
            rows = sorted(
                rows,
                key=lambda row: self.sort_key(row[self.current_sort_column]),
                reverse=self.current_sort_reverse,
            )

        self.current_visible_rows = rows
        self.populate_tree(self.current_tree, rows)
        if self.current_count_label:
            self.current_count_label.configure(text=f"{len(rows)} of {len(self.current_rows)} records")

    def populate_tree(self, tree, rows):
        for item in tree.get_children():
            tree.delete(item)

        for index, row in enumerate(rows):
            tag = "even" if index % 2 == 0 else "odd"
            tree.insert("", "end", values=[self.clean_value(value) for value in row], tags=(tag,))

        tree.tag_configure("even", background=CARD_BG)
        tree.tag_configure("odd", background="#162033")

    def sort_key(self, value):
        text = self.clean_value(value).replace("Le ", "").replace(",", "").strip()
        try:
            return float(text)
        except ValueError:
            return text.lower()

    def export_current_rows(self):
        if not self.current_visible_rows:
            messagebox.showinfo("Export CSV", "There are no visible records to export.")
            return

        path = filedialog.asksaveasfilename(
            title="Export records",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(self.current_headings)
            writer.writerows(self.current_visible_rows)

        logger.info("Exported %s visible rows to %s", len(self.current_visible_rows), path)
        messagebox.showinfo("Export CSV", "Records exported successfully.")

    def get_selected_id(self, label, silent=False):
        if not self.current_tree:
            if not silent:
                messagebox.showinfo(label, "Open a table and select a record first.")
            return None

        selected = self.current_tree.selection()
        if not selected:
            if not silent:
                messagebox.showinfo(label, "Select a record first.")
            return None

        values = self.current_tree.item(selected[0], "values")
        try:
            return int(values[0])
        except (IndexError, TypeError, ValueError):
            messagebox.showerror(label, "The selected record does not have a valid ID.")
            return None

    def open_selected_record(self, label, form_callback):
        record_id = self.get_selected_id(label)
        if record_id is not None:
            form_callback(record_id)

    def create_modal(self, title, width=560, height=560):
        modal = ctk.CTkToplevel(self)
        modal.title(title)
        modal.geometry(f"{width}x{height}")
        modal.minsize(width, height)
        modal.configure(fg_color=PANEL_BG)
        modal.transient(self)
        modal.grab_set()
        modal.focus()
        return modal

    def modal_body(self, modal, title, subtitle):
        body = ctk.CTkScrollableFrame(modal, fg_color="transparent", scrollbar_button_color="#334155")
        body.pack(fill="both", expand=True, padx=24, pady=20)
        body.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            body,
            text=title,
            font=("Segoe UI", 22, "bold"),
            text_color=TEXT_PRIMARY,
        )
        title_label.grid(row=0, column=0, sticky="w")

        subtitle_label = ctk.CTkLabel(
            body,
            text=subtitle,
            font=("Segoe UI", 13),
            text_color=TEXT_MUTED,
            wraplength=500,
            justify="left",
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(4, 16))
        return body

    def form_entry(self, parent, label, row, placeholder="", value=""):
        field_label = ctk.CTkLabel(
            parent,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color=TEXT_MUTED,
        )
        field_label.grid(row=row, column=0, sticky="w", pady=(0, 4))

        entry = ctk.CTkEntry(
            parent,
            height=38,
            placeholder_text=placeholder,
            fg_color=CARD_BG,
            border_color="#334155",
            text_color=TEXT_PRIMARY,
            font=("Segoe UI", 13),
        )
        entry.grid(row=row + 1, column=0, sticky="ew", pady=(0, 10))
        if value:
            entry.insert(0, value)
        return entry

    def form_combo(self, parent, label, row, values):
        field_label = ctk.CTkLabel(
            parent,
            text=label,
            font=("Segoe UI", 12, "bold"),
            text_color=TEXT_MUTED,
        )
        field_label.grid(row=row, column=0, sticky="w", pady=(0, 4))

        combo = ctk.CTkComboBox(
            parent,
            values=values,
            height=38,
            fg_color=CARD_BG,
            border_color="#334155",
            button_color="#334155",
            button_hover_color="#475569",
            text_color=TEXT_PRIMARY,
            font=("Segoe UI", 13),
            state="readonly",
        )
        combo.grid(row=row + 1, column=0, sticky="ew", pady=(0, 10))
        if values:
            combo.set(values[0])
        return combo

    def action_row(self, parent, row, save_label, save_command, cancel_command):
        buttons = ctk.CTkFrame(parent, fg_color="transparent")
        buttons.grid(row=row, column=0, sticky="ew", pady=(8, 0))
        buttons.grid_columnconfigure(0, weight=1)

        cancel = ctk.CTkButton(
            buttons,
            text="Cancel",
            width=110,
            height=38,
            fg_color="#334155",
            hover_color="#475569",
            command=cancel_command,
            font=("Segoe UI", 13, "bold"),
        )
        cancel.grid(row=0, column=1, padx=(0, 10))

        save = ctk.CTkButton(
            buttons,
            text=save_label,
            width=150,
            height=38,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=save_command,
            font=("Segoe UI", 13, "bold"),
        )
        save.grid(row=0, column=2)

    def parse_required_date(self, value, field_name):
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"{field_name} must use YYYY-MM-DD format.")

    def parse_optional_date(self, value, field_name):
        if not value.strip():
            return None
        return self.parse_required_date(value, field_name)

    def parse_required_time(self, value, field_name):
        try:
            return datetime.strptime(value.strip(), "%H:%M").time()
        except ValueError:
            raise ValueError(f"{field_name} must use HH:MM format.")

    def parse_positive_int(self, value, field_name):
        try:
            number = int(value.strip())
        except ValueError:
            raise ValueError(f"{field_name} must be a whole number.")
        if number <= 0:
            raise ValueError(f"{field_name} must be greater than zero.")
        return number

    def parse_nonnegative_int(self, value, field_name):
        try:
            number = int(value.strip())
        except ValueError:
            raise ValueError(f"{field_name} must be a whole number.")
        if number < 0:
            raise ValueError(f"{field_name} cannot be negative.")
        return number

    def parse_decimal_amount(self, value, field_name):
        try:
            amount = Decimal(value.strip())
        except (InvalidOperation, ValueError):
            raise ValueError(f"{field_name} must be a valid amount.")
        if amount < 0:
            raise ValueError(f"{field_name} cannot be negative.")
        return amount.quantize(Decimal("0.01"))

    def selected_option_id(self, value):
        return int(value.split(" - ", 1)[0])

    def show_database_error(self, container, error):
        panel = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=8)
        panel.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        panel.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            panel,
            text="Database connection unavailable",
            font=("Segoe UI", 20, "bold"),
            text_color=TEXT_PRIMARY,
        )
        title.grid(row=0, column=0, sticky="w", padx=22, pady=(22, 6))

        config = DatabaseConfig()
        detail = (
            f"Could not connect to '{config.database}' on {config.host}:{config.port}. "
            "Check that the XAMPP MySQL/MariaDB service is running and that the schema has been imported."
        )
        detail_label = ctk.CTkLabel(
            panel,
            text=detail,
            font=("Segoe UI", 13),
            text_color=TEXT_MUTED,
            wraplength=720,
            justify="left",
        )
        detail_label.grid(row=1, column=0, sticky="w", padx=22, pady=(0, 8))

        error_label = ctk.CTkLabel(
            panel,
            text=str(error),
            font=("Segoe UI", 12),
            text_color="#fca5a5",
            wraplength=720,
            justify="left",
        )
        error_label.grid(row=2, column=0, sticky="w", padx=22, pady=(0, 22))

        messagebox.showerror("Database Error", str(error))

    def clean_value(self, value):
        return "-" if value is None else str(value)

    def money(self, value):
        return f"Le {float(value):,.0f}"


if __name__ == "__main__":
    app = ClinicSystem()
    app.mainloop()
