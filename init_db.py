from datetime import datetime
from app import app
from database import db, Event, Seat

def init_data():
    with app.app_context():
        # Очищаем базу
        db.drop_all()
        db.create_all()
        
        # Создаем тестовое мероприятие
        event = Event(
            name="Новогодний концерт",
            description="Праздничный концерт с участием городских коллективов",
            date=datetime(2025, 12, 31, 19, 0)
        )
        db.session.add(event)
        db.session.commit()
        
        # Создаем 20 мест
        for i in range(1, 21):
            seat = Seat(number=i, event_id=event.id)
            db.session.add(seat)
        db.session.commit()
        
        print("Тестовые данные добавлены!")

if __name__ == '__main__':
    init_data()