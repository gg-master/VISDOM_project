import os
import sys


def abspath(rel_path: str) -> str:
    rel_path = '/'.join(rel_path.split('\\'))
    if os.getcwd().endswith('modules'):
        os.chdir('..')
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, rel_path)
