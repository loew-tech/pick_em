import json
from typing import List, Dict, Tuple

from flask import Flask
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

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


@app.get('/categories/<string:category>/pick')
def pick() -> str:
    return NotImplemented


@app.get('/categories/<string:category>/remove/<string:name>')
def remove(category, name: str) -> Tuple[Dict[str, Dict[str, str]], int]:
    name = name.replace('+', ' ')
    print(f'{category=} {name=}')
    if category not in db or name not in (indices:={d['name']: i for i, d
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
