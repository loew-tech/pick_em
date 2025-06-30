import json
from collections import namedtuple
from random import randint
from typing import List, Dict, Tuple

from flask import Flask, request
from flask_cors import CORS


Option = namedtuple('Option', ['name', 'start', 'weight'])

app = Flask(__name__)
CORS(app)


tiers = ['low', 'medium', 'high']
weights = dict(zip(tiers, [1, 3, 6]))
with open('db.json') as in_:
    db = json.load(in_)['categories']


@app.get('/')
def index():
    return '<div>Hello World</div>'


@app.get('/categories')
def categories() -> List[str]:
    return [*db.keys()]


@app.get('/categories/<string:category>')
def get_category(category: str) -> List[Dict[str, str]]:
    return db[category]


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
            options.append(Option(name=d['name'], start=start, weight=wght))
    return {'selection': pick_item(options)}


def pick_item(options: List[Option]):
    start, stop = 0, len(options) - 1
    selection = randint(start, options[-1].start + options[-1].weight)
    while start <= stop:
        mid = (start + stop) // 2
        end = options[mid].start + options[mid].weight
        if options[mid].start <= selection <= end:
            return options[mid].name
        elif end < selection:
            start = mid + 1
        else:
            stop = mid - 1
    return ''


@app.get('/categories/<string:category>/remove/<string:name>')
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
