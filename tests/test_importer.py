"""Simple smoke test for importer. Run with pytest after saving a sample CSV file."""
from core.data_manager import DataManager
import tempfile

SAMPLE_CSV = '''Activity Id,Day,Hour,Subject,Teachers,Room,Students Sets
1,الاثنين,1,Math,Ali Ahmed,101,4M1
2,الثلاثاء,2,Physics,Mohamed Salah,102,4M2
'''


def test_import_sample(tmp_path):
    p = tmp_path / "sample.csv"
    p.write_text(SAMPLE_CSV, encoding='utf-8')
    dm = DataManager()
    ok = dm.import_fet_activities_csv_files([str(p)])
    assert ok
    assert 'Math' in dm.materials_teachers
    assert 'Ali Ahmed' in dm.timetable_data

# End of project content
