"""Static checks that the frontend's ES modules and assets resolve."""
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
IMPORT = re.compile(r"from\s+'(\.[^']+)'")


def js_files():
    for base, _, files in os.walk(os.path.join(ROOT, 'js')):
        for name in files:
            if name.endswith('.js'):
                yield os.path.join(base, name)


def test_index_references_existing_files():
    html = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    for ref in re.findall(r'(?:src|href)="((?:js|css)/[^"]+)"', html):
        assert os.path.exists(os.path.join(ROOT, ref)), ref


def test_relative_imports_resolve():
    for path in js_files():
        for target in IMPORT.findall(open(path, encoding='utf-8').read()):
            assert os.path.exists(os.path.normpath(os.path.join(os.path.dirname(path), target))), \
                f'{path} imports missing {target}'


def test_no_innerhtml_in_frontend():
    """All dynamic text must go through text nodes (XSS-safe by construction)."""
    for path in js_files():
        assert 'innerHTML' not in open(path, encoding='utf-8').read(), path


def test_vercel_entrypoint_exposes_app():
    """api/index.py must keep a module-level `app` (an unused-import cleanup once removed it)."""
    path = os.path.join(ROOT, '..', 'api', 'index.py')
    source = open(path, encoding='utf-8').read()
    assert re.search(r'^from backend\.app import app\b', source, re.M)
