"""Algorithm registry, parameter schema validation and result helpers.

An algorithm is registered once with `@algorithm(...)`. Its metadata (summary, complexity,
pseudocode, parameter schema) is served to the frontend, which builds forms and pages from it,
so adding an algorithm never requires frontend form code.
"""

import random
from dataclasses import dataclass, field
from numbers import Real
from typing import Any, Callable, Dict, List, Optional


class ValidationError(ValueError):
    """Raised for malformed client input. Maps to HTTP 400."""


# The chapters shown on the home page, in order. Every algorithm names one of these ids as its `category`.
CATEGORIES = [
    {'id': 'cpu', 'name': 'CPU Scheduling', 'blurb': 'Who gets the processor next, and for how long.'},
    {'id': 'realtime', 'name': 'Real-time', 'blurb': 'Scheduling when missing a deadline is a failure.'},
    {'id': 'sync', 'name': 'Synchronization', 'blurb': 'Threads sharing state without corrupting it.'},
    {'id': 'deadlock', 'name': 'Deadlocks', 'blurb': 'Avoiding, detecting and reading circular waits.'},
    {'id': 'paging', 'name': 'Virtual Memory', 'blurb': 'Pages, frames, translation and eviction.'},
    {'id': 'memory', 'name': 'Memory Allocation', 'blurb': 'Carving a finite address space into pieces.'},
    {'id': 'disk', 'name': 'Disk and Storage', 'blurb': 'Moving a head, spreading blocks, surviving failure.'},
    {'id': 'files', 'name': 'File Systems', 'blurb': 'How a file becomes a set of blocks.'},
    {'id': 'misc', 'name': 'Processes and Caches', 'blurb': 'Process creation and cache behaviour.'},
]

# Safety limits so a request can never make the server do unbounded work.
# MAX_ROWS caps list and table inputs; MAX_TIME caps arrival/burst-style numbers.
MAX_ROWS = 60
MAX_TIME = 1000


# One entry in the catalog. Everything the front end needs to build a page comes from here:
# the text (name, summary, notes), the figure kind (viz), the pseudocode lines that steps refer to by index,
# the parameter schema (params) that drives the input form, an example input and a random-input generator.
@dataclass
class Algorithm:
    id: str
    name: str
    category: str
    summary: str
    viz: str
    complexity: Dict[str, str]
    pseudocode: List[str]
    params: List[Dict[str, Any]]
    run: Callable[[Dict[str, Any]], Dict[str, Any]]
    example: Dict[str, Any]
    random: Callable[[random.Random], Dict[str, Any]]
    notes: List[str] = field(default_factory=list)
    # Algorithms sharing a `family` can be raced against each other on the same input (see compare.py).
    family: Optional[str] = None       # algorithms in the same family can be compared
    tags: List[str] = field(default_factory=list)

    def public(self) -> Dict[str, Any]:
        return {'id': self.id, 'name': self.name, 'category': self.category, 'summary': self.summary,
                'viz': self.viz, 'complexity': self.complexity, 'pseudocode': self.pseudocode,
                'params': self.params, 'example': self.example, 'notes': self.notes,
                'family': self.family, 'tags': self.tags}


# id -> Algorithm. Filled at import time by the @algorithm decorator in vizos/algos/*.
REGISTRY: Dict[str, Algorithm] = {}


# Registration is a decorator so an algorithm's metadata sits right next to its code:
#
#     @algorithm(id='fcfs', name='...', category='cpu', viz='timeline', ...)
#     def fcfs(params): ...
def algorithm(**meta):
    """Decorator: register `run(params) -> result` together with its metadata."""
    def wrap(fn):
        # Fail loudly at import time (not at request time) if the registry is inconsistent.
        alg = Algorithm(run=fn, **meta)
        if alg.id in REGISTRY:
            raise RuntimeError(f'duplicate algorithm id: {alg.id}')
        if alg.category not in {c['id'] for c in CATEGORIES}:
            raise RuntimeError(f'unknown category: {alg.category}')
        REGISTRY[alg.id] = alg
        return fn
    return wrap


# --------------------------------------------------------------------------- parameter schema
# ---- schema builders -------------------------------------------------------------------------------
# Each returns a plain dict. The dict is sent to the browser (to draw the form) and used by validate() below
# (to check the request), so the two can never disagree.
def Int(name, label, default, lo=0, hi=1000, hint=''):
    return {'name': name, 'type': 'int', 'label': label, 'default': default, 'min': lo, 'max': hi, 'hint': hint}


