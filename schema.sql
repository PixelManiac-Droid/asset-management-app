DROP TABLE IF EXISTS winners;

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    password TEXT NOT NULL
        );

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('deposit','withdrawal')), 
    price REAL NOT NULL,
    date  DATE NOT NULL,
    profit_loss TEXT CHECK(profit_loss IN('profit','loss','none')),
    FOREIGN KEY (asset_id) REFERENCES assets(id)
        );

CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    purchase_price REAL NOT NULL,
    current_value REAL NOT NULL,
    quantity INTEGER NOT NULL,
    purchase_date DATE NOT NULL,
    is_deleted INTEGER DEFAULT 0 NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
        );

CREATE TABLE IF NOT EXISTS delta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    old_value FLOAT NOT NULL,
    new_value FLOAT NOT NULL,
    delta FLOAT NOT NULL,
    date DATE NOT NULL,
    delta_type TEXT NOT NULL CHECK(delta_type IN('depreciation','appreciation')),
    FOREIGN KEY (asset_id) references assets(id)
    );

