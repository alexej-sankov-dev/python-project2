# Run Server

In directory /shop
```bash
$ python3 -m venv venv  # on Windows, use "python -m venv venv" instead
$ . venv/bin/activate  # on Windows, use "venv\Scripts\activate" instead
$ pip3 install -r requirements.txt
```

Run the server on http://localhost:3000
```bash
$ python3 server.py
```

# Data Model
## Order
### Comlumns:
    productid - Integer, primary_key
    title - String(80), nullable=False
    description - String(300), nullable=False
    type - String(80), nullable=False
    game - String(80), nullable=False
    stock - Integer, nullable=False
    price - Integer, nullable=False
    imageurl - String(100), nullable=False


# Routes
## Home Page /
### Not authorized user
    - can see list of products
    - can login with Google account
### Logged-in user
    - has /profile route in header menu
    - can select amount of product to buy
    - can buy product if product is in stock and user has enough money on balance else Error 404

## Profile /profile
### Not authorized user
    - Error 401
### Logged-in user
    - can deposit money to balance by clicking button (adds 100$)
    - can withdraw all money from balance
    - can edit Username and Email
    - can become a seller and will have /sell route in header menu
    - can see data of all his orders 

## Sell /sell
### Not authorized user
    - Error 401
### For normal users seller
    - Error 404
### For sellers
    - can see all orders of all users with stats 'processing'
    - can complete order and will receive Payout to balance, the status of the order will change to completed

## Admin Page /admin