def Choice(name, label, options, default=None, hint=''):
    opts = [{'value': o, 'label': o} if isinstance(o, str) else {'value': o[0], 'label': o[1]} for o in options]
    return {'name': name, 'type': 'choice', 'label': label, 'options': opts,
            'default': default if default is not None else opts[0]['value'], 'hint': hint}


def Bool(name, label, default=False, hint=''):
    return {'name': name, 'type': 'bool', 'label': label, 'default': default, 'hint': hint}


def IntList(name, label, default, lo=0, hi=1000, min_len=1, max_len=MAX_ROWS, hint=''):
    return {'name': name, 'type': 'intlist', 'label': label, 'default': default, 'min': lo, 'max': hi,
            'minLen': min_len, 'maxLen': max_len, 'hint': hint}


def Lines(name, label, default, max_len=MAX_ROWS, hint='', placeholder=''):
    return {'name': name, 'type': 'lines', 'label': label, 'default': default, 'maxLen': max_len,
            'hint': hint, 'placeholder': placeholder}


def Seed(name='seed', label='Random seed', default=1):
    return {'name': name, 'type': 'int', 'label': label, 'default': default, 'min': 0, 'max': 10_000_000,
            'hint': 'The same seed always gives the same run.'}


def Table(name, label, columns, default, min_rows=1, max_rows=MAX_ROWS, hint='', id_prefix='P'):
    """Editable rows. columns: [{'key', 'label', 'kind': 'int'|'text', 'min', 'max'}]. A row's `id` is automatic."""
    return {'name': name, 'type': 'table', 'label': label, 'columns': columns, 'default': default,
            'minRows': min_rows, 'maxRows': max_rows, 'hint': hint, 'idPrefix': id_prefix}


def Col(key, label, lo=0, hi=MAX_TIME, kind='int'):
    return {'key': key, 'label': label, 'kind': kind, 'min': lo, 'max': hi}


def Matrix(name, label, rows, cols, default, lo=0, hi=99, hint=''):
    return {'name': name, 'type': 'matrix', 'label': label, 'rows': rows, 'cols': cols, 'default': default,
            'min': lo, 'max': hi, 'hint': hint}


def Vector(name, label, length, default, lo=0, hi=99, hint=''):
    return {'name': name, 'type': 'vector', 'label': label, 'length': length, 'default': default,
            'min': lo, 'max': hi, 'hint': hint}


# Strict integer check. Booleans are rejected because JSON `true` would otherwise pass as the number 1.
def _int(value, label, lo, hi):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValidationError(f'{label} must be a number')
    if int(value) != value:
        raise ValidationError(f'{label} must be a whole number')
    value = int(value)
    if value < lo:
        raise ValidationError(f'{label} must be at least {lo}')
    if value > hi:
        raise ValidationError(f'{label} must be at most {hi}')
    return value


# Turn untrusted request JSON into clean Python values, or raise ValidationError with a readable message.
# Fields missing from `raw` take the schema default, so `{}` is always a valid request.
def validate(schema: List[Dict[str, Any]], raw: Any) -> Dict[str, Any]:
    """Validate and coerce `raw` against `schema`. Missing fields take their defaults."""
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValidationError('params must be an object')
    out: Dict[str, Any] = {}
    for spec in schema:
        name, kind, label = spec['name'], spec['type'], spec['label']
        value = raw.get(name, spec.get('default'))
        if kind == 'int':
            out[name] = _int(value, label, spec['min'], spec['max'])
        elif kind == 'bool':
            out[name] = bool(value)
        elif kind == 'choice':
            allowed = [o['value'] for o in spec['options']]
            if value not in allowed:
                raise ValidationError(f'{label} must be one of: {", ".join(map(str, allowed))}')
            out[name] = value
        elif kind == 'intlist':
            if not isinstance(value, list) or not spec['minLen'] <= len(value) <= spec['maxLen']:
                raise ValidationError(f'{label} needs {spec["minLen"]} to {spec["maxLen"]} numbers')
            out[name] = [_int(v, f'{label}[{i + 1}]', spec['min'], spec['max']) for i, v in enumerate(value)]
        elif kind == 'lines':
            if not isinstance(value, list) or not 1 <= len(value) <= spec['maxLen']:
                raise ValidationError(f'{label} needs 1 to {spec["maxLen"]} lines')
            out[name] = [str(v).strip() for v in value if str(v).strip()]
            if not out[name]:
                raise ValidationError(f'{label} must not be empty')
        elif kind == 'table':
            out[name] = _table(spec, value)
        # Matrices and vectors size themselves from other integer parameters (e.g. n processes x m resources),
        # which is why those integers must appear earlier in the schema.
        elif kind == 'matrix':
            rows, cols = out.get(spec['rows']), out.get(spec['cols'])
            if rows is None or cols is None:
                raise ValidationError(f'{label}: size parameters must come first in the schema')
            if not isinstance(value, list) or len(value) != rows:
                raise ValidationError(f'{label} must have {rows} rows')
            out[name] = []
            for i, row in enumerate(value):
                if not isinstance(row, list) or len(row) != cols:
                    raise ValidationError(f'{label} row {i + 1} must have {cols} columns')
                out[name].append([_int(v, f'{label}[{i + 1}][{j + 1}]', spec['min'], spec['max'])
                                  for j, v in enumerate(row)])
        elif kind == 'vector':
            length = out.get(spec['length'], spec['length']) if isinstance(spec['length'], str) else spec['length']
            if not isinstance(value, list) or len(value) != length:
                raise ValidationError(f'{label} must have {length} entries')
            out[name] = [_int(v, f'{label}[{i + 1}]', spec['min'], spec['max']) for i, v in enumerate(value)]
        else:
            raise RuntimeError(f'unknown schema type {kind}')
    return out


