"""DataManager: centralizes timetable data, parsing, and caching.
Keep Arabic UI labels and comments intact.
"""
from __future__ import annotations
import csv
import os
import re
import logging
from typing import Dict, List, Optional, Set, Any

logger = logging.getLogger(__name__)

DEFAULT_COLORS = ["#FFCCCB", "#B2FF66", "#FFD580", "#AED6F1", "#D7BDE2", "#ABEBC6",
                  "#F9E79F", "#F5CBA7", "#A9DFBF", "#F5B7B1", "#85C1E9", "#D6EAF8", "#FADBD8"]


class DataManager:
    """Manage import, in-memory data structures and simple queries.
    This replaces global dictionaries from the original single-file program.
    """

    def __init__(self):
        # key structures
        self.materials_teachers: Dict[str, List[str]] = {}
        self.materials_colors: Dict[str, str] = {}
        self.teachers_subjects: Dict[str, List[str]] = {}
        self.teachers_classes: Dict[str, List[str]] = {}
        self.classes_teachers: Dict[str, List[str]] = {}
        self.classes_timetable: Dict[str, List[Dict[str, Any]]] = {}
        self.timetable_data: Dict[str, List[Dict[str, Any]]] = {}

    # ----------------- normalization helpers -----------------
    @staticmethod
    def normalize_teacher_name(raw: Optional[str]) -> str:
        if raw is None:
            return ""
        s = str(raw).strip()
        if not s:
            return ""
        s = re.sub(r'\s+', ' ', s)
        parts = re.split(r'\s*(?:,|/|\+|؛|;|\||&| and )\s*', s)
        first = parts[0].strip()
        first = re.sub(r'\s*\d+$', '', first).strip()
        words = first.split()
        return " ".join(words[:2]) if len(words) >= 2 else first

    @staticmethod
    def split_teachers_field(raw: Optional[str]) -> List[str]:
        if raw is None:
            return []
        s = str(raw).strip()
        if not s:
            return []
        parts = re.split(r'\s*(?:,|/|\+|؛|;|\||&| and )\s*', s)
        out: List[str] = []
        seen: Set[str] = set()
        for p in parts:
            n = DataManager.normalize_teacher_name(p)
            if n and n not in seen:
                seen.add(n)
                out.append(n)
        return out

    @staticmethod
    def extract_weekday(day_field: Optional[str]) -> Optional[int]:
        if day_field is None:
            return None
        s = str(day_field).strip().lower()
        if not s:
            return None
        if s.isdigit():
            v = int(s)
            if 1 <= v <= 7:
                return v - 1
            if 0 <= v <= 6:
                return v
        mapping = {
            'الاثنين': 0, 'اثنين': 0, 'الإثنين': 0,
            'الثلاثاء': 1, 'الثلاثاء': 1,
            'الاربعاء': 2, 'الأربعاء': 2,
            'الخميس': 3, 'الجمعة': 4, 'السبت': 5,
            'الاحد': 6,
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        if s in mapping:
            return mapping[s]
        for k, v in mapping.items():
            if k in s:
                return v
        return None

    @staticmethod
    def hour_from_field_enhanced(h_field: Optional[str], period_from_day: Optional[str] = None) -> Optional[int]:
        if h_field is None:
            return None
        s = str(h_field).strip()
        if not s:
            return None
        numbers = re.findall(r'\d+', s)
        if not numbers:
            return None
        n = int(numbers[0])
        if period_from_day == "morning":
            if 1 <= n <= 4:
                return 7 + n
            return 8 + (n % 4)
        elif period_from_day == "afternoon":
            if 1 <= n <= 4:
                return 13 + n
            return 14 + (n % 4)
        else:
            if 1 <= n <= 8:
                if n <= 4:
                    return 7 + n
                else:
                    return 9 + n
            if 8 <= n <= 23:
                return n
            return 8 + (n % 8)

    @staticmethod
    def is_real_class(class_name: Optional[str]) -> bool:
        if not class_name:
            return False
        class_str = str(class_name).strip()
        real_classes = {f"{g}M{i}" for g in (1, 2, 3, 4) for i in range(1, 6)}
        # quick membership
        if class_str in real_classes:
            return True
        if class_str.endswith('_G1') or class_str.endswith('_G2'):
            return False
        if '_G1' in class_str or '_G2' in class_str:
            return False
        if 'استدراك' in class_str or '+' in class_str:
            return False
        return True

    @staticmethod
    def extract_main_class(class_name: Optional[str]) -> Optional[str]:
        if not class_name:
            return class_name
        s = str(class_name).strip()
        for suffix in ('_G1', '_G2'):
            if suffix in s:
                return s.split(suffix)[0]
        return s

    def color_for_subject(self, subject: Optional[str]) -> str:
        if not subject:
            return "#FFFFFF"
        if subject not in self.materials_colors:
            self.materials_colors[subject] = DEFAULT_COLORS[len(self.materials_colors) % len(DEFAULT_COLORS)]
        return self.materials_colors[subject]

    # ----------------- CSV import -----------------
    def import_fet_activities_csv_files(self, paths: List[str]) -> bool:
        """Import multiple CSVs and populate all structures.
        Returns True on success; logs issues but keeps best-effort parsing.
        """
        # clear
        self.timetable_data.clear()
        self.materials_teachers.clear()
        self.materials_colors.clear()
        self.teachers_subjects.clear()
        self.teachers_classes.clear()
        self.classes_teachers.clear()
        self.classes_timetable.clear()

        total = 0
        problematic_rows = []

        for path in paths:
            if not path or not os.path.exists(path):
                logger.warning("ملف غير موجود: %s", path)
                continue
            with open(path, encoding='utf-8-sig') as f:
                # detect delimiter by checking header line
                header = f.readline()
                f.seek(0)
                delimiter = ','
                if '\t' in header:
                    delimiter = '\t'
                elif ';' in header and header.count(';') > header.count(','):
                    delimiter = ';'
                reader = csv.DictReader(f, delimiter=delimiter)

                for row_num, row in enumerate(reader, start=1):
                    act_id = (row.get('Activity Id') or row.get('ActivityId') or row.get('ID') or '')
                    day_raw = row.get('Day') or row.get('day') or row.get('اليوم') or ''
                    hour_raw = row.get('Hour') or row.get('Period') or row.get('الساعة') or ''
                    subject = (row.get('Subject') or row.get('subject') or row.get('المادة') or '').strip()
                    teachers_raw = (row.get('Teachers') or row.get('Teacher') or row.get('الأستاذ') or '').strip()
                    students_set = (row.get('Students Sets') or row.get('Students') or row.get('Classe') or row.get('الصف') or '').strip()
                    room = (row.get('Room') or row.get('Classroom') or row.get('القاعة') or '').strip()

                    if not any([day_raw, hour_raw, teachers_raw]):
                        continue
                    teacher_names = self.split_teachers_field(teachers_raw)
                    if not teacher_names:
                        continue
                    day_str = str(day_raw)
                    period = None
                    if ' ص' in day_str:
                        period = 'morning'
                    elif ' م' in day_str:
                        period = 'afternoon'
                    day_clean = re.sub(r'\s*[مص]\s*$', '', day_str).strip()
                    wd = self.extract_weekday(day_clean)
                    start_hour = self.hour_from_field_enhanced(hour_raw, period)
                    duration = 1
                    if 'Duration' in row and row.get('Duration'):
                        try:
                            duration = int(row.get('Duration'))
                        except Exception:
                            duration = 1
                    if wd is None or start_hour is None:
                        problematic_rows.append((path, row_num, day_raw, hour_raw))

                    for teacher in teacher_names:
                        if subject:
                            self.materials_teachers.setdefault(subject, set()).add(teacher)
                            self.teachers_subjects.setdefault(teacher, set()).add(subject)
                        if students_set:
                            main_class = self.extract_main_class(students_set)
                            if self.is_real_class(main_class):
                                self.teachers_classes.setdefault(teacher, set()).add(main_class)
                                self.classes_teachers.setdefault(main_class, set()).add(teacher)
                        activity = {
                            'weekday': wd,
                            'start_hour': start_hour,
                            'duration': duration,
                            'subject': subject,
                            'room': room,
                            'class': students_set,
                            'activity_id': act_id or None,
                            'source_file': os.path.basename(path),
                            'original_hour_field': hour_raw,
                            'original_day_field': day_raw,
                            'period': period
                        }
                        self.timetable_data.setdefault(teacher, []).append(activity)
                        if students_set:
                            main_class = self.extract_main_class(students_set)
                            if self.is_real_class(main_class):
                                class_activity = activity.copy()
                                class_activity['teacher'] = teacher
                                class_activity['original_class'] = students_set
                                self.classes_timetable.setdefault(main_class, []).append(class_activity)
                        total += 1

        # finalize: convert sets to sorted lists
        for subject in list(self.materials_teachers.keys()):
            self.materials_teachers[subject] = sorted(list(self.materials_teachers[subject]))
        for teacher in list(self.teachers_subjects.keys()):
            self.teachers_subjects[teacher] = sorted(list(self.teachers_subjects[teacher]))
        for teacher in list(self.teachers_classes.keys()):
            self.teachers_classes[teacher] = sorted(list(self.teachers_classes[teacher]))
        for class_name in list(self.classes_teachers.keys()):
            self.classes_teachers[class_name] = sorted(list(self.classes_teachers[class_name]))

        # assign colors deterministically
        mats = sorted(list(self.materials_teachers.keys()))
        for i, m in enumerate(mats):
            self.materials_colors[m] = DEFAULT_COLORS[i % len(DEFAULT_COLORS)]

        logger.info("Imported %d activities from %d files (%d problematic rows)", total, len(paths), len(problematic_rows))
        return True

    # ----------------- query helpers -----------------
    def sessions_for_prof_on_date(self, prof: str, date_obj) -> Optional[List[Dict[str, Any]]]:
        if prof not in self.timetable_data:
            return None
        wd = date_obj.weekday()
        sessions: List[Dict[str, Any]] = []
        for s in self.timetable_data.get(prof, []):
            s_wd = s.get('weekday')
            s_start = s.get('start_hour')
            s_dur = s.get('duration', 1)
            if s_start is None:
                continue
            if s_wd is not None and s_wd != wd:
                continue
            for h in range(s_start, s_start + max(1, s_dur)):
                if 8 <= h <= 20:
                    sessions.append({'start_hour': h, 'subject': s.get('subject', ''), 'room': s.get('room', ''), 'class': s.get('class', '')})
        uniq = {it['start_hour']: it for it in sessions}
        return [uniq[h] for h in sorted(uniq.keys())]


