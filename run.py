"""Entry point to start the refactored app."""
from __future__ import annotations
import tkinter as tk
from utils.helpers import setup_logging
from core.data_manager import DataManager
from report.report_manager import ReportManager
from ui.main_ui import UIManager


def main():
    setup_logging(None)
    dm = DataManager()
    rm = ReportManager()
    root = tk.Tk()
    root.title('ناظر المدرسة - Suivi des enseignants')
    root.geometry('1200x800')
    root.configure(bg='#f8f9fa')
    # 
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - 1200) // 2
    y = (screen_height - 800) // 2
    root.geometry(f'1200x800+{x}+{y}')
    # 
    root.minsize(1000, 700)
    ui = UIManager(root, dm, rm)
    ui.build_main_ui()
    root.mainloop()

if __name__ == '__main__':
    main()

