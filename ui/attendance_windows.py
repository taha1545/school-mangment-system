"""Windows for teacher attendance tracking and report generation.
Keeps Arabic labels intact and maintains consistent styling with main UI.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import datetime
from typing import Optional, Dict, Any

from core.data_manager import DataManager
from report.report_manager import ReportManager

# Modern color scheme (matching main_ui.py)
BG = "#f8f9fa"
ACCENT = "#4361ee"
ACCENT_LIGHT = "#4895ef"
TEXT_PRIMARY = "#212529"
TEXT_SECONDARY = "#6c757d"

# Status colors
COLOR_PRESENT = "#00b4d8"
COLOR_ABSENT = "#ef476f"
COLOR_LATE = "#ffd60a"

class TeacherAttendanceWindow:
    """Window for tracking teacher attendance and adding notes."""
    
    def __init__(self, parent: tk.Tk, teacher: str, dm: DataManager, rm: ReportManager):
        self.top = tk.Toplevel(parent)
        self.top.title(f"متابعة الأستاذ: {teacher}")
        self.top.geometry("600x700")
        self.top.configure(bg=BG)
        
        self.teacher = teacher
        self.dm = dm
        self.rm = rm
        
        self._build_ui()
        
    def _build_ui(self):
        # Title
        title_frame = tk.Frame(self.top, bg=BG)
        title_frame.pack(fill='x', pady=15, padx=20)
        
        tk.Label(title_frame,
                text=f"👨‍🏫 متابعة الأستاذ: {self.teacher}",
                font=("Segoe UI", 16, "bold"),
                bg=BG,
                fg=TEXT_PRIMARY).pack()
                
        # Date Selection
        date_frame = tk.Frame(self.top, bg=BG)
        date_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(date_frame,
                text="التاريخ:",
                font=("Segoe UI", 11),
                bg=BG).pack(side='left', padx=5)
                
        self.date_entry = DateEntry(date_frame,
                                  width=12,
                                  background=ACCENT,
                                  foreground='white',
                                  borderwidth=2)
        self.date_entry.pack(side='left', padx=5)
        
        # Status Selection
        status_frame = tk.Frame(self.top, bg=BG)
        status_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(status_frame,
                text="الحالة:",
                font=("Segoe UI", 11),
                bg=BG).pack(side='left', padx=5)
                
        self.status_var = tk.StringVar(value="حاضر")
        for status, color in [("حاضر", COLOR_PRESENT),
                            ("غائب", COLOR_ABSENT),
                            ("متأخر", COLOR_LATE)]:
            rb = tk.Radiobutton(status_frame,
                              text=status,
                              value=status,
                              variable=self.status_var,
                              bg=BG,
                              activebackground=color,
                              font=("Segoe UI", 10))
            rb.pack(side='left', padx=10)
        
        # Subject Selection
        subject_frame = tk.Frame(self.top, bg=BG)
        subject_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(subject_frame,
                text="المادة:",
                font=("Segoe UI", 11),
                bg=BG).pack(side='left', padx=5)
                
        subjects = []
        for subject, teachers in self.dm.materials_teachers.items():
            if self.teacher in teachers:
                subjects.append(subject)
                
        self.subject_var = tk.StringVar(value=subjects[0] if subjects else "")
        subject_cb = ttk.Combobox(subject_frame,
                                textvariable=self.subject_var,
                                values=subjects,
                                width=30,
                                state="readonly")
        subject_cb.pack(side='left', padx=5)
        
        # Hour Selection
        hour_frame = tk.Frame(self.top, bg=BG)
        hour_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(hour_frame,
                text="الساعة:",
                font=("Segoe UI", 11),
                bg=BG).pack(side='left', padx=5)
                
        self.hour_var = tk.StringVar()
        hours = ["08:00", "09:00", "10:00", "11:00", "12:00",
                "13:00", "14:00", "15:00", "16:00", "17:00"]
        hour_cb = ttk.Combobox(hour_frame,
                              textvariable=self.hour_var,
                              values=hours,
                              width=10,
                              state="readonly")
        hour_cb.pack(side='left', padx=5)
        
        # Notes
        notes_frame = tk.Frame(self.top, bg=BG)
        notes_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(notes_frame,
                text="ملاحظات:",
                font=("Segoe UI", 11),
                bg=BG).pack(anchor='w')
                
        self.notes_text = tk.Text(notes_frame,
                                height=4,
                                width=50,
                                font=("Segoe UI", 10),
                                wrap='word')
        self.notes_text.pack(pady=5)
        
        # Buttons
        btn_frame = tk.Frame(self.top, bg=BG)
        btn_frame.pack(fill='x', padx=20, pady=15)
        
        ttk.Button(btn_frame,
                  text="حفظ المتابعة",
                  command=self._save_attendance).pack(side='left', padx=5)
                  
        ttk.Button(btn_frame,
                  text="توليد تقرير",
                  command=self._show_report_window).pack(side='left', padx=5)
    
    def _save_attendance(self):
        """Save attendance record to Excel file."""
        date_str = self.date_entry.get_date().strftime("%Y-%m-%d")
        status = self.status_var.get()
        subject = self.subject_var.get()
        hour = self.hour_var.get()
        notes = self.notes_text.get("1.0", "end-1c")
        
        if not all([date_str, status, subject, hour]):
            messagebox.showerror("خطأ", "الرجاء ملء جميع الحقول المطلوبة")
            return
            
        success = self.rm.append_row_to_excel(
            date_str=date_str,
            prof=self.teacher,
            type_str=status,
            matiere=subject,
            hour_str=hour,
            note=notes
        )
        
        if success:
            messagebox.showinfo("نجاح", "تم حفظ المتابعة بنجاح")
            self.notes_text.delete("1.0", "end")
        else:
            messagebox.showerror("خطأ", "حدث خطأ أثناء حفظ المتابعة")
            
    def _show_report_window(self):
        """Open report generation window for this teacher."""
        ReportGenerationWindow(self.top, self.teacher, self.dm, self.rm)


class ReportGenerationWindow:
    """Window for generating teacher attendance reports."""
    
    def __init__(self, parent: tk.Tk, teacher: str, dm: DataManager, rm: ReportManager):
        self.top = tk.Toplevel(parent)
        self.top.title(f"توليد تقرير: {teacher}")
        self.top.geometry("500x400")
        self.top.configure(bg=BG)
        
        self.teacher = teacher
        self.dm = dm
        self.rm = rm
        
        self._build_ui()
        
    def _build_ui(self):
        # Title
        title_frame = tk.Frame(self.top, bg=BG)
        title_frame.pack(fill='x', pady=15, padx=20)
        
        tk.Label(title_frame,
                text=f"📊 توليد تقرير: {self.teacher}",
                font=("Segoe UI", 16, "bold"),
                bg=BG,
                fg=TEXT_PRIMARY).pack()
        
        # Period Selection
        period_frame = tk.Frame(self.top, bg=BG)
        period_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(period_frame,
                text="الفترة:",
                font=("Segoe UI", 11),
                bg=BG).pack(side='left', padx=5)
                
        self.period_var = tk.StringVar(value="الشهر الحالي")
        periods = ["اليوم", "الأسبوع الحالي", "الشهر الحالي", "السنة الحالية"]
        period_cb = ttk.Combobox(period_frame,
                                textvariable=self.period_var,
                                values=periods,
                                width=20,
                                state="readonly")
        period_cb.pack(side='left', padx=5)
        
        # Subject Filter
        subject_frame = tk.Frame(self.top, bg=BG)
        subject_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(subject_frame,
                text="المادة (اختياري):",
                font=("Segoe UI", 11),
                bg=BG).pack(side='left', padx=5)
                
        subjects = ["كل المواد"]
        for subject, teachers in self.dm.materials_teachers.items():
            if self.teacher in teachers:
                subjects.append(subject)
                
        self.subject_var = tk.StringVar(value="كل المواد")
        subject_cb = ttk.Combobox(subject_frame,
                                textvariable=self.subject_var,
                                values=subjects,
                                width=30,
                                state="readonly")
        subject_cb.pack(side='left', padx=5)
        
        # Generate Button
        btn_frame = tk.Frame(self.top, bg=BG)
        btn_frame.pack(fill='x', padx=20, pady=20)
        
        ttk.Button(btn_frame,
                  text="توليد التقرير",
                  command=self._generate_report).pack()
                  
    def _generate_report(self):
        """Generate PDF report based on selected options."""
        period = self.period_var.get()
        subject = self.subject_var.get()
        if subject == "كل المواد":
            subject = None
            
        # Get date filter based on period
        date_filter = None
        today = datetime.date.today()
        if period == "اليوم":
            date_filter = today.strftime("%Y-%m-%d")
        
        filename = self.rm.generate_pdf_for_prof(
            prof=self.teacher,
            periode=period,
            matiere=subject,
            date_filter=date_filter
        )
        
        if filename:
            messagebox.showinfo("نجاح", f"تم توليد التقرير بنجاح\n{filename}")
        else:
            messagebox.showerror("خطأ", "حدث خطأ أثناء توليد التقرير")