"""Run every algorithm in a family on the same input and rank them."""

from typing import Any, Dict

from .core import REGISTRY, ValidationError, validate

# family -> (tile label to rank on, lower_is_better)
# Which measurement decides the winner for each comparable family, and whether smaller is better.
# The label must match a summary tile label produced by every algorithm in that family.
RANK = {
    'cpu': ('Avg waiting', True), 'page': ('Page faults', True), 'disk': ('Total head movement', True),
    'fit': ('Failed', True), 'files': ('Files placed', False), 'realtime': ('Deadline misses', True),
}


# Sibling algorithms need slightly different inputs (Priority wants a priority column, Lottery wants tickets, ...).
# When racing a family we take the caller's rows and add any missing columns with harmless defaults.
def _fill(schema, raw):
    """Give rows the columns a sibling algorithm needs (priority, tickets, nice, ...) if the caller omitted them."""
    raw = dict(raw or {})
    for spec in schema:
        if spec['type'] == 'table' and isinstance(raw.get(spec['name']), list):
            rows = []
            for row in raw[spec['name']]:
                row = dict(row)
                for col in spec['columns']:
                    row.setdefault(col['key'], col['min'] if col['kind'] == 'int' else 'x')
                rows.append(row)
            raw[spec['name']] = rows
    return raw


# Run every registered algorithm of `family` on the same input and report the ranking metric for each.
def compare(family: str, raw: Dict[str, Any]) -> Dict[str, Any]:
    if family not in RANK:
        raise ValidationError(f'Cannot compare family: {family}')
    label, lower = RANK[family]
    entries = []
    for alg in REGISTRY.values():
        if alg.family != family:
            continue
        # An algorithm that cannot accept this input (for example a size limit) is skipped rather than failing the whole race.
        try:
            out = alg.run(validate(alg.params, {**alg.example, **_fill(alg.params, raw)}))
        except ValidationError:
            continue
        # Tile values may be numbers or display strings such as '12.5%' or '3/4'; pull out the leading number.
        tiles = {t['label']: t['value'] for t in out['summary']}
        value = tiles.get(label)
        if isinstance(value, str):
            head = value.split('/')[0].rstrip('%').split()[0] if value.strip() else ''
            value = float(head) if head.replace('.', '', 1).isdigit() else None
        if value is None:
            continue
        entries.append({'id': alg.id, 'name': alg.name, 'value': value, 'tiles': out['summary'],
                        'lanes': out['data'].get('lanes') if out['viz'] == 'timeline' else None,
                        'total': out['data'].get('total') if out['viz'] == 'timeline' else None})
    if len(entries) < 2:
        raise ValidationError('Nothing to compare')
    best = min(e['value'] for e in entries) if lower else max(e['value'] for e in entries)
    for e in entries:
        e['best'] = e['value'] == best
    return {'success': True, 'family': family, 'metric': label, 'lowerIsBetter': lower, 'results': entries}
