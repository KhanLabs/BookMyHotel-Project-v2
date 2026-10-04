import os

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookmyhotel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD_HASH = generate_password_hash('admin123', method='pbkdf2:sha256')

db = SQLAlchemy(app)

# --- MODELS ---
class Hotel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, default=5.0) 
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    amenities = db.Column(db.String(200), nullable=False)
    total_rooms = db.Column(db.Integer, default=50)
    # Advanced Features
    sustainability_rating = db.Column(db.Float, default=0.0)
    wifi_speed = db.Column(db.Integer, default=0)
    has_kitchen = db.Column(db.Boolean, default=False)
    is_work_friendly = db.Column(db.Boolean, default=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hotel_id = db.Column(db.Integer, db.ForeignKey('hotel.id'), nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), default="Guest User")
    email = db.Column(db.String(100), default="guest@example.com")
    phone = db.Column(db.String(20), default="N/A")
    reward_points = db.Column(db.Integer, default=0)

class Promotion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    percentage = db.Column(db.Integer, nullable=False)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    guest_name = db.Column(db.String(100), nullable=False)
    hotel_name = db.Column(db.String(100), nullable=False)
    check_in = db.Column(db.String(20), nullable=False)
    check_out = db.Column(db.String(20), nullable=False)
    nights = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Confirmed')
    payment_method = db.Column(db.String(50), nullable=True)
    cancellation_reason = db.Column(db.String(200), nullable=True)
    promo_used = db.Column(db.String(20), nullable=True)
    services_requested = db.Column(db.String(200), default="None")

# --- SEEDING ---
def seed_database():
    if not Hotel.query.first():
        hotels = [
            Hotel(name="Serena Hotel Islamabad", location="Islamabad", price=75000.0, rating=5.0, description="Luxury stay.", image_url="https://images.unsplash.com/photo-1566665797739-1674de7a421a?auto=format&fit=crop&w=800&q=80", amenities="Spa, Pool", sustainability_rating=8.5, wifi_speed=100, is_work_friendly=True),
            Hotel(name="PC Hotel Bhurban", location="Bhurban", price=45000.0, rating=4.8, description="Mountain resort.", image_url="https://images.unsplash.com/photo-1445019980597-93fa8acb246c?auto=format&fit=crop&w=800&q=80", amenities="Golf, Hiking", sustainability_rating=9.0, wifi_speed=50),
            Hotel(name="Avari Hotel Lahore", location="Lahore", price=35000.0, rating=4.7, description="Historic luxury.", image_url="https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?auto=format&fit=crop&w=800&q=80", amenities="Gym, Dining", has_kitchen=True),
            Hotel(name="Movenpick Hotel Karachi", location="Karachi", price=40000.0, rating=4.9, description="Business district.", image_url="https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?auto=format&fit=crop&w=800&q=80", amenities="High Tea, Pool", is_work_friendly=True, wifi_speed=300)
        ]
        db.session.bulk_save_objects(hotels)
        if not Promotion.query.first(): db.session.add(Promotion(code="WELCOME10", percentage=10))
        db.session.commit()

# --- ROUTES ---
@app.route('/')
def index():
    query = Hotel.query
    search_term = request.args.get('search')
    if search_term:
        search = f"%{search_term}%"
        query = query.filter((Hotel.name.like(search)) | (Hotel.location.like(search)))
    
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    if min_price: query = query.filter(Hotel.price >= min_price)
    if max_price: query = query.filter(Hotel.price <= max_price)

    if request.args.get('work_friendly'): query = query.filter(Hotel.is_work_friendly == True)
    if request.args.get('kitchen'): query = query.filter(Hotel.has_kitchen == True)
    if request.args.get('eco_friendly'): query = query.filter(Hotel.sustainability_rating >= 7.0)

    hotels = query.all()
    return render_template('index.html', hotels=hotels)

