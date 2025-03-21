from flask import Flask, render_template, url_for, redirect, session, request, g, Response, send_file
from forms import *
from database import *
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime,date
from flask_session import Session
from functools import wraps
import matplotlib.pyplot as plt
import io
import csv

'''
User Details for Demo Account (Pre-added assets and transactions):
Username: admin
Password: admin123

** Please reload dashboard if graphs don't load **
'''

#Initializing App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'this-is_isasecretkey'
app.config['SESSION_PERMANENT']=False
app.config['SESSION_TYPE']='filesystem'
app.teardown_appcontext(close_db)
Session(app)
init_db()


#Functions
@app.before_request
def load_logged_in_user():
    g.user = session.get('user_id', None)


#Custom Decorator
def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for('login', next=request.url))
        return view(*args,**kwargs)
    return wrapped_view


#Index Route
@app.route('/')
def index_redirect():
    return redirect(url_for('index'))


#Index Route Redirect
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html',
                            title='Home')

#Tutorial Route
@app.route('/tutorial')
def tutorial():
    return render_template('tutorial.html', title='Tutorial')


#Settings Route
@app.route('/settings', methods=['GET','POST'])
@login_required
def settings():
    
    db = get_db()
    form = SettingsForm()
    current_password_error=''
    new_password_error=''
    success_message=''
    user_id = session.get('user_id')
    current_password = form.current_password.data
    new_password = form.new_password.data

    old_password = db.execute('''SELECT password
                                FROM users
                                WHERE user_id = ?''', (user_id,)).fetchone()[0]
    
    if form.validate_on_submit():
        if check_password_hash(old_password, current_password) and current_password != new_password:

            db.execute('''UPDATE users 
                          SET password = ?
                          WHERE user_id = ?''', (generate_password_hash(new_password), user_id))
            db.commit()
            current_password_error = ''
            new_password_error = ''
            success_message='Password updated successfully.'

        elif check_password_hash(old_password, current_password) and current_password == new_password:
            current_password_error = ''
            new_password_error = 'New password cannot be the same as the current password.'

        elif not check_password_hash(old_password, current_password):
            current_password_error = 'Current password is incorrect.'
            new_password_error = ''

    if form.clear_data.data:

        db.execute('''DELETE FROM assets
                      WHERE user_id = ?''', (user_id,))
        db.execute('''DELETE FROM delta
                      WHERE asset_id IN (SELECT id FROM assets WHERE user_id = ?);''', (user_id,))
        db.execute('''DELETE FROM transactions 
                      WHERE asset_id IN (SELECT id FROM assets WHERE user_id = ?);''', (user_id,))
        db.commit()
        current_password_error = ''
        new_password_error = ''
        success_message='Data cleared successfully.'
    
    return render_template('settings.html',
                            title='Settings',
                            form=form,
                            current_password_error=current_password_error,
                            new_password_error=new_password_error,
                            success_message=success_message)


#Sign Up Route
@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():

    success_message = ''
    email_error = ''
    username_error = ''

    form = SignUpForm()

    if form.validate_on_submit():

        username = form.username.data
        first_name = form.first_name.data
        second_name = form.second_name.data
        password = form.password.data
        email = form.email.data

        db = get_db()
        existing_user = db.execute('''SELECT *
                                      FROM users
                                      WHERE username = ? OR email = ?''', (username,email)).fetchone()

        if existing_user:
            if existing_user[2] == email:
                email_error = 'Email is taken, please try choose another one.'
            if existing_user[1] == username:
                username_error = 'Username is taken, please try choose another one.'

        if not existing_user:
            hashed_password = generate_password_hash(password)
            db.execute('''INSERT INTO users(username, first_name, last_name, email, password)
                          VALUES (?, ?, ?, ?, ?)''', (username, first_name, second_name, email, hashed_password))
            db.commit()

            success_message = 'You have successfully signed up!'
            email_error = ''
            username_error = ''
        
    return render_template('sign_up.html',
                            form=form,
                            title='Sign Up',
                            success_message = success_message,
                            email_error=email_error,
                            username_error=username_error)


#Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():

    password_error=''
    email_error=''
    form = LoginForm()

    if form.validate_on_submit():

        db = get_db()
        email = form.email.data
        entered_password = form.password.data

        user_details = db.execute('''SELECT *
                                     FROM users 
                                     WHERE email = ?''', (email,)).fetchone()
        
        if user_details:
            if check_password_hash(user_details[5], entered_password):

                password_error=''
                email_error=''
                session['first_name'] = user_details['first_name']
                session['last_name'] = user_details['last_name']
                session['username'] = user_details['username']
                session['user_id'] = user_details['user_id']

                return redirect(url_for('dashboard'))
            
            elif not check_password_hash(user_details[5], entered_password):
                password_error = 'Password is incorrect. '

        else:
            email_error = 'User does not exist. '

    return render_template('login.html',
                            form=form,
                            email_error = email_error,
                            password_error = password_error,
                            title='Login')


#Portfolio Graph Function
def portfolio_graph():

    db = get_db()
    user_id = session.get('user_id')
    details = db.execute('''SELECT purchase_date, SUM(current_value*quantity) AS total_value
                            FROM assets
                            WHERE user_id = ? AND is_deleted=0
                            GROUP BY purchase_date
                            ORDER BY purchase_date''', (user_id,)).fetchall()
    
    dates = [row["purchase_date"] for row in details]
    values = [row["total_value"] for row in details]

    return dates, values


