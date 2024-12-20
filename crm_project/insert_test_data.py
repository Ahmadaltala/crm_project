import sqlite3

def insert_test_users():
    conn = sqlite3.connect('sample_auth.db')
    c = conn.cursor()
    
    #!!!!!passwords are here!!!!!
    test_users = [
        ('admin', 'admin123', 'admin', 'active'),
        ('sales1', 'sales123', 'sales', 'active'),
        ('manager1', 'manager123', 'manager', 'active')
    ]
    
    c.executemany('INSERT INTO user (username, password, role, status) VALUES (?, ?, ?, ?)', test_users)
    

    test_customers = [
        ('John Doe', 'active'),
        ('Jane Smith', 'active'),
        ('Bob Johnson', 'inactive')
    ]
    
    c.executemany('INSERT INTO customer (name, status) VALUES (?, ?)', test_customers)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    insert_test_users()
    print("Test data inserted successfully!")