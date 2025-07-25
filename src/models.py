from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

db = SQLAlchemy()


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    surname: Mapped[str] = mapped_column(String(120))
    signup_date: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)
    favorites: Mapped[List["Favorites"]] = relationship()

    def serialize(self):
        return {
            "id": self.id,
            "username": self.username,
            "name": self.name,
            "surname": self.surname,
            "email": self.email,
            # do not serialize the password, its a security breach
        }


class Characters(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    height: Mapped[int] = mapped_column(Integer())
    mass: Mapped[int] = mapped_column(Integer())
    hair_color: Mapped[str] = mapped_column(String(120))
    skin_color: Mapped[str] = mapped_column(String(120))
    eye_color: Mapped[str] = mapped_column(String(120))
    birth_year: Mapped[str] = mapped_column(String(120))
    gender: Mapped[str] = mapped_column(String(120))
    homeworld: Mapped[int] = mapped_column(ForeignKey("planets.id"))
    favorite: Mapped[int] = mapped_column(ForeignKey("favorites.id")) 

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "height": self.height,
            "mass": self.mass,
            "hair_color": self.hair_color,
            "skin_color": self.skin_color,
            "eye_color": self.eye_color,
            "birth_year": self.birth_year,
            "gender": self.gender,
        }


class Planets(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    rotation_period: Mapped[int] = mapped_column(Integer())
    orbital_period: Mapped[int] = mapped_column(Integer())
    diameter: Mapped[int] = mapped_column(Integer())
    climate: Mapped[str] = mapped_column(String(120))
    terrain: Mapped[str] = mapped_column(String(120))
    surface_water: Mapped[int] = mapped_column(Integer())
    population: Mapped[int] = mapped_column(Integer())
    was_born: Mapped[List["Characters"]] = relationship()
    favorite: Mapped[int] = mapped_column(ForeignKey("favorites.id"), nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "rotation_period": self.rotation_period,
            "orbital_period": self.orbital_period,
            "diameter": self.diameter,
            "climate": self.climate,
            "terrain": self.terrain,
            "surface_water": self.surface_water,
            "population": self.population,
        }


class Favorites(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    user: Mapped[int] = mapped_column(ForeignKey("user.id"))
    character: Mapped[List["Characters"]] = relationship()
    planet: Mapped[List["Characters"]] = relationship()

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
        }
