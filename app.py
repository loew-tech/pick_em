import json
from collections import namedtuple
from random import randint
from typing import List, Dict, Tuple

from flask import Flask, request
from flask_cors import CORS


Option = namedtuple('Option', ['name', 'start', 'weight', 'category'])

app = Flask(__name__)
CORS(app)


tiers = ['low', 'medium', 'high']
weights = dict(zip(tiers, [1, 3, 6]))
with open('db.json') as in_:
    db = {e['name']: e['choices'] for e in json.load(in_)}


@app.get('/')
def index():
    return '<div>Hello World</div>'


@app.get('/categories')
def categories() -> List[str]:
    return [*db.keys()]


@app.get('/categories/<string:category>')
def get_category(category: str) -> Dict[str, str | Dict[str, str]]:
    if category not in db:
        return {'name': category, 'choices': []}
    return {'name': category, 'choices': db[category]}


@app.get('/categories/pick')
def pick() -> Dict[str, str]:
    cats = request.args.getlist('categories')
    interest = {*tiers[tiers.index(request.args.get('interest', 'low')):]}
    effort = {*tiers[:tiers.index(request.args.get('effort', 'low'))+1]}
    options: List[Option] = []
    for c in cats:
        for d in db[c]:
            if not (d['interest'] in interest and d['effort'] in effort):
                continue
            start = options[-1].start + options[-1].weight if options else 0
            # @TODO: is this how I want to handle interest < effort
            wght = max(1, weights[d['interest']] // weights[d['effort']])
            options.append(Option(name=d['name'], start=start, weight=wght,
                                  category=c))
    selection = pick_item(options)
    return {'selection': selection.name, 'category': selection.category}


def pick_item(options: List[Option]) -> Option:
    start, stop = 0, len(options) - 1
    selection = randint(start, options[-1].start + options[-1].weight-1)
    while start <= stop:
        mid = (start + stop) // 2
        end = options[mid].start + options[mid].weight
        if options[mid].start <= selection < end:
            return options[mid]
        elif end <= selection:
            start = mid + 1
        else:
            stop = mid - 1
    return Option(name='NOT FOUND', start=-1, weight=-1, category='NOT FOUND')


@app.delete('/categories/<string:category>/remove/<string:name>')
def remove(category, name: str) -> Tuple[Dict[str, Dict[str, str]], int]:
    name = name.replace('+', ' ')
    if category not in db or name not in (indices := {d['name']: i for i, d
                                          in enumerate(db[category])}):
        return db, 404
    del db[category][indices[name]]
    if not db[category]:
        del db[category]

    with open('db.json', 'w') as out:
        out.write(json.dumps({'categories': db}, indent=4))
    return db, 202


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
