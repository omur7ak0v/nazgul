document.addEventListener('DOMContentLoaded', function() {
    // Анимация загрузки
    function showLoader() {
        const loader = document.createElement('div');
        loader.className = 'loader';
        document.body.appendChild(loader);
        return loader;
    }

    // Обработка выбора места
    const seats = document.querySelectorAll('.seat:not(.booked)');
    
    seats.forEach(seat => {
        seat.addEventListener('click', async function() {
            const seatId = this.dataset.seatId;
            const loader = showLoader();
            
            try {
                const response = await fetch(`/select_seat/${seatId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                if (response.redirected) {
                    window.location.href = response.url;
                }
            } catch (error) {
                console.error('Error:', error);
            } finally {
                loader.remove();
            }
        });
    });

    // Плавная прокрутка
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Валидация формы
    const bookingForm = document.querySelector('form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            const phoneInput = this.querySelector('input[name="phone"]');
            if (!/^[\d\+]{10,15}$/.test(phoneInput.value)) {
                e.preventDefault();
                phoneInput.style.borderColor = 'var(--danger)';
                alert('Пожалуйста, введите корректный номер телефона');
            }
        });
    }
});

// Показать/скрыть кнопку "Наверх"
window.addEventListener('scroll', function() {
    const toTop = document.getElementById('toTop');
    if (window.pageYOffset > 300) {
        toTop.style.display = 'block';
    } else {
        toTop.style.display = 'none';
    }
});

document.getElementById('toTop').addEventListener('click', function() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});