"""Tkinter main UI entry point. Keeps Arabic labels intact.
This module uses DataManager and ReportManager to provide functionality.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import os
from typing import List
from tkcalendar import DateEntry

from core.data_manager import DataManager
from report.report_manager import ReportManager
from ui.attendance_windows import TeacherAttendanceWindow, ReportGenerationWindow

logger = logging.getLogger(__name__)

# Modern color scheme
BG = "#f8f9fa" 
ACCENT = "#4361ee"  
ACCENT_LIGHT = "#4895ef" 
TEXT_PRIMARY = "#212529"  
TEXT_SECONDARY = "#6c757d"  

# Status colors with modern hues
COLOR_PRESENT = "#00b4d8"  
COLOR_ABSENT = "#ef476f"  
COLOR_LATE = "#ffd60a"    

# Button styles
BTN_STYLE = {
    "font": ("Segoe UI", 10),
    "borderwidth": 0,
    "relief": "flat",
    "padx": 15,
    "pady": 8,
}


class UIManager:
    def __init__(self, root: tk.Tk, data_manager: DataManager, report_manager: ReportManager):
        self.root = root
        self.dm = data_manager
        self.rm = report_manager

    def build_main_ui(self):
        style = ttk.Style()
        style.configure('Modern.TButton', 
                       font=('Segoe UI', 10),
                       padding=(15, 8))
        style.configure('Title.TLabel',
                       font=('Segoe UI', 24, 'bold'),
                       background=BG,
                       foreground=ACCENT)
        
        for w in self.root.winfo_children():
            w.destroy()
            
        # Create main container with padding
        main_container = tk.Frame(self.root, bg=BG)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title with modern styling
        title_frame = tk.Frame(main_container, bg=BG)
        title_frame.pack(fill='x', pady=(0, 20))
        tk.Label(title_frame, 
                text='📚 برنامج منصوري لمتابعة عمل الأساتذة',
                font=("Segoe UI", 24, "bold"),
                bg=BG,
                fg=ACCENT).pack(pady=10)
        
        # Top controls with modern buttons
        top_controls = tk.Frame(main_container, bg=BG)
        top_controls.pack(fill='x', pady=(0, 15))
        
        for btn_text, cmd in [
            ("📅 استيراد جدول CSV", self.import_csv_and_refresh),
            ("🔍 التحقق من البيانات", self.verify_timetable_match),
            ("🏫 عرض جميع الأقسام", self.open_classes_window)
        ]:
            btn = tk.Button(top_controls, 
                          text=btn_text,
                          command=cmd,
                          bg=ACCENT,
                          fg='white',
                          **BTN_STYLE)
            btn.pack(side='left', padx=5)
            # Add hover effect
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=ACCENT_LIGHT))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=ACCENT))
            
        tk.Label(top_controls,
                text="(استيراد CSV من FET)",
                bg=BG,
                fg=TEXT_SECONDARY,
                font=("Segoe UI", 9)).pack(side='left', padx=15)

        # Stats with modern cards
        stats_frame = tk.Frame(main_container, bg=BG)
        stats_frame.pack(fill='x', pady=(0, 20))
        
        stats = [
            ("📚 المواد", len(self.dm.materials_teachers)),
            ("👨‍🏫 الأساتذة", len(self.dm.timetable_data)),
            ("🏫 الأقسام", len(self.dm.classes_timetable))
        ]
        
        for label, count in stats:
            stat_card = tk.Frame(stats_frame, bg='white', bd=0)
            stat_card.pack(side='left', padx=10, expand=True, fill='x')
            
            # Add subtle border and shadow effect
            stat_card.config(highlightbackground="#e9ecef", highlightthickness=1)
            
            tk.Label(stat_card,
                    text=label,
                    bg='white',
                    fg=TEXT_SECONDARY,
                    font=("Segoe UI", 11)).pack(pady=(10, 5))
            tk.Label(stat_card,
                    text=str(count),
                    bg='white',
                    fg=TEXT_PRIMARY,
                    font=("Segoe UI", 16, "bold")).pack(pady=(0, 10))

        # Main content area
        main_frame = tk.Frame(main_container, bg=BG)
        main_frame.pack(fill='both', expand=True, pady=10)
        
        # Left side - Subjects grid
        left = tk.Frame(main_frame, bg=BG)
        left.pack(side='left', fill='both', expand=True, padx=10)
        
        if not self.dm.materials_teachers:
            empty_frame = tk.Frame(left, bg='white', bd=0)
            empty_frame.pack(expand=True, fill='both', padx=20, pady=20)
            empty_frame.config(highlightbackground="#e9ecef", highlightthickness=1)
            
            tk.Label(empty_frame,
                    text="لم يتم استيراد الجدول بعد",
                    bg='white',
                    fg=TEXT_PRIMARY,
                    font=("Segoe UI", 12, "bold")).pack(pady=(20, 10))
            tk.Label(empty_frame,
                    text="اضغط 'استيراد جدول CSV' أو ضع ملف CSV في المجلد",
                    bg='white',
                    fg=TEXT_SECONDARY,
                    font=("Segoe UI", 10)).pack(pady=(0, 20))
        else:
            mats = list(self.dm.materials_teachers.keys())
            cols = 3; r = c = 0
            for i, mat in enumerate(mats):
                color = self.dm.materials_colors.get(mat, '#ddd')
                btn = tk.Button(left, 
                              text=mat,
                              font=("Segoe UI", 11, "bold"),
                              fg=TEXT_PRIMARY,
                              bg='white',
                              width=24,
                              height=2,
                              command=lambda m=mat: self.open_material_window(m))
                btn.grid(row=r, column=c, padx=5, pady=5, sticky='nsew')
                
                # Add hover effect and modern styling
                btn.config(highlightbackground=color, highlightthickness=2,
                         relief='flat', borderwidth=0)
                btn.bind('<Enter>', lambda e, b=btn: b.configure(bg='#f8f9fa'))
                btn.bind('<Leave>', lambda e, b=btn: b.configure(bg='white'))
                
                c += 1
                if c >= cols:
                    c = 0; r += 1
        # Right side - Teachers list
        right = tk.Frame(main_frame, bg='white', width=360)
        right.pack(side='right', fill='y', padx=10)
        right.config(highlightbackground="#e9ecef", highlightthickness=1)
        
        # Teachers list header
        tk.Label(right,
                text="👨‍🏫 قائمة الأساتذة",
                font=("Segoe UI", 12, "bold"),
                bg='white',
                fg=TEXT_PRIMARY).pack(pady=15)
        
        # Modern listbox with custom styling
        lb_frame = tk.Frame(right, bg='white')
        lb_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        lb = tk.Listbox(lb_frame,
                       width=36,
                       height=20,
                       font=("Segoe UI", 10),
                       selectmode='browse',
                       activestyle='none',
                       relief='flat',
                       bg='white',
                       fg=TEXT_PRIMARY,
                       selectbackground=ACCENT,
                       selectforeground='white',
                       highlightthickness=1,
                       highlightbackground="#e9ecef")
        lb.pack(side='left', fill='both', expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(lb_frame, orient='vertical', command=lb.yview)
        scrollbar.pack(side='right', fill='y')
        lb.configure(yscrollcommand=scrollbar.set)
        
        # Populate list
        for t in sorted(self.dm.timetable_data.keys()):
            lb.insert('end', t)

        def on_select_teacher(evt=None):
            sel = lb.curselection()
            if not sel: return
            prof = lb.get(sel[0])
            TeacherAttendanceWindow(self.root, prof, self.dm, self.rm)

        lb.bind("<Double-Button-1>", on_select_teacher)
        ttk.Button(right, text="فتح ملف الأستاذ", command=on_select_teacher).pack(pady=6)
        ttk.Button(right, text="استيراد CSV", command=self.import_csv_and_refresh).pack(pady=6)
        ttk.Button(right, text="عرض الأقسام", command=self.open_classes_window).pack(pady=6)

    # ----- simplified windows (you can expand) -----
    def import_csv_and_refresh(self):
        file_paths = filedialog.askopenfilenames(title="استيراد جدول CSV من FET",
                                                 filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not file_paths:
            return
        ok = self.dm.import_fet_activities_csv_files(list(file_paths))
        if ok:
            self.build_main_ui()

    def verify_timetable_match(self):
        if not self.dm.timetable_data:
            messagebox.showinfo("Info", "لم يتم استيراد أي بيانات بعد")
            return
        summary = f"البيانات المستوردة:\n" \
                  f"عدد الأساتذة: {len(self.dm.timetable_data)}\n" \
                  f"عدد المواد: {len(self.dm.materials_teachers)}\n" \
                  f"عدد الأقسام: {len(self.dm.classes_timetable)}\n"
        messagebox.showinfo("تحقق من البيانات", summary)

    def open_classes_window(self):
        if not self.dm.classes_timetable:
            messagebox.showinfo("معلومة", "لم يتم استيراد أي بيانات عن الأقسام بعد")
            return
        top = tk.Toplevel(self.root); top.title("جميع الأقسام"); top.geometry("500x600"); top.configure(bg=BG)
        tk.Label(top, text="🏫 جميع الأقسام", font=("Arial", 16, "bold"), bg=BG).pack(pady=12)
        lb = tk.Listbox(top, width=60, height=25)
        lb.pack(padx=8, pady=8, fill='both', expand=True)
        for class_name in sorted(self.dm.classes_timetable.keys()):
            teachers_count = len(self.dm.classes_teachers.get(class_name, []))
            activities_count = len(self.dm.classes_timetable.get(class_name, []))
            lb.insert('end', f"{class_name} ({teachers_count} أستاذ - {activities_count} حصة)")

    def open_material_window(self, matiere: str):
        top = tk.Toplevel(self.root); top.title(f"أساتذة {matiere}"); top.geometry("380x480"); top.configure(bg=BG)
        tk.Label(top, text=f"أساتذة {matiere}", font=("Arial", 14, "bold"), bg=BG).pack(pady=10)
        profs = self.dm.materials_teachers.get(matiere, [])
        if not profs:
            tk.Label(top, text="لا يوجد أساتذة مسجلين لهذه المادة", bg=BG).pack(pady=8); return
        for p in profs:
            ttk.Button(top, text=p, width=34, command=lambda pr=p: TeacherAttendanceWindow(self.root, pr, self.dm, self.rm)).pack(pady=6)


