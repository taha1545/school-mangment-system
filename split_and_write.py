"""
Splitter for `test.py` that writes embedded `### FILE: <path>` sections to real files.
Run: python split_and_write.py
"""
import os
import re

SRC = r"c:\Users\DELL\Desktop\3ami\test.py"
BASE = os.path.dirname(SRC)

def main():
    with open(SRC, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_path = None
    buf = []
    created = []

    def flush():
        if not current_path:
            return
        dest = os.path.join(BASE, current_path)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        # remove leading/trailing code fence lines
        while buf and buf[0].strip().startswith('```'):
            buf.pop(0)
        while buf and buf[-1].strip().startswith('```'):
            buf.pop()
        with open(dest, 'w', encoding='utf-8') as out:
            out.writelines(buf)
        created.append(dest)

    header_re = re.compile(r'^### FILE:\s*(.+)')
    for line in lines:
        m = header_re.match(line)
        if m:
            # flush previous
            if current_path:
                flush()
            current_path = m.group(1).strip()
            buf = []
            continue
        if current_path is None:
            # skip preamble
            continue
        buf.append(line)

    if current_path:
        flush()

    print(f"Wrote {len(created)} files:")
    for p in created:
        print(" -", p)

if __name__ == '__main__':
    main()