# Validate an editable table. Row ids (P1, P2, ...) are generated here, never trusted from the client.
def _table(spec, value):
    if not isinstance(value, list) or not spec['minRows'] <= len(value) <= spec['maxRows']:
        raise ValidationError(f'{spec["label"]} needs {spec["minRows"]} to {spec["maxRows"]} rows')
    rows, seen = [], set()
    for i, raw in enumerate(value):
        if not isinstance(raw, dict):
            raise ValidationError(f'{spec["label"]} row {i + 1} must be an object')
        row = {'id': str(raw.get('id') or f'{spec["idPrefix"]}{i + 1}')}
        if row['id'] in seen:
            raise ValidationError(f'duplicate id {row["id"]}')
        seen.add(row['id'])
        for col in spec['columns']:
            v = raw.get(col['key'], 0 if col['kind'] == 'int' else '')
            if col['kind'] == 'int':
                row[col['key']] = _int(v, f'{row["id"]} {col["label"]}', col['min'], col['max'])
            else:
                row[col['key']] = str(v).strip()
                if not row[col['key']]:
                    raise ValidationError(f'{row["id"]} {col["label"]} must not be empty')
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- results
# ---- results ------------------------------------------------------------------------------------------
# A `tile` is one labelled number in the Measurements panel. tone is 'good', 'bad' or None (colours the value).
def tile(label, value, hint=None, tone=None):
    return {'label': label, 'value': value, 'hint': hint, 'tone': tone}


# Collects the playback steps of a run. Each step is one frame of the animation:
#   note  - the sentence shown as the figure caption
#   lines - indexes into the algorithm's pseudocode to highlight
#   at    - where the figure should be drawn: a time value for timelines, a snapshot index for everything else
class Trace:
    """Collects playback steps. `at` is the cursor value the visualisation should render at."""

    def __init__(self):
        self.steps: List[Dict[str, Any]] = []

    def add(self, note: str, lines=(), at: Optional[float] = None, **extra):
        step = {'note': note, 'lines': list(lines), 'at': len(self.steps) + 1 if at is None else at}
        step.update(extra)
        self.steps.append(step)


# The one response shape every algorithm returns, so the front end has a single contract to code against.
#   summary - list of tiles, steps - the Trace, data - whatever the figure needs, table - optional results table,
#   verdict - optional {ok, label, text} shown as a rubber stamp (e.g. 'Deadlock').
def result(alg_id: str, viz: str, summary, trace: Trace, data: Dict[str, Any], table=None, verdict=None):
    return {'success': True, 'id': alg_id, 'viz': viz, 'summary': summary, 'steps': trace.steps,
            'data': data, 'table': table, 'verdict': verdict}


# Look up, validate, run. The only entry point the API uses to execute an algorithm.
def run_algorithm(alg_id: str, raw: Any) -> Dict[str, Any]:
    alg = REGISTRY.get(alg_id)
    if alg is None:
        raise ValidationError(f'Unknown algorithm: {alg_id}')
    return alg.run(validate(alg.params, raw))


# A random but always valid input. The same seed gives the same input, which makes shared links and tests repeatable.
def random_params(alg_id: str, seed: Optional[int] = None) -> Dict[str, Any]:
    alg = REGISTRY.get(alg_id)
    if alg is None:
        raise ValidationError(f'Unknown algorithm: {alg_id}')
    rng = random.Random(seed if seed is not None else random.randrange(1 << 30))
    params = alg.random(rng)
    validate(alg.params, params)  # generators must always produce valid input
    return params
