from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin # <<< ДОБАВЛЯЕМ ЭТОТ ИМПОРТ
from datetime import datetime # <<< ДОБАВЛЯЕМ ЭТОТ ИМПОРТ (если его нет и вы хотите booking_time)

db = SQLAlchemy()

# --- НОВАЯ МОДЕЛЬ USER ---
class User(db.Model, UserMixin): # Наследуется от UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False) # Для хранения хэшированного пароля

    def __repr__(self):
        return f"User('{self.username}')"

# --- СУЩЕСТВУЮЩИЕ МОДЕЛИ ---
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False)
    seats = db.relationship('Seat', backref='event', lazy=True, cascade="all, delete-orphan") 

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='available')  # available, booked, selected
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    booking = db.relationship('Booking', backref='seat', uselist=False, cascade="all, delete-orphan")

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False)
    booking_time = db.Column(db.DateTime, default=datetime.utcnow) # Добавлено для примера