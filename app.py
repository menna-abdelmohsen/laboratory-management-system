# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime, date
from io import BytesIO
import base64
import hashlib
import json
import shutil
import sqlite3

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "laboratory_database.db"
BACKUP_DIR = BASE_DIR / "backups"
LOGO_PATH = BASE_DIR / "assets" / "seif_logo.png"

BRAND_BLUE = "#003B73"
BRAND_DARK = "#002B5B"
BRAND_LIGHT = "#F4F8FC"
SUCCESS_GREEN = "#2b8a3e"
DANGER_RED = "#c92a2a"
WARNING_ORANGE = "#f59f00"

SAMPLE_TYPES = [
    "دم كامل EDTA (Whole Blood - EDTA)",
    "دم كامل Citrate (Citrated Blood)",
    "دم كامل Heparin (Heparinized Blood)",
    "سيرم (Serum)",
    "بلازما EDTA (EDTA Plasma)",
    "بلازما Citrate (Citrate Plasma)",
    "بلازما Heparin (Heparin Plasma)",
    "دم شعيري (Capillary Blood)",
    "دم شرياني للغازات ABG (Arterial Blood)",
    "مزرعة دم (Blood Culture)",
    "بقعة دم جافة DBS (Dried Blood Spot)",
    "بول عشوائي (Random Urine)",
    "بول 24 ساعة (24h Urine)",
    "بول مزرعة (Urine Culture)",
    "براز (Stool)",
    "مسحة حلق (Throat Swab)",
    "مسحة أنف/بلعوم (Nasopharyngeal Swab)",
    "بلغم (Sputum)",
    "سائل نخاعي CSF", 
    "سائل جنبي Pleural Fluid",
    "سائل بريتوني Ascitic Fluid",
    "سائل زلالي Synovial Fluid",
    "سائل منوي Semen",
    "خزعة/نسيج Tissue Biopsy",
    "نخاع عظم Bone Marrow",
]

DEPARTMENTS = [
    "Hematology - أمراض الدم",
    "Clinical Chemistry - الكيمياء الإكلينيكية",
    "Coagulation - التجلط",
    "Immunology / Serology - المناعة والسيرولوجي",
    "Microbiology - الميكروبيولوجي",
    "Parasitology - الطفيليات",
    "Urinalysis - تحليل البول",
    "Stool Analysis - تحليل البراز",
    "Hormones - الهرمونات",
    "Tumor Markers - دلالات الأورام",
    "Molecular / PCR - البيولوجيا الجزيئية",
    "Histopathology - باثولوجي الأنسجة",
    "Cytology - السيتولوجي",
    "Blood Bank - بنك الدم",
    "Genetics - الوراثة",
    "Toxicology - السموم",
    "Allergy - الحساسية",
    "ABG / Electrolytes - غازات الدم والأملاح",
    "Therapeutic Drug Monitoring - متابعة مستوى الأدوية",
]

