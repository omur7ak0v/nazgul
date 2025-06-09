from flask import Flask, render_template, request, redirect, url_for, flash
from database import db, Event, Seat, Booking, User # <<< ДОБАВЛЯЕМ User сюда
from datetime import datetime

# --- НОВЫЕ ИМПОРТЫ ДЛЯ FLASK-LOGIN И FLASK-BCRYPT ---
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

app = Flask(__name__)
# Убедитесь, что путь к базе данных правильный. 
# Мы предположили, что вы используете 'instance' папку.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- ОЧЕНЬ ВАЖНО: ЗАМЕНИТЕ ЭТУ СТРОКУ НА СВОЙ УНИКАЛЬНЫЙ, СЛОЖНЫЙ СЕКРЕТНЫЙ КЛЮЧ ---
# Как сгенерировать:
# 1. Откройте терминал (убедитесь, что вы в виртуальном окружении).
# 2. Запустите Python: python
# 3. Введите: import secrets
# 4. Введите: print(secrets.token_hex(32))
# 5. Скопируйте вывод (длинную случайную строку) и вставьте сюда.
app.secret_key = '123456789' 


# --- Инициализация Flask-Bcrypt и Flask-Login ---
bcrypt = Bcrypt(app) # Инициализируем Bcrypt с приложением
login_manager = LoginManager() # Создаем объект LoginManager
login_manager.init_app(app) # Инициализируем его с приложением
login_manager.login_view = 'login' # Указываем Flask-Login, куда перенаправлять неавторизованных пользователей
login_manager.login_message = "Пожалуйста, войдите, чтобы получить доступ к этой странице."
login_manager.login_message_category = "info" # Категория для flash-сообщения

# Функция для загрузки пользователя, необходимая Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


db.init_app(app)

with app.app_context():
    db.create_all() # Создаст новую базу данных и таблицу 'users'

# --- Существующие маршруты (без изменений, кроме добавления flash-сообщений) ---
@app.route('/')
def events_list():
    events = Event.query.all()
    return render_template('events.html', events=events)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    seats = Seat.query.filter_by(event_id=event_id).order_by(Seat.number).all()
    return render_template('event_detail.html', event=event, seats=seats)

@app.route('/select_seat/<int:seat_id>', methods=['POST'])
def select_seat(seat_id):
    seat = Seat.query.get_or_404(seat_id)
    if seat.status == 'available':
        seat.status = 'selected'
        db.session.commit()
        return redirect(url_for('booking_form', seat_id=seat_id))
    flash('Это место недоступно для выбора.', 'error')
    return redirect(url_for('event_detail', event_id=seat.event_id))

@app.route('/booking/<int:seat_id>', methods=['GET', 'POST'])
def booking_form(seat_id):
    seat = Seat.query.get_or_404(seat_id)
    
    if seat.status == 'booked':
        flash('Это место уже забронировано.', 'error')
        return redirect(url_for('event_detail', event_id=seat.event_id))
    elif seat.status == 'available' and request.method == 'GET':
        flash('Пожалуйста, сначала выберите место.', 'info')
        return redirect(url_for('event_detail', event_id=seat.event_id))

    if request.method == 'POST':
        if not request.form.get('name') or not request.form.get('phone'):
            flash('Пожалуйста, заполните все поля.', 'error')
            return render_template('booking_form.html', seat=seat)

        booking = Booking(
            customer_name=request.form['name'],
            phone_number=request.form['phone'],
            seat_id=seat_id
        )
        seat.status = 'booked'
        db.session.add(booking)
        db.session.commit()
        
        flash('Бронирование успешно завершено!', 'success')
        return redirect(url_for('my_bookings', phone=request.form['phone']))
    
    return render_template('booking_form.html', seat=seat)

@app.route('/my_bookings')
def my_bookings():
    phone = request.args.get('phone')
    bookings = []
    if phone:
        bookings = Booking.query.filter_by(phone_number=phone).all()
        if not bookings:
            flash(f'Бронирования по номеру {phone} не найдены.', 'info')
    else:
        flash('Пожалуйста, введите номер телефона для просмотра бронирований.', 'info')
    return render_template('my_bookings.html', bookings=bookings)

# --- НОВЫЕ МАРШРУТЫ АУТЕНТИФИКАЦИИ ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: # Если пользователь уже вошел, перенаправляем его
        return redirect(url_for('events_list'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        # Проверяем, существует ли пользователь и совпадает ли хэш пароля
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user) # Вход пользователя
            flash('Вы успешно вошли в систему!', 'success')
            next_page = request.args.get('next') # Если был запрос на защищенную страницу, переходим туда
            return redirect(next_page or url_for('events_list'))
        else:
            flash('Неверное имя пользователя или пароль.', 'error')
    
    return render_template('login_form.html') # Позже создадим этот шаблон

@app.route('/logout')
@login_required # Только авторизованные пользователи могут выйти
def logout():
    logout_user() # Выход пользователя
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('events_list'))

# --- ЗАЩИЩЕННЫЕ МАРШРУТЫ ДЛЯ АДМИНИСТРАТОРА ---
@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        date_str = request.form['date']
        time_str = request.form['time']

        try:
            event_datetime = datetime.strptime(f"{date_str} {time_str}", '%Y-%m-%d %H:%M')
            new_event = Event(name=name, description=description, date=event_datetime)
            db.session.add(new_event)
            db.session.commit() # <-- Это должно быть здесь, чтобы new_event.id был доступен

            # --- НОВЫЙ БЛОК КОДА ДЛЯ СОЗДАНИЯ МЕСТ ---
            num_seats = 20 # Или другое желаемое количество мест
            for i in range(1, num_seats + 1):
                new_seat = Seat(event_id=new_event.id, number=i, status='available')
                db.session.add(new_seat)
            db.session.commit() # <-- Коммит для сохранения мест
            # --- КОНЕЦ НОВОГО БЛОКА КОДА ---

            flash(f'Мероприятие "{name}" успешно добавлено!', 'success')
            return redirect(url_for('events_list'))
        except ValueError:
            flash('Неверный формат даты или времени. Используйте ГГГГ-ММ-ДД и ЧЧ:ММ.', 'error')
            db.session.rollback()
        except Exception as e:
            db.session.rollback()
            flash(f'Произошла ошибка при добавлении мероприятия: {e}', 'error')
    return render_template('add_event_form.html')


@app.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required # <<< Теперь доступно только авторизованным пользователям
def delete_event(event_id):
    # Остальной код функции delete_event остается прежним
    event = Event.query.get_or_404(event_id)
    try:
        db.session.delete(event)
        db.session.commit()
        flash(f'Мероприятие "{event.name}" успешно удалено!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Произошла ошибка при удалении мероприятия "{event.name}": {e}', 'error')
    
    return redirect(url_for('events_list'))

if __name__ == '__main__':
    app.run(debug=True)