"""
Simple smoke script: writes a small CSV, imports it with DataManager, and prints some stats.
Run: python run_smoke.py
"""
from core.data_manager import DataManager
import tempfile
import os

SAMPLE_CSV = '''Activity Id,Day,Hour,Subject,Teachers,Room,Students Sets
1,الاثنين,1,Math,Ali Ahmed,101,4M1
2,الثلاثاء,2,Physics,Mohamed Salah,102,4M2
'''

p = tempfile.gettempdir()
path = os.path.join(p, 'sample_timetable.csv')
with open(path, 'w', encoding='utf-8') as f:
    f.write(SAMPLE_CSV)

print('Wrote sample CSV to', path)

dm = DataManager()
ok = dm.import_fet_activities_csv_files([path])
print('Import OK:', ok)
print('Subjects:', list(dm.materials_teachers.keys()))
print('Teachers:', list(dm.timetable_data.keys()))
print('Classes:', list(dm.classes_timetable.keys()))