TESTS_BY_DEPARTMENT = {
    "Hematology - أمراض الدم": [
        "CBC", "ESR", "Reticulocyte Count", "Blood Film", "Malaria Parasite", "Sickling Test",
        "Hb Electrophoresis", "G6PD", "Osmotic Fragility", "Bone Marrow Aspirate"
    ],
    "Clinical Chemistry - الكيمياء الإكلينيكية": [
        "Fasting Blood Glucose", "Random Blood Glucose", "HbA1c", "Urea", "Creatinine", "Uric Acid",
        "ALT", "AST", "ALP", "GGT", "Total Bilirubin", "Direct Bilirubin", "Albumin", "Total Protein",
        "Cholesterol", "Triglycerides", "HDL", "LDL", "Calcium", "Phosphorus", "Magnesium", "Iron", "Ferritin", "TIBC", "CRP"
    ],
    "Coagulation - التجلط": ["PT", "INR", "aPTT", "Bleeding Time", "Clotting Time", "D-Dimer", "Fibrinogen"],
    "Immunology / Serology - المناعة والسيرولوجي": [
        "HBsAg", "Anti-HBs", "Anti-HCV", "HIV Ag/Ab", "Widal", "Brucella", "ASOT", "RF", "ANA", "Anti-dsDNA", "C3", "C4", "IgE", "COVID-19 Antigen"
    ],
    "Microbiology - الميكروبيولوجي": [
        "Urine Culture", "Blood Culture", "Stool Culture", "Sputum Culture", "Throat Swab Culture", "Wound Swab Culture", "Antibiotic Sensitivity"
    ],
    "Parasitology - الطفيليات": ["Stool Ova & Parasites", "Occult Blood", "Giardia Antigen", "Entamoeba Antigen", "Pinworm Tape Test"],
    "Urinalysis - تحليل البول": ["Complete Urine Analysis", "Urine Protein/Creatinine Ratio", "Microalbuminuria", "Pregnancy Test", "24h Urine Protein"],
    "Stool Analysis - تحليل البراز": ["Complete Stool Analysis", "Stool Occult Blood", "Stool Reducing Substances", "Stool pH", "Fecal Calprotectin"],
    "Hormones - الهرمونات": ["TSH", "Free T3", "Free T4", "T3", "T4", "Prolactin", "FSH", "LH", "Estradiol", "Progesterone", "Testosterone", "Cortisol", "Insulin", "PTH", "Vitamin D"],
    "Tumor Markers - دلالات الأورام": ["AFP", "CEA", "CA 125", "CA 15-3", "CA 19-9", "PSA Total", "PSA Free", "Beta-hCG"],
    "Molecular / PCR - البيولوجيا الجزيئية": ["COVID-19 PCR", "HBV PCR", "HCV PCR", "HPV PCR", "TB PCR", "Genetic Mutation Test"],
    "Histopathology - باثولوجي الأنسجة": ["Histopathology Report", "Frozen Section", "Immunohistochemistry"],
    "Cytology - السيتولوجي": ["Pap Smear", "FNAC", "Fluid Cytology", "Sputum Cytology"],
    "Blood Bank - بنك الدم": ["Blood Group", "Rh Typing", "Cross Match", "Direct Coombs Test", "Indirect Coombs Test"],
    "Genetics - الوراثة": ["Karyotyping", "Thrombophilia Profile", "BRCA Test", "Carrier Screening"],
    "Toxicology - السموم": ["Drug Screen", "Alcohol Level", "Lead Level", "Lithium Level", "Digoxin Level"],
    "Allergy - الحساسية": ["Total IgE", "Specific IgE Panel", "Food Allergy Panel", "Inhalant Allergy Panel"],
    "ABG / Electrolytes - غازات الدم والأملاح": ["ABG", "Na", "K", "Cl", "Ionized Calcium", "Lactate", "Bicarbonate"],
    "Therapeutic Drug Monitoring - متابعة مستوى الأدوية": ["Vancomycin Level", "Gentamicin Level", "Valproic Acid Level", "Carbamazepine Level", "Phenytoin Level"],
}

STATUS_OPTIONS = ["Pending", "In progress", "Completed", "Cancelled"]
GENDER_OPTIONS = ["ذكر", "أنثى"]

