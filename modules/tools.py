import os


def abspath(rel_path: str) -> str:
    rel_path = '/'.join(rel_path.split('\\'))
    if os.getcwd().endswith('modules'):
        os.chdir('..')
    return rel_path
