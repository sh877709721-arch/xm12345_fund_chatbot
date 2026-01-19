import sys
import builtins
import os
import traceback
from pathlib import Path

TARGET = None
if len(sys.argv) >= 2:
    TARGET = sys.argv[1]

orig_makedirs = os.makedirs
orig_mkdir = os.mkdir
orig_pathlib_mkdir = Path.mkdir


def _report_and_call(func, path, *args, **kwargs):
    try:
        if 'workspace' in str(path):
            print('Detected creation of path containing "workspace"')
            traceback.print_stack()
        return func(path, *args, **kwargs)
    except Exception:
        raise


def watched_makedirs(path, *args, **kwargs):
    return _report_and_call(orig_makedirs, path, *args, **kwargs)


def watched_mkdir(path, *args, **kwargs):
    return _report_and_call(orig_mkdir, path, *args, **kwargs)


def watched_pathlib_mkdir(self, *args, **kwargs):
    return _report_and_call(orig_pathlib_mkdir, self, *args, **kwargs)


# Patch
os.makedirs = watched_makedirs
os.mkdir = watched_mkdir
Path.mkdir = watched_pathlib_mkdir

print('Patched os.makedirs, os.mkdir, and pathlib.Path.mkdir')

if TARGET:
    # Execute target module as script
    with open(TARGET, 'rb') as f:
        code = compile(f.read(), TARGET, 'exec')
        globals_dict = {'__name__': '__main__', '__file__': TARGET}
        exec(code, globals_dict)
else:
    print('Usage: python run_with_monitor.py <script.py>')
