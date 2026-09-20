"""Every registered algorithm must honour the same contract the front end relies on."""
import json

import pytest

import vizos.algos  # noqa: F401
from vizos.core import CATEGORIES, REGISTRY, ValidationError, random_params, run_algorithm, validate

IDS = sorted(REGISTRY)
VIZ = {'timeline', 'philosophers', 'buffer', 'race', 'sync-state', 'banker', 'graph', 'frames', 'curve', 'translate', 'multilevel',
       'partitions', 'memory', 'disk', 'grid', 'inode', 'tree'}


def test_catalog_is_large_and_categories_are_all_used():
    assert len(REGISTRY) >= 50
    assert {a.category for a in REGISTRY.values()} == {c['id'] for c in CATEGORIES}


@pytest.mark.parametrize('alg_id', IDS)
def test_metadata_is_complete(alg_id):
    alg = REGISTRY[alg_id]
    assert alg.name and alg.summary and alg.viz in VIZ
    assert alg.pseudocode and all(isinstance(line, str) for line in alg.pseudocode)
    assert alg.complexity.get('time') and alg.complexity.get('space')
    assert alg.params and alg.notes
    json.dumps(alg.public())


@pytest.mark.parametrize('alg_id', IDS)
def test_example_runs_and_result_follows_contract(alg_id):
    alg = REGISTRY[alg_id]
    out = run_algorithm(alg_id, alg.example)
    assert out['success'] and out['id'] == alg_id and out['viz'] == alg.viz
    assert out['summary'] and out['steps']
    for step in out['steps']:
        assert isinstance(step['note'], str) and step['note']
        assert all(isinstance(i, int) and 0 <= i < len(alg.pseudocode) for i in step['lines']), (alg_id, step)
        assert isinstance(step['at'], (int, float))
    for tile in out['summary']:
        assert {'label', 'value'} <= set(tile)
    json.dumps(out)


@pytest.mark.parametrize('alg_id', IDS)
def test_random_inputs_are_always_valid_and_deterministic(alg_id):
    for seed in range(25):
        params = random_params(alg_id, seed)
        assert params == random_params(alg_id, seed)
        run_algorithm(alg_id, params)


@pytest.mark.parametrize('alg_id', IDS)
def test_defaults_alone_are_a_valid_input(alg_id):
    run_algorithm(alg_id, {})


def test_unknown_algorithm_and_bad_params_rejected():
    with pytest.raises(ValidationError):
        run_algorithm('nope', {})
    with pytest.raises(ValidationError):
        run_algorithm('fcfs', 'x')
    with pytest.raises(ValidationError):
        run_algorithm('fcfs', {'processes': []})
    with pytest.raises(ValidationError):
        run_algorithm('rr', {'quantum': 0})


def test_schema_types_validate():
    schema = REGISTRY['bankers'].params
    good = REGISTRY['bankers'].example
    validate(schema, good)
    for mutate in (lambda d: d.update(n=0), lambda d: d.update(available=[1]), lambda d: d.update(allocation=[[1]]),
                   lambda d: d.update(n=True), lambda d: d.update(m=1.5)):
        bad = json.loads(json.dumps(good))
        mutate(bad)
        with pytest.raises(ValidationError):
            validate(schema, bad)
