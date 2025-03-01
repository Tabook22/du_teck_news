from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import news_processing
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from flask_mail import Mail, Message
from dotenv import load_dotenv
import json
import os
from collections import defaultdict

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')  # Your email
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')  # Your email password
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')  # Sender's email

# Initialize Flask-Mail
mail = Mail(app)

# Connect to the SQLite database
def get_db_connection():
    try:
        conn = sqlite3.connect('news.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

# Create the database schema if it doesn't exist
def create_table():
    try:
        conn = get_db_connection()
        if conn:
            # Create the users table with additional fields
            conn.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL UNIQUE,
                            email TEXT NOT NULL,  -- Added email with NOT NULL constraint
                            password TEXT NOT NULL,
                            user_address TEXT,
                            user_tel TEXT,
                            user_type TEXT NOT NULL,  -- Either 'admin' or 'normal'
                            role TEXT NOT NULL)''')

            # Create the tblNews table if not exists
            conn.execute('''CREATE TABLE IF NOT EXISTS tblNews (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            addDate TEXT NOT NULL,
                            news_title TEXT NOT NULL,
                            news_image TEXT,
                            news_summary TEXT,
                            news_url TEXT NOT NULL,
                            show TEXT DEFAULT 'yes')''')

            # Create the tblmgz table for the AI News Magazine
            conn.execute('''CREATE TABLE IF NOT EXISTS tblmgz (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            add_date TEXT NOT NULL,
                            news_title TEXT NOT NULL,
                            news_image TEXT,
                            news_summary TEXT,
                            news_url TEXT NOT NULL,
                            news_location TEXT NOT NULL)''')

            conn.commit()
        else:
            print("Failed to create database connection.")
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")
    finally:
        if conn:
            conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))  # Redirect to login if user is not logged in
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_type') != 'admin':
            return redirect(url_for('index'))  # Only admin users can access this page
        return f(*args, **kwargs)
    return decorated_function

# Route for the homepage (index)
@app.route('/')
@login_required
def index():
    # Load titles from config.json
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            home_title = config.get('home_title', 'News Room')
            home_subtitle = config.get('home_subtitle', 'We bring the latest AI News, up to date')
    except FileNotFoundError:
        home_title = 'News Room'
        home_subtitle = 'We bring the latest AI News, up to date'

    return render_template('index.html', home_title=home_title, home_subtitle=home_subtitle)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_db_connection()
            # Fetch the user from the database
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

            if user and check_password_hash(user['password'], password):
                # If user exists and password matches
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['user_type'] = user['user_type']

                # Redirect logic based on user type
                if user['user_type'] == 'admin':
                    return redirect(url_for('control'))  # This redirects admin users to the control page
                else:
                    return redirect(url_for('index'))  # Normal users should go to the index

            else:
                # If no user found or password is incorrect
                error = "Invalid username or password"
                return render_template('login.html', error=error)

        except sqlite3.Error as e:
            error = f"Error during login: {e}"
            return render_template('login.html', error=error)

    return render_template('login.html')

# User Logout
@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

# Route for managing users (only accessible by admin)
@app.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_users():
    conn = get_db_connection()
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user_address = request.form['user_address']
        user_tel = request.form['user_tel']
        user_type = request.form['user_type']  # admin or normal
        role = request.form['role']

        try:
            conn.execute('''INSERT INTO users 
                            (username, password, user_address, user_tel, user_type, role) 
                            VALUES (?, ?, ?, ?, ?, ?)''', 
                            (username, password, user_address, user_tel, user_type, role))
            conn.commit()
            flash('User added successfully')
        except sqlite3.Error as e:
            flash(f"Error adding user: {e}")
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()

    return render_template('users.html', users=users)

# Route for editing a user
@app.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password']) if request.form['password'] else user['password']
        user_address = request.form['user_address']
        user_tel = request.form['user_tel']
        user_type = request.form['user_type']
        role = request.form['role']

        conn.execute('''UPDATE users SET username = ?, password = ?, user_address = ?, 
                        user_tel = ?, user_type = ?, role = ? WHERE id = ?''', 
                     (username, password, user_address, user_tel, user_type, role, user_id))
        conn.commit()
        conn.close()
        flash('User updated successfully')
        return redirect(url_for('manage_users'))

    conn.close()
    return render_template('edit_user.html', user=user)

# Route for deleting a user
@app.route('/delete-user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash('User deleted successfully')
    return redirect(url_for('manage_users'))

@login_required
@admin_required
@app.route('/control', methods=['GET', 'POST'])
def control():
    # Load current values
    department_name = "Computer Science Department"
    magazine_title = "AI Magazine"
    news_subtitle = "AI Latest News"
    home_title = "News Room"
    home_subtitle = "We bring the latest AI News, up to date"

    # Load existing values from config.json
    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            department_name = config.get('department_name', department_name)
            magazine_title = config.get('magazine_title', magazine_title)
            news_subtitle = config.get('news_subtitle', news_subtitle)
            home_title = config.get('home_title', home_title)
            home_subtitle = config.get('home_subtitle', home_subtitle)
    except FileNotFoundError:
        pass

    # Handle form submissions
    message = None
    if request.method == 'POST':
        # If logo form is submitted
        if 'logo_image' in request.files:
            logo_image = request.files['logo_image']
            if logo_image and logo_image.filename != '':
                logo_path = os.path.join('static/images', 'new_logo.png')
                logo_image.save(logo_path)
                message = "Logo updated successfully!"

        # If magazine titles form is submitted
        elif 'department_name' in request.form and 'magazine_title' in request.form and 'news_subtitle' in request.form:
            department_name = request.form['department_name']
            magazine_title = request.form['magazine_title']
            news_subtitle = request.form['news_subtitle']
            message = "Magazine titles updated successfully!"

        # If home titles form is submitted
        elif 'home_title' in request.form and 'home_subtitle' in request.form:
            home_title = request.form['home_title']
            home_subtitle = request.form['home_subtitle']
            message = "Home page titles updated successfully!"

        # Save the updated titles into config.json
        with open('config.json', 'w') as config_file:
            json.dump({
                'department_name': department_name,
                'magazine_title': magazine_title,
                'news_subtitle': news_subtitle,
                'home_title': home_title,
                'home_subtitle': home_subtitle
            }, config_file)

    # Render the control panel page
    return render_template('control.html', message=message,
                           department_name=department_name,
                           magazine_title=magazine_title,
                           news_subtitle=news_subtitle,
                           home_title=home_title,
                           home_subtitle=home_subtitle)

# Route for registering a new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        email = request.form['email']  # Get the email from form data
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        user_address = request.form['user_address']
        user_tel = request.form['user_tel']
        user_type = request.form['user_type']
        role = request.form['role']  # Get the role from the form

        # Check if password and confirm password match
        if password != confirm_password:
            error = "Passwords do not match"
            return render_template('register.html', error=error)

        # Check if email is already in use
        try:
            conn = get_db_connection()
            existing_user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            if existing_user:
                error = "Email is already registered."
                return render_template('register.html', error=error)
            
            # Add user to the database with role field
            conn.execute('INSERT INTO users (username, email, password, user_address, user_tel, user_type, role) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                         (username, email, generate_password_hash(password), user_address, user_tel, user_type, role))
            conn.commit()
            conn.close()

            # Redirect to login after successful registration
            return redirect('/login')

        except sqlite3.Error as e:
            error = f"Error registering user: {e}"
            return render_template('register.html', error=error)

    return render_template('register.html')

# Route for searching news based on query and timeframe
@login_required
@admin_required
@app.route('/search-news', methods=['POST'])
def search_news_items():
    query = request.form['query']
    timeframe = request.form.get('timeframe', 'd1')  # Default to 'd1' (today)
    news_data = news_processing.search_news(query, num_results=10, restrict_timeframe=timeframe)

    # Check if each news item is already in the list
    conn = get_db_connection()
    if conn:
        saved_news = conn.execute("SELECT news_url FROM tblNews").fetchall()
        saved_urls = [row['news_url'] for row in saved_news]
        conn.close()

        # Mark news items that are already in the list
        for news in news_data:
            news['in_list'] = news['link'] in saved_urls
    else:
        print("Error retrieving saved news from the database.")

    return render_template('news.html', news_data=news_data, query=query, timeframe=timeframe)

# Route to add/remove news to/from the list (AJAX)
@app.route('/toggle-news-list', methods=['POST'])
def toggle_news_list():
    news_title = request.form['news_title']
    news_image = request.form['news_image']
    news_summary = request.form['news_summary']
    news_url = request.form['news_url']
    action = request.form['action']

    conn = get_db_connection()

    if conn:
        try:
            if action == 'add':
                # Add news to the list
                add_date = datetime.now().strftime("%Y-%m-%d")
                conn.execute("INSERT INTO tblNews (addDate, news_title, news_image, news_summary, news_url) VALUES (?, ?, ?, ?, ?)",
                             (add_date, news_title, news_image, news_summary, news_url))
                conn.commit()
                message = "News Added Successfully to the News List"
            else:
                # Remove news from the list
                conn.execute("DELETE FROM tblNews WHERE news_url = ?", (news_url,))
                conn.commit()
                message = "Removed from list of selected news successfully"

            # After each operation, calculate the new total number of saved news
            total_saved_news = conn.execute("SELECT COUNT(*) FROM tblNews WHERE show = 'yes'").fetchone()[0]

        except sqlite3.Error as e:
            print(f"Error while adding/removing news: {e}")
            message = "Failed to update the news list"
            total_saved_news = 0
        finally:
            conn.close()
    else:
        message = "Failed to connect to the database."
        total_saved_news = 0

    return jsonify({"message": message, "total_saved_news": total_saved_news})

# Route to create the AI News Magazine
@app.route('/create-ai-magazine', methods=['POST'])
def create_ai_magazine():

    selected_news_ids = request.form.getlist('selectedNews[]')
    news_locations_str = request.form.get('newsLocations')  # Fetch the 'newsLocations' as a string


    # Parse the 'newsLocations' string to a dictionary
    try:
        news_locations = json.loads(news_locations_str)  # Convert the JSON string to a Python dictionary
    except Exception as e:
        print(f"Error parsing news locations: {e}")
        return jsonify({"message": "Failed to parse news locations"}), 400

    conn = get_db_connection()
    getDate=current_date = datetime.now().date()
    if conn:
        try:
            # Clear the tblmgz table before adding new data
            conn.execute("DELETE FROM tblmgz")
            conn.commit()

            # Insert selected news into the tblmgz table along with their corresponding locations
            for news_id in selected_news_ids:
                news = conn.execute("SELECT * FROM tblNews WHERE id = ?", (news_id,)).fetchone()
                if news:
                    news_location = news_locations.get(news_id, 'Top News')  # Default to 'Top News'
                    conn.execute("""
                        INSERT INTO tblmgz (add_date, news_title, news_image, news_summary, news_url, news_location)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (getDate, news['news_title'], news['news_image'], news['news_summary'], news['news_url'], news_location))
                    conn.commit()
            message = "AI News Magazine created successfully."
        except sqlite3.Error as e:
            print(f"Error creating AI News Magazine: {e}")
            message = "Failed to create AI News Magazine."
        finally:
            conn.close()
    else:
        message = "Failed to connect to the database."

    return jsonify({"message": message})

# Route for displaying the saved news list
@login_required
@admin_required
@app.route('/saved-news')
def saved_news():
    conn = get_db_connection()
    if conn:
        try:
            # Fetch all saved news from tblNews
            news_list = conn.execute("SELECT * FROM tblNews WHERE show = 'yes' ORDER BY addDate, news_title").fetchall()

            # Fetch all news URLs from tblmgz to match with the news in tblNews
            mgz_news = conn.execute("SELECT news_title, news_url, news_location FROM tblmgz").fetchall()
            
            # Create a dictionary to store the news_title and its corresponding location from tblmgz
            mgz_news_dict = {news['news_title']: news['news_location'] for news in mgz_news}
            
            # Create a set of URLs to keep track of news saved in tblmgz
            saved_news_urls = {news['news_url'] for news in mgz_news}

            # Calculate total number of saved news
            total_saved_news = len(news_list)

            # Group news items by their added date and mark those that exist in tblmgz
            news_dict = defaultdict(list)
            for news in news_list:
                # Check if the current news exists in tblmgz
                if news['news_title'] in mgz_news_dict:
                    # If yes, add a 'news_location' field to the news item, which contains the location from tblmgz
                    news = dict(news)  # Convert row object to dict to modify it
                    news['news_location'] = mgz_news_dict[news['news_title']]
                else:
                    # If not, assign a default value (None or empty) for 'news_location'
                    news = dict(news)
                    news['news_location'] = None  # No location if not in tblmgz
                
                # Group news by the date
                news_dict[news['addDate']].append(news)

        except sqlite3.Error as e:
            print(f"Error fetching saved news: {e}")
            news_dict = {}
            total_saved_news = 0
        finally:
            conn.close()
    else:
        news_dict = {}
        total_saved_news = 0

    # Pass saved_news_urls to the template to mark the news that exist in tblmgz
    return render_template('saved_news.html', news_dict=news_dict, total_saved_news=total_saved_news, saved_news_urls=saved_news_urls)



# Route to fetch the latest random AI news (default to today's news)
@app.route('/latest-ai-news', methods=['POST'])
def latest_ai_news():
    query = "latest AI news"
    news_data = news_processing.search_news(query, num_results=10, restrict_timeframe="d1")  # Default to today's news
    return render_template('news.html', news_data=news_data, query=query, timeframe="d1")

# Route for the AI magazine page
@app.route('/ai-magazine')
def ai_magazine():
    conn = get_db_connection()
    top_news, second_news, sidebar_news, magazine_date = None, [], [], 'N/A'

    try:
        # Fetch the news categorized by location
        top_news = conn.execute("SELECT * FROM tblmgz WHERE news_location = 'Top News'").fetchone()
        second_news = conn.execute("SELECT * FROM tblmgz WHERE news_location = 'Second News'").fetchall()
        sidebar_news = conn.execute("SELECT * FROM tblmgz WHERE news_location = 'Sidebar List'").fetchall()

        # Fetch the date from the first news entry in tblmgz (if available)
        first_news = conn.execute("SELECT add_date FROM tblmgz ORDER BY add_date LIMIT 1").fetchone()
        if first_news:
            # Convert the date string to a datetime object
            date_obj = datetime.strptime(first_news['add_date'], "%Y-%m-%d")
            # Format the date to the desired format (e.g., 'Wed October 16, 2024')
            magazine_date = date_obj.strftime("%a %B %d, %Y")
        else:
            magazine_date = 'N/A'

        # Load titles from config.json
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            department_name = config.get('department_name', 'Computer Science Department')
            magazine_title = config.get('magazine_title', 'AI Magazine')
            news_subtitle = config.get('news_subtitle', 'AI Latest News')

    except sqlite3.Error as e:
        print(f"Error fetching AI Magazine news: {e}")
        top_news, second_news, sidebar_news, magazine_date = None, [], [], 'N/A'
        department_name, magazine_title, news_subtitle = 'N/A', 'N/A', 'N/A'

    except FileNotFoundError:
        print("Error: config.json not found.")
        department_name, magazine_title, news_subtitle = 'Computer Science Department', 'AI Magazine', 'AI Latest News'

    finally:
        if conn:
            conn.close()

    return render_template('aimgz.html', 
                           top_news=top_news, 
                           second_news=second_news, 
                           sidebar_news=sidebar_news,
                           magazine_date=magazine_date,
                           department_name=department_name,
                           magazine_title=magazine_title,
                           news_subtitle=news_subtitle)

@app.route('/remove-news', methods=['POST'])
def remove_single_news():
    news_id = request.form['news_id']  # Ensure this is the correct news_id being passed

    conn = get_db_connection()
    if conn:
        try:
            # Delete the news from the database
            conn.execute("DELETE FROM tblNews WHERE id = ?", (news_id,))
            conn.commit()

            # Fetch the updated total count
            total_saved_news = conn.execute("SELECT COUNT(*) FROM tblNews WHERE show = 'yes'").fetchone()[0]
            message = "News removed successfully."
        except sqlite3.Error as e:
            print(f"Error removing news: {e}")
            message = "Failed to remove news."
            total_saved_news = 0
        finally:
            conn.close()
    else:
        message = "Failed to connect to the database."
        total_saved_news = 0

    # Return a success message along with the updated total saved news count as a JSON response
    return jsonify({"message": message, "total_saved_news": total_saved_news})

@app.route('/delete_selected_news', methods=['POST'])
def delete_selected_news():
    selected_news_ids = request.form.getlist('selectedNews[]')  # List of selected news IDs
    conn = get_db_connection()
    if conn:
        try:
            # Delete the selected news from the database
            for news_id in selected_news_ids:
                conn.execute("DELETE FROM tblNews WHERE id = ?", (news_id,))
            conn.commit()

            # Fetch the updated total count of saved news
            total_saved_news = conn.execute("SELECT COUNT(*) FROM tblNews WHERE show = 'yes'").fetchone()[0]
            message = f"Deleted {len(selected_news_ids)} selected news successfully."
        except sqlite3.Error as e:
            print(f"Error deleting selected news: {e}")
            message = "Failed to delete selected news."
            total_saved_news = 0
        finally:
            conn.close()
    else:
        message = "Failed to connect to the database."
        total_saved_news = 0

    # Return a JSON response to the client
    return jsonify({"message": message, "total_saved_news": total_saved_news})

if __name__ == '__main__':
    create_table()  # Ensure the table is created before running the app
    #app.run(host="0.0.0.0", port=5000, debug=True)
    app.run(debug=True)

