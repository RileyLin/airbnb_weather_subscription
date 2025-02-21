import os
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length
from models import db, Subscriber, Admin
from weather_service import WeatherService
from dotenv import load_dotenv
import threading
import schedule
import time
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather_service.db'
db.init_app(app)

weather_service = WeatherService()

# Forms
class SubscriptionForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    zip_code = StringField('Zip Code', validators=[DataRequired()])
    yard_size = FloatField('Yard Size (in acres)', validators=[DataRequired()])
    elevation = FloatField('Elevation (in feet)', validators=[DataRequired()])

class AdminLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])

class AdminRegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please log in as admin first.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.route('/', methods=['GET', 'POST'])
def index():
    form = SubscriptionForm()
    if form.validate_on_submit():
        try:
            # Use zip code for coordinates
            coords = weather_service._get_coordinates(form.zip_code.data)
            
            # Determine the action from the form
            action = request.form.get('action')
            
            # Create a temporary subscriber object
            temp_subscriber = Subscriber(
                email=form.email.data,
                location=form.zip_code.data,  # store zip code in location field
                yard_size=form.yard_size.data,
                elevation=form.elevation.data,
                latitude=coords['lat'],
                longitude=coords['lon']
            )
            
            if action == 'subscribe':
                # Save subscriber to DB
                db.session.add(temp_subscriber)
                db.session.commit()
                flash('Successfully subscribed to weather alerts!', 'success')
                return redirect(url_for('index'))
            elif action == 'sample_daily':
                weather_service.send_daily_update_for_subscriber(temp_subscriber)
                flash('Sample daily update sent to your email!', 'success')
            elif action == 'sample_weekly':
                weather_service.send_weekly_summary_for_subscriber(temp_subscriber)
                flash('Sample weekly summary sent to your email!', 'success')
            else:
                flash('Unknown action.', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    return render_template('index.html', form=form)

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if Admin.query.first():
        flash('Admin already registered.', 'error')
        return redirect(url_for('admin_login'))
        
    form = AdminRegistrationForm()
    if form.validate_on_submit():
        admin = Admin(email=form.email.data)
        admin.set_password(form.password.data)
        db.session.add(admin)
        db.session.commit()
        flash('Admin registered successfully!', 'success')
        return redirect(url_for('admin_login'))
    return render_template('admin/register.html', form=form)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(email=form.email.data).first()
        if admin and admin.check_password(form.password.data):
            session['admin_id'] = admin.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid email or password.', 'error')
    return render_template('admin/login.html', form=form)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    subscribers = Subscriber.query.order_by(Subscriber.created_at.desc()).all()
    return render_template('admin/dashboard.html', subscribers=subscribers)

@app.route('/admin/subscriber/<int:id>/toggle')
@admin_required
def toggle_subscriber(id):
    subscriber = Subscriber.query.get_or_404(id)
    subscriber.active = not subscriber.active
    db.session.commit()
    flash(f'Subscriber {subscriber.email} {"activated" if subscriber.active else "deactivated"} successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/subscriber/<int:id>/delete')
@admin_required
def delete_subscriber(id):
    subscriber = Subscriber.query.get_or_404(id)
    db.session.delete(subscriber)
    db.session.commit()
    flash(f'Subscriber {subscriber.email} deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/send-report/<int:id>/<report_type>')
@admin_required
def send_report(id, report_type):
    subscriber = Subscriber.query.get_or_404(id)
    try:
        if report_type == 'daily':
            weather_service.send_daily_update_for_subscriber(subscriber)
            flash(f'Daily report sent to {subscriber.email}!', 'success')
        elif report_type == 'weekly':
            weather_service.send_weekly_summary_for_subscriber(subscriber)
            flash(f'Weekly report sent to {subscriber.email}!', 'success')
    except Exception as e:
        flash(f'Error sending report: {str(e)}', 'error')
    return redirect(url_for('admin_dashboard'))

def init_scheduler():
    schedule.every().day.at("08:00").do(weather_service.send_daily_update)
    schedule.every().sunday.at("09:00").do(weather_service.send_weekly_summary)
    scheduler_thread = threading.Thread(target=run_schedule)
    scheduler_thread.daemon = True
    scheduler_thread.start()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    init_scheduler()
    app.run(debug=True, port=5002) 