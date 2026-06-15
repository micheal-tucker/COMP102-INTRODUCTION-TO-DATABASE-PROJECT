import csv
import logging
from decimal import Decimal, InvalidOperation
from datetime import date, datetime
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

import customtkinter as ctk
import mysql.connector

from db import DatabaseConfig, execute, fetch_all, fetch_one


# ─── Theme constants ──────────────────────────────────────────────────────────
APP_TITLE        = "Public Health Clinic Records"
APP_VERSION      = "v2.0"

PANEL_BG         = "#0f172a"
PANEL_ALT        = "#172033"
CARD_BG          = "#111827"
CARD_BORDER      = "#1e293b"

TEXT_PRIMARY     = "#f8fafc"
TEXT_MUTED       = "#94a3b8"
TEXT_DIM         = "#475569"

ACCENT           = "#2563eb"
ACCENT_HOVER     = "#1d4ed8"
ACCENT_LIGHT     = "#3b82f6"

SUCCESS          = "#059669"
SUCCESS_HOVER    = "#047857"
WARNING          = "#d97706"
DANGER           = "#dc2626"
DANGER_HOVER     = "#b91c1c"

NAV_ACTIVE_BG    = "#1e3a5f"
NAV_ACTIVE_TEXT  = "#60a5fa"
NAV_HOVER        = "#1e293b"

SIDEBAR_W        = 220

logger = logging.getLogger("clinic_records.main")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─── Nav items: (label, emoji icon, handler-name) ────────────────────────────
NAV_ITEMS = [
    ("Dashboard",      "🏠", "show_dashboard"),
    ("Patients",       "🧑‍⚕️", "show_patients"),
    ("Staff",          "👔", "show_staff"),
    ("Clinics",        "🏥", "show_clinics"),
    ("Appointments",   "📅", "show_appointments"),
    ("Diagnoses",      "🩺", "show_diagnoses"),
    ("Prescriptions",  "💊", "show_prescriptions"),
    ("Medications",    "🧴", "show_medications"),
    ("Billing",        "💰", "show_bills"),
    ("Reports",        "📊", "show_reports"),
]


