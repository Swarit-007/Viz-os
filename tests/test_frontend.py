"""Static checks that the front end is wired to the back end and stays free of unsafe patterns."""
import os
import re

import vizos.algos  # noqa: F401
from vizos.core import REGISTRY

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WEB = os.path.join(ROOT, 'web')
IMPORT = re.compile(r"from\s+'(\.[^']+)'")


def js_files():
    for base, _, files in os.walk(os.path.join(WEB, 'js')):
        for name in files:
            if name.endswith('.js'):
                yield os.path.join(base, name)


def read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def test_index_references_existing_files():
    html = read(os.path.join(WEB, 'index.html'))
    for ref in re.findall(r'(?:src|href)="((?:js|css)/[^"]+)"', html):
        assert os.path.exists(os.path.join(WEB, ref)), ref


def test_relative_imports_resolve():
    for path in js_files():
        for target in IMPORT.findall(read(path)):
            assert os.path.exists(os.path.normpath(os.path.join(os.path.dirname(path), target))), f'{path} imports missing {target}'


def test_every_viz_kind_has_a_renderer():
    registry = read(os.path.join(WEB, 'js', 'viz', 'index.js'))
    block = re.search(r'RENDERERS = \{(.*?)\};', registry, re.S).group(1)
    renderers = set(re.findall(r"[\w-]+", block))
    used = {a.viz for a in REGISTRY.values()}
    assert used <= renderers, used - renderers


def test_no_innerhtml_and_no_em_dash_in_copy():
    for path in js_files():
        text = read(path)
        assert 'innerHTML' not in text, path
        assert '—' not in text, path
    assert '—' not in read(os.path.join(WEB, 'index.html'))


def test_vercel_entrypoint_exposes_app():
    """api/index.py must keep a module-level `app`; an unused-import cleanup once removed it and broke every deploy."""
    source = read(os.path.join(ROOT, 'api', 'index.py'))
    assert re.search(r'^from vizos\.app import app\b', source, re.M)


def test_vercel_config_routes_to_entrypoint():
    config = read(os.path.join(ROOT, 'vercel.json'))
    assert 'api/index.py' in config
