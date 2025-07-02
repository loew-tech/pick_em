from unittest.mock import patch, mock_open

import pytest

import pick_em
from pick_em import app, pick_item, Option

# test cases generated with ChatGPT


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Hello World' in rv.data


def test_categories(client):
    rv = client.get('/categories')
    assert rv.status_code == 200
    categories = rv.get_json()
    assert isinstance(categories, list)


def test_get_category_existing(client):
    # Pick one category from the db loaded in your app or mock
    sample_category = next(iter(pick_em.db.keys()))
    rv = client.get(f'/categories/{sample_category}')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['name'] == sample_category
    assert isinstance(data['choices'], list)


def test_get_category_missing(client):
    rv = client.get('/categories/nonexistent-category')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['name'] == 'nonexistent-category'
    assert data['choices'] == []


def test_pick_invalid_params(client):
    rv = client.get('/categories/pick')
    assert rv.status_code == 400
    assert b'Invalid interest or effort tier' in rv.data

    rv = client.get(
        '/categories/pick?categories=somecat&interest=invalid&effort=low'
    )
    assert rv.status_code == 400


def test_pick_no_matches(client):
    # Pick categories and params that produce no matches,
    # e.g. interest='high', effort='low' for a category with none
    rv = client.get(
        '/categories/pick?categories=somecat&interest=high&effort=low'
    )
    data = rv.get_json()
    assert 'NO ITEMS FOUND' in data['selection']


def test_pick_valid(client):
    # This test assumes there is a valid category and options in your db.json
    categories = list(pick_em.db.keys())
    if not categories:
        pytest.skip("No categories in db to test pick")
    cat = categories[0]
    rv = client.get(f'/categories/pick?categories={cat}&interest=low&effort=high')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'selection' in data and 'category' in data


def test_pick_item():
    options = [
        Option(name="a", start=0, weight=2, category="cat1"),
        Option(name="b", start=2, weight=3, category="cat1"),
        Option(name="c", start=5, weight=1, category="cat1"),
    ]
    results = {opt.name: 0 for opt in options}
    # run many times to check distribution
    for _ in range(1000):
        sel = pick_item(options)
        assert sel in options
        results[sel.name] += 1

    # a should be selected roughly 2/6 times, b 3/6, c 1/6
    total = sum(results.values())
    for opt in options:
        prop = results[opt.name] / total
        expected = opt.weight / (options[-1].start + options[-1].weight)
        # Allow some margin of error
        assert abs(prop - expected) < 0.1


def test_remove(client):
    # Setup: ensure a category and choice exists
    categories = list(pick_em.db.keys())
    if not categories:
        pytest.skip("No categories to test remove")
    cat = categories[0]
    if not pick_em.db[cat]:
        pytest.skip("No choices in category to test remove")

    choice_name = pick_em.db[cat][0]['name']

    with patch('builtins.open', mock_open()) as mock_file, \
         patch('json.dump') as mock_dump:
        rv = client.delete(f'/categories/{cat}/remove/{choice_name}')

        assert rv.status_code == 202
        data = rv.get_json()

        # Confirm dump called
        mock_dump.assert_called_once()

        # Confirm file was opened for writing
        mock_file.assert_called_with('db.json', 'w')

        # Confirm the removed item is no longer present
        names = [d['name'] for d in data.get(cat, [])]
        assert choice_name not in names


def test_remove_missing(client):
    rv = client.delete(
        '/categories/nonexistent-category/remove/nonexistent-choice'
    )
    assert rv.status_code == 404
