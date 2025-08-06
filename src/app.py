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


from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager


app = Flask(__name__)
app.url_map.strict_slashes = False


# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = "super-secret"  # Change this!
jwt = JWTManager(app)

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace("postgres://", "postgresql://")
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


# Create a route to authenticate your users and return JWTs. The
# create_access_token() function is used to actually generate the JWT.
@app.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    print("email: " + email, "Password: " + password)

    # ------consulta en la tabla "User" ↓↓ donde el "email" ↓↓ coincida con el introducido
    query_user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    print(query_user)
    # si devuelve "None", es porque no encuentra dicho usuario, entonces podemos tratar el error.

    if query_user is None:
        return jsonify({"msg": "email does not exist"}), 404

    # --- si el "email" ↓↓ o el "password" ↓↓ no coincide con la bd, lanza el error
    if email != query_user.email or password != query_user.password:
        return jsonify({"msg": "Bad email or password"}), 401

    access_token = create_access_token(identity=email)
    return jsonify({"user_id": query_user.id, "user_logged": query_user.email, "access_token": access_token})


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


@app.route("/user/<int:user_id>", methods=["GET"])
def get_one_user(user_id):

    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({"msg": "El usuario no existe"}), 404

    response_body = {"msg": "ok", "result": user.serialize()}

    return jsonify(response_body), 200


@app.route("/favorites", methods=["GET"])
@jwt_required()
def protected_fav():
    email = get_jwt_identity()

    query_user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()

    user_favorites = query_user.all_user_favorites()

    return jsonify(logged_in_as=email, favorites=user_favorites), 200


@app.route("/favorites", methods=["POST"])
@jwt_required()
def add_protected_fav():
    email = get_jwt_identity()
    request_body = request.json

    query_user = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    character = db.session.execute(select(Characters).where(Characters.id == request_body.get("characters_id"))).scalar_one_or_none()
    planet = db.session.execute(select(Planets).where(Planets.id == request_body.get("planets_id"))).scalar_one_or_none()

    already_fav_character = db.session.execute(
        select(Favorites).where(
            Favorites.user_id == query_user.id, Favorites.characters_id != None, Favorites.characters_id == request_body.get("characters_id")
        )
    ).scalar_one_or_none()

    already_fav_planet = db.session.execute(
        select(Favorites).where(
            Favorites.user_id == query_user.id, Favorites.planets_id != None, Favorites.planets_id == request_body.get("planets_id")
        )
    ).scalar_one_or_none()

    print(already_fav_character, already_fav_planet)

    if request_body.get("characters_id") is None and request_body.get("planets_id") is None:
        return jsonify(msg="El favorito debe señalar a un personaje o planeta, no puede estar vacío"), 401

    if request_body.get("characters_id") is not None and request_body.get("planets_id") is not None:
        return jsonify(msg="El favorito debe señalar a un personaje o planeta, no puede guardar ambos"), 401

    if request_body.get("characters_id") is not None and character is None:
        return jsonify(msg="El personaje no existe"), 404

    if request_body.get("planets_id") is not None and planet is None:
        return jsonify(msg="El planeta no existe"), 404

    if already_fav_character is not None:
        return jsonify(msg="Este favorito ya existe para este usuario", favorite=already_fav_character.serialize()), 401

    if already_fav_planet is not None:
        return jsonify(msg="Este favorito ya existe para este usuario", favorite=already_fav_planet.serialize()), 401

    fav = Favorites(user_id=query_user.id, characters_id=request_body.get("characters_id"), planets_id=request_body.get("planets_id"))

    character = db.session.execute(select(Characters).where(Characters.id == request_body.get("characters_id"))).scalar_one_or_none()
    print(character, planet)

    db.session.add(fav)
    db.session.commit()

    return jsonify(logged_in_as=email, favorite=fav.serialize()), 200


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


@app.route("/people", methods=["POST"])
def post_one_character():
    request_body = request.json

    character = Characters(
        name=request_body["name"],
        height=request_body["height"],
        mass=request_body["mass"],
        hair_color=request_body["hair_color"],
        skin_color=request_body["skin_color"],
        eye_color=request_body["eye_color"],
        birth_year=request_body["birth_year"],
        gender=request_body["gender"],
        homeworld=request_body["homeworld"],
    )

    print(character.serialize())

    db.session.add(character)
    db.session.commit()

    response_body = {"msg": "personaje agregado", "results": character.serialize()}

    return jsonify(response_body), 200


@app.route("/people/<int:id>", methods=["GET"])
def get_one_person(id):

    person = db.session.get(Characters, id)

    if person is None:
        return jsonify({"msg": "El personaje no existe"}), 404

    response_body = {"msg": "ok", "result": person.serialize()}

    return jsonify(response_body), 200


@app.route("/people/<int:id>", methods=["DELETE"])
def delete_one_person(id):

    person = db.session.get(Characters, id)

    if person is None:
        return jsonify({"msg": "El personaje no existe"}), 404

    db.session.delete(person)
    db.session.commit()

    response_body = {"msg": "El personaje se ha eliminado"}

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


@app.route("/planets", methods=["POST"])
def post_one_planet():
    request_body = request.json

    planet = Planets(
        name=request_body["name"],
        rotation_period=request_body["rotation_period"],
        orbital_period=request_body["orbital_period"],
        diameter=request_body["diameter"],
        climate=request_body["climate"],
        terrain=request_body["terrain"],
        surface_water=request_body["surface_water"],
        population=request_body["population"],
    )

    print(planet.serialize())

    db.session.add(planet)
    db.session.commit()

    response_body = {"msg": "planeta agregado", "results": planet.serialize()}

    return jsonify(response_body), 200


@app.route("/planets/<int:id>", methods=["GET"])
def get_one_planet(id):

    planet = db.session.get(Planets, id)

    if planet is None:
        return jsonify({"msg": "El planeta no existe"}), 404

    response_body = {"msg": "ok", "result": planet.serialize()}

    return jsonify(response_body), 200


@app.route("/planets/<int:id>", methods=["DELETE"])
def delete_one_planet(id):

    planet = db.session.get(Planets, id)

    if planet is None:
        return jsonify({"msg": "El planeta no existe"}), 404

    db.session.delete(planet)
    db.session.commit()

    response_body = {"msg": "El planeta se ha eliminado"}

    return jsonify(response_body), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=PORT, debug=False)
