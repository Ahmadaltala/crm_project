DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS communication;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE customer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE communication (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    communication_type TEXT NOT NULL,
    notes TEXT,
    response INTEGER NOT NULL,
    contact_date DATETIME NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customer (id),
    FOREIGN KEY (user_id) REFERENCES user (id)
);