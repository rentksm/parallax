import duckdb
import os

def init_db(db_path='news.duckdb'):
    # Ensure db is in the correct path
    conn = duckdb.connect(db_path)
    
    # Create stories table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS stories (
        id VARCHAR PRIMARY KEY,
        title VARCHAR,
        topic VARCHAR DEFAULT 'Other',
        structured_data VARCHAR,
        created_at TIMESTAMP
    )
    ''')
    
    # Create events table
    conn.execute('''
    CREATE SEQUENCE IF NOT EXISTS seq_event_id;
    CREATE TABLE IF NOT EXISTS events (
        id VARCHAR PRIMARY KEY,
        story_id VARCHAR,
        title VARCHAR,
        topic VARCHAR DEFAULT 'Other',
        structured_data VARCHAR,
        created_at TIMESTAMP
    )
    ''')
    
    # Create articles table
    conn.execute('''
    CREATE TABLE IF NOT EXISTS articles (
        id VARCHAR PRIMARY KEY,
        title VARCHAR,
        source VARCHAR,
        url VARCHAR UNIQUE,
        published_at TIMESTAMP,
        event_id VARCHAR,
        FOREIGN KEY (event_id) REFERENCES events(id)
    )
    ''')
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    init_db()
