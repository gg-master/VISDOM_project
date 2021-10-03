import os


def abspath(rel_path):
    if os.getcwd().endswith('modules'):
        os.chdir('..')
    return os.path.join(os.getcwd(), rel_path)