@app.route('/services')
def services(): return render_template('services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        db.session.add(ContactMessage(sender_name=request.form['name'], message=request.form['message']))
        db.session.commit()
        flash('Message Sent!', 'success')
        return redirect(url_for('index'))
    return render_template('contact.html')

# --- AUTH ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
            db.session.add(User(username=request.form['username'], password_hash=hashed_pw, full_name=request.form.get('full_name', 'Guest')))
            db.session.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except: flash('Username taken.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('index'))
        flash('Invalid credentials', 'danger')
    return render_template('login_user.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('profile.html', user=User.query.get(session['user_id']))

# --- BOOKING & REVIEWS ---
@app.route('/hotel/<int:hotel_id>')
def hotel_details(hotel_id):
    hotel = Hotel.query.get_or_404(hotel_id)
    reviews = Review.query.filter_by(hotel_id=hotel_id).all()
    return render_template('hotel_details.html', hotel=hotel, reviews=reviews)

@app.route('/book/<int:hotel_id>', methods=['GET', 'POST'])
def book(hotel_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    hotel = Hotel.query.get_or_404(hotel_id)
    
    if request.method == 'POST':
        check_in, check_out = request.form['check_in'], request.form['check_out']
        try:
            d1, d2 = datetime.strptime(check_in, "%Y-%m-%d"), datetime.strptime(check_out, "%Y-%m-%d")
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('book', hotel_id=hotel.id))

        if d2 <= d1: 
            flash('Invalid dates.', 'danger')
            return redirect(url_for('book', hotel_id=hotel.id))
            
        nights = (d2 - d1).days
        price = hotel.price * nights
        discount = 0
        
        services = []
        if request.form.get('service_car'): services.append("Car Rental")
        if request.form.get('service_spa'): services.append("Spa Package")
        if request.form.get('service_bar'): services.append("Bar Reservation")
        if request.form.get('service_tour'): services.append("City Tour")
        services_str = ", ".join(services) if services else "None"

        code = request.form.get('promo_code')
        promo = Promotion.query.filter_by(code=code).first()
        if promo:
            discount = price * (promo.percentage / 100)
            flash(f'Promo {code} applied!', 'success')
            
        points_to_earn = 0
        if hotel.sustainability_rating >= 7.0:
            points_to_earn = 10 * nights

        session['pending_booking'] = {
            'hotel_name': hotel.name, 'check_in': check_in, 'check_out': check_out,
            'nights': nights, 'original_price': price, 'discount': discount,
            'total_price': price - discount, 'guest_name': request.form['guest_name'],
            'promo_used': promo.code if promo else None,
            'services_requested': services_str,
            'points_earned': points_to_earn
        }
        return redirect(url_for('payment_selection'))
        
    return render_template('booking.html', hotel=hotel, user=User.query.get(session['user_id']))

@app.route('/payment-selection')
def payment_selection():
    if not session.get('pending_booking'): return redirect(url_for('index'))
    return render_template('payment_selection.html', booking=session['pending_booking'])

@app.route('/process-payment/<method>', methods=['GET', 'POST'])
def process_payment(method):
    if method == 'card' and request.method != 'POST': 
        return render_template('payment_card.html', booking=session['pending_booking'])
    
    b = session['pending_booking']
    db.session.add(Reservation(
        user_id=session['user_id'], guest_name=b['guest_name'], hotel_name=b['hotel_name'],
        check_in=b['check_in'], check_out=b['check_out'], nights=b['nights'],
        total_price=b['total_price'], payment_method="Paid Online" if method=='card' else "Pay on Arrival",
        promo_used=b['promo_used'], services_requested=b['services_requested']
    ))
    
    if b.get('points_earned', 0) > 0:
        user = User.query.get(session['user_id'])
        user.reward_points += b['points_earned']
        flash(f"Booking Confirmed! You earned {b['points_earned']} Green Points!", 'success')
    else:
        flash("Booking Confirmed!", 'success')

    db.session.commit()
    session.pop('pending_booking', None)
    return redirect(url_for('my_bookings'))

@app.route('/submit_review/<int:hotel_id>', methods=['POST'])
def submit_review(hotel_id):
    if 'user_id' not in session: return redirect(url_for('login'))
    db.session.add(Review(
        hotel_id=hotel_id, user_name=session['username'],
        rating=int(request.form['rating']), comment=request.form['comment']
    ))
    db.session.commit()
    flash('Review Submitted!', 'success')
    return redirect(url_for('hotel_details', hotel_id=hotel_id))

@app.route('/my-bookings')
def my_bookings():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('my_bookings.html', reservations=Reservation.query.filter_by(user_id=session['user_id']).all())

@app.route('/cancel/<int:id>')
def cancel_booking(id):
    res = Reservation.query.get_or_404(id)
    if res.user_id == session.get('user_id'):
        db.session.delete(res)
        db.session.commit()
    return redirect(url_for('my_bookings'))

# --- ADMIN ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST' and request.form['username'] == ADMIN_USERNAME \
            and check_password_hash(ADMIN_PASSWORD_HASH, request.form['password']):
        session['admin'] = True
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'): return redirect(url_for('admin_login'))
    res = Reservation.query.all()
    total_rev = sum(r.total_price for r in res)
    return render_template('dashboard.html', reservations=res, users=User.query.all(), 
                           promotions=Promotion.query.all(), messages=ContactMessage.query.all(), 
                           hotels=Hotel.query.all(), revenue=total_rev, count=len(res), adr=total_rev/len(res) if res else 0)

@app.route('/admin/add_hotel', methods=['POST'])
def add_hotel():
    if session.get('admin'):
        db.session.add(Hotel(
            name=request.form['name'], 
            location=request.form['location'], 
            price=float(request.form['price']), 
            description=request.form['description'], 
            # NEW: Getting URL from form
            image_url=request.form['image_url'], 
            amenities=request.form['amenities'],
            sustainability_rating=float(request.form.get('sustainability_rating', 0)),
            wifi_speed=int(request.form.get('wifi_speed', 0)),
            has_kitchen='has_kitchen' in request.form,
            is_work_friendly='is_work_friendly' in request.form
        ))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/admin/edit_hotel/<int:id>', methods=['GET', 'POST'])
def edit_hotel(id):
    if not session.get('admin'): return redirect(url_for('admin_login'))
    hotel = Hotel.query.get_or_404(id)
    if request.method == 'POST':
        hotel.name = request.form['name']
        hotel.price = float(request.form['price'])
        hotel.description = request.form['description']
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit_hotel.html', hotel=hotel)

@app.route('/admin/delete_hotel/<int:id>')
def delete_hotel(id):
    if session.get('admin'):
        db.session.delete(Hotel.query.get(id))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database()
    app.run(debug=True)