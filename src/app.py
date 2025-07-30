"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""

import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Characters, Planets, Favorites
from sqlalchemy import select

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace(
        "postgres://", "postgresql://"
    )
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)


# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


# generate sitemap with all your endpoints
@app.route("/")
def sitemap():
    return generate_sitemap(app)


@app.route("/user", methods=["GET"])
def get_all_users():

    # ↓↓↓ Consultar todos los registros de una tabla, modelo o entidad
    all_users = db.session.execute(select(User)).scalars().all()
    # ↓↓↓ Se encarga de procesar la info en un formato legible para devs
    results = list(map(lambda item: item.serialize(), all_users))

    if results is None:
        return jsonify({"msg": "No hay usuarios"}), 404

    response_body = {"msg": "ok", "results": results}

    return jsonify(response_body), 200


@app.route("/people", methods=["GET"])
def get_all_people():

    # ↓↓↓ Consultar todos los registros de una tabla, modelo o entidad
    all_people = db.session.execute(select(Characters)).scalars().all()
    # ↓↓↓ Se encarga de procesar la info en un formato legible para devs
    results = list(map(lambda item: item.serialize(), all_people))

    if results is None:
        return jsonify({"msg": "No hay personajes"}), 404

    response_body = {"msg": "ok", "results": results}

    return jsonify(response_body), 200


@app.route("/people/<int:id>", methods=["GET"])
def get_one_person(id):

    person = db.session.get(Characters, id)

    if person is None:
        return jsonify({"msg": "El personaje no existe"}), 404

    response_body = {"msg": "ok", "result": person.serialize()}

    return jsonify(response_body), 200


@app.route("/planets", methods=["GET"])
def get_all_planets():

    # ↓↓↓ Consultar todos los registros de una tabla, modelo o entidad
    all_planets = db.session.execute(select(Planets)).scalars().all()
    # ↓↓↓ Se encarga de procesar la info en un formato legible para devs
    results = list(map(lambda item: item.serialize(), all_planets))

    if results is None:
        return jsonify({"msg": "No hay planetas"}), 404

    response_body = {"msg": "ok", "results": results}

    return jsonify(response_body), 200


@app.route("/planets/<int:id>", methods=["GET"])
def get_one_planet(id):

    planet = db.session.get(Planets, id)

    if planet is None:
        return jsonify({"msg": "El planeta no existe"}), 404

    response_body = {"msg": "ok", "result": planet.serialize()}

    return jsonify(response_body), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=PORT, debug=False)