#Portfolio Graph Route
@app.route('/graph', methods=['GET', 'POST'])
@login_required
def graph():

    dates, values = portfolio_graph()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, values, marker='', linestyle='-', color='#d9d9d9', label="Portfolio Value")

    ax.fill_between(dates, values, color='#d9d9d9', alpha=0.2)
    ax.set_xlabel("Date", color='white')
    ax.set_ylabel("Portfolio Value ($)", color='white')
    ax.set_title("Asset Portfolio Value Over Time", color='white')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(False)
    
    ax.spines['top'].set_color('white')
    ax.spines['right'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['bottom'].set_color('white')
    ax.yaxis.set_tick_params(color='white')
    ax.xaxis.set_tick_params(color='white')

    ax.xaxis.set_tick_params(labelcolor='white')
    ax.yaxis.set_tick_params(labelcolor='white')

    img = io.BytesIO()
    fig.savefig(img, format='png', bbox_inches='tight', transparent=True)
    img.seek(0)

    return Response(img.getvalue(), mimetype='image/png')


#Pie Chart Function
def pie_chart():

    db = get_db()
    user_id = session.get('user_id')
    details = db.execute('''SELECT category, SUM(current_value*quantity) AS total_value
                            FROM assets
                            WHERE user_id = ? AND is_deleted=0
                            GROUP BY category
                            ORDER BY category''', (user_id,)).fetchall()

    categories = [row["category"] for row in details]
    values = [row["total_value"] for row in details]

    return categories, values


#Pie Chart Route
@app.route('/pie_chart', methods=['GET', 'POST'])
def display_pie_chart():

    categories, values = pie_chart()

    grey_colors = [
        '#A0A0A0',  
        '#B0B8B1',  
        '#D1D1D1',  
        '#8F8F8F'   
    ]

    if len(categories) > len(grey_colors):
        extra_colors = plt.cm.Paired(range(len(categories) - len(grey_colors)))  
        grey_colors.extend(extra_colors)

    fig, ax = plt.subplots(figsize=(3, 3))  
    wedges, texts, autotexts = ax.pie(
        values, 
        labels=categories,  
        autopct='%1.1f%%',  
        colors=grey_colors[:len(categories)], 
        startangle=90, 
        wedgeprops={'edgecolor': 'none'},
        textprops={'fontsize': 6, 'color': 'white'} 
    )

    
    for text in texts:
        text.set_fontsize(6)  

    for autotext in autotexts:
        autotext.set_fontsize(6)  
        autotext.set_color('white')

    ax.axis('equal') 

    img = io.BytesIO()
    plt.savefig(img, format='png', transparent=True, bbox_inches='tight')  
    img.seek(0)  

    return Response(img.getvalue(), mimetype='image/png')


#Dashboard Route
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():

    db = get_db()
    user_id = session.get('user_id')
    first_name = session.get('first_name')
    last_name = session.get('last_name')
    username = session.get('username')

    details = db.execute('''SELECT *
                            FROM assets
                            WHERE user_id = ? AND is_deleted=0''', (user_id,)).fetchall()
    
    appreciation = db.execute('''SELECT *
                                 FROM assets
                                 JOIN delta ON assets.id = delta.asset_id
                                 WHERE assets.user_id = ? AND delta.delta_type = "appreciation" AND assets.is_deleted=0''', (user_id,)).fetchall()
    
    depreciation = db.execute('''SELECT *
                                 FROM assets
                                 JOIN delta ON assets.id = delta.asset_id
                                 WHERE assets.user_id = ? AND delta.delta_type = "depreciation" AND assets.is_deleted=0''', (user_id,)).fetchall()
    
    real_estate = db.execute(''' SELECT *
                                 FROM assets
                                 WHERE user_id = ? AND category = "Real Estate" AND is_deleted=0''', (user_id,)).fetchall()
    
    personal_valuables = db.execute('''SELECT *
                                FROM assets
                                WHERE user_id = ? AND category = "Personal Valuables" AND is_deleted=0''', (user_id,)).fetchall()

    investments = db.execute('''SELECT *
                                 FROM assets
                                 WHERE user_id = ? AND category = "Investments" AND is_deleted=0''', (user_id,)).fetchall()
    
    vehicles = db.execute('''SELECT *
                                 FROM assets
                                 WHERE user_id = ? AND category = "Vehicles" AND is_deleted=0''', (user_id,)).fetchall()
    
    real_estate_total = db.execute('''SELECT SUM(current_value*quantity) AS total_value
                                     FROM assets
                                     WHERE user_id = ? AND category = "Real Estate" AND is_deleted=0''', (user_id,)).fetchone()[0]
    
    investments_total = db.execute('''SELECT SUM(current_value*quantity) AS total_value
                                     FROM assets
                                     WHERE user_id = ? AND category = "Investments" AND is_deleted=0''', (user_id,)).fetchone()[0]
    
    vehicles_total = db.execute('''SELECT SUM(current_value*quantity) AS total_value
                                     FROM assets
                                     WHERE user_id = ? AND category = "Vehicles" AND is_deleted=0''', (user_id,)).fetchone()[0]
    
    personal_valuables_total = db.execute('''SELECT SUM(current_value*quantity) AS total_value
                                     FROM assets
                                     WHERE user_id = ? AND category = "Personal Valuables" AND is_deleted=0''', (user_id,)).fetchone()[0]

    real_estate_total = '{:,.2f}'.format(real_estate_total if real_estate_total is not None else 0)
    investments_total = '{:,.2f}'.format(investments_total if investments_total is not None else 0)
    personal_valuables_total = '{:,.2f}'.format(personal_valuables_total if personal_valuables_total is not None else 0)
    vehicles_total = '{:,.2f}'.format(vehicles_total if vehicles_total is not None else 0)
    
    return render_template('dashboard.html',
                            first_name = first_name,
                            last_name = last_name,
                            user_id = user_id,
                            details=details,
                            title='Dashboard',
                            appreciation=appreciation,
                            depreciation=depreciation,
                            real_estate=real_estate,
                            personal_valuables=personal_valuables,
                            investments=investments,
                            vehicles=vehicles,
                            real_estate_total=real_estate_total,
                            investments_total=investments_total,
                            vehicles_total=vehicles_total,
                            personal_valuables_total=personal_valuables_total)


#Add Asset Route
@app.route('/add_asset', methods=['GET', 'POST'])
@login_required
def add_asset():

    form=AddAssetForm()
    db = get_db()
    date_error = ''

    if form.validate_on_submit():

        name = form.name.data
        quantity = form.quantity.data
        category = form.category.data
        purchase_date = form.purchase_date.data
        purchase_price = form.purchase_price.data
        current_value = form.current_value.data
        today = date.today()
        date_str = today.strftime('%Y-%m-%m')
        user_id = session.get('user_id')

        if purchase_date > date.today():

            date_error = 'Date cannot be in the future.'

        elif purchase_date <= date.today():

            db.execute('''INSERT INTO assets(user_id,name, quantity, category, purchase_date, purchase_price, current_value)
                          VALUES (?, ?, ?, ?, ?, ?, ?)''', (user_id,name, quantity, category, purchase_date, purchase_price, current_value))
            asset = db.execute('''SELECT * FROM assets WHERE user_id = ? ORDER BY id DESC LIMIT 1''',(user_id,)).fetchone()
            asset_id = asset['id']

            delta = current_value - purchase_price
            if delta > 0:
                delta_type = 'appreciation'
                db.execute('''INSERT INTO delta(asset_id,name, old_value, new_value, delta, date, delta_type)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',(asset_id,name, purchase_price, current_value, delta, date_str, delta_type)) 
                db.execute('''INSERT INTO transactions(asset_id,name,transaction_type,price,date, profit_loss) 
                              VALUES(?, ?, ?, ?, ?, 'profit')''',(asset_id,name,'deposit',purchase_price,date_str))

            elif delta < 0:
                delta_type = 'depreciation'
                db.execute('''INSERT INTO delta(asset_id, name, old_value, new_value, delta, date, delta_type)
                              VALUES (?, ?, ?, ?, ?, ?, ?)''',(asset_id,name, purchase_price, current_value, delta, date_str, delta_type)) 
                db.execute('''INSERT INTO transactions(asset_id,name,transaction_type,price,date, profit_loss) 
                              VALUES(?, ?, ?, ?, ?, 'loss')''',(asset_id,name,'deposit',purchase_price,date_str))
            elif delta == 0:
                db.execute('''INSERT INTO transactions(asset_id,name,transaction_type,price,date) VALUES(?, ?, ?, ?, ?)''',(asset_id,name,'deposit',purchase_price,date_str))

            db.commit()

            date_error=''
            return redirect(url_for('dashboard'))

    return render_template('add_asset.html',
                           form=form,
                           title='Add Asset',
                           date_error=date_error)

#Delete Asset Route
@app.route('/delete_asset/<int:asset_id>', methods=['GET','POST'])
@login_required
def delete_asset(asset_id):

    db = get_db()
    form = DeleteAssetForm()
    today = date.today()
    date_str = today.strftime('%Y-%m-%d')

    if form.validate_on_submit():

        sale_price = form.price.data   
        asset = db.execute('''SELECT * FROM assets WHERE id = ?''',(asset_id,)).fetchone()
        asset_id = asset['id']
        name = asset['name']
        purchase_price = asset['purchase_price']
        delta_list = db.execute('''SELECT delta FROM delta WHERE asset_id = ?''',(asset_id,)).fetchall()
        total_delta = 0
        profit_loss_message = ''

        for _ in delta_list:
            total_delta += _['delta']
        price = purchase_price + total_delta
        profit_loss = sale_price - price

        if profit_loss < 0:
            profit_loss_message = 'loss'

        if profit_loss > 0:
            profit_loss_message = 'profit'

        if profit_loss == 0:
            profit_loss_message = 'none'

        db.execute('UPDATE assets SET is_deleted = 1 WHERE id = ?', (asset_id,))
        db.execute('''INSERT INTO transactions (asset_id,name,transaction_type,price,date,profit_loss)
                      VALUES (?, ?, ?, ?, ?, ?)''',(asset_id,name,'withdrawal',price,date_str,profit_loss_message))
        db.commit()

        return redirect(url_for('dashboard'))

    return render_template('sale_asset.html',
                           form=form,
                           asset_id=asset_id,
                           title='Sell Asset')


#Edit Asset Route
@app.route('/edit_asset/<int:asset_id>', methods=['GET', 'POST'])
@login_required
def edit_asset(asset_id):

    db = get_db()
    asset = db.execute('SELECT * FROM assets WHERE id = ?', (asset_id,)).fetchone()
    purchase_date = asset['purchase_date']

    form = EditAssetForm(
        name = asset['name'],
        quantity = asset['quantity'],
        category = asset['category'],
        purchase_date = purchase_date,
        purchase_price = asset['purchase_price'],
        current_value = asset['current_value']
    )

    if form.validate_on_submit():
        
        name = form.name.data
        quantity = form.quantity.data
        category = form.category.data
        purchase_date = form.purchase_date.data
        purchase_price = form.purchase_price.data
        current_value = form.current_value.data

        db.execute('UPDATE assets SET name = ?, quantity = ?, category = ?, purchase_date = ?, purchase_price = ?, current_value = ? WHERE id = ?',
                   (name, quantity, category, purchase_date, purchase_price, current_value, asset_id))
        db.commit()
        return redirect(url_for('dashboard'))

    return render_template('edit_asset.html',
                           form=form,
                           title='Edit Asset')


#Update Asset Route
@app.route('/update_asset/<int:asset_id>', methods=['GET', 'POST'])
@login_required
def update_asset(asset_id):

    db = get_db()
    form = UpdateAssetForm()
    if form.validate_on_submit():
        current_value = form.price.data
        asset = db.execute('''SELECT * FROM assets where id = ?''',(asset_id,)).fetchone()
        old_value = asset['current_value']
        name = asset['name']
        delta = int(current_value) - int(old_value)
        delta_type=''
        today = date.today()
        date_str = today.strftime('%Y-%m-%d')
        if delta < 0:
            delta_type = 'depreciation'
        else:
            delta_type = 'appreciation'

        db.execute('''UPDATE assets SET current_value = ? WHERE id = ?''',(current_value,asset_id)).fetchone()
        db.execute('''UPDATE delta SET new_value = ?, delta = ?, delta_type = ? WHERE asset_id = ?''',(current_value, delta, delta_type, asset_id ))
        db.commit()

        return redirect(url_for('dashboard'))
    return render_template('update_asset.html',
                           form=form,
                           asset_id=asset_id,
                           title='Update Asset')


#CSV Conversion Function
def convert_csv(queries_and_labels):

    db = get_db()
    output = io.StringIO()
    writer = csv.writer(output)
    
    for i, (query, params, label) in enumerate(queries_and_labels):
        if i > 0:
            writer.writerow([]) 
        
        writer.writerow([f"--- {label} ---"])
        
        cursor = db.execute(query, params)
        
        column_names = [description[0] for description in cursor.description]
        
        writer.writerow(column_names)
        
        for row in cursor.fetchall():
            writer.writerow([row[col] for col in column_names])
    
    byte_output = io.BytesIO()
    byte_output.write(output.getvalue().encode('utf-8'))
    byte_output.seek(0)
    
    return byte_output


#CSV Conversion Route
@app.route('/export', methods=['GET', 'POST'])
@login_required
def export():

    user_id = session.get('user_id')

    queries_and_labels = [
        (
            "SELECT transactions.asset_id, transactions.name, transactions.transaction_type, "
            "transactions.price, transactions.date, transactions.profit_loss "
            "FROM transactions JOIN assets ON assets.id = transactions.asset_id "
            "WHERE assets.user_id = ?", 
            (user_id,), 
            "Transactions"
        ),
        (
            "SELECT id, name, category, purchase_price, current_value, quantity, purchase_date "
            "FROM assets WHERE user_id = ? AND is_deleted = 0", 
            (user_id,), 
            "Assets"
        ),
        (
            "SELECT * FROM assets JOIN delta ON assets.id = delta.asset_id "
            "WHERE assets.user_id = ? AND delta.delta_type = 'appreciation' AND assets.is_deleted=0", 
            (user_id,), 
            "Appreciation"
        ),
        (
            "SELECT * FROM assets JOIN delta ON assets.id = delta.asset_id "
            "WHERE assets.user_id = ? AND delta.delta_type = 'depreciation' AND assets.is_deleted=0", 
            (user_id,), 
            "Depreciation"
        )
    ]
    
    csv_file = convert_csv(queries_and_labels)
    
    return send_file(
        csv_file, 
        as_attachment=True, 
        download_name=f'user_{user_id}_exported_data.csv', 
        mimetype="text/csv"
    )


#Insights Route
@app.route('/insights', methods=['GET', 'POST'])
@login_required
def insights():

    db = get_db()
    user_id = session.get('user_id')

    depr_advice = db.execute('''SELECT *
                                FROM delta AS d
                                JOIN assets AS a ON d.asset_id = a.id
                                WHERE a.user_id = ?
                                AND d.delta_type = 'depreciation' 
                                AND a.is_deleted = 0
                                AND d.id = (
                                    SELECT MAX(d2.id) 
                                    FROM delta AS d2 
                                    WHERE d2.asset_id = d.asset_id 
                                    AND d2.delta_type = 'depreciation'
                                )
                                 AND a.current_value < (a.purchase_price * 0.7);''',(user_id,)).fetchall()

    return render_template('insights.html', depr_advice=depr_advice, title='Insights')

#Logs Route
@app.route('/logs', methods=['GET', 'POST'])
@login_required
def logs():

    db = get_db()
    user_id = session.get('user_id')

    transactions = db.execute('''SELECT *
                                 FROM assets
                                 JOIN transactions ON assets.id = transactions.asset_id
                                 WHERE assets.user_id = ?''',(user_id,)).fetchall()
    appr_depr = db.execute('''SELECT *
                              FROM assets
                              JOIN delta ON assets.id = delta.asset_id
                              WHERE assets.user_id = ?''',(user_id,)).fetchall()

    return render_template('logs.html', transactions=transactions, appr_depr=appr_depr, title='Logs')
    

#Logout Route
@app.route('/logout')
@login_required
def logout():
    session.clear()
    session.modified = True
    return redirect(url_for('index'))

