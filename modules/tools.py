import os


def abspath(rel_path):
    rel_path = '/'.join(rel_path.split('\\'))
    if os.getcwd().endswith('modules'):
        os.chdir('..')
    return os.path.join(os.getcwd(), rel_path)
