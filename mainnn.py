
#MY STUDENT PRODUCTIVITY MANAGER#

import sqlite3
import random
import tkinter as tk
from datetime import date, datetime
from pathlib import Path
from tkinter import ttk, messagebox

import matplotlib.pyplot as plt

# ============================================================
# DATABASE
# ============================================================

DB_PATH = Path(__file__).parent / "student_data.db"

def connect():
    return sqlite3.connect(DB_PATH)

def init_database():
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT,
                due_date TEXT,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Pending'
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                minutes INTEGER NOT NULL,
                session_date TEXT NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                attended INTEGER NOT NULL,
                total INTEGER NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                target TEXT,
                progress INTEGER DEFAULT 0
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                exam_date TEXT NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                name TEXT NOT NULL
            )
        """)

        
        con.execute("""
            CREATE TABLE IF NOT EXISTS daily_notes (
                note_date TEXT PRIMARY KEY,
                note TEXT
            )
        """)

        
        if con.execute("SELECT COUNT(*) FROM profile").fetchone()[0] == 0:
            con.execute("INSERT INTO profile(id, name) VALUES(1, ?)",
                        ("Student",))

# ---------- Profile ----------

def get_name():
    with connect() as con:
        row = con.execute("SELECT name FROM profile WHERE id=1").fetchone()
        return row[0] if row else "Student"

def save_name(name):
    name = name.strip() or "Student"
    with connect() as con:
        con.execute("UPDATE profile SET name=? WHERE id=1", (name,))

# ---------- Tasks ----------

def add_task(title, subject, due_date, priority):
    with connect() as con:
        con.execute(
            "INSERT INTO tasks(title,subject,due_date,priority) VALUES(?,?,?,?)",
            (title, subject, due_date, priority)
        )

def get_tasks():
    with connect() as con:
        return con.execute(
            "SELECT id,title,subject,due_date,priority,status "
            "FROM tasks ORDER BY due_date,id DESC"
        ).fetchall()

def mark_task_done(task_id):
    with connect() as con:
        con.execute("UPDATE tasks SET status='Completed' WHERE id=?", (task_id,))

def delete_task(task_id):
    with connect() as con:
        con.execute("DELETE FROM tasks WHERE id=?", (task_id,))

#Study 
def add_study_session(subject, minutes):
    with connect() as con:
        con.execute(
            "INSERT INTO study_sessions(subject,minutes,session_date) "
            "VALUES(?,?,?)",
            (subject, minutes, date.today().isoformat())
        )

def get_today_study_minutes():
    with connect() as con:
        row = con.execute(
            "SELECT COALESCE(SUM(minutes),0) FROM study_sessions "
            "WHERE session_date=?",
            (date.today().isoformat(),)
        ).fetchone()
        return row[0]

def get_total_study_minutes():
    with connect() as con:
        row = con.execute(
            "SELECT COALESCE(SUM(minutes),0) FROM study_sessions"
        ).fetchone()
        return row[0]

def get_study_summary():
    with connect() as con:
        return con.execute(
            "SELECT subject,SUM(minutes) FROM study_sessions "
            "GROUP BY subject ORDER BY SUM(minutes) DESC"
        ).fetchall()

#  Attendance 

def save_attendance(subject, attended, total):
    with connect() as con:
        con.execute(
            "INSERT INTO attendance(subject,attended,total) VALUES(?,?,?)",
            (subject, attended, total)
        )

def get_attendance():
    with connect() as con:
        return con.execute(
            "SELECT id,subject,attended,total FROM attendance ORDER BY subject"
        ).fetchall()

def delete_attendance(record_id):
    with connect() as con:
        con.execute("DELETE FROM attendance WHERE id=?", (record_id,))

#Goals 

def add_goal(title, target):
    with connect() as con:
        con.execute(
            "INSERT INTO goals(title,target,progress) VALUES(?,?,0)",
            (title, target)
        )

def get_goals():
    with connect() as con:
        return con.execute(
            "SELECT id,title,target,progress FROM goals ORDER BY id DESC"
        ).fetchall()

def update_goal(goal_id, progress):
    with connect() as con:
        con.execute(
            "UPDATE goals SET progress=? WHERE id=?",
            (progress, goal_id)
        )

def delete_goal(goal_id):
    with connect() as con:
        con.execute("DELETE FROM goals WHERE id=?", (goal_id,))

# -Exams 

def add_exam(subject, exam_date):
    with connect() as con:
        con.execute(
            "INSERT INTO exams(subject,exam_date) VALUES(?,?)",
            (subject, exam_date)
        )

def get_exams():
    with connect() as con:
        return con.execute(
            "SELECT id,subject,exam_date FROM exams ORDER BY exam_date"
        ).fetchall()

def delete_exam(exam_id):
    with connect() as con:
        con.execute("DELETE FROM exams WHERE id=?", (exam_id,))

# -- Daily note ---

def save_note(note):
    with connect() as con:
        con.execute(
            "INSERT INTO daily_notes(note_date,note) VALUES(?,?) "
            "ON CONFLICT(note_date) DO UPDATE SET note=excluded.note",
            (date.today().isoformat(), note)
        )

def get_today_note():
    with connect() as con:
        row = con.execute(
            "SELECT note FROM daily_notes WHERE note_date=?",
            (date.today().isoformat(),)
        ).fetchone()
        return row[0] if row else ""

# =======
# CHARTS
# =======

def show_study_chart():
    data = get_study_summary()
    if not data:
        return False

    subjects = [row[0] for row in data]
    minutes = [row[1] for row in data]

    plt.figure(figsize=(8, 5))
    plt.bar(subjects, minutes)
    plt.title("Study Time by Subject")
    plt.xlabel("Subject")
    plt.ylabel("Minutes")
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.show()
    return True

def show_task_chart():
    tasks = get_tasks()
    if not tasks:
        return False

    pending = sum(row[5] == "Pending" for row in tasks)
    completed = sum(row[5] == "Completed" for row in tasks)

    if pending + completed == 0:
        return False

    plt.figure(figsize=(6, 5))
    plt.pie(
        [pending, completed],
        labels=["Pending", "Completed"],
        autopct="%1.0f%%"
    )
    plt.title("Task Completion")
    plt.show()
    return True

# ===
# GUI
# ===

class StudentStudyApp:

    BG = "#0b1020"
    PANEL = "#11182b"
    PANEL_2 = "#17213a"
    PANEL_3 = "#1d2945"
    TEXT = "#f4f7fb"
    MUTED = "#9aa8bf"
    ACCENT = "#6c63ff"
    ACCENT_2 = "#8b83ff"
    GREEN = "#35d07f"
    ORANGE = "#ffb454"
    BORDER = "#263453"

    SUBJECTS = [
        "Python",
        "Mathematics",
        "EVS",
        "Communication",
        "Other"
    ]

    TIPS = [
        "Start small. One finished task is better than ten unfinished plans.",
        "Keep your phone away for one focused session.",
        "You do not need a perfect study day.",
        "Record your study time so you can see your progress.",
        "Finish one important thing before jumping to the next one."
    ]

    def __init__(self, window):
        self.window = window
        self.window.title("My Student Study Companion")
        self.window.geometry("1180x760")
        self.window.minsize(1000, 680)
        self.window.configure(bg=self.BG)

        self.timer_seconds = 25 * 60
        self.timer_running = False

        self.setup_style()
        self.build_shell()
        self.show_view("Dashboard")
        self.refresh_everything()

    # ======
    # STYLE
    # ======

    def setup_style(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            ".",
            font=("Segoe UI", 10),
            background=self.BG,
            foreground=self.TEXT
        )

        style.configure("TFrame", background=self.BG)
        style.configure("TLabel", background=self.BG, foreground=self.TEXT)

        style.configure(
            "BigTimer.TLabel",
            background=self.PANEL,
            foreground=self.TEXT,
            font=("Segoe UI", 56, "bold")
        )

        style.configure(
            "TButton",
            background=self.PANEL_3,
            foreground=self.TEXT,
            borderwidth=0,
            padding=(12, 8),
            font=("Segoe UI", 10, "bold")
        )

        style.map(
            "TButton",
            background=[("active", self.ACCENT)]
        )

        style.configure(
            "Accent.TButton",
            background=self.ACCENT,
            foreground="white",
            padding=(14, 9),
            font=("Segoe UI", 10, "bold")
        )

        style.map(
            "Accent.TButton",
            background=[("active", self.ACCENT_2)]
        )

        style.configure(
            "Treeview",
            background=self.PANEL,
            fieldbackground=self.PANEL,
            foreground=self.TEXT,
            rowheight=34,
            borderwidth=0
        )

        style.configure(
            "Treeview.Heading",
            background=self.PANEL_2,
            foreground=self.MUTED,
            relief="flat",
            font=("Segoe UI", 9, "bold")
        )

        style.map(
            "Treeview",
            background=[("selected", self.ACCENT)],
            foreground=[("selected", "white")]
        )

        style.configure(
            "TCombobox",
            fieldbackground=self.PANEL_2,
            background=self.PANEL_2,
            foreground=self.TEXT
        )

    # ==========
    # MAIN SHELL
    # ==========

    def build_shell(self):

        self.sidebar = tk.Frame(
            self.window,
            bg=self.PANEL,
            width=220
        )

        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=self.PANEL)
        brand.pack(fill="x", padx=18, pady=(22, 25))

        tk.Label(
            brand,
            text="✦",
            bg=self.PANEL,
            fg=self.ACCENT_2,
            font=("Segoe UI", 23, "bold")
        ).pack(side="left")

        brand_text = tk.Frame(brand, bg=self.PANEL)
        brand_text.pack(side="left", padx=9)

        tk.Label(
            brand_text,
            text="Study Companion",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w")

        tk.Label(
            brand_text,
            text="offline • personal",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 8)
        ).pack(anchor="w")

        navigation = [
            ("⌂", "Dashboard"),
            ("✓", "Tasks"),
            ("◷", "Study Timer"),
            ("▣", "Attendance"),
            ("★", "Goals"),
            ("◈", "Graphs"),
            ("✎", "Daily Note"),
            ("⏳", "Exams")
        ]

        self.nav_buttons = {}

        for icon, name in navigation:

            button = tk.Button(
                self.sidebar,
                text=f"  {icon}   {name}",
                anchor="w",
                relief="flat",
                bd=0,
                cursor="hand2",
                bg=self.PANEL,
                fg=self.MUTED,
                activebackground=self.PANEL_2,
                activeforeground=self.TEXT,
                font=("Segoe UI", 10, "bold"),
                padx=16,
                pady=11,
                command=lambda n=name: self.show_view(n)
            )

            button.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[name] = button

        bottom = tk.Frame(self.sidebar, bg=self.PANEL)
        bottom.pack(side="bottom", fill="x", padx=16, pady=18)

        tk.Label(
            bottom,
            text="Local data",
            bg=self.PANEL,
            fg=self.GREEN,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")

        tk.Label(
            bottom,
            text="Saved on this laptop\nNo cloud account required",
            bg=self.PANEL,
            fg=self.MUTED,
            justify="left",
            font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(3, 10))

        tk.Button(
            bottom,
            text="Change my name",
            command=self.change_name,
            relief="flat",
            bd=0,
            bg=self.PANEL_2,
            fg=self.TEXT,
            activebackground=self.ACCENT,
            activeforeground="white",
            cursor="hand2",
            padx=10,
            pady=8
        ).pack(fill="x")

        self.main = tk.Frame(self.window, bg=self.BG)
        self.main.pack(side="left", fill="both", expand=True)

        self.topbar = tk.Frame(
            self.main,
            bg=self.BG,
            height=76
        )

        self.topbar.pack(fill="x", padx=28, pady=(16, 0))
        self.topbar.pack_propagate(False)

        self.page_title = tk.Label(
            self.topbar,
            text="Dashboard",
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI", 22, "bold")
        )

        self.page_title.pack(side="left", anchor="center")

        self.date_label = tk.Label(
            self.topbar,
            text=date.today().strftime("%A  •  %d %b %Y"),
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 10)
        )

        self.date_label.pack(side="right", anchor="center")

        self.content = tk.Frame(self.main, bg=self.BG)
        self.content.pack(fill="both", expand=True, padx=28, pady=(0, 25))

        names = [
            "Dashboard",
            "Tasks",
            "Study Timer",
            "Attendance",
            "Goals",
            "Graphs",
            "Daily Note",
            "Exams"
        ]

        self.views = {}

        for name in names:
            self.views[name] = tk.Frame(
                self.content,
                bg=self.BG
            )

        self.make_dashboard()
        self.make_tasks()
        self.make_study()
        self.make_attendance()
        self.make_goals()
        self.make_stats()
        self.make_notes()
        self.make_exams()

    def show_view(self, name):

        for frame in self.views.values():
            frame.pack_forget()

        self.views[name].pack(
            fill="both",
            expand=True
        )

        self.page_title.config(text=name)

        for nav_name, button in self.nav_buttons.items():

            if nav_name == name:
                button.config(
                    bg=self.ACCENT,
                    fg="white"
                )

            else:
                button.config(
                    bg=self.PANEL,
                    fg=self.MUTED
                )

    
# HELPER

    def panel(self, parent):
        return tk.Frame(
            parent,
            bg=self.PANEL,
            highlightthickness=1,
            highlightbackground=self.BORDER
        )

    def dark_entry(self, parent, variable, width):
        return tk.Entry(
            parent,
            textvariable=variable,
            width=width,
            bg=self.PANEL_2,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 10)
        )

    @staticmethod
    def clock_text(seconds):
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    @staticmethod
    def format_minutes(minutes):
        if minutes < 60:
            return f"{minutes}m"
        return f"{minutes // 60}h {minutes % 60}m"

# PROFILE
# ========

    def change_name(self):

        popup = tk.Toplevel(self.window)
        popup.title("Your name")
        popup.geometry("360x190")
        popup.configure(bg=self.PANEL)
        popup.resizable(False, False)

        tk.Label(
            popup,
            text="What should the app call you?",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(pady=(25, 10))

        value = tk.StringVar(value=get_name())

        entry = tk.Entry(
            popup,
            textvariable=value,
            bg=self.PANEL_2,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            font=("Segoe UI", 11)
        )

        entry.pack(
            fill="x",
            padx=35,
            ipady=8
        )

        entry.focus_set()

        def save():
            save_name(value.get())
            popup.destroy()
            self.refresh_dashboard()

        tk.Button(
            popup,
            text="Save",
            command=save,
            bg=self.ACCENT,
            fg="white",
            activebackground=self.ACCENT_2,
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=18,
            pady=8
        ).pack(pady=18)

    # DASHBOARD
    

    def make_dashboard(self):

        view = self.views["Dashboard"]

        self.greeting = tk.Label(
            view,
            text="",
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 10)
        )

        self.greeting.pack(
            anchor="w",
            pady=(4, 18)
        )

        cards = tk.Frame(view, bg=self.BG)
        cards.pack(fill="x", pady=(0, 20))

        self.card_tasks = self.make_card(
            cards,
            "TASKS",
            "0",
            "completed / pending"
        )

        self.card_study = self.make_card(
            cards,
            "STUDY TODAY",
            "0m",
            "focused study time",
            self.ACCENT_2
        )

        self.card_attendance = self.make_card(
            cards,
            "ATTENDANCE",
            "0%",
            "average across subjects",
            self.GREEN
        )

        self.card_goals = self.make_card(
            cards,
            "GOALS",
            "0",
            "active goals",
            self.ORANGE
        )

        body = tk.Frame(view, bg=self.BG)
        body.pack(fill="both", expand=True)

        left = self.panel(body)
        left.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 8)
        )

        tk.Label(
            left,
            text="Upcoming exams",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(
            anchor="w",
            padx=18,
            pady=(16, 2)
        )

        self.exam_preview = tk.Listbox(
            left,
            bg=self.PANEL,
            fg=self.TEXT,
            selectbackground=self.ACCENT,
            relief="flat",
            highlightthickness=0,
            font=("Segoe UI", 10)
        )

        self.exam_preview.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=12
        )

        right = self.panel(body)
        right.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(8, 0)
        )

        tk.Label(
            right,
            text="Next things to do",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(
            anchor="w",
            padx=18,
            pady=(16, 2)
        )

        self.task_preview = tk.Listbox(
            right,
            bg=self.PANEL,
            fg=self.TEXT,
            selectbackground=self.ACCENT,
            relief="flat",
            highlightthickness=0,
            font=("Segoe UI", 10)
        )

        self.task_preview.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=12
        )

    def make_card(self, parent, title, value, subtitle, accent=None):

        card = self.panel(parent)

        card.pack(
            side="left",
            fill="both",
            expand=True,
            padx=5
        )

        inner = tk.Frame(
            card,
            bg=self.PANEL
        )

        inner.pack(
            fill="both",
            expand=True,
            padx=16,
            pady=14
        )

        tk.Label(
            inner,
            text=title,
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w")

        value_label = tk.Label(
            inner,
            text=value,
            bg=self.PANEL,
            fg=accent or self.TEXT,
            font=("Segoe UI", 21, "bold")
        )

        value_label.pack(
            anchor="w",
            pady=(7, 1)
        )

        tk.Label(
            inner,
            text=subtitle,
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 8)
        ).pack(anchor="w")

        return value_label

    def refresh_dashboard(self):

        tasks = get_tasks()

        pending = sum(
            row[5] == "Pending"
            for row in tasks
        )

        completed = sum(
            row[5] == "Completed"
            for row in tasks
        )

        self.card_tasks.config(
            text=f"{completed} / {pending}"
        )

        self.card_study.config(
            text=self.format_minutes(
                get_today_study_minutes()
            )
        )

        attendance = get_attendance()

        percentages = [
            attended / total * 100
            for _, _, attended, total in attendance
            if total
        ]

        average = (
            sum(percentages) / len(percentages)
            if percentages else 0
        )

        self.card_attendance.config(
            text=f"{average:.0f}%"
        )

        self.card_goals.config(
            text=str(len(get_goals()))
        )

        self.greeting.config(
            text=f"Hi {get_name()}  •  {random.choice(self.TIPS)}"
        )

        self.exam_preview.delete(0, tk.END)

        exams = get_exams()

        if not exams:
            self.exam_preview.insert(
                tk.END,
                "  No exams added yet."
            )

        for _, subject, exam_date in exams[:8]:

            exam_day = datetime.strptime(
                exam_date,
                "%Y-%m-%d"
            ).date()

            days = (
                exam_day - date.today()
            ).days

            if days > 0:
                text = f"  {subject}  •  {days} days left"

            elif days == 0:
                text = f"  {subject}  •  TODAY"

            else:
                text = f"  {subject}  •  passed"

            self.exam_preview.insert(
                tk.END,
                text
            )

        self.task_preview.delete(0, tk.END)

        pending_tasks = [
            row for row in tasks
            if row[5] == "Pending"
        ]

        if not pending_tasks:
            self.task_preview.insert(
                tk.END,
                "  Nothing pending. Nice!"
            )

        for row in pending_tasks[:8]:

            self.task_preview.insert(
                tk.END,
                f"  {row[1]}  •  {row[3]}  •  {row[4]}"
            )

   # =TASKS=

    def make_tasks(self):

        view = self.views["Tasks"]

        form = self.panel(view)
        form.pack(
            fill="x",
            pady=(0, 14)
        )

        tk.Label(
            form,
            text="Add something you need to finish",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 12, "bold")
        ).pack(
            anchor="w",
            padx=16,
            pady=(13, 10)
        )

        row = tk.Frame(
            form,
            bg=self.PANEL
        )

        row.pack(
            fill="x",
            padx=16,
            pady=(0, 14)
        )

        self.task_title = tk.StringVar()
        self.task_subject = tk.StringVar(value="Python")
        self.task_due = tk.StringVar(value=date.today().isoformat())
        self.task_priority = tk.StringVar(value="Medium")

        self.dark_entry(
            row,
            self.task_title,
            24
        ).pack(side="left", padx=(0, 7))

        ttk.Combobox(
            row,
            textvariable=self.task_subject,
            values=self.SUBJECTS,
            width=14
        ).pack(side="left", padx=7)

        self.dark_entry(
            row,
            self.task_due,
            13
        ).pack(side="left", padx=7)

        ttk.Combobox(
            row,
            textvariable=self.task_priority,
            values=("Low", "Medium", "High"),
            state="readonly",
            width=10
        ).pack(side="left", padx=7)

        ttk.Button(
            row,
            text="+ Add task",
            style="Accent.TButton",
            command=self.add_task
        ).pack(side="left", padx=7)

        box = self.panel(view)
        box.pack(fill="both", expand=True)

        columns = (
            "id",
            "title",
            "subject",
            "due",
            "priority",
            "status"
        )

        self.task_table = ttk.Treeview(
            box,
            columns=columns,
            show="headings"
        )

        headings = [
            ("id", "ID", 50),
            ("title", "Task", 320),
            ("subject", "Subject", 150),
            ("due", "Due", 120),
            ("priority", "Priority", 100),
            ("status", "Status", 120)
        ]

        for column, heading, width in headings:
            self.task_table.heading(
                column,
                text=heading
            )

            self.task_table.column(
                column,
                width=width
            )

        self.task_table.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        buttons = tk.Frame(
            view,
            bg=self.BG
        )

        buttons.pack(
            fill="x",
            pady=(10, 0)
        )

        ttk.Button(
            buttons,
            text="✓ Mark completed",
            command=self.complete_task
        ).pack(side="left")

        ttk.Button(
            buttons,
            text="Delete selected",
            command=self.remove_task
        ).pack(
            side="left",
            padx=8
        )

    def add_task(self):

        title = self.task_title.get().strip()
        due = self.task_due.get().strip()

        if not title:
            messagebox.showwarning(
                "Missing task",
                "Write the task first."
            )
            return

        try:
            datetime.strptime(
                due,
                "%Y-%m-%d"
            )

        except ValueError:
            messagebox.showwarning(
                "Wrong date",
                "Use YYYY-MM-DD for the due date."
            )
            return

        add_task(
            title,
            self.task_subject.get(),
            due,
            self.task_priority.get()
        )

        self.task_title.set("")

        self.refresh_tasks()
        self.refresh_dashboard()

    def selected_task_id(self):

        selected = self.task_table.selection()

        if not selected:
            return None

        return int(
            self.task_table.item(
                selected[0],
                "values"
            )[0]
        )

    def complete_task(self):

        task_id = self.selected_task_id()

        if task_id is None:
            messagebox.showinfo(
                "Select a task",
                "Select a task first."
            )
            return

        mark_task_done(task_id)

        self.refresh_tasks()
        self.refresh_dashboard()

    def remove_task(self):

        task_id = self.selected_task_id()

        if task_id is None:
            messagebox.showinfo(
                "Select a task",
                "Select a task first."
            )
            return

        delete_task(task_id)

        self.refresh_tasks()
        self.refresh_dashboard()

    def refresh_tasks(self):

        for item in self.task_table.get_children():
            self.task_table.delete(item)

        for row in get_tasks():
            self.task_table.insert(
                "",
                "end",
                values=row
            )

   # STUDY TIMER

    def make_study(self):

        view = self.views["Study Timer"]

        entry = self.panel(view)
        entry.pack(
            fill="x",
            pady=(0, 14)
        )

        tk.Label(
            entry,
            text="Record study time",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 12, "bold")
        ).pack(
            anchor="w",
            padx=16,
            pady=(13, 10)
        )

        row = tk.Frame(
            entry,
            bg=self.PANEL
        )

        row.pack(
            fill="x",
            padx=16,
            pady=(0, 14)
        )

        self.study_subject = tk.StringVar(value="Python")
        self.study_minutes = tk.IntVar(value=25)

        ttk.Combobox(
            row,
            textvariable=self.study_subject,
            values=self.SUBJECTS,
            width=18
        ).pack(side="left")

        ttk.Spinbox(
            row,
            from_=1,
            to=500,
            textvariable=self.study_minutes,
            width=8
        ).pack(
            side="left",
            padx=8
        )

        ttk.Button(
            row,
            text="Save session",
            style="Accent.TButton",
            command=self.save_study
        ).pack(side="left")

        timer_box = self.panel(view)
        timer_box.pack(
            fill="both",
            expand=True
        )

        tk.Label(
            timer_box,
            text="FOCUS SESSION",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9, "bold")
        ).pack(pady=(28, 4))

        tk.Label(
            timer_box,
            text="One thing. Twenty-five minutes. No pressure.",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 13)
        ).pack()

        self.timer_label = ttk.Label(
            timer_box,
            text="25:00",
            style="BigTimer.TLabel"
        )

        self.timer_label.pack(
            pady=35
        )

        buttons = tk.Frame(
            timer_box,
            bg=self.PANEL
        )

        buttons.pack()

        ttk.Button(
            buttons,
            text="Start",
            style="Accent.TButton",
            command=self.start_timer
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Pause",
            command=self.pause_timer
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Reset",
            command=self.reset_timer
        ).pack(side="left", padx=5)

        self.timer_status = tk.Label(
            timer_box,
            text="Ready when you are.",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9)
        )

        self.timer_status.pack(pady=18)

    def save_study(self):

        subject = self.study_subject.get().strip()
        minutes = self.study_minutes.get()

        if not subject or minutes <= 0:
            messagebox.showwarning(
                "Check study time",
                "Enter a subject and a positive number of minutes."
            )
            return

        add_study_session(
            subject,
            minutes
        )

        self.refresh_dashboard()

        messagebox.showinfo(
            "Saved",
            f"Added {minutes} minutes for {subject}."
        )

    def start_timer(self):

        if not self.timer_running:

            self.timer_running = True

            self.timer_status.config(
                text="Focus mode is on. You've got this.",
                fg=self.GREEN
            )

            self.run_timer()

    def pause_timer(self):

        self.timer_running = False

        self.timer_status.config(
            text="Paused. Continue when you're ready.",
            fg=self.ORANGE
        )

    def reset_timer(self):

        self.timer_running = False
        self.timer_seconds = 25 * 60

        self.timer_label.config(
            text=self.clock_text(
                self.timer_seconds
            )
        )

        self.timer_status.config(
            text="Ready when you are.",
            fg=self.MUTED
        )

    def run_timer(self):

        if not self.timer_running:
            return

        self.timer_label.config(
            text=self.clock_text(
                self.timer_seconds
            )
        )

        if self.timer_seconds == 0:

            self.timer_running = False

            self.timer_status.config(
                text="Session finished. Take a short break.",
                fg=self.GREEN
            )

            messagebox.showinfo(
                "Nice work",
                "25 minutes are done. Take a short break."
            )

            return

        self.timer_seconds -= 1

        self.window.after(
            1000,
            self.run_timer
        )

    # ATTENDENCE

    def make_attendance(self):

        view = self.views["Attendance"]

        form = self.panel(view)

        form.pack(
            fill="x",
            pady=(0, 14)
        )

        tk.Label(
            form,
            text="Keep attendance updated",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 12, "bold")
        ).pack(
            anchor="w",
            padx=16,
            pady=(13, 10)
        )

        row = tk.Frame(
            form,
            bg=self.PANEL
        )

        row.pack(
            fill="x",
            padx=16,
            pady=(0, 14)
        )

        self.att_subject = tk.StringVar(value="Python")
        self.att_present = tk.IntVar(value=0)
        self.att_total = tk.IntVar(value=0)

        ttk.Combobox(
            row,
            textvariable=self.att_subject,
            values=self.SUBJECTS,
            width=18
        ).pack(side="left")

        ttk.Spinbox(
            row,
            from_=0,
            to=500,
            textvariable=self.att_present,
            width=8
        ).pack(side="left", padx=8)

        ttk.Spinbox(
            row,
            from_=0,
            to=500,
            textvariable=self.att_total,
            width=8
        ).pack(side="left", padx=8)

        ttk.Button(
            row,
            text="Save attendance",
            style="Accent.TButton",
            command=self.save_attendance
        ).pack(side="left")

        box = self.panel(view)

        box.pack(
            fill="both",
            expand=True
        )

        columns = (
            "id",
            "subject",
            "attended",
            "total",
            "percentage"
        )

        self.att_table = ttk.Treeview(
            box,
            columns=columns,
            show="headings"
        )

        for col, heading, width in [
            ("id", "ID", 50),
            ("subject", "Subject", 230),
            ("attended", "Attended", 150),
            ("total", "Total", 150),
            ("percentage", "Attendance", 160)
        ]:
            self.att_table.heading(
                col,
                text=heading
            )
            self.att_table.column(
                col,
                width=width
            )

        self.att_table.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        ttk.Button(
            view,
            text="Delete selected",
            command=self.remove_attendance
        ).pack(
            anchor="w",
            pady=10
        )

    def save_attendance(self):

        subject = self.att_subject.get().strip()
        attended = self.att_present.get()
        total = self.att_total.get()

        if (
            not subject
            or total <= 0
            or attended < 0
            or attended > total
        ):
            messagebox.showwarning(
                "Check values",
                "Attended classes cannot be greater than total classes."
            )
            return

        save_attendance(
            subject,
            attended,
            total
        )

        self.refresh_attendance()
        self.refresh_dashboard()

    def remove_attendance(self):

        selected = self.att_table.selection()

        if not selected:
            messagebox.showinfo(
                "Select a row",
                "Select an attendance record first."
            )
            return

        record_id = int(
            self.att_table.item(
                selected[0],
                "values"
            )[0]
        )

        delete_attendance(record_id)

        self.refresh_attendance()
        self.refresh_dashboard()

    def refresh_attendance(self):

        for item in self.att_table.get_children():
            self.att_table.delete(item)

        for record_id, subject, attended, total in get_attendance():

            percentage = (
                attended / total * 100
                if total else 0
            )

            self.att_table.insert(
                "",
                "end",
                values=(
                    record_id,
                    subject,
                    attended,
                    total,
                    f"{percentage:.1f}%"
                )
            )

    # GOALS

    def make_goals(self):

        view = self.views["Goals"]

        form = self.panel(view)
        form.pack(
            fill="x",
            pady=(0, 14)
        )

        tk.Label(
            form,
            text="Something I want to improve",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 12, "bold")
        ).pack(
            anchor="w",
            padx=16,
            pady=(13, 10)
        )

        row = tk.Frame(
            form,
            bg=self.PANEL
        )

        row.pack(
            fill="x",
            padx=16,
            pady=(0, 14)
        )

        self.goal_name = tk.StringVar()
        self.goal_target = tk.StringVar()

        self.dark_entry(
            row,
            self.goal_name,
            34
        ).pack(side="left")

        self.dark_entry(
            row,
            self.goal_target,
            25
        ).pack(
            side="left",
            padx=8
        )

        ttk.Button(
            row,
            text="+ Add goal",
            style="Accent.TButton",
            command=self.add_goal_gui
        ).pack(side="left")

        box = self.panel(view)
        box.pack(
            fill="both",
            expand=True
        )

        columns = (
            "id",
            "goal",
            "target",
            "progress"
        )

        self.goal_table = ttk.Treeview(
            box,
            columns=columns,
            show="headings"
        )

        for col, heading, width in [
            ("id", "ID", 50),
            ("goal", "Goal", 350),
            ("target", "Target", 280),
            ("progress", "Progress %", 150)
        ]:
            self.goal_table.heading(
                col,
                text=heading
            )

            self.goal_table.column(
                col,
                width=width
            )

        self.goal_table.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        buttons = tk.Frame(
            view,
            bg=self.BG
        )

        buttons.pack(
            fill="x",
            pady=10
        )

        ttk.Button(
            buttons,
            text="Change progress",
            command=self.change_goal_progress
        ).pack(side="left")

        ttk.Button(
            buttons,
            text="Delete",
            command=self.remove_goal
        ).pack(
            side="left",
            padx=8
        )

    def add_goal_gui(self):

        title = self.goal_name.get().strip()

        if not title:
            messagebox.showwarning(
                "Missing goal",
                "Write the goal first."
            )
            return

        add_goal(
            title,
            self.goal_target.get().strip()
        )

        self.goal_name.set("")
        self.goal_target.set("")

        self.refresh_goals()
        self.refresh_dashboard()

    def selected_goal_id(self):

        selected = self.goal_table.selection()

        if not selected:
            return None

        return int(
            self.goal_table.item(
                selected[0],
                "values"
            )[0]
        )

    def change_goal_progress(self):

        goal_id = self.selected_goal_id()

        if goal_id is None:
            messagebox.showinfo(
                "Select a goal",
                "Select a goal first."
            )
            return

        popup = tk.Toplevel(self.window)
        popup.title("Goal progress")
        popup.geometry("330x190")
        popup.configure(bg=self.PANEL)
        popup.resizable(False, False)

        value = tk.IntVar(value=0)

        tk.Label(
            popup,
            text="How far are you?",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 12, "bold")
        ).pack(
            pady=(25, 8)
        )

        ttk.Spinbox(
            popup,
            from_=0,
            to=100,
            textvariable=value,
            width=10
        ).pack()

        ttk.Button(
            popup,
            text="Save",
            style="Accent.TButton",
            command=lambda: self.save_goal_progress(
                popup,
                goal_id,
                value.get()
            )
        ).pack(pady=20)

    def save_goal_progress(
        self,
        popup,
        goal_id,
        progress
    ):

        progress = max(
            0,
            min(100, progress)
        )

        update_goal(
            goal_id,
            progress
        )

        popup.destroy()

        self.refresh_goals()
        self.refresh_dashboard()

    def remove_goal(self):

        goal_id = self.selected_goal_id()

        if goal_id is None:
            messagebox.showinfo(
                "Select a goal",
                "Select a goal first."
            )
            return

        delete_goal(goal_id)

        self.refresh_goals()
        self.refresh_dashboard()

    def refresh_goals(self):

        for item in self.goal_table.get_children():
            self.goal_table.delete(item)

        for row in get_goals():

            self.goal_table.insert(
                "",
                "end",
                values=row
            )

    # =======
    # GRAPHS
    # =======

    def make_stats(self):

        view = self.views["Graphs"]

        tk.Label(
            view,
            text="Progress at a glance",
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI", 14, "bold")
        ).pack(
            anchor="w",
            pady=(0, 10)
        )

        tk.Label(
            view,
            text="Charts use the records saved on this laptop.",
            bg=self.BG,
            fg=self.MUTED
        ).pack(
            anchor="w",
            pady=(0, 20)
        )

        buttons = tk.Frame(
            view,
            bg=self.BG
        )

        buttons.pack(
            anchor="w"
        )

        ttk.Button(
            buttons,
            text="Study time by subject",
            style="Accent.TButton",
            command=self.study_chart
        ).pack(
            side="left",
            padx=(0, 10)
        )

        ttk.Button(
            buttons,
            text="Completed vs pending tasks",
            command=self.task_chart
        ).pack(side="left")

        note = self.panel(view)

        note.pack(
            fill="x",
            pady=25
        )

        tk.Label(
            note,
            text="Tip",
            bg=self.PANEL,
            fg=self.ACCENT_2,
            font=("Segoe UI", 10, "bold")
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 4)
        )

        tk.Label(
            note,
            text="The more consistently you record your study sessions, "
                 "the more useful these graphs become.",
            bg=self.PANEL,
            fg=self.TEXT,
            wraplength=800,
            justify="left"
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 15)
        )

    def study_chart(self):

        if not show_study_chart():
            messagebox.showinfo(
                "No study data",
                "Save at least one study session first."
            )

    def task_chart(self):

        if not show_task_chart():
            messagebox.showinfo(
                "No task data",
                "Add at least one task first."
            )

    # ----DAILY NOTE-----

    def make_notes(self):

        view = self.views["Daily Note"]

        tk.Label(
            view,
            text="A note to myself",
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI", 14, "bold")
        ).pack(
            anchor="w",
            pady=(0, 8)
        )

        tk.Label(
            view,
            text="Write down what went well, what is left, "
                 "or what you want to remember tomorrow.",
            bg=self.BG,
            fg=self.MUTED
        ).pack(
            anchor="w",
            pady=(0, 12)
        )

        box = self.panel(view)
        box.pack(
            fill="both",
            expand=True
        )

        self.note_box = tk.Text(
            box,
            wrap="word",
            bg=self.PANEL_2,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            selectbackground=self.ACCENT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 11),
            padx=14,
            pady=14
        )

        self.note_box.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=14
        )

        ttk.Button(
            view,
            text="Save today's note",
            style="Accent.TButton",
            command=self.save_daily_note
        ).pack(
            anchor="e",
            pady=10
        )

    def save_daily_note(self):

        save_note(
            self.note_box.get(
                "1.0",
                tk.END
            ).strip()
        )

        messagebox.showinfo(
            "Saved",
            "Today's note has been saved locally."
        )

    # --EXAMS--

    def make_exams(self):

        view = self.views["Exams"]

        form = self.panel(view)
        form.pack(
            fill="x",
            pady=(0, 14)
        )

        tk.Label(
            form,
            text="Add an exam date",
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 12, "bold")
        ).pack(
            anchor="w",
            padx=16,
            pady=(13, 10)
        )

        row = tk.Frame(
            form,
            bg=self.PANEL
        )

        row.pack(
            fill="x",
            padx=16,
            pady=(0, 14)
        )

        self.exam_subject = tk.StringVar(value="Mathematics")
        self.exam_date = tk.StringVar()

        ttk.Combobox(
            row,
            textvariable=self.exam_subject,
            values=self.SUBJECTS,
            width=18
        ).pack(side="left")

        self.dark_entry(
            row,
            self.exam_date,
            14
        ).pack(
            side="left",
            padx=8
        )

        ttk.Button(
            row,
            text="+ Add exam",
            style="Accent.TButton",
            command=self.add_exam_gui
        ).pack(side="left")

        box = self.panel(view)
        box.pack(
            fill="both",
            expand=True
        )

        self.exam_table = ttk.Treeview(
            box,
            columns=("id", "subject", "date", "remaining"),
            show="headings"
        )

        for col, heading, width in [
            ("id", "ID", 50),
            ("subject", "Subject", 250),
            ("date", "Exam date", 200),
            ("remaining", "Status", 250)
        ]:
            self.exam_table.heading(
                col,
                text=heading
            )

            self.exam_table.column(
                col,
                width=width
            )

        self.exam_table.pack(
            fill="both",
            expand=True,
            padx=12,
            pady=12
        )

        ttk.Button(
            view,
            text="Delete selected",
            command=self.remove_exam
        ).pack(
            anchor="w",
            pady=10
        )

    def add_exam_gui(self):

        subject = self.exam_subject.get().strip()
        exam_date = self.exam_date.get().strip()

        if not subject:
            messagebox.showwarning(
                "Missing subject",
                "Enter an exam subject."
            )
            return

        try:
            datetime.strptime(
                exam_date,
                "%Y-%m-%d"
            )

        except ValueError:
            messagebox.showwarning(
                "Wrong date",
                "Use YYYY-MM-DD."
            )
            return

        add_exam(
            subject,
            exam_date
        )

        self.exam_date.set("")

        self.refresh_exams()
        self.refresh_dashboard()

    def remove_exam(self):

        selected = self.exam_table.selection()

        if not selected:
            messagebox.showinfo(
                "Select an exam",
                "Select an exam first."
            )
            return

        exam_id = int(
            self.exam_table.item(
                selected[0],
                "values"
            )[0]
        )

        delete_exam(exam_id)

        self.refresh_exams()
        self.refresh_dashboard()

    def refresh_exams(self):

        for item in self.exam_table.get_children():
            self.exam_table.delete(item)

        for exam_id, subject, exam_date in get_exams():

            exam_day = datetime.strptime(
                exam_date,
                "%Y-%m-%d"
            ).date()

            days = (
                exam_day - date.today()
            ).days

            if days > 0:
                status = f"{days} days left"
            elif days == 0:
                status = "TODAY"
            else:
                status = "Passed"

            self.exam_table.insert(
                "",
                "end",
                values=(
                    exam_id,
                    subject,
                    exam_date,
                    status
                )
            )

    
    # REFRESH
    
    def refresh_everything(self):

        self.refresh_dashboard()
        self.refresh_tasks()
        self.refresh_attendance()
        self.refresh_goals()
        self.refresh_exams()

        self.note_box.delete(
            "1.0",
            tk.END
        )

        self.note_box.insert(
            "1.0",
            get_today_note()
        )

# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":

    init_database()

    root = tk.Tk()

    app = StudentStudyApp(root)

    root.mainloop()