class ClinicSystem(ctk.CTk):
    # ─── Init & shell ─────────────────────────────────────────────────────────
    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE}  {APP_VERSION}")
        self.geometry("1360x800")
        self.minsize(1100, 660)
        self.configure(fg_color=PANEL_BG)

        # table state
        self.nav_buttons            = {}
        self.current_rows           = []
        self.current_visible_rows   = []
        self.current_columns        = []
        self.current_headings       = []
        self.current_tree           = None
        self.current_count_label    = None
        self.current_search_entry   = None
        self.current_filter_var     = None
        self.current_filter_column_index = None
        self.current_sort_column    = None
        self.current_sort_reverse   = False

        # toast state
        self._toast_after_id = None

        logger.info("Starting %s %s", APP_TITLE, APP_VERSION)
        self._build_shell()
        self._bind_shortcuts()
        self.show_dashboard()

    # ──────────────────────────────────────────────────────────────────────────
    def _build_shell(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # ── Sidebar ──────────────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(self, width=SIDEBAR_W, corner_radius=0,
                                    fg_color=CARD_BG)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Brand
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(22, 0))

        ctk.CTkLabel(brand_frame, text="🏥", font=("Segoe UI Emoji", 28),
                     text_color=ACCENT_LIGHT).pack(side="left", padx=(0, 8))

        title_stack = ctk.CTkFrame(brand_frame, fg_color="transparent")
        title_stack.pack(side="left")
        ctk.CTkLabel(title_stack, text="Clinic Records",
                     font=("Segoe UI", 16, "bold"),
                     text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(title_stack, text="Public health operations",
                     font=("Segoe UI", 10),
                     text_color=TEXT_MUTED).pack(anchor="w")

        # Separator
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=CARD_BORDER)
        sep.pack(fill="x", padx=12, pady=(16, 8))

        # Nav section label
        ctk.CTkLabel(self.sidebar, text="NAVIGATION",
                     font=("Segoe UI", 9, "bold"),
                     text_color=TEXT_DIM).pack(anchor="w", padx=20, pady=(4, 6))

        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10)

        for name, icon, handler in NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {icon}  {name}",
                anchor="w",
                height=38,
                corner_radius=8,
                command=lambda n=name, h=handler: self._navigate(n, h),
                fg_color="transparent",
                hover_color=NAV_HOVER,
                text_color=TEXT_MUTED,
                font=("Segoe UI", 13),
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[name] = btn

        # Footer
        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(side="bottom", fill="x", padx=12, pady=14)

        db_config = DatabaseConfig()
        ctk.CTkLabel(footer,
                     text=f"⚙  {db_config.database}",
                     font=("Segoe UI", 10),
                     text_color=TEXT_DIM,
                     wraplength=190, justify="left").pack(anchor="w", pady=(0, 8))

        ctk.CTkButton(footer, text="🔌  Test DB", height=34, corner_radius=8,
                      command=self.test_database_connection,
                      fg_color="#0f766e", hover_color="#0d9488",
                      font=("Segoe UI", 12, "bold")).pack(fill="x", pady=(0, 6))

        ctk.CTkButton(footer, text="✕  Exit", height=34, corner_radius=8,
                      command=self._confirm_exit,
                      fg_color="#334155", hover_color=DANGER,
                      font=("Segoe UI", 12, "bold")).pack(fill="x")

        # ── Main content ──────────────────────────────────────────────────────
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=PANEL_BG)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        # ── Status bar ────────────────────────────────────────────────────────
        self.status_bar = ctk.CTkFrame(self, height=28, corner_radius=0,
                                       fg_color="#0a0f1a")
        self.status_bar.grid(row=1, column=1, sticky="ew")
        self.status_bar.grid_propagate(False)
        self.status_bar.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready",
                                         font=("Segoe UI", 11),
                                         text_color=TEXT_MUTED)
        self.status_label.grid(row=0, column=0, sticky="w", padx=14)

        self._clock_label = ctk.CTkLabel(self.status_bar, text="",
                                          font=("Segoe UI", 11),
                                          text_color=TEXT_DIM)
        self._clock_label.grid(row=0, column=1, sticky="e", padx=14)
        self._tick_clock()

        # ── Toast overlay label ───────────────────────────────────────────────
        self._toast_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 13, "bold"),
                                          fg_color="#1e3a5f", corner_radius=8,
                                          text_color=TEXT_PRIMARY,
                                          padx=18, pady=8)

    # ── Keyboard shortcuts ────────────────────────────────────────────────────
    def _bind_shortcuts(self):
        self.bind("<Control-f>", lambda _e: self._focus_search())
        self.bind("<F5>",        lambda _e: self._refresh_current())
        self.bind("<Escape>",    lambda _e: self._clear_search())

    def _focus_search(self):
        if self.current_search_entry:
            self.current_search_entry.focus_set()

    def _clear_search(self):
        if self.current_search_entry:
            self.current_search_entry.delete(0, "end")
            self.filter_rows()

    def _refresh_current(self):
        # Find which nav button is active and re-trigger it
        for name, _icon, handler in NAV_ITEMS:
            btn = self.nav_buttons[name]
            if btn.cget("text_color") == NAV_ACTIVE_TEXT:
                getattr(self, handler)()
                return

    # ── Clock ─────────────────────────────────────────────────────────────────
    def _tick_clock(self):
        self._clock_label.configure(
            text=datetime.now().strftime("  %a %d %b %Y  |  %H:%M:%S  "))
        self.after(1000, self._tick_clock)

    # ── Toast notification ────────────────────────────────────────────────────
    def toast(self, message, kind="info"):
        colors = {"info": "#1e3a5f", "success": "#064e3b", "error": "#7f1d1d",
                  "warning": "#78350f"}
        icons  = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}
        self._toast_label.configure(
            text=f"  {icons.get(kind,'ℹ️')}  {message}  ",
            fg_color=colors.get(kind, "#1e3a5f"))
        self._toast_label.place(relx=0.5, rely=0.97, anchor="s")
        if self._toast_after_id:
            self.after_cancel(self._toast_after_id)
        self._toast_after_id = self.after(3200, self._toast_label.place_forget)

    def set_status(self, text):
        self.status_label.configure(text=text)

    # ── Navigation ────────────────────────────────────────────────────────────
    def _navigate(self, name, handler_name):
        logger.info("Navigating to %s", name)
        self._set_active_nav(name)
        getattr(self, handler_name)()

    def _set_active_nav(self, name):
        for btn_name, btn in self.nav_buttons.items():
            active = (btn_name == name)
            # find icon for this button
            icon = next((i for n, i, _ in NAV_ITEMS if n == btn_name), "")
            btn.configure(
                text=f"  {icon}  {btn_name}",
                fg_color=NAV_ACTIVE_BG if active else "transparent",
                text_color=NAV_ACTIVE_TEXT if active else TEXT_MUTED,
                hover_color=NAV_ACTIVE_BG if active else NAV_HOVER,
                font=("Segoe UI", 13, "bold") if active else ("Segoe UI", 13),
            )

    def _confirm_exit(self):
        if messagebox.askyesno("Exit", "Exit the application?"):
            self.destroy()

    # ── DB test ───────────────────────────────────────────────────────────────
    def test_database_connection(self):
        try:
            result = fetch_one("SELECT 1")
            if result and result[0] == 1:
                logger.info("DB connection OK")
                self.toast("Database connection is healthy.", "success")
            else:
                self.toast("Database responded unexpectedly.", "warning")
        except mysql.connector.Error as error:
            logger.exception("DB connection test failed")
            self.toast(f"DB error: {error}", "error")

    # ── Content helpers ───────────────────────────────────────────────────────
    def clear_content(self):
        for child in self.content.winfo_children():
            child.destroy()
        self._reset_table_state()

    def _reset_table_state(self):
        self.current_rows                = []
        self.current_visible_rows        = []
        self.current_columns             = []
        self.current_headings            = []
        self.current_tree                = None
        self.current_count_label         = None
        self.current_search_entry        = None
        self.current_filter_var          = None
        self.current_filter_column_index = None
        self.current_sort_column         = None
        self.current_sort_reverse        = False

    def _page_header(self, parent, title, subtitle, icon=""):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(20, 12))
        header.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(header, fg_color="transparent")
        top.grid(row=0, column=0, sticky="w")
        if icon:
            ctk.CTkLabel(top, text=icon, font=("Segoe UI Emoji", 26),
                         text_color=ACCENT_LIGHT).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(top, text=title, font=("Segoe UI", 26, "bold"),
                     text_color=TEXT_PRIMARY).pack(side="left")

        ctk.CTkLabel(header, text=subtitle, font=("Segoe UI", 13),
                     text_color=TEXT_MUTED).grid(row=1, column=0, sticky="w",
                                                  pady=(4, 0))

    def _create_page_container(self):
        self.clear_content()
        container = ctk.CTkFrame(self.content, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=26, pady=0)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(2, weight=1)
        return container

    # ─── Dashboard ────────────────────────────────────────────────────────────
    def show_dashboard(self):
        self._set_active_nav("Dashboard")
        container = self._create_page_container()
        self._page_header(container, "Dashboard", "Operational snapshot across patients, clinics, appointments, and billing.", "🏠")

        try:
            metrics = self._get_dashboard_metrics()
            recent_appointments = fetch_all("""
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
                LIMIT 10
            """)
        except mysql.connector.Error as error:
            self._show_database_error(container, error)
            return

        # Metric cards
        cards = ctk.CTkFrame(container, fg_color="transparent")
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 18))

        accent_colors = [ACCENT, "#7c3aed", SUCCESS, "#0891b2", WARNING, DANGER]
        for index, metric in enumerate(metrics):
            cards.grid_columnconfigure(index % 3, weight=1, uniform="metric")
            self._stat_card(cards, metric["title"], metric["value"],
                            metric["note"], index // 3, index % 3,
                            accent_colors[index % len(accent_colors)])

        # Recent appointments table
        table_panel = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=10)
        table_panel.grid(row=2, column=0, sticky="nsew")
        table_panel.grid_columnconfigure(0, weight=1)
        table_panel.grid_rowconfigure(1, weight=1)

        header_row = ctk.CTkFrame(table_panel, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
        header_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header_row, text="Recent Appointments",
                     font=("Segoe UI", 17, "bold"),
                     text_color=TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header_row, text="Latest 10 visits",
                     font=("Segoe UI", 11),
                     text_color=TEXT_MUTED).grid(row=0, column=1, sticky="e")

        self.create_tree(table_panel, [
            ("ID",      70,  "center"),
            ("Date",    120, "w"),
            ("Time",    80,  "center"),
            ("Patient", 180, "w"),
            ("Staff",   170, "w"),
            ("Clinic",  220, "w"),
            ("Status",  120, "center"),
        ], recent_appointments, row=1, searchable=False)

        self.set_status("Dashboard loaded")

    def _get_dashboard_metrics(self):
        queries = {
            "patients":    "SELECT COUNT(*) FROM Patient",
            "staff":       "SELECT COUNT(*) FROM Staff",
            "clinics":     "SELECT COUNT(*) FROM Clinic",
            "appointments":"SELECT COUNT(*) FROM Appointment",
            "revenue":     "SELECT IFNULL(SUM(amount_paid), 0) FROM Bill",
            "outstanding": "SELECT IFNULL(SUM(total_amount - amount_paid), 0) FROM Bill",
        }
        values = {name: fetch_one(query)[0] for name, query in queries.items()}
        return [
            {"title": "Patients",     "value": f"{values['patients']:,}",      "note": "registered records"},
            {"title": "Staff",        "value": f"{values['staff']:,}",         "note": "clinic team members"},
            {"title": "Clinics",      "value": f"{values['clinics']:,}",       "note": "service locations"},
            {"title": "Appointments", "value": f"{values['appointments']:,}",   "note": "scheduled or completed"},
            {"title": "Collected",    "value": self.money(values["revenue"]),   "note": "payments received"},
            {"title": "Outstanding",  "value": self.money(values["outstanding"]),"note": "balance to collect"},
        ]

    def _stat_card(self, parent, title, value, note, row, column, accent=ACCENT):
        card = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=10)
        card.grid(row=row, column=column, sticky="ew", padx=6, pady=6)
        card.grid_columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(card, height=3, fg_color=accent, corner_radius=2)
        bar.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 0))

        ctk.CTkLabel(card, text=title, font=("Segoe UI", 12, "bold"),
                     text_color=TEXT_MUTED).grid(row=1, column=0, sticky="w",
                                                  padx=16, pady=(12, 0))
        ctk.CTkLabel(card, text=value, font=("Segoe UI", 26, "bold"),
                     text_color=TEXT_PRIMARY).grid(row=2, column=0, sticky="w",
                                                    padx=16, pady=(2, 0))
        ctk.CTkLabel(card, text=note, font=("Segoe UI", 11),
                     text_color=TEXT_DIM).grid(row=3, column=0, sticky="w",
                                                padx=16, pady=(0, 14))

    # ─── Table pages ──────────────────────────────────────────────────────────
    def show_patients(self):
        self.show_table_page(
            "Patients", "Patients", "Registered patients with demographic and contact details.", "🧑‍⚕️",
            [("ID",70,"center"),("Name",220,"w"),("DOB",120,"w"),("Gender",100,"center"),
             ("Phone",145,"w"),("Blood Type",110,"center"),("Registered",120,"w")],
            """SELECT patient_id, CONCAT(first_name,' ',last_name),
                   DATE_FORMAT(date_of_birth,'%d %b %Y'), gender, phone,
                   IFNULL(blood_type,'-'), DATE_FORMAT(registration_date,'%d %b %Y')
               FROM Patient ORDER BY last_name, first_name""",
            actions=[
                ("➕  Register", self.open_patient_form),
                ("✏️  Edit",     lambda: self.open_selected_record("Edit Patient", self.open_patient_form)),
                ("🗑  Delete",   lambda: self._delete_record("Patient","patient_id","Patient",self.show_patients)),
                ("📋  History",  self.open_patient_history),
            ],
        )

    def show_staff(self):
        self.show_table_page(
            "Staff", "Staff", "Clinic personnel, roles, assigned locations, and contact information.", "👔",
            [("ID",70,"center"),("Name",210,"w"),("Role",140,"w"),("Clinic",220,"w"),
             ("Gender",100,"center"),("Phone",145,"w"),("Email",200,"w"),("Hire Date",120,"w")],
            """SELECT s.staff_id, CONCAT(s.first_name,' ',s.last_name), s.role,
                   c.clinic_name, s.gender, s.phone, IFNULL(s.email,'-'),
                   DATE_FORMAT(s.hire_date,'%d %b %Y')
               FROM Staff s JOIN Clinic c ON s.clinic_id=c.clinic_id
               ORDER BY c.clinic_name, s.role, s.last_name""",
            actions=[
                ("➕  Add",    self.open_staff_form),
                ("✏️  Edit",   lambda: self.open_selected_record("Edit Staff", self.open_staff_form_edit)),
                ("🗑  Delete", lambda: self._delete_record("Staff","staff_id","Staff",self.show_staff)),
            ],
        )

    def show_clinics(self):
        self.show_table_page(
            "Clinics", "Clinics", "Clinic locations with staffing and appointment activity.", "🏥",
            [("ID",70,"center"),("Clinic",220,"w"),("District",160,"w"),("Location",240,"w"),
             ("Phone",145,"w"),("Email",200,"w"),("Staff",80,"center"),("Appts",80,"center")],
            """SELECT c.clinic_id, c.clinic_name, c.district, c.location, c.phone,
                   IFNULL(c.email,'-'),
                   COUNT(DISTINCT s.staff_id), COUNT(DISTINCT a.appointment_id)
               FROM Clinic c
               LEFT JOIN Staff s ON c.clinic_id=s.clinic_id
               LEFT JOIN Appointment a ON c.clinic_id=a.clinic_id
               GROUP BY c.clinic_id,c.clinic_name,c.district,c.location,c.phone,c.email
               ORDER BY c.clinic_name""",
            actions=[
                ("➕  Add",    self.open_clinic_form),
                ("✏️  Edit",   lambda: self.open_selected_record("Edit Clinic", self.open_clinic_form_edit)),
                ("🗑  Delete", lambda: self._delete_record("Clinic","clinic_id","Clinic",self.show_clinics)),
            ],
        )

    def show_appointments(self):
        self.show_table_page(
            "Appointments", "Appointments", "Visit schedule with patient, staff, clinic, and status details.", "📅",
            [("ID",70,"center"),("Date",120,"w"),("Time",80,"center"),
             ("Patient",190,"w"),("Staff",175,"w"),("Clinic",210,"w"),
             ("Status",120,"center"),("Reason",280,"w")],
            """SELECT a.appointment_id,
                   DATE_FORMAT(a.appointment_date,'%d %b %Y'),
                   TIME_FORMAT(a.appointment_time,'%H:%i'),
                   CONCAT(p.first_name,' ',p.last_name),
                   CONCAT(s.first_name,' ',s.last_name),
                   c.clinic_name, a.status, a.reason
               FROM Appointment a
               JOIN Patient p ON a.patient_id=p.patient_id
               JOIN Staff s ON a.staff_id=s.staff_id
               JOIN Clinic c ON a.clinic_id=c.clinic_id
               ORDER BY a.appointment_date DESC, a.appointment_time DESC""",
            actions=[
                ("➕  Schedule",     self.open_appointment_form),
                ("✏️  Edit",         lambda: self.open_selected_record("Edit Appointment", self.open_appointment_form_edit)),
                ("✅  Complete",      lambda: self.update_selected_appointment_status("Completed")),
                ("❌  Cancel",        lambda: self.update_selected_appointment_status("Cancelled")),
                ("🗑  Delete",        lambda: self._delete_record("Appointment","appointment_id","Appointment",self.show_appointments)),
            ],
            filter_column="Status",
            filter_options=["All", "Scheduled", "Completed", "Cancelled"],
        )

    def show_diagnoses(self):
        self.show_table_page(
            "Diagnoses", "Diagnoses", "Clinical diagnosis history linked to patient visits.", "🩺",
            [("ID",70,"center"),("Date",120,"w"),("Patient",200,"w"),("Code",90,"center"),
             ("Description",340,"w"),("Severity",120,"center"),("Visit Status",120,"center")],
            """SELECT d.diagnosis_id,
                   DATE_FORMAT(d.diagnosed_date,'%d %b %Y'),
                   CONCAT(p.first_name,' ',p.last_name),
                   d.diagnosis_code, d.description, d.severity, a.status
               FROM Diagnosis d
               JOIN Appointment a ON d.appointment_id=a.appointment_id
               JOIN Patient p ON a.patient_id=p.patient_id
               ORDER BY d.diagnosed_date DESC, d.diagnosis_id DESC""",
            actions=[
                ("➕  Add",    self.open_diagnosis_form),
                ("✏️  Edit",   lambda: self.open_selected_record("Edit Diagnosis", self.open_diagnosis_form_edit)),
                ("🗑  Delete", lambda: self._delete_record("Diagnosis","diagnosis_id","Diagnosis",self.show_diagnoses)),
            ],
            filter_column="Severity",
            filter_options=["All", "Mild", "Moderate", "Severe"],
        )

    def show_prescriptions(self):
        self.show_table_page(
            "Prescriptions", "Prescriptions", "Medication orders with dosage, frequency, and treatment duration.", "💊",
            [("ID",70,"center"),("Date",120,"w"),("Patient",200,"w"),("Medication",220,"w"),
             ("Dosage",120,"w"),("Frequency",175,"w"),("Days",80,"center")],
            """SELECT pr.prescription_id,
                   DATE_FORMAT(pr.prescribed_date,'%d %b %Y'),
                   CONCAT(p.first_name,' ',p.last_name),
                   m.medication_name, pr.dosage, pr.frequency,
                   CONCAT(pr.duration_days,' days')
               FROM Prescription pr
               JOIN Diagnosis d ON pr.diagnosis_id=d.diagnosis_id
               JOIN Appointment a ON d.appointment_id=a.appointment_id
               JOIN Patient p ON a.patient_id=p.patient_id
               JOIN Medication m ON pr.medication_id=m.medication_id
               ORDER BY pr.prescribed_date DESC, pr.prescription_id DESC""",
            actions=[
                ("➕  Add",    self.open_prescription_form),
                ("🗑  Delete", lambda: self._delete_record("Prescription","prescription_id","Prescription",self.show_prescriptions)),
            ],
        )

    def show_medications(self):
        self.show_table_page(
            "Medications", "Medications", "Medication inventory with unit type and available stock.", "🧴",
            [("ID",70,"center"),("Medication",250,"w"),("Unit",110,"center"),
             ("Stock",100,"center"),("Description",400,"w")],
            """SELECT medication_id, medication_name, unit, stock_quantity, IFNULL(description,'-')
               FROM Medication ORDER BY medication_name""",
            actions=[
                ("➕  Add",     self.open_medication_form),
                ("✏️  Edit",    lambda: self.open_selected_record("Edit Medication", self.open_medication_form_edit)),
                ("📦  Restock", self.open_restock_form),
                ("🗑  Delete",  lambda: self._delete_record("Medication","medication_id","Medication",self.show_medications)),
            ],
        )

    def show_bills(self):
        self.show_table_page(
            "Billing", "Billing", "Patient billing records with collected and outstanding balances.", "💰",
            [("ID",70,"center"),("Patient",200,"w"),("Bill Date",120,"w"),
             ("Total",130,"e"),("Paid",130,"e"),("Balance",130,"e"),("Status",120,"center")],
            """SELECT b.bill_id, CONCAT(p.first_name,' ',p.last_name),
                   DATE_FORMAT(b.bill_date,'%d %b %Y'),
                   CONCAT('Le ',FORMAT(b.total_amount,0)),
                   CONCAT('Le ',FORMAT(b.amount_paid,0)),
                   CONCAT('Le ',FORMAT(b.total_amount-b.amount_paid,0)),
                   b.payment_status
               FROM Bill b JOIN Patient p ON b.patient_id=p.patient_id
               ORDER BY b.bill_date DESC, b.bill_id DESC""",
            actions=[
                ("➕  Create Bill",    self.open_bill_form),
                ("💳  Record Payment", self.open_payment_form),
                ("🗑  Delete",         lambda: self._delete_record("Bill","bill_id","Bill",self.show_bills)),
            ],
            filter_column="Status",
            filter_options=["All", "Unpaid", "Partial", "Paid"],
        )

    # ─── Reports ──────────────────────────────────────────────────────────────
    def show_reports(self):
        self._set_active_nav("Reports")
        container = self._create_page_container()
        container.grid_rowconfigure(1, weight=1)
        self._page_header(container, "Reports",
                          "Management summaries for revenue collection and clinical activity.", "📊")

        try:
            revenue_rows = fetch_all("""
                SELECT c.clinic_name, COUNT(DISTINCT a.appointment_id),
                    CONCAT('Le ',FORMAT(IFNULL(SUM(b.total_amount),0),0)),
                    CONCAT('Le ',FORMAT(IFNULL(SUM(b.amount_paid),0),0)),
                    CONCAT('Le ',FORMAT(IFNULL(SUM(b.total_amount-b.amount_paid),0),0))
                FROM Clinic c
                LEFT JOIN Appointment a ON c.clinic_id=a.clinic_id
                LEFT JOIN Bill b ON a.appointment_id=b.appointment_id
                GROUP BY c.clinic_id, c.clinic_name
                ORDER BY IFNULL(SUM(b.amount_paid),0) DESC""")

            diagnosis_rows = fetch_all("""
                SELECT diagnosis_code, description, COUNT(diagnosis_id),
                    SUM(CASE WHEN severity='Severe'   THEN 1 ELSE 0 END),
                    SUM(CASE WHEN severity='Moderate' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN severity='Mild'     THEN 1 ELSE 0 END)
                FROM Diagnosis
                GROUP BY diagnosis_code, description
                ORDER BY COUNT(diagnosis_id) DESC, diagnosis_code""")

            outstanding_rows = fetch_all("""
                SELECT CONCAT(p.first_name,' ',p.last_name), p.phone,
                    CONCAT('Le ',FORMAT(SUM(b.total_amount-b.amount_paid),0)),
                    GROUP_CONCAT(DISTINCT b.payment_status ORDER BY b.payment_status SEPARATOR ', ')
                FROM Patient p
                JOIN Bill b ON p.patient_id=b.patient_id
                WHERE b.total_amount>b.amount_paid
                GROUP BY p.patient_id,p.first_name,p.last_name,p.phone
                ORDER BY SUM(b.total_amount-b.amount_paid) DESC""")

            top_meds = fetch_all("""
                SELECT m.medication_name, COUNT(pr.prescription_id) AS cnt,
                    CONCAT(m.stock_quantity,' ',m.unit)
                FROM Medication m
                LEFT JOIN Prescription pr ON m.medication_id=pr.medication_id
                GROUP BY m.medication_id, m.medication_name, m.stock_quantity, m.unit
                ORDER BY cnt DESC LIMIT 10""")

        except mysql.connector.Error as error:
            self._show_database_error(container, error)
            return

        reports = ctk.CTkFrame(container, fg_color="transparent")
        reports.grid(row=1, column=0, sticky="nsew")
        reports.grid_columnconfigure((0, 1), weight=1, uniform="report")
        reports.grid_rowconfigure((0, 1), weight=1, uniform="report")

        self._report_panel(reports, "Revenue by Clinic",
            [("Clinic",220,"w"),("Visits",70,"center"),("Billed",120,"e"),
             ("Collected",120,"e"),("Outstanding",130,"e")],
            revenue_rows, 0, 0, columnspan=2)

        self._report_panel(reports, "Common Diagnoses",
            [("Code",85,"center"),("Description",300,"w"),("Cases",70,"center"),
             ("Severe",70,"center"),("Moderate",80,"center"),("Mild",70,"center")],
            diagnosis_rows, 1, 0)

        self._report_panel(reports, "Outstanding Balances",
            [("Patient",185,"w"),("Phone",135,"w"),("Balance",120,"e"),("Status",165,"w")],
            outstanding_rows, 1, 1)

        self.set_status("Reports loaded")

    def _report_panel(self, parent, title, columns, rows, row, column, columnspan=1):
        panel = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=10)
        panel.grid(row=row, column=column, columnspan=columnspan,
                   sticky="nsew", padx=6, pady=6)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(panel, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr, text=title, font=("Segoe UI", 15, "bold"),
                     text_color=TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(hdr, text=f"{len(rows)} rows", font=("Segoe UI", 11),
                     text_color=TEXT_DIM).grid(row=0, column=1, sticky="e")

        self.create_tree(panel, columns, rows, row=1, searchable=False)

    # ─── Generic table page ───────────────────────────────────────────────────
    def show_table_page(self, nav_name, title, subtitle, icon_or_columns,
                        columns_or_query, query_or_actions=None,
                        actions=None, filter_column=None, filter_options=None):
        """
        Overloaded: new signature includes icon as 4th arg.
        Old callers pass (nav_name, title, subtitle, columns, query, actions=…)
        New callers pass (nav_name, title, subtitle, icon, columns, query, actions=…)
        """
        # detect new signature
        if isinstance(icon_or_columns, str):
            icon    = icon_or_columns
            columns = columns_or_query
            query   = query_or_actions
        else:
            icon    = ""
            columns = icon_or_columns
            query   = columns_or_query
            actions = query_or_actions

        self._set_active_nav(nav_name)
        container = self._create_page_container()
        self._page_header(container, title, subtitle, icon)

        try:
            rows = fetch_all(query)
        except mysql.connector.Error as error:
            self._show_database_error(container, error)
            return

        self.current_sort_column         = None
        self.current_sort_reverse        = False
        self.current_filter_column_index = None
        if filter_column:
            headings = [col[0] for col in columns]
            if filter_column in headings:
                self.current_filter_column_index = headings.index(filter_column)

        # ── Controls bar ──────────────────────────────────────────────────────
        controls = ctk.CTkFrame(container, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        controls.grid_columnconfigure(0, weight=1)

        search = ctk.CTkEntry(controls, height=40,
                              placeholder_text="🔍  Search records  (Ctrl+F)",
                              border_width=1, border_color=CARD_BORDER,
                              fg_color=CARD_BG, text_color=TEXT_PRIMARY,
                              font=("Segoe UI", 13))
        search.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.current_search_entry = search

        col_idx = 1
        if filter_options:
            self.current_filter_var = ctk.StringVar(value=filter_options[0])
            ctk.CTkOptionMenu(controls, values=filter_options,
                              variable=self.current_filter_var,
                              width=130, height=40,
                              fg_color=CARD_BG, button_color="#334155",
                              button_hover_color="#475569",
                              command=lambda _: self.filter_rows(),
                              font=("Segoe UI", 13),
                              ).grid(row=0, column=col_idx, sticky="e", padx=(0, 8))
            col_idx += 1
        else:
            self.current_filter_var = None

        for label, callback in (actions or []):
            # Choose colour based on label prefix
            if "Delete" in label or "❌" in label or "Cancel" in label:
                fc, hc = "#7f1d1d", DANGER
            elif "➕" in label or "Schedule" in label or "Create" in label:
                fc, hc = ACCENT, ACCENT_HOVER
            elif "💳" in label or "Payment" in label:
                fc, hc = "#065f46", SUCCESS
            else:
                fc, hc = "#1e293b", "#334155"

            ctk.CTkButton(controls, text=label, width=150, height=40,
                          corner_radius=8, command=callback,
                          fg_color=fc, hover_color=hc,
                          font=("Segoe UI", 12, "bold"),
                          ).grid(row=0, column=col_idx, sticky="e", padx=(0, 6))
            col_idx += 1

        # Refresh + Export
        ctk.CTkButton(controls, text="🔄  Refresh", width=110, height=40,
                      corner_radius=8, fg_color="#1e293b", hover_color="#334155",
                      command=lambda: self.show_table_page(
                          nav_name, title, subtitle, icon, columns, query,
                          actions=actions, filter_column=filter_column,
                          filter_options=filter_options),
                      font=("Segoe UI", 12, "bold"),
                      ).grid(row=0, column=col_idx, sticky="e", padx=(0, 6))
        col_idx += 1

        ctk.CTkButton(controls, text="📥  Export CSV", width=130, height=40,
                      corner_radius=8, fg_color="#0f766e", hover_color="#0d9488",
                      command=self.export_current_rows,
                      font=("Segoe UI", 12, "bold"),
                      ).grid(row=0, column=col_idx, sticky="e")

        # Table
        table_panel = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=10)
        table_panel.grid(row=2, column=0, sticky="nsew")
        table_panel.grid_columnconfigure(0, weight=1)
        table_panel.grid_rowconfigure(0, weight=1)

        self.create_tree(table_panel, columns, rows, row=0)
        search.bind("<KeyRelease>", lambda _e: self.filter_rows(search.get()))

        self.set_status(f"{len(rows)} records loaded")

    # ─── Treeview ─────────────────────────────────────────────────────────────
    def create_tree(self, parent, columns, rows, row, searchable=True):
        self._configure_tree_style()

        table_frame = ctk.CTkFrame(parent, fg_color="transparent")
        table_frame.grid(row=row, column=0, sticky="nsew", padx=12, pady=12)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        column_ids = [f"col_{i}" for i in range(len(columns))]
        tree = ttk.Treeview(table_frame, columns=column_ids,
                            show="headings", style="Pro.Treeview")

        for i, (col_id, (heading, width, anchor)) in enumerate(
                zip(column_ids, columns)):
            if searchable:
                tree.heading(col_id, text=heading,
                             command=lambda ci=i: self.sort_rows(ci))
            else:
                tree.heading(col_id, text=heading)
            tree.column(col_id, width=width, minwidth=60,
                        anchor=anchor, stretch=False)

        vsb = ttk.Scrollbar(table_frame, orient="vertical",   command=tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        count_label = ctk.CTkLabel(parent, text="",
                                   font=("Segoe UI", 11),
                                   text_color=TEXT_MUTED)
        count_label.grid(row=row + 1, column=0, sticky="w", padx=16, pady=(0, 10))

        if searchable:
            self.current_rows    = [tuple(self.clean_value(v) for v in r) for r in rows]
            self.current_columns = column_ids
            self.current_headings = [c[0] for c in columns]
            self.current_tree    = tree
            self.current_count_label = count_label
            self.filter_rows()
        else:
            self._populate_tree(tree, rows)
            count_label.configure(text=f"{len(rows)} records")

        return tree

    def _configure_tree_style(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Pro.Treeview",
                        background=CARD_BG, foreground=TEXT_PRIMARY,
                        fieldbackground=CARD_BG, bordercolor=CARD_BORDER,
                        borderwidth=0, rowheight=34,
                        font=("Segoe UI", 11))
        style.configure("Pro.Treeview.Heading",
                        background="#1e293b", foreground=TEXT_PRIMARY,
                        relief="flat", font=("Segoe UI", 11, "bold"), padding=8)
        style.map("Pro.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "#ffffff")])

    def sort_rows(self, column_index):
        if self.current_sort_column == column_index:
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            self.current_sort_column  = column_index
            self.current_sort_reverse = False
        self.filter_rows()

    def filter_rows(self, term=None):
        if term is None and self.current_search_entry:
            term = self.current_search_entry.get()

        normalized = (term or "").strip().lower()
        rows = (
            [r for r in self.current_rows
             if normalized in " ".join(str(v).lower() for v in r)]
            if normalized else self.current_rows
        )

        if self.current_filter_var and self.current_filter_column_index is not None:
            sel = self.current_filter_var.get()
            if sel != "All":
                rows = [r for r in rows
                        if str(r[self.current_filter_column_index]).lower() == sel.lower()]

        if self.current_sort_column is not None:
            rows = sorted(rows,
                          key=lambda r: self._sort_key(r[self.current_sort_column]),
                          reverse=self.current_sort_reverse)

        self.current_visible_rows = rows
        self._populate_tree(self.current_tree, rows)
        if self.current_count_label:
            self.current_count_label.configure(
                text=f"{len(rows):,} of {len(self.current_rows):,} records")

    def _populate_tree(self, tree, rows):
        for item in tree.get_children():
            tree.delete(item)

        STATUS_TAGS = {
            "completed": "tag_green", "paid": "tag_green",
            "scheduled": "tag_blue",
            "cancelled": "tag_red",   "unpaid": "tag_red",
            "partial":   "tag_amber",
            "severe":    "tag_red",
            "moderate":  "tag_amber",
            "mild":      "tag_green",
        }

        for index, row in enumerate(rows):
            base_tag = "even" if index % 2 == 0 else "odd"
            row_vals = [self.clean_value(v) for v in row]
            status_tag = None
            for val in row_vals:
                low = str(val).lower()
                if low in STATUS_TAGS:
                    status_tag = STATUS_TAGS[low]
                    break
            tags = (base_tag,) + ((status_tag,) if status_tag else ())
            tree.insert("", "end", values=row_vals, tags=tags)

        tree.tag_configure("even",      background=CARD_BG)
        tree.tag_configure("odd",       background="#0e1826")
        tree.tag_configure("tag_green", foreground="#34d399")
        tree.tag_configure("tag_red",   foreground="#f87171")
        tree.tag_configure("tag_amber", foreground="#fbbf24")
        tree.tag_configure("tag_blue",  foreground="#60a5fa")

    def _sort_key(self, value):
        text = self.clean_value(value).replace("Le ", "").replace(",", "").strip()
        try:
            return (0, float(text))
        except ValueError:
            return (1, text.lower())

    # ─── Export ───────────────────────────────────────────────────────────────
    def export_current_rows(self):
        if not self.current_visible_rows:
            self.toast("No visible records to export.", "warning")
            return
        path = filedialog.asksaveasfilename(
            title="Export records", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(self.current_headings)
            w.writerows(self.current_visible_rows)
        logger.info("Exported %s rows to %s", len(self.current_visible_rows), path)
        self.toast(f"Exported {len(self.current_visible_rows):,} records.", "success")

    # ─── Generic delete ───────────────────────────────────────────────────────
    def _delete_record(self, label, id_col, table, refresh_fn):
        record_id = self.get_selected_id(f"Delete {label}")
        if record_id is None:
            return
        if not messagebox.askyesno(
                f"Delete {label}",
                f"Permanently delete {label.lower()} #{record_id}?\n\nThis cannot be undone."):
            return
        try:
            result = execute(
                f"DELETE FROM {table} WHERE {id_col} = %s", (record_id,))
            if result["rowcount"]:
                logger.info("Deleted %s id=%s", table, record_id)
                self.toast(f"{label} #{record_id} deleted.", "success")
                refresh_fn()
            else:
                self.toast("Record not found or already removed.", "warning")
        except mysql.connector.Error as error:
            self.toast(f"Cannot delete: {error}", "error")

    # ─── Record selection helpers ─────────────────────────────────────────────
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

    # ─── Modal builders ───────────────────────────────────────────────────────
    def create_modal(self, title, width=580, height=580):
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
        body = ctk.CTkScrollableFrame(modal, fg_color="transparent",
                                      scrollbar_button_color="#334155")
        body.pack(fill="both", expand=True, padx=24, pady=20)
        body.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(body, text=title, font=("Segoe UI", 22, "bold"),
                     text_color=TEXT_PRIMARY).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(body, text=subtitle, font=("Segoe UI", 13),
                     text_color=TEXT_MUTED, wraplength=500,
                     justify="left").grid(row=1, column=0, sticky="w",
                                          pady=(4, 16))
        return body

    def form_entry(self, parent, label, row, placeholder="", value=""):
        ctk.CTkLabel(parent, text=label, font=("Segoe UI", 12, "bold"),
                     text_color=TEXT_MUTED).grid(row=row, column=0, sticky="w",
                                                  pady=(0, 3))
        entry = ctk.CTkEntry(parent, height=38, placeholder_text=placeholder,
                             fg_color=CARD_BG, border_color=CARD_BORDER,
                             text_color=TEXT_PRIMARY, font=("Segoe UI", 13))
        entry.grid(row=row + 1, column=0, sticky="ew", pady=(0, 10))
        if value:
            entry.insert(0, value)
        return entry

    def form_combo(self, parent, label, row, values):
        ctk.CTkLabel(parent, text=label, font=("Segoe UI", 12, "bold"),
                     text_color=TEXT_MUTED).grid(row=row, column=0, sticky="w",
                                                  pady=(0, 3))
        combo = ctk.CTkComboBox(parent, values=values, height=38,
                                fg_color=CARD_BG, border_color=CARD_BORDER,
                                button_color="#334155", button_hover_color="#475569",
                                text_color=TEXT_PRIMARY, font=("Segoe UI", 13),
                                state="readonly")
        combo.grid(row=row + 1, column=0, sticky="ew", pady=(0, 10))
        if values:
            combo.set(values[0])
        return combo

    def action_row(self, parent, row, save_label, save_command, cancel_command,
                   danger=False):
        buttons = ctk.CTkFrame(parent, fg_color="transparent")
        buttons.grid(row=row, column=0, sticky="ew", pady=(10, 0))
        buttons.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(buttons, text="Cancel", width=110, height=38,
                      fg_color="#334155", hover_color="#475569",
                      command=cancel_command,
                      font=("Segoe UI", 13, "bold")).grid(row=0, column=1,
                                                           padx=(0, 8))
        save_color = DANGER if danger else ACCENT
        save_hover = DANGER_HOVER if danger else ACCENT_HOVER
        ctk.CTkButton(buttons, text=save_label, width=160, height=38,
                      fg_color=save_color, hover_color=save_hover,
                      command=save_command,
                      font=("Segoe UI", 13, "bold")).grid(row=0, column=2)

    # ─── Date / parse helpers ─────────────────────────────────────────────────
    def date_value(self, value):
        if value is None:
            return ""
        if isinstance(value, (date, datetime)):
            return value.strftime("%Y-%m-%d")
        return str(value)

    def parse_required_date(self, value, field_name):
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"{field_name} must use YYYY-MM-DD format.")

    def parse_optional_date(self, value, field_name):
        return None if not value.strip() else self.parse_required_date(value, field_name)

    def parse_required_time(self, value, field_name):
        try:
            return datetime.strptime(value.strip(), "%H:%M").time()
        except ValueError:
            raise ValueError(f"{field_name} must use HH:MM format.")

    def parse_positive_int(self, value, field_name):
        try:
            n = int(value.strip())
        except ValueError:
            raise ValueError(f"{field_name} must be a whole number.")
        if n <= 0:
            raise ValueError(f"{field_name} must be greater than zero.")
        return n

    def parse_nonnegative_int(self, value, field_name):
        try:
            n = int(value.strip())
        except ValueError:
            raise ValueError(f"{field_name} must be a whole number.")
        if n < 0:
            raise ValueError(f"{field_name} cannot be negative.")
        return n

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

    def clean_value(self, value):
        return "-" if value is None else str(value)

    def money(self, value):
        return f"Le {float(value):,.0f}"

    # ─── Error panel ──────────────────────────────────────────────────────────
    def _show_database_error(self, container, error):
        panel = ctk.CTkFrame(container, fg_color=CARD_BG, corner_radius=10)
        panel.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(panel, text="⚠  Database connection unavailable",
                     font=("Segoe UI", 20, "bold"),
                     text_color=TEXT_PRIMARY).grid(row=0, column=0, sticky="w",
                                                   padx=22, pady=(22, 6))
        config = DatabaseConfig()
        ctk.CTkLabel(panel,
                     text=(f"Could not connect to '{config.database}' on "
                           f"{config.host}:{config.port}. "
                           "Ensure XAMPP MySQL/MariaDB is running."),
                     font=("Segoe UI", 13), text_color=TEXT_MUTED,
                     wraplength=720, justify="left").grid(row=1, column=0,
                                                          sticky="w", padx=22)
        ctk.CTkLabel(panel, text=str(error), font=("Segoe UI", 12),
                     text_color="#fca5a5", wraplength=720,
                     justify="left").grid(row=2, column=0, sticky="w",
                                          padx=22, pady=(0, 22))
        self.toast(f"DB error: {error}", "error")

    # ─────────────────────────────────────────────────────────────────────────
    # FORMS
    # ─────────────────────────────────────────────────────────────────────────

    # ── Patient ───────────────────────────────────────────────────────────────
    def open_patient_form(self, patient_id=None):
        record = None
        if patient_id is not None:
            try:
                record = fetch_one(
                    """SELECT first_name,last_name,date_of_birth,gender,address,
                              phone,blood_type,registration_date
                       FROM Patient WHERE patient_id=%s""", (patient_id,))
            except mysql.connector.Error as error:
                messagebox.showerror("Edit Patient", str(error)); return
            if not record:
                messagebox.showerror("Edit Patient", "Record not found."); return

        is_edit = patient_id is not None
        title = "Edit Patient" if is_edit else "Register Patient"
        modal = self.create_modal(title, 600, 660)
        body  = self.modal_body(modal, title,
            "Update patient demographics." if is_edit
            else "Create a new patient record.")

        first_name  = self.form_entry(body, "First Name *",  2,  value=record[0] if record else "")
        last_name   = self.form_entry(body, "Last Name *",   4,  value=record[1] if record else "")
        dob         = self.form_entry(body, "Date of Birth *", 6, "YYYY-MM-DD",
                                      self.date_value(record[2]) if record else "")
        gender      = self.form_combo(body, "Gender *",      8,  ["Female","Male","Other"])
        if record: gender.set(record[3])
        address     = self.form_entry(body, "Address *",     10, value=record[4] if record else "")
        phone       = self.form_entry(body, "Phone *",       12, value=record[5] if record else "")
        blood_type  = self.form_combo(body, "Blood Type",    14,
                                      ["None","O+","O-","A+","A-","B+","B-","AB+","AB-"])
        blood_type.set(record[6] if record and record[6] else "None")
        registered  = self.form_entry(body, "Registration Date *", 16, "YYYY-MM-DD",
                                      self.date_value(record[7]) if record
                                      else date.today().isoformat())

        def save():
            try:
                vals = {
                    "first_name":        first_name.get().strip(),
                    "last_name":         last_name.get().strip(),
                    "date_of_birth":     self.parse_required_date(dob.get(), "Date of Birth"),
                    "gender":            gender.get().strip(),
                    "address":           address.get().strip(),
                    "phone":             phone.get().strip(),
                    "blood_type":        None if blood_type.get()=="None" else blood_type.get(),
                    "registration_date": self.parse_required_date(registered.get(), "Registration Date"),
                }
                missing = [f.replace("_"," ").title()
                           for f in ("first_name","last_name","gender","address","phone")
                           if not vals[f]]
                if missing:
                    raise ValueError(f"Required: {', '.join(missing)}.")
                params = (vals["first_name"],vals["last_name"],vals["date_of_birth"],
                          vals["gender"],vals["address"],vals["phone"],
                          vals["blood_type"],vals["registration_date"])
                if not is_edit:
                    r = execute("""INSERT INTO Patient
                        (first_name,last_name,date_of_birth,gender,address,phone,blood_type,registration_date)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", params)
                    logger.info("Registered patient id=%s", r["lastrowid"])
                    self.toast("Patient registered successfully.", "success")
                else:
                    execute("""UPDATE Patient SET first_name=%s,last_name=%s,date_of_birth=%s,
                        gender=%s,address=%s,phone=%s,blood_type=%s,registration_date=%s
                        WHERE patient_id=%s""", params + (patient_id,))
                    self.toast("Patient updated.", "success")
                modal.destroy()
                self.show_patients()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror(title, str(error))

        self.action_row(body, 18, "Save Patient", save, modal.destroy)

    def open_patient_history(self):
        patient_id = self.get_selected_id("Visit History")
        if patient_id is None:
            return
        try:
            patient = fetch_one(
                "SELECT CONCAT(first_name,' ',last_name),phone,blood_type,gender "
                "FROM Patient WHERE patient_id=%s", (patient_id,))
            rows = fetch_all("""
                SELECT DATE_FORMAT(a.appointment_date,'%d %b %Y'),
                       TIME_FORMAT(a.appointment_time,'%H:%i'),
                       c.clinic_name, CONCAT(s.first_name,' ',s.last_name),
                       a.status, a.reason,
                       IFNULL(d.description,'-'), IFNULL(d.severity,'-'),
                       IFNULL(CONCAT('Le ',FORMAT(b.total_amount,0)),'-'),
                       IFNULL(b.payment_status,'-')
                FROM Appointment a
                JOIN Clinic c ON a.clinic_id=c.clinic_id
                JOIN Staff s ON a.staff_id=s.staff_id
                LEFT JOIN Diagnosis d ON a.appointment_id=d.appointment_id
                LEFT JOIN Bill b ON a.appointment_id=b.appointment_id
                WHERE a.patient_id=%s
                ORDER BY a.appointment_date DESC, a.appointment_time DESC""",
                (patient_id,))
        except mysql.connector.Error as error:
            messagebox.showerror("Visit History", str(error)); return
        if not patient:
            messagebox.showerror("Visit History", "Patient not found."); return

        modal = self.create_modal("Patient Visit History", 1080, 580)
        body  = self.modal_body(modal, patient[0],
                                f"📞 {patient[1]}  |  🩸 {patient[2] or 'Unknown'}  |  {patient[3]}  "
                                f"|  {len(rows)} visit(s)")
        body.grid_rowconfigure(2, weight=1)

        panel = ctk.CTkFrame(body, fg_color=CARD_BG, corner_radius=8)
        panel.grid(row=2, column=0, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)

        self.create_tree(panel, [
            ("Date",120,"w"),("Time",75,"center"),("Clinic",200,"w"),
            ("Staff",160,"w"),("Status",110,"center"),("Reason",220,"w"),
            ("Diagnosis",280,"w"),("Severity",95,"center"),
            ("Bill",110,"e"),("Payment",110,"center"),
        ], rows, row=0, searchable=False)

    # ── Clinic forms ──────────────────────────────────────────────────────────
    def open_clinic_form(self, clinic_id=None):
        record = None
        if clinic_id is not None:
            try:
                record = fetch_one(
                    "SELECT clinic_name,location,district,phone,email,established_date "
                    "FROM Clinic WHERE clinic_id=%s", (clinic_id,))
            except mysql.connector.Error as error:
                messagebox.showerror("Edit Clinic", str(error)); return
            if not record:
                messagebox.showerror("Edit Clinic", "Clinic not found."); return

        is_edit = clinic_id is not None
        title = "Edit Clinic" if is_edit else "Add Clinic"
        modal = self.create_modal(title, 580, 600)
        body  = self.modal_body(modal, title,
                                "Update clinic details." if is_edit
                                else "Create a new clinic location.")

        name        = self.form_entry(body, "Clinic Name *", 2,  value=record[0] if record else "")
        location    = self.form_entry(body, "Location *",    4,  value=record[1] if record else "")
        district    = self.form_entry(body, "District *",    6,  value=record[2] if record else "")
        phone       = self.form_entry(body, "Phone *",       8,  value=record[3] if record else "")
        email       = self.form_entry(body, "Email",         10, "Optional",
                                      record[4] if record and record[4] else "")
        established = self.form_entry(body, "Established Date", 12, "Optional YYYY-MM-DD",
                                      self.date_value(record[5]) if record else "")

        def save():
            try:
                vals = {
                    "clinic_name":      name.get().strip(),
                    "location":         location.get().strip(),
                    "district":         district.get().strip(),
                    "phone":            phone.get().strip(),
                    "email":            email.get().strip() or None,
                    "established_date": self.parse_optional_date(established.get(), "Established Date"),
                }
                missing = [f.replace("_"," ").title()
                           for f in ("clinic_name","location","district","phone")
                           if not vals[f]]
                if missing:
                    raise ValueError(f"Required: {', '.join(missing)}.")
                params = (vals["clinic_name"],vals["location"],vals["district"],
                          vals["phone"],vals["email"],vals["established_date"])
                if not is_edit:
                    r = execute("""INSERT INTO Clinic
                        (clinic_name,location,district,phone,email,established_date)
                        VALUES (%s,%s,%s,%s,%s,%s)""", params)
                    logger.info("Created clinic id=%s", r["lastrowid"])
                    self.toast("Clinic added.", "success")
                else:
                    execute("""UPDATE Clinic SET clinic_name=%s,location=%s,district=%s,
                        phone=%s,email=%s,established_date=%s WHERE clinic_id=%s""",
                            params + (clinic_id,))
                    self.toast("Clinic updated.", "success")
                modal.destroy()
                self.show_clinics()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror(title, str(error))

        self.action_row(body, 14, "Save Clinic", save, modal.destroy)

    def open_clinic_form_edit(self, clinic_id):
        self.open_clinic_form(clinic_id)

    # ── Staff forms ───────────────────────────────────────────────────────────
    def open_staff_form(self, staff_id=None):
        try:
            clinics = fetch_all("SELECT clinic_id,clinic_name FROM Clinic ORDER BY clinic_name")
        except mysql.connector.Error as error:
            messagebox.showerror("Staff", str(error)); return
        if not clinics:
            messagebox.showinfo("Staff", "Add a clinic before adding staff."); return

        record = None
        if staff_id is not None:
            try:
                record = fetch_one(
                    """SELECT clinic_id,first_name,last_name,role,gender,phone,email,hire_date
                       FROM Staff WHERE staff_id=%s""", (staff_id,))
            except mysql.connector.Error as error:
                messagebox.showerror("Edit Staff", str(error)); return
            if not record:
                messagebox.showerror("Edit Staff", "Record not found."); return

        is_edit = staff_id is not None
        title = "Edit Staff" if is_edit else "Add Staff"
        modal = self.create_modal(title, 600, 700)
        body  = self.modal_body(modal, title,
                                "Update staff details." if is_edit
                                else "Create a staff record and assign to a clinic.")

        clinic_values = [f"{cid} - {n}" for cid, n in clinics]
        clinic_combo  = self.form_combo(body, "Clinic *",     2, clinic_values)
        if record:
            for v in clinic_values:
                if v.startswith(f"{record[0]} - "):
                    clinic_combo.set(v); break

        first_name  = self.form_entry(body, "First Name *", 4, value=record[1] if record else "")
        last_name   = self.form_entry(body, "Last Name *",  6, value=record[2] if record else "")
        role        = self.form_entry(body, "Role *",       8, "Doctor, Nurse, Receptionist",
                                      record[3] if record else "")
        gender      = self.form_combo(body, "Gender *",     10, ["Female","Male","Other"])
        if record: gender.set(record[4])
        phone       = self.form_entry(body, "Phone *",      12, value=record[5] if record else "")
        email       = self.form_entry(body, "Email",        14, "Optional",
                                      record[6] if record and record[6] else "")
        hire_date   = self.form_entry(body, "Hire Date *",  16, "YYYY-MM-DD",
                                      self.date_value(record[7]) if record
                                      else date.today().isoformat())

        def save():
            try:
                vals = {
                    "clinic_id":  self.selected_option_id(clinic_combo.get()),
                    "first_name": first_name.get().strip(),
                    "last_name":  last_name.get().strip(),
                    "role":       role.get().strip(),
                    "gender":     gender.get().strip(),
                    "phone":      phone.get().strip(),
                    "email":      email.get().strip() or None,
                    "hire_date":  self.parse_required_date(hire_date.get(), "Hire Date"),
                }
                missing = [f.replace("_"," ").title()
                           for f in ("first_name","last_name","role","gender","phone")
                           if not vals[f]]
                if missing:
                    raise ValueError(f"Required: {', '.join(missing)}.")
                params = (vals["clinic_id"],vals["first_name"],vals["last_name"],
                          vals["role"],vals["gender"],vals["phone"],
                          vals["email"],vals["hire_date"])
                if not is_edit:
                    r = execute("""INSERT INTO Staff
                        (clinic_id,first_name,last_name,role,gender,phone,email,hire_date)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""", params)
                    logger.info("Created staff id=%s", r["lastrowid"])
                    self.toast("Staff member added.", "success")
                else:
                    execute("""UPDATE Staff SET clinic_id=%s,first_name=%s,last_name=%s,
                        role=%s,gender=%s,phone=%s,email=%s,hire_date=%s WHERE staff_id=%s""",
                            params + (staff_id,))
                    self.toast("Staff updated.", "success")
                modal.destroy()
                self.show_staff()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror(title, str(error))

        self.action_row(body, 18, "Save Staff", save, modal.destroy)

    def open_staff_form_edit(self, staff_id):
        self.open_staff_form(staff_id)

    # ── Appointment forms ─────────────────────────────────────────────────────
    def open_appointment_form(self, appointment_id=None):
        try:
            patients = fetch_all(
                "SELECT patient_id,CONCAT(first_name,' ',last_name) FROM Patient ORDER BY last_name,first_name")
            staff    = fetch_all(
                "SELECT staff_id,CONCAT(first_name,' ',last_name),role FROM Staff ORDER BY last_name,first_name")
            clinics  = fetch_all("SELECT clinic_id,clinic_name FROM Clinic ORDER BY clinic_name")
        except mysql.connector.Error as error:
            messagebox.showerror("Appointment", str(error)); return
        if not patients or not staff or not clinics:
            messagebox.showinfo("Appointment", "Patients, staff, and clinics are required."); return

        record = None
        if appointment_id is not None:
            try:
                record = fetch_one(
                    """SELECT patient_id,staff_id,clinic_id,appointment_date,
                              appointment_time,reason,status
                       FROM Appointment WHERE appointment_id=%s""", (appointment_id,))
            except mysql.connector.Error as error:
                messagebox.showerror("Edit Appointment", str(error)); return

        is_edit = appointment_id is not None
        title   = "Edit Appointment" if is_edit else "Schedule Appointment"
        modal   = self.create_modal(title, 600, 640)
        body    = self.modal_body(modal, title,
                                  "Update appointment details." if is_edit
                                  else "Create a new clinic visit.")

        patient_vals = [f"{pid} - {n}" for pid, n in patients]
        staff_vals   = [f"{sid} - {n} ({r})" for sid, n, r in staff]
        clinic_vals  = [f"{cid} - {n}" for cid, n in clinics]

        patient_combo = self.form_combo(body, "Patient *",  2, patient_vals)
        staff_combo   = self.form_combo(body, "Staff *",    4, staff_vals)
        clinic_combo  = self.form_combo(body, "Clinic *",   6, clinic_vals)
        appt_date     = self.form_entry(body, "Date *",     8, "YYYY-MM-DD",
                                        self.date_value(record[3]) if record else date.today().isoformat())
        appt_time     = self.form_entry(body, "Time *",     10, "HH:MM",
                                        str(record[4])[:5] if record else "09:00")
        reason        = self.form_entry(body, "Reason *",   12,
                                        value=record[5] if record else "")
        status_combo  = self.form_combo(body, "Status *",   14,
                                        ["Scheduled","Completed","Cancelled"])
        if record:
            for combo, id_val, vals in (
                    (patient_combo, record[0], patient_vals),
                    (staff_combo,   record[1], staff_vals),
                    (clinic_combo,  record[2], clinic_vals)):
                for v in vals:
                    if v.startswith(f"{id_val} - "):
                        combo.set(v); break
            status_combo.set(record[6])

        def save():
            try:
                appt_reason = reason.get().strip()
                if not appt_reason:
                    raise ValueError("Reason is required.")
                params = (
                    self.selected_option_id(patient_combo.get()),
                    self.selected_option_id(staff_combo.get()),
                    self.selected_option_id(clinic_combo.get()),
                    self.parse_required_date(appt_date.get(), "Date"),
                    self.parse_required_time(appt_time.get(), "Time"),
                    appt_reason, status_combo.get())
                if not is_edit:
                    r = execute("""INSERT INTO Appointment
                        (patient_id,staff_id,clinic_id,appointment_date,appointment_time,reason,status)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)""", params)
                    logger.info("Scheduled appointment id=%s", r["lastrowid"])
                    self.toast("Appointment scheduled.", "success")
                else:
                    execute("""UPDATE Appointment SET patient_id=%s,staff_id=%s,clinic_id=%s,
                        appointment_date=%s,appointment_time=%s,reason=%s,status=%s
                        WHERE appointment_id=%s""", params + (appointment_id,))
                    self.toast("Appointment updated.", "success")
                modal.destroy()
                self.show_appointments()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror(title, str(error))

        self.action_row(body, 16, "Save Appointment", save, modal.destroy)

    def open_appointment_form_edit(self, appointment_id):
        self.open_appointment_form(appointment_id)

    def update_selected_appointment_status(self, status):
        appt_id = self.get_selected_id("Appointment Status")
        if appt_id is None:
            return
        if status == "Cancelled" and not messagebox.askyesno(
                "Cancel Appointment", f"Cancel appointment #{appt_id}?"):
            return
        try:
            execute("UPDATE Appointment SET status=%s WHERE appointment_id=%s",
                    (status, appt_id))
            self.toast(f"Appointment marked as {status}.", "success")
            self.show_appointments()
        except mysql.connector.Error as error:
            self.toast(str(error), "error")

    # ── Diagnosis forms ───────────────────────────────────────────────────────
    def open_diagnosis_form(self, diagnosis_id=None):
        try:
            appointments = fetch_all("""
                SELECT a.appointment_id, CONCAT(p.first_name,' ',p.last_name),
                       DATE_FORMAT(a.appointment_date,'%d %b %Y'), a.status
                FROM Appointment a JOIN Patient p ON a.patient_id=p.patient_id
                ORDER BY a.appointment_date DESC, a.appointment_time DESC""")
        except mysql.connector.Error as error:
            messagebox.showerror("Diagnosis", str(error)); return
        if not appointments:
            messagebox.showinfo("Diagnosis", "Create an appointment first."); return

        record = None
        if diagnosis_id is not None:
            try:
                record = fetch_one(
                    """SELECT appointment_id,diagnosis_code,description,severity,diagnosed_date
                       FROM Diagnosis WHERE diagnosis_id=%s""", (diagnosis_id,))
            except mysql.connector.Error as error:
                messagebox.showerror("Edit Diagnosis", str(error)); return

        is_edit = diagnosis_id is not None
        title   = "Edit Diagnosis" if is_edit else "Add Diagnosis"
        modal   = self.create_modal(title, 640, 620)
        body    = self.modal_body(modal, title,
                                  "Update diagnosis." if is_edit
                                  else "Record a diagnosis for an existing appointment.")

        appt_vals = [f"{aid} - {p} | {d} | {s}"
                     for aid, p, d, s in appointments]
        appt_combo    = self.form_combo(body, "Appointment *", 2, appt_vals)
        if record:
            for v in appt_vals:
                if v.startswith(f"{record[0]} - "):
                    appt_combo.set(v); break

        code        = self.form_entry(body, "Diagnosis Code *", 4, "Example: B54",
                                      record[1] if record else "")
        description = self.form_entry(body, "Description *",   6,
                                      value=record[2] if record else "")
        severity    = self.form_combo(body, "Severity *",       8,
                                      ["Mild","Moderate","Severe"])
        if record: severity.set(record[3])
        dx_date     = self.form_entry(body, "Diagnosed Date *", 10, "YYYY-MM-DD",
                                      self.date_value(record[4]) if record
                                      else date.today().isoformat())

        def save():
            try:
                dx_code = code.get().strip()
                dx_desc = description.get().strip()
                if not dx_code or not dx_desc:
                    raise ValueError("Code and description are required.")
                params = (self.selected_option_id(appt_combo.get()),
                          dx_code, dx_desc, severity.get(),
                          self.parse_required_date(dx_date.get(), "Diagnosed Date"))
                if not is_edit:
                    r = execute("""INSERT INTO Diagnosis
                        (appointment_id,diagnosis_code,description,severity,diagnosed_date)
                        VALUES (%s,%s,%s,%s,%s)""", params)
                    logger.info("Created diagnosis id=%s", r["lastrowid"])
                    self.toast("Diagnosis added.", "success")
                else:
                    execute("""UPDATE Diagnosis SET appointment_id=%s,diagnosis_code=%s,
                        description=%s,severity=%s,diagnosed_date=%s WHERE diagnosis_id=%s""",
                            params + (diagnosis_id,))
                    self.toast("Diagnosis updated.", "success")
                modal.destroy()
                self.show_diagnoses()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror(title, str(error))

        self.action_row(body, 12, "Save Diagnosis", save, modal.destroy)

    def open_diagnosis_form_edit(self, diagnosis_id):
        self.open_diagnosis_form(diagnosis_id)

    # ── Prescription form ─────────────────────────────────────────────────────
    def open_prescription_form(self):
        try:
            diagnoses   = fetch_all("""
                SELECT d.diagnosis_id, d.diagnosis_code,
                       CONCAT(p.first_name,' ',p.last_name),
                       DATE_FORMAT(d.diagnosed_date,'%d %b %Y')
                FROM Diagnosis d
                JOIN Appointment a ON d.appointment_id=a.appointment_id
                JOIN Patient p ON a.patient_id=p.patient_id
                ORDER BY d.diagnosed_date DESC, d.diagnosis_id DESC""")
            medications = fetch_all(
                "SELECT medication_id,medication_name FROM Medication ORDER BY medication_name")
        except mysql.connector.Error as error:
            messagebox.showerror("Prescription", str(error)); return
        if not diagnoses:
            messagebox.showinfo("Prescription", "Add a diagnosis first."); return
        if not medications:
            messagebox.showinfo("Prescription", "Add a medication first."); return

        modal = self.create_modal("Add Prescription", 660, 680)
        body  = self.modal_body(modal, "Add Prescription",
                                "Create a prescription linked to a diagnosis and medication.")

        diag_vals = [f"{did} - {patient} | {code} | {dx_date}"
                     for did, code, patient, dx_date in diagnoses]
        med_vals  = [f"{mid} - {n}" for mid, n in medications]

        diagnosis   = self.form_combo(body, "Diagnosis *",       2, diag_vals)
        medication  = self.form_combo(body, "Medication *",      4, med_vals)
        dosage      = self.form_entry(body, "Dosage *",          6, "Example: 500mg")
        frequency   = self.form_entry(body, "Frequency *",       8, "Example: Twice daily")
        duration    = self.form_entry(body, "Duration (Days) *", 10, "Example: 7")
        px_date     = self.form_entry(body, "Prescribed Date *", 12, "YYYY-MM-DD",
                                      date.today().isoformat())

        def save():
            try:
                if not dosage.get().strip() or not frequency.get().strip():
                    raise ValueError("Dosage and frequency are required.")
                r = execute("""INSERT INTO Prescription
                    (diagnosis_id,medication_id,dosage,frequency,duration_days,prescribed_date)
                    VALUES (%s,%s,%s,%s,%s,%s)""", (
                    self.selected_option_id(diagnosis.get()),
                    self.selected_option_id(medication.get()),
                    dosage.get().strip(), frequency.get().strip(),
                    self.parse_positive_int(duration.get(), "Duration Days"),
                    self.parse_required_date(px_date.get(), "Prescribed Date")))
                logger.info("Created prescription id=%s", r["lastrowid"])
                self.toast("Prescription added.", "success")
                modal.destroy()
                self.show_prescriptions()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror("Add Prescription", str(error))

        self.action_row(body, 14, "Save Prescription", save, modal.destroy)

    # ── Medication forms ──────────────────────────────────────────────────────
    def open_medication_form(self, medication_id=None):
        record = None
        if medication_id is not None:
            try:
                record = fetch_one(
                    "SELECT medication_name,description,unit,stock_quantity "
                    "FROM Medication WHERE medication_id=%s", (medication_id,))
            except mysql.connector.Error as error:
                messagebox.showerror("Edit Medication", str(error)); return

        is_edit = medication_id is not None
        title   = "Edit Medication" if is_edit else "Add Medication"
        modal   = self.create_modal(title, 580, 540)
        body    = self.modal_body(modal, title,
                                  "Update medication record." if is_edit
                                  else "Create a medication inventory record.")

        name        = self.form_entry(body, "Medication Name *", 2,
                                      value=record[0] if record else "")
        unit        = self.form_entry(body, "Unit *",            4, "tablet, capsule, ml",
                                      record[2] if record else "")
        stock       = self.form_entry(body, "Stock Quantity *",  6, "Example: 100",
                                      str(record[3]) if record else "")
        description = self.form_entry(body, "Description",       8, "Optional",
                                      record[1] if record and record[1] else "")

        def save():
            try:
                med_name = name.get().strip()
                med_unit = unit.get().strip()
                if not med_name or not med_unit:
                    raise ValueError("Name and unit are required.")
                params = (med_name, description.get().strip() or None,
                          med_unit,
                          self.parse_nonnegative_int(stock.get(), "Stock Quantity"))
                if not is_edit:
                    r = execute("""INSERT INTO Medication
                        (medication_name,description,unit,stock_quantity)
                        VALUES (%s,%s,%s,%s)""", params)
                    logger.info("Created medication id=%s", r["lastrowid"])
                    self.toast("Medication added.", "success")
                else:
                    execute("""UPDATE Medication SET medication_name=%s,description=%s,
                        unit=%s,stock_quantity=%s WHERE medication_id=%s""",
                            params + (medication_id,))
                    self.toast("Medication updated.", "success")
                modal.destroy()
                self.show_medications()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror(title, str(error))

        self.action_row(body, 10, "Save Medication", save, modal.destroy)

    def open_medication_form_edit(self, medication_id):
        self.open_medication_form(medication_id)

    def open_restock_form(self):
        selected_id = self.get_selected_id("Restock Medication", silent=True)
        try:
            medications = fetch_all(
                "SELECT medication_id,medication_name,stock_quantity FROM Medication ORDER BY medication_name")
        except mysql.connector.Error as error:
            messagebox.showerror("Restock", str(error)); return
        if not medications:
            messagebox.showinfo("Restock", "No medications available."); return

        med_vals = [f"{mid} - {n} (stock: {s})" for mid, n, s in medications]
        modal = self.create_modal("Restock Medication", 560, 380)
        body  = self.modal_body(modal, "Restock Medication",
                                "Add new stock to an existing medication record.")

        med_combo = self.form_combo(body, "Medication", 2, med_vals)
        if selected_id:
            for v in med_vals:
                if v.startswith(f"{selected_id} - "):
                    med_combo.set(v); break
        qty = self.form_entry(body, "Quantity to Add", 4, "Example: 100")

        def save():
            try:
                amount = self.parse_positive_int(qty.get(), "Quantity")
                execute("UPDATE Medication SET stock_quantity=stock_quantity+%s WHERE medication_id=%s",
                        (amount, self.selected_option_id(med_combo.get())))
                self.toast(f"+{amount} units restocked.", "success")
                modal.destroy()
                self.show_medications()
            except (ValueError, mysql.connector.Error) as error:
                messagebox.showerror("Restock", str(error))

        self.action_row(body, 6, "Save Stock", save, modal.destroy)

    # ── Billing forms ─────────────────────────────────────────────────────────
    def open_bill_form(self):
        try:
            appointments = fetch_all("""
                SELECT a.appointment_id, a.patient_id,
                       CONCAT(p.first_name,' ',p.last_name),
                       DATE_FORMAT(a.appointment_date,'%d %b %Y'), c.clinic_name
                FROM Appointment a
                JOIN Patient p ON a.patient_id=p.patient_id
                JOIN Clinic c ON a.clinic_id=c.clinic_id
                LEFT JOIN Bill b ON a.appointment_id=b.appointment_id
                WHERE b.bill_id IS NULL
                ORDER BY a.appointment_date DESC, a.appointment_time DESC""")
        except mysql.connector.Error as error:
            messagebox.showerror("Create Bill", str(error)); return
        if not appointments:
            messagebox.showinfo("Create Bill", "Every appointment already has a bill."); return

        appt_map = {}
        for aid, pid, patient, adate, clinic in appointments:
            label = f"{aid} - {patient} | {adate} | {clinic}"
            appt_map[label] = (aid, pid)

        modal = self.create_modal("Create Bill", 640, 540)
        body  = self.modal_body(modal, "Create Bill",
                                "Create a billing record for an unbilled appointment.")

        appt     = self.form_combo(body, "Appointment *",  2, list(appt_map))
        total    = self.form_entry(body, "Total Amount *", 4, "Example: 75000")
        paid     = self.form_entry(body, "Amount Paid",    6, "Example: 0", "0")
        bill_dt  = self.form_entry(body, "Bill Date *",    8, "YYYY-MM-DD",
                                   date.today().isoformat())

        def save():
            try:
                total_val = self.parse_decimal_amount(total.get(), "Total Amount")
                paid_val  = self.parse_decimal_amount(paid.get(), "Amount Paid")
                if total_val <= 0:
                    raise ValueError("Total must be greater than zero.")
                if paid_val > total_val:
                    raise ValueError("Paid cannot exceed total.")
                status = ("Paid" if paid_val == total_val
                          else "Partial" if paid_val > 0 else "Unpaid")
                appt_id, patient_id = appt_map[appt.get()]
                r = execute("""INSERT INTO Bill
                    (patient_id,appointment_id,total_amount,amount_paid,bill_date,payment_status)
                    VALUES (%s,%s,%s,%s,%s,%s)""",
                    (patient_id, appt_id, total_val, paid_val,
                     self.parse_required_date(bill_dt.get(), "Bill Date"), status))
                logger.info("Created bill id=%s", r["lastrowid"])
                self.toast("Bill created.", "success")
                modal.destroy()
                self.show_bills()
            except (ValueError, KeyError, mysql.connector.Error) as error:
                messagebox.showerror("Create Bill", str(error))

        self.action_row(body, 10, "Save Bill", save, modal.destroy)

    def open_payment_form(self):
        selected_id = self.get_selected_id("Record Payment", silent=True)
        try:
            bills = fetch_all("""
                SELECT b.bill_id, CONCAT(p.first_name,' ',p.last_name),
                       b.total_amount, b.amount_paid
                FROM Bill b JOIN Patient p ON b.patient_id=p.patient_id
                WHERE b.total_amount>b.amount_paid
                ORDER BY b.bill_date DESC, b.bill_id DESC""")
        except mysql.connector.Error as error:
            messagebox.showerror("Record Payment", str(error)); return
        if not bills:
            messagebox.showinfo("Record Payment", "No outstanding bills."); return

        bill_map = {}
        for bid, patient, total, paid in bills:
            balance = float(total) - float(paid)
            label = f"{bid} - {patient} | Balance {self.money(balance)}"
            bill_map[label] = (bid, float(total), float(paid))

        modal = self.create_modal("Record Payment", 580, 420)
        body  = self.modal_body(modal, "Record Payment",
                                "Apply a payment to an unpaid or partially paid bill.")

        bill_combo = self.form_combo(body, "Bill",            2, list(bill_map))
        if selected_id:
            for v in bill_map:
                if v.startswith(f"{selected_id} - "):
                    bill_combo.set(v); break
        amount = self.form_entry(body, "Payment Amount *",    4, "Example: 25000")

        def save():
            try:
                payment = float(amount.get().strip())
                if payment <= 0:
                    raise ValueError("Payment must be greater than zero.")
                bid, total, paid = bill_map[bill_combo.get()]
                new_paid = min(total, paid + payment)
                status   = "Paid" if new_paid >= total else "Partial"
                execute("UPDATE Bill SET amount_paid=%s,payment_status=%s WHERE bill_id=%s",
                        (new_paid, status, bid))
                self.toast(f"Payment of {self.money(payment)} recorded.", "success")
                modal.destroy()
                self.show_bills()
            except (ValueError, KeyError, mysql.connector.Error) as error:
                messagebox.showerror("Record Payment", str(error))

        self.action_row(body, 6, "Save Payment", save, modal.destroy)


if __name__ == "__main__":
    app = ClinicSystem()
    app.mainloop()