st.set_page_config(page_title="SEIF Lab Management Pro", page_icon="🔬", layout="wide")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def column_exists(conn, table_name: str, column_name: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


def safe_add_column(conn, table_name: str, column_def: str):
    column_name = column_def.split()[0]
    if not column_exists(conn, table_name, column_name):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")


def init_database():
    BACKUP_DIR.mkdir(exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin',
                created_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                phone TEXT,
                age TEXT,
                gender TEXT,
                referring_doctor TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lab_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                patient_name TEXT NOT NULL,
                phone TEXT,
                age TEXT,
                gender TEXT,
                referring_doctor TEXT,
                sample_type TEXT NOT NULL,
                department TEXT NOT NULL,
                test_name TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                record_date TEXT,
                record_time TEXT,
                created_by TEXT,
                updated_by TEXT,
                updated_at TEXT,
                FOREIGN KEY(patient_id) REFERENCES patients(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                action TEXT NOT NULL,
                table_name TEXT,
                record_id TEXT,
                details TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        # Migration for older database versions
        for col in [
            "patient_id INTEGER", "phone TEXT", "age TEXT", "gender TEXT", "referring_doctor TEXT",
            "status TEXT DEFAULT 'Pending'", "created_by TEXT", "updated_by TEXT", "updated_at TEXT"
        ]:
            safe_add_column(conn, "lab_tests", col)
        safe_add_column(conn, "admins", "created_at TEXT")

        cur = conn.execute("SELECT COUNT(*) FROM admins")
        if cur.fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO admins (username, password, role, created_at) VALUES (?, ?, ?, ?)",
                ("admin", hash_password("admin123"), "superadmin", now_stamp()),
            )

        migrate_patients_from_old_records(conn)
        conn.commit()
    auto_backup_database()


def migrate_patients_from_old_records(conn):
    rows = conn.execute(
        """
        SELECT DISTINCT patient_name, phone, age, gender, referring_doctor
        FROM lab_tests
        WHERE patient_name IS NOT NULL AND TRIM(patient_name) <> ''
        """
    ).fetchall()
    for row in rows:
        existing = conn.execute(
            "SELECT id FROM patients WHERE patient_name = ? AND IFNULL(phone, '') = IFNULL(?, '') LIMIT 1",
            (row["patient_name"], row["phone"]),
        ).fetchone()
        if not existing:
            conn.execute(
                """
                INSERT INTO patients (patient_name, phone, age, gender, referring_doctor, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (row["patient_name"], row["phone"], row["age"], row["gender"], row["referring_doctor"], now_stamp(), now_stamp()),
            )


def now_stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_action(username: str, action: str, table_name: str = "", record_id: str = "", details: dict | str | None = None):
    if isinstance(details, dict):
        details = json.dumps(details, ensure_ascii=False)
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO audit_log (username, action, table_name, record_id, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (username, action, table_name, str(record_id or ""), details or "", now_stamp()),
        )
        conn.commit()


def authenticate(username: str, password: str):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT username, role FROM admins WHERE username = ? AND password = ?",
            (username.strip(), hash_password(password.strip())),
        ).fetchone()
        return row


def get_patient_suggestions(query: str, limit: int = 8) -> pd.DataFrame:
    query = query.strip()
    if not query:
        return pd.DataFrame(columns=["id", "patient_name", "phone", "age", "gender", "referring_doctor"])
    like = f"%{query}%"
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT id, patient_name, phone, age, gender, referring_doctor
            FROM patients
            WHERE patient_name LIKE ? OR phone LIKE ?
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            conn,
            params=(like, like, limit),
        )


def upsert_patient(patient_name, phone, age, gender, referring_doctor) -> int:
    patient_name = patient_name.strip()
    phone = phone.strip()
    with get_connection() as conn:
        row = None
        if phone:
            row = conn.execute("SELECT id FROM patients WHERE phone = ? LIMIT 1", (phone,)).fetchone()
        if not row:
            row = conn.execute("SELECT id FROM patients WHERE patient_name = ? LIMIT 1", (patient_name,)).fetchone()
        if row:
            patient_id = row["id"]
            conn.execute(
                """
                UPDATE patients
                SET patient_name=?, phone=?, age=?, gender=?, referring_doctor=?, updated_at=?
                WHERE id=?
                """,
                (patient_name, phone, age, gender, referring_doctor, now_stamp(), patient_id),
            )
        else:
            cur = conn.execute(
                """
                INSERT INTO patients (patient_name, phone, age, gender, referring_doctor, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (patient_name, phone, age, gender, referring_doctor, now_stamp(), now_stamp()),
            )
            patient_id = cur.lastrowid
        conn.commit()
        return patient_id


def insert_record(data: dict, username: str):
    patient_id = upsert_patient(data["patient_name"], data["phone"], data["age"], data["gender"], data["referring_doctor"])
    now = datetime.now()
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO lab_tests (
                patient_id, patient_name, phone, age, gender, referring_doctor,
                sample_type, department, test_name, status, record_date, record_time, created_by, updated_by, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id, data["patient_name"], data["phone"], data["age"], data["gender"], data["referring_doctor"],
                data["sample_type"], data["department"], data["test_name"], data["status"],
                now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), username, username, now_stamp(),
            ),
        )
        record_id = cur.lastrowid
        conn.commit()
    log_action(username, "CREATE", "lab_tests", record_id, data)
    auto_backup_database()


def update_record(record_id: int, data: dict, username: str):
    patient_id = upsert_patient(data["patient_name"], data["phone"], data["age"], data["gender"], data["referring_doctor"])
    with get_connection() as conn:
        old = conn.execute("SELECT * FROM lab_tests WHERE id = ?", (record_id,)).fetchone()
        conn.execute(
            """
            UPDATE lab_tests
            SET patient_id=?, patient_name=?, phone=?, age=?, gender=?, referring_doctor=?,
                sample_type=?, department=?, test_name=?, status=?, updated_by=?, updated_at=?
            WHERE id=?
            """,
            (
                patient_id, data["patient_name"], data["phone"], data["age"], data["gender"], data["referring_doctor"],
                data["sample_type"], data["department"], data["test_name"], data["status"], username, now_stamp(), record_id,
            ),
        )
        conn.commit()
    details = {"old": dict(old) if old else {}, "new": data}
    log_action(username, "UPDATE", "lab_tests", record_id, details)
    auto_backup_database()


def delete_record(record_id: int, username: str):
    with get_connection() as conn:
        old = conn.execute("SELECT * FROM lab_tests WHERE id = ?", (record_id,)).fetchone()
        conn.execute("DELETE FROM lab_tests WHERE id = ?", (record_id,))
        conn.commit()
    log_action(username, "DELETE", "lab_tests", record_id, dict(old) if old else {})
    auto_backup_database()


def load_records(search_text: str = "", status: str = "الكل", department: str = "الكل") -> pd.DataFrame:
    clauses = []
    params = []
    if search_text.strip():
        like = f"%{search_text.strip()}%"
        clauses.append("(patient_name LIKE ? OR phone LIKE ? OR test_name LIKE ? OR CAST(id AS TEXT) = ?)")
        params.extend([like, like, like, search_text.strip()])
    if status != "الكل":
        clauses.append("status = ?")
        params.append(status)
    if department != "الكل":
        clauses.append("department = ?")
        params.append(department)
    where_sql = " WHERE " + " AND ".join(clauses) if clauses else ""
    with get_connection() as conn:
        return pd.read_sql_query(
            f"""
            SELECT
                id AS 'رقم السجل',
                patient_name AS 'اسم المريض',
                phone AS 'الموبايل',
                age AS 'السن',
                gender AS 'النوع',
                referring_doctor AS 'الطبيب المحوّل',
                sample_type AS 'نوع العينة',
                department AS 'القسم',
                test_name AS 'الفحص',
                status AS 'الحالة',
                record_date AS 'تاريخ التسجيل',
                record_time AS 'وقت التسجيل',
                created_by AS 'أُضيف بواسطة',
                updated_by AS 'آخر تعديل بواسطة',
                updated_at AS 'آخر تعديل'
            FROM lab_tests
            {where_sql}
            ORDER BY id DESC
            """,
            conn,
            params=params,
        )


def load_record_by_id(record_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM lab_tests WHERE id = ?", (record_id,)).fetchone()
        return dict(row) if row else None


def load_admins() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query("SELECT id, username, role, created_at FROM admins ORDER BY id", conn)


def add_admin(username, password, role, actor):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO admins (username, password, role, created_at) VALUES (?, ?, ?, ?)",
            (username.strip(), hash_password(password.strip()), role, now_stamp()),
        )
        conn.commit()
    log_action(actor, "CREATE_ADMIN", "admins", username, {"role": role})


def delete_admin(admin_id, actor):
    with get_connection() as conn:
        row = conn.execute("SELECT username FROM admins WHERE id=?", (admin_id,)).fetchone()
        conn.execute("DELETE FROM admins WHERE id = ? AND username <> 'admin'", (admin_id,))
        conn.commit()
    log_action(actor, "DELETE_ADMIN", "admins", admin_id, {"username": row["username"] if row else ""})


def change_admin_password(admin_id, new_password, actor):
    with get_connection() as conn:
        conn.execute("UPDATE admins SET password = ? WHERE id = ?", (hash_password(new_password), admin_id))
        conn.commit()
    log_action(actor, "CHANGE_ADMIN_PASSWORD", "admins", admin_id, {})


def load_audit_log() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT id AS 'ID', username AS 'المستخدم', action AS 'الإجراء', table_name AS 'الجدول',
                   record_id AS 'رقم السجل', details AS 'التفاصيل', created_at AS 'التاريخ والوقت'
            FROM audit_log
            ORDER BY id DESC
            LIMIT 500
            """,
            conn,
        )


def auto_backup_database() -> Path | None:
    if not DB_PATH.exists():
        return None
    BACKUP_DIR.mkdir(exist_ok=True)
    today_name = f"laboratory_database_auto_{date.today().isoformat()}.db"
    dest = BACKUP_DIR / today_name
    if not dest.exists():
        shutil.copy2(DB_PATH, dest)
    return dest


def manual_backup(username: str) -> Path | None:
    if not DB_PATH.exists():
        return None
    BACKUP_DIR.mkdir(exist_ok=True)
    dest = BACKUP_DIR / f"laboratory_database_manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(DB_PATH, dest)
    log_action(username, "MANUAL_BACKUP", "database", dest.name, {})
    return dest


def dataframe_to_excel_bytes(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Lab Records")
    return output.getvalue()


def find_unicode_font():
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


def reshape_arabic(text: str) -> str:
    text = "" if text is None else str(text)
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def dataframe_to_pdf_bytes(df: pd.DataFrame, title: str = "SEIF Laboratory Report") -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    output = BytesIO()
    font_name = "Helvetica"
    font_path = find_unicode_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont("ArabicFont", font_path))
            font_name = "ArabicFont"
        except Exception:
            font_name = "Helvetica"

    doc = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    styles["Title"].fontName = font_name
    styles["BodyText"].fontName = font_name

    elements = []
    elements.append(Paragraph(reshape_arabic(title), styles["Title"]))
    elements.append(Paragraph(reshape_arabic(f"Export date: {now_stamp()}"), styles["BodyText"]))
    elements.append(Spacer(1, 12))

    export_cols = ["رقم السجل", "اسم المريض", "الموبايل", "الفحص", "القسم", "نوع العينة", "الحالة", "تاريخ التسجيل"]
    compact_df = df[[c for c in export_cols if c in df.columns]].copy().head(200)
    data = [[reshape_arabic(c) for c in compact_df.columns.tolist()]]
    for _, row in compact_df.iterrows():
        data.append([reshape_arabic(row.get(c, "")) for c in compact_df.columns.tolist()])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_BLUE)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(table)
    doc.build(elements)
    return output.getvalue()


def inject_css():
    st.markdown(
        f"""
        <style>
        html, body, [class*="css"] {{ direction: rtl; text-align: right; }}
        .main .block-container {{padding-top: 1rem; max-width: 1400px;}}
        section[data-testid="stSidebar"] {{direction: rtl; text-align: right;}}
        .seif-hero {{
            border: 1px solid #dbe4f0; border-radius: 22px; padding: 22px 26px;
            background: linear-gradient(135deg, #ffffff 0%, #f4f8fc 60%, #eef6ff 100%);
            box-shadow: 0 12px 32px rgba(0, 59, 115, 0.08); margin-bottom: 18px;
        }}
        .seif-title {{color:{BRAND_BLUE}; font-size:36px; font-weight:900; margin:0; line-height:1.35;}}
        .seif-subtitle {{color:#475569; font-size:17px; margin-top:6px;}}
        .soft-card {{
            border: 1px solid #e2e8f0; border-radius: 18px; padding: 18px;
            background: white; box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
        }}
        div.stButton > button:first-child, div.stDownloadButton > button:first-child {{
            border-radius: 12px; font-weight: 800; min-height: 44px;
        }}
        input, textarea, .stSelectbox, .stMultiSelect {{direction: rtl; text-align: right;}}
        [data-testid="stMetricValue"] {{direction:ltr; text-align:right;}}
        .small-note {{ color:#64748b; font-size:14px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def logo_as_base64():
    if not LOGO_PATH.exists():
        return ""
    return base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")


def render_header():
    logo64 = logo_as_base64()
    logo_html = f"<img src='data:image/png;base64,{logo64}' style='max-width:210px; margin-bottom:8px;'/>" if logo64 else ""
    st.markdown(
        f"""
        <div class="seif-hero">
            {logo_html}
            <div class="seif-title">نظام إدارة معمل التحاليل</div>
            <div class="seif-subtitle">Laboratory Management System — Developed by SEIF for Digital & Smart Solutions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def login_screen():
    logo64 = logo_as_base64()
    logo_html = f"<img src='data:image/png;base64,{logo64}' style='max-width:240px; display:block; margin:auto;'/>" if logo64 else ""
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown(logo_html, unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;color:#003B73'>Laboratory Management System</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#64748b'>Developed by SEIF for Digital & Smart Solutions</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("اسم المستخدم", placeholder="username")
            password = st.text_input("كلمة المرور", type="password", placeholder="password")
            submitted = st.form_submit_button("دخول 🔑", use_container_width=True)
        if submitted:
            row = authenticate(username, password)
            if row:
                st.session_state["logged_in"] = True
                st.session_state["username"] = row["username"]
                st.session_state["role"] = row["role"]
                log_action(row["username"], "LOGIN", "admins", row["username"], {})
                st.rerun()
            else:
                st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
        st.caption("بيانات التجربة الافتراضية: admin / admin123 — لا تظهر كـ placeholder داخل الخانات.")


def dashboard_page():
    df_all = load_records("")
    today = date.today().isoformat()
    today_count = int((df_all["تاريخ التسجيل"] == today).sum()) if not df_all.empty and "تاريخ التسجيل" in df_all else 0
    completed = int((df_all["الحالة"] == "Completed").sum()) if not df_all.empty and "الحالة" in df_all else 0
    pending = int((df_all["الحالة"] == "Pending").sum()) if not df_all.empty and "الحالة" in df_all else 0

    st.markdown("### 📊 لوحة التحكم")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("إجمالي الفحوصات", len(df_all))
    m2.metric("فحوصات اليوم", today_count)
    m3.metric("مكتملة", completed)
    m4.metric("قيد الانتظار", pending)

    if df_all.empty:
        st.info("لا توجد بيانات بعد. سجّلي أول فحص من صفحة تسجيل فحص جديد.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### عدد العينات حسب القسم")
        dept_counts = df_all.groupby("القسم").size().sort_values(ascending=False)
        st.bar_chart(dept_counts)
    with c2:
        st.markdown("#### حالة العينات")
        status_counts = df_all.groupby("الحالة").size().sort_values(ascending=False)
        st.bar_chart(status_counts)

    st.markdown("#### آخر 10 سجلات")
    st.dataframe(df_all.head(10), use_container_width=True, hide_index=True)


def record_form_page():
    st.markdown("### ➕ تسجيل فحص جديد")
    st.markdown("<div class='small-note'>ابدئي بكتابة أول حرف من اسم المريض أو رقم الموبايل؛ لو موجود قبل كده هتظهر اقتراحات فورًا.</div>", unsafe_allow_html=True)

    patient_query = st.text_input("بحث سريع عن مريض مسجل", placeholder="اكتبي أول اسم من اسم المريض أو رقم الموبايل")
    suggestions = get_patient_suggestions(patient_query) if patient_query else pd.DataFrame()
    selected_patient = None

    if not suggestions.empty:
        labels = [f"{r.patient_name} — {r.phone or 'بدون موبايل'} — ID:{r.id}" for r in suggestions.itertuples()]
        choice = st.selectbox("اقتراحات مرضى مسجلين", ["مريض جديد / عدم اختيار"] + labels)
        if choice != "مريض جديد / عدم اختيار":
            selected_patient = suggestions.iloc[labels.index(choice)].to_dict()
            st.success(f"تم اختيار بيانات: {selected_patient['patient_name']}")

    with st.form("insert_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        patient_name = c1.text_input("اسم المريض", value=(selected_patient or {}).get("patient_name", patient_query or ""))
        phone = c2.text_input("رقم موبايل المريض", value=(selected_patient or {}).get("phone") or "", placeholder="01xxxxxxxxx")
        c3, c4, c5 = st.columns(3)
        age = c3.text_input("السن", value=(selected_patient or {}).get("age") or "", placeholder="مثال: 35 سنة / 6 شهور")
        gender = c4.selectbox("النوع", GENDER_OPTIONS, index=GENDER_OPTIONS.index((selected_patient or {}).get("gender")) if (selected_patient or {}).get("gender") in GENDER_OPTIONS else 0)
        referring_doctor = c5.text_input("اسم الطبيب المحوّل", value=(selected_patient or {}).get("referring_doctor") or "")

        c6, c7 = st.columns(2)
        sample_type = c6.selectbox("نوع العينة", SAMPLE_TYPES)
        department = c7.selectbox("قسم التحليل المختص", DEPARTMENTS)

        tests = TESTS_BY_DEPARTMENT.get(department, []) + ["فحص آخر / كتابة يدويًا"]
        c8, c9 = st.columns(2)
        chosen_test = c8.selectbox("اسم الفحص المطلوب", tests)
        custom_test = c9.text_input("اكتبي اسم الفحص لو غير موجود", placeholder="يستخدم فقط عند اختيار فحص آخر")
        status = st.selectbox("حالة العينة", STATUS_OPTIONS)

        save_btn = st.form_submit_button("حفظ السجل الجديد ✅", use_container_width=True)

    if save_btn:
        final_test = custom_test.strip() if chosen_test == "فحص آخر / كتابة يدويًا" else chosen_test
        if not patient_name.strip() or not final_test.strip() or not phone.strip():
            st.warning("اسم المريض، رقم الموبايل، واسم الفحص مطلوبين عشان السجل يبقى كامل واحترافي.")
            return
        data = {
            "patient_name": patient_name.strip(), "phone": phone.strip(), "age": age.strip(), "gender": gender,
            "referring_doctor": referring_doctor.strip(), "sample_type": sample_type, "department": department,
            "test_name": final_test, "status": status,
        }
        insert_record(data, st.session_state.get("username", "unknown"))
        st.success("تم حفظ السجل بنجاح، وتم تحديث بيانات المريض والـ Audit Log والنسخة الاحتياطية.")
        st.rerun()


def records_page():
    st.markdown("### 📋 السجلات المسجلة")
    c1, c2, c3 = st.columns([2, 1, 1])
    search = c1.text_input("🔎 ابحث بالاسم أو رقم السجل أو الموبايل أو اسم الفحص", placeholder="مثال: أحمد / CBC / 010 / 15")
    status_filter = c2.selectbox("فلترة حسب الحالة", ["الكل"] + STATUS_OPTIONS)
    dept_filter = c3.selectbox("فلترة حسب القسم", ["الكل"] + DEPARTMENTS)
    df = load_records(search, status_filter, dept_filter)

    if df.empty:
        st.info("لا توجد سجلات مطابقة.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)
    st.markdown("### ✏️ تعديل السجل")
    selected_id = st.selectbox("اختاري رقم السجل", df["رقم السجل"].tolist())
    record = load_record_by_id(int(selected_id))
    if not record:
        st.error("السجل غير موجود.")
        return

    with st.form("edit_form"):
        c1, c2 = st.columns(2)
        patient_name = c1.text_input("اسم المريض", value=record.get("patient_name") or "")
        phone = c2.text_input("رقم الموبايل", value=record.get("phone") or "")
        c3, c4, c5 = st.columns(3)
        age = c3.text_input("السن", value=record.get("age") or "")
        gender = c4.selectbox("النوع", GENDER_OPTIONS, index=GENDER_OPTIONS.index(record.get("gender")) if record.get("gender") in GENDER_OPTIONS else 0)
        referring_doctor = c5.text_input("الطبيب المحوّل", value=record.get("referring_doctor") or "")

        c6, c7 = st.columns(2)
        sample_type = c6.selectbox("نوع العينة", SAMPLE_TYPES, index=SAMPLE_TYPES.index(record.get("sample_type")) if record.get("sample_type") in SAMPLE_TYPES else 0)
        department = c7.selectbox("القسم", DEPARTMENTS, index=DEPARTMENTS.index(record.get("department")) if record.get("department") in DEPARTMENTS else 0)
        test_options = TESTS_BY_DEPARTMENT.get(department, [])
        if record.get("test_name") not in test_options:
            test_options = [record.get("test_name") or ""] + test_options
        c8, c9 = st.columns(2)
        test_name = c8.selectbox("الفحص", test_options, index=0)
        status = c9.selectbox("الحالة", STATUS_OPTIONS, index=STATUS_OPTIONS.index(record.get("status")) if record.get("status") in STATUS_OPTIONS else 0)

        update_btn = st.form_submit_button("تحديث البيانات 🔄", use_container_width=True)

    if update_btn:
        data = {
            "patient_name": patient_name.strip(), "phone": phone.strip(), "age": age.strip(), "gender": gender,
            "referring_doctor": referring_doctor.strip(), "sample_type": sample_type, "department": department,
            "test_name": test_name.strip(), "status": status,
        }
        if not data["patient_name"] or not data["test_name"]:
            st.warning("اسم المريض واسم الفحص مطلوبين.")
            return
        update_record(int(selected_id), data, st.session_state.get("username", "unknown"))
        st.success("تم تحديث السجل وتسجيل العملية في Audit Log.")
        st.rerun()

    if st.session_state.get("role") == "superadmin":
        st.markdown("### 🗑 حذف السجل — Superadmin فقط")
        confirm = st.checkbox("أؤكد أنني أريد حذف السجل المحدد")
        if st.button("حذف السجل المحدد", type="primary", disabled=not confirm):
            delete_record(int(selected_id), st.session_state.get("username", "unknown"))
            st.success("تم حذف السجل وتسجيل العملية في Audit Log.")
            st.rerun()
    else:
        st.info("الحذف مقفول على حسابات Admin العادية. الحذف متاح للـ Superadmin فقط.")


def reports_page():
    st.markdown("### 📤 التقارير والتصدير")
    c1, c2, c3 = st.columns([2, 1, 1])
    search = c1.text_input("بحث داخل التقرير", placeholder="اسم / رقم / فحص / موبايل")
    status_filter = c2.selectbox("الحالة", ["الكل"] + STATUS_OPTIONS, key="report_status")
    dept_filter = c3.selectbox("القسم", ["الكل"] + DEPARTMENTS, key="report_dept")
    df = load_records(search, status_filter, dept_filter)
    st.dataframe(df, use_container_width=True, hide_index=True)

    if df.empty:
        st.info("لا توجد بيانات للتصدير.")
        return

    excel_bytes = dataframe_to_excel_bytes(df)
    st.download_button(
        "تحميل Excel 📊",
        data=excel_bytes,
        file_name=f"seif_lab_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    try:
        pdf_bytes = dataframe_to_pdf_bytes(df, "SEIF Laboratory Report")
        st.download_button(
            "تحميل PDF 📄",
            data=pdf_bytes,
            file_name=f"seif_lab_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as exc:
        st.warning("تصدير PDF يحتاج تثبيت مكتبات reportlab + arabic-reshaper + python-bidi. Excel يعمل بدون مشكلة بعد تثبيت requirements.")
        st.caption(str(exc))


def audit_page():
    st.markdown("### 🧾 Audit Log")
    st.markdown("كل إضافة أو تعديل أو حذف أو Backup بيتسجل هنا باسم المستخدم والتاريخ والوقت.")
    df = load_audit_log()
    st.dataframe(df, use_container_width=True, hide_index=True)


def backup_page():
    st.markdown("### 💾 Backup قاعدة البيانات")
    st.info("النظام يعمل Backup تلقائي مرة يوميًا، وكمان يعمل Backup بعد العمليات المهمة. ممكن تعملي Backup يدوي وتحميله.")
    auto_path = auto_backup_database()
    if auto_path:
        st.success(f"آخر Backup تلقائي اليوم: {auto_path.name}")

    if st.button("إنشاء Backup يدوي الآن", use_container_width=True):
        path = manual_backup(st.session_state.get("username", "unknown"))
        if path:
            st.success(f"تم إنشاء نسخة احتياطية: {path.name}")
            st.session_state["last_manual_backup"] = str(path)
            st.rerun()

    backup_files = sorted(BACKUP_DIR.glob("*.db"), reverse=True)
    if backup_files:
        selected = st.selectbox("اختاري Backup للتحميل", [p.name for p in backup_files])
        selected_path = BACKUP_DIR / selected
        st.download_button("تحميل ملف الـ Backup", selected_path.read_bytes(), file_name=selected_path.name, mime="application/octet-stream", use_container_width=True)
    else:
        st.warning("لا توجد نسخ احتياطية بعد.")


def admin_page():
    st.markdown("### ⚙ إدارة المسؤولين")
    if st.session_state.get("role") != "superadmin":
        st.error("هذه الصفحة متاحة للـ Superadmin فقط.")
        return
    admins_df = load_admins()
    st.dataframe(admins_df, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("إضافة مسؤول")
        with st.form("add_admin_form"):
            new_user = st.text_input("اسم المستخدم الجديد")
            new_pass = st.text_input("كلمة المرور", type="password")
            role = st.selectbox("الصلاحية", ["admin", "superadmin"])
            add_btn = st.form_submit_button("إضافة مسؤول")
        if add_btn:
            if new_user.strip() and new_pass.strip():
                try:
                    add_admin(new_user, new_pass, role, st.session_state.get("username", "unknown"))
                    st.success("تم إضافة المسؤول بنجاح.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("اسم المستخدم موجود مسبقًا.")
            else:
                st.warning("اكتبي اسم المستخدم وكلمة المرور.")

    with c2:
        st.subheader("تعديل/حذف مسؤول")
        if admins_df.empty:
            st.info("لا يوجد مسؤولون.")
            return
        chosen_admin = st.selectbox("اختاري ID المسؤول", admins_df["id"].tolist())
        new_password = st.text_input("كلمة مرور جديدة", type="password", key="admin_new_pass")
        if st.button("تغيير كلمة المرور", use_container_width=True):
            if new_password.strip():
                change_admin_password(chosen_admin, new_password, st.session_state.get("username", "unknown"))
                st.success("تم تغيير كلمة المرور.")
            else:
                st.warning("اكتبي كلمة المرور الجديدة.")
        chosen_row = admins_df[admins_df["id"] == chosen_admin].iloc[0]
        if chosen_row["username"] == "admin":
            st.info("لا يمكن حذف الحساب الرئيسي admin.")
        else:
            if st.button("حذف المسؤول", use_container_width=True):
                delete_admin(chosen_admin, st.session_state.get("username", "unknown"))
                st.success("تم حذف المسؤول.")
                st.rerun()


def main_app():
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        st.markdown("---")
        st.write(f"👤 **{st.session_state.get('username')}**")
        st.write(f"الصلاحية: `{st.session_state.get('role')}`")
        menu_options = [
            "📊 Dashboard",
            "➕ تسجيل فحص جديد",
            "📋 السجلات",
            "📤 التقارير والتصدير",
            "🧾 Audit Log",
            "💾 Backup",
        ]
        if st.session_state.get("role") == "superadmin":
            menu_options.append("⚙ إدارة المسؤولين")
        page = st.radio("القائمة", menu_options)
        if st.button("خروج 🔓", use_container_width=True):
            log_action(st.session_state.get("username", "unknown"), "LOGOUT", "admins", st.session_state.get("username", ""), {})
            st.session_state.clear()
            st.rerun()

    render_header()
    if page == "📊 Dashboard":
        dashboard_page()
    elif page == "➕ تسجيل فحص جديد":
        record_form_page()
    elif page == "📋 السجلات":
        records_page()
    elif page == "📤 التقارير والتصدير":
        reports_page()
    elif page == "🧾 Audit Log":
        audit_page()
    elif page == "💾 Backup":
        backup_page()
    elif page == "⚙ إدارة المسؤولين":
        admin_page()


def main():
    init_database()
    inject_css()
    if not st.session_state.get("logged_in"):
        login_screen()
    else:
        main_app()


if __name__ == "__main__":
    main()
