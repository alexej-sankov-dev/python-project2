import os
import pathlib
import functools

import requests
from flask import Flask, request, session, abort, redirect, render_template
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests

from flask_sqlalchemy import SQLAlchemy
import os
from flask_cors import CORS

from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey, inspect

# Init flask app
app = Flask(__name__, static_url_path='/static')
app.secret_key = "thisisascrretkey"
CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))

# Configure Google OAuth
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
GOOGLE_CLIENT_ID = '284367183567-on8o315hgl0ce948c78l6f6dr82sc8o6.apps.googleusercontent.com'
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, 'client_secret.json')
flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'openid'],
    redirect_uri='http://localhost:3000/callback'
)

# Configure Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'shop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'lsekjrldskjf324asd'
app.config['DEBUG'] = True

# Init db
db = SQLAlchemy(app)

# Product Class/Model
class Product(db.Model):
    productid = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    type = db.Column(db.String(80), nullable=False)
    game = db.Column(db.String(80), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    imageurl = db.Column(db.String(100), nullable=False)

    def __init__(self, title, description, type, game, stock, price, imageurl):
        self.title = title
        self.description = description
        self.type = type
        self.game = game
        self.stock = stock
        self.price = price
        self.imageurl = imageurl

# User Class/Model
class User(db.Model):
    userid = db.Column(db.String(80), primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(300), nullable=False)
    balance = db.Column(db.Integer, nullable=False)
    ifseller = db.Column(db.Boolean, nullable=False)

    def __init__(self, userid, name, email):
        self.userid = userid
        self.name = name
        self.email = email
        self.ifseller = False
        self.balance = 0

# Order Class/Model
class Order(db.Model):
    orderid = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.String(80), ForeignKey(User.userid), nullable=False)
    productid = db.Column(db.Integer, ForeignKey(Product.productid), nullable=False)
    date_start = db.Column(db.DateTime(timezone=True), server_default=func.now())
    status = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Integer, nullable=False)

    def __init__(self, userid, productid, amount):
        self.userid = userid
        self.productid = productid
        self.amount = amount
        self.status = 'processing'

# edited ModelViews with Primary and Forgein Keys
class ProductView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    column_list = [c_attr.key for c_attr in inspect(Product).mapper.column_attrs]

class UserView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    column_list = [c_attr.key for c_attr in inspect(User).mapper.column_attrs]

class OrderView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    column_list = [c_attr.key for c_attr in inspect(Order).mapper.column_attrs]

# init Admin
admin = Admin(app)
admin.add_view(ProductView(Product, db.session))
admin.add_view(UserView(User, db.session))
admin.add_view(OrderView(Order, db.session))

# Decorators for protected routes
def login_is_required(func):
    @functools.wraps(func) 
    def wrapper(*args, **kwargs):
        if 'google_id' not in session:
            return abort(401)
        else:
            u = User.query.get(session['google_id'])
            if u is not None:
                session['name'] = u.name
                session['email'] = u.email
                session['ifseller'] = u.ifseller
            return func(*args, **kwargs)
    return wrapper

def seller_is_required(func):
    @functools.wraps(func) 
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)
        elif not session['ifseller']:
            return abort(404)
        else:
            u = User.query.get(session['google_id'])
            if u is not None:
                session['name'] = u.name
                session['email'] = u.email
                session['ifseller'] = u.ifseller
            return func(*args, **kwargs)
    return wrapper

# OAuth Routes
@app.route('/login')
def login():
    authorization_url, state = flow.authorization_url()
    session['state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session['state'] == request.args['state']:
        abort(500)

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID
    )

    session['google_id'] = id_info.get('sub')
    session['name'] = id_info.get('name')
    session['email'] = id_info.get('email')
    session['ifseller'] = False
    
    u = User.query.get(session['google_id'])
    if u is None:
        new_user = User(session['google_id'], session['name'], session['email'])
        db.session.add(new_user)
        db.session.commit()
    else:
        session['ifseller'] = u.ifseller
    return redirect('/profile')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/logintestuser/<int:id>')
def login_test_user(id):
    session['google_id'] = id
    session['name'] = f'Test User{id}'
    session['email'] = f'test{id}@gmail.com'
    session['ifseller'] = False
    
    u = User.query.get(session['google_id'])
    if u is None:
        new_user = User(session['google_id'], session['name'], session['email'])
        db.session.add(new_user)
        db.session.commit()
    else:
        session['ifseller'] = u.ifseller
    return redirect('/profile')

# Home Route
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'google_id' not in session:
            return abort(401)
        pid = int(request.form.get('productid'))
        amount = int(request.form.get('amount'))
        
        p = Product.query.get(pid)
        u = User.query.get(session['google_id'])
        if amount > p.stock or amount * p.price > u.balance or amount <= 0:
            return abort(404)
        new_order = Order(session['google_id'], pid, amount)
        db.session.add(new_order)
        u.balance = u.balance - amount * p.price
        p.stock = p.stock - amount
        db.session.commit()
        return redirect('profile')
    else:
        products = Product.query.filter(Product.stock > 0).all()
        return render_template('index.jinja2', products=products)

@app.route('/profile', methods=['GET', 'POST'])
@login_is_required
def profile():
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_email = request.form.get('email')
        new_ifseller = request.form.get('ifseller') is not None
        u = User.query.get(session['google_id'])
        u.name = new_name
        u.email = new_email
        u.ifseller = new_ifseller
        session['name'] = u.name
        session['email'] = u.email
        session['ifseller'] = u.ifseller
        db.session.commit()
        return redirect('/')
    else:
        my_orders = Order.query.filter_by(userid=session['google_id']).all()
        data_my_orders = []
        u = User.query.get(session['google_id'])
        for i, o in enumerate(my_orders):
            p = Product.query.get(o.productid)
            d = (i+1, p.title, p.price*o.amount, o.amount, o.date_start, o.status)
            data_my_orders.append(d)
        return render_template('profile.jinja2', data=data_my_orders, balance=u.balance)

# Route to add money to balance
@app.route('/addmoney/', methods=['POST'])
@login_is_required
def addmoney():
        u = User.query.get(session['google_id'])
        u.balance = u.balance + 100
        db.session.commit()
        return redirect('/profile')

# Seller Route
@app.route('/sell', methods=['GET', 'POST'])
@seller_is_required
def sell():
    if request.method == 'POST':
        o = Order.query.get(request.form.get('orderid'))
        o.status = 'completed'
        u = User.query.get(session['google_id'])
        p = Product.query.get(o.productid)
        u.balance = u.balance + p.price*o.amount*0.6
        db.session.commit()
        return redirect('sell')
    else:    
        proc_orders = Order.query.filter_by(status='processing').all()
        data_proc_orders = []
        for i, o in enumerate(proc_orders):
            p = Product.query.get(o.productid)
            u = User.query.get(o.userid)
            if u is None:
                continue
            d = (i+1, p.title, p.price*o.amount*0.6, o.amount, u.email, o.orderid)
            data_proc_orders.append(d)
        return render_template('sell.jinja2', data=data_proc_orders)

# Route to withdraw money from balance
@app.route('/witmoney/', methods=['POST'])
@login_is_required
def witmoney():
        u = User.query.get(session['google_id'])
        u.balance = 0
        db.session.commit()
        return redirect('/profile')

# run server on localhost
if __name__ == '__main__':
    app.run(host='localhost', port=3000)