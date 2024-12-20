from flask import Flask, render_template, request, session, redirect
from functools import wraps
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  
 
#decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                return redirect('/login')
            if session['user_role'] not in roles:
                return redirect('/') 
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# get_db function
def get_db():
    db = sqlite3.connect('sample_auth.db')
    db.row_factory = sqlite3.Row 
    return db

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM user WHERE username=? AND password=? and status= 'active'", 
                         (username, password)).fetchone()
        if user is None:
            return render_template('login.html', error="Wrong Credentials")
        else:
            session['user_id'] = user['id']
            session['user_role'] = user['role']
            

            if user['role'] == 'admin':
                return redirect('/admin')
            elif user['role'] == 'manager':
                return redirect('/manager')
            else:  
                return redirect('/user')
                
    return render_template("login.html", error="")

@app.route('/user')
@login_required
@role_required(['sales'])
def user():
    db = get_db()
    customers = db.execute("""
        SELECT 
            c.id,
            c.name,
            c.status,
            CAST((JULIANDAY('now') - JULIANDAY(MAX(com.contact_date))) AS INTEGER) as days_since_contact
        FROM customer c
        LEFT JOIN communication com ON c.id = com.customer_id
        GROUP BY c.id, c.name, c.status
        ORDER BY days_since_contact DESC NULLS FIRST
    """).fetchall()
    return render_template("user.html", customers=customers)

@app.route('/record-communication', methods=['POST'])
@login_required
@role_required(['sales'])
def record_communication():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        communication_type = request.form['communication_type']
        notes = request.form['notes']
        response = request.form['response']
        
        db = get_db()
        db.execute("""
            INSERT INTO communication (customer_id, user_id, communication_type, notes, response, contact_date)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (customer_id, session['user_id'], communication_type, notes, response))
        db.commit()
        
        return redirect('/user')

@app.route('/manager')
@login_required
@role_required(['manager'])
def manager():
    db = get_db()
    

    metrics = {
        'total_customers': db.execute("SELECT COUNT(*) as count FROM customer").fetchone()['count'],
        'total_communications': db.execute("SELECT COUNT(*) as count FROM communication").fetchone()['count'],
        'no_response_count': db.execute("""
            SELECT COUNT(*) as count FROM customer 
            WHERE id NOT IN (SELECT DISTINCT customer_id FROM communication WHERE response = 1)
        """).fetchone()['count']
    }


    sales_performance = db.execute("""
        SELECT 
            u.username,
            COUNT(c.id) as calls,
            SUM(CASE WHEN c.response = 1 THEN 1 ELSE 0 END) as successful_contacts,
            ROUND(CAST(SUM(CASE WHEN c.response = 1 THEN 1 ELSE 0 END) AS FLOAT) / 
                  COUNT(c.id) * 100, 2) as response_rate
        FROM user u
        LEFT JOIN communication c ON u.id = c.user_id
        WHERE u.role = 'sales'
        AND c.contact_date >= date('now', 'start of month')
        GROUP BY u.id, u.username
    """).fetchall()


    attention_needed = db.execute("""
        SELECT 
            c.name,
            c.status,
            CAST((JULIANDAY('now') - JULIANDAY(MAX(com.contact_date))) AS INTEGER) as days_since_contact
        FROM customer c
        LEFT JOIN communication com ON c.id = com.customer_id
        GROUP BY c.id, c.name, c.status
        HAVING days_since_contact >= 30 OR days_since_contact IS NULL
        ORDER BY days_since_contact DESC NULLS FIRST
    """).fetchall()

    return render_template("manager.html", 
                         metrics=metrics,
                         sales_performance=sales_performance,
                         attention_needed=attention_needed)

@app.route('/admin')
@login_required
@role_required(['admin'])
def admin():
    db = get_db()
    users = db.execute("SELECT * FROM user WHERE role != 'admin'").fetchall()
    return render_template("admin.html", users=users)

@app.route('/admin/add-user', methods=['POST'])
@login_required
@role_required(['admin'])
def add_user():
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    
    print(f"Attempting to add user: {username} with role: {role}")  
    
    db = get_db()
    try:
        db.execute("""
            INSERT INTO user (username, password, role, status)
            VALUES (?, ?, ?, 'active')
        """, (username, password, role))
        db.commit()
        print("User added successfully")  
    except sqlite3.IntegrityError as e:
        print(f"Error adding user: {e}")  
        return "Username already exists", 400
    except Exception as e:
        print(f"Unexpected error: {e}")  
        return "An error occurred", 500
    finally:
        db.close()
    
    return redirect('/admin')

@app.route('/admin/block-user/<int:user_id>')
@login_required
@role_required(['admin'])
def block_user(user_id):
    db = get_db()
    db.execute("UPDATE user SET status = 'blocked' WHERE id = ?", (user_id,))
    db.commit()
    return redirect('/admin')

@app.route('/admin/activate-user/<int:user_id>')
@login_required
@role_required(['admin'])
def activate_user(user_id):
    db = get_db()
    db.execute("UPDATE user SET status = 'active' WHERE id = ?", (user_id,))
    db.commit()
    return redirect('/admin')

@app.route('/admin/delete-user/<int:user_id>')
@login_required
@role_required(['admin'])
def delete_user(user_id):
    db = get_db()
    db.execute("DELETE FROM user WHERE id = ?", (user_id,))
    db.commit()
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/check-users')
@login_required
@role_required(['admin'])
def check_users():
    db = get_db()
    users = db.execute("SELECT username, role, status FROM user").fetchall()
    db.close()
    return str([dict(user) for user in users])  

@app.route('/add-customer', methods=['POST'])
@login_required
@role_required(['sales'])
def add_customer():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        status = request.form['status']
        
        db = get_db()
        try:
            db.execute("""
                INSERT INTO customer (name, status)
                VALUES (?, ?)
            """, (customer_name, status))
            db.commit()
        except Exception as e:
            print(f"Error adding customer: {e}")
            return "An error occurred", 500
        finally:
            db.close()
        
        return redirect('/user')

@app.route('/delete-customer/<int:customer_id>')
@login_required
@role_required(['sales'])
def delete_customer(customer_id):
    db = get_db()
    db.execute("DELETE FROM customer WHERE id = ?", (customer_id,))
    db.commit()
    return redirect('/user')

