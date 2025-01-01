import pandas as pd

def init_analysis_table(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS whatsapp_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            chat_name TEXT,
            total_messages INTEGER,
            total_users INTEGER,
            total_words INTEGER,
            total_media INTEGER,
            total_links INTEGER,
            most_active_user TEXT,
            most_used_emoji TEXT,
            chat_start_date TEXT,
            chat_end_date TEXT,
            analysis_data TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()

def store_analysis_results(conn, user_id, df, analysis_stats):
    cursor = conn.cursor()
    
    chat_name = df['user'].iloc[0] if len(df) > 0 else 'Unknown'
    most_active_user = df['user'].value_counts().index[0] if len(df) > 0 else 'Unknown'
    
    cursor.execute("""
        INSERT INTO whatsapp_analyses (
            user_id, chat_name, total_messages, total_users, 
            total_words, total_media, total_links, most_active_user,
            chat_start_date, chat_end_date, analysis_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, chat_name, analysis_stats['total_messages'],
        analysis_stats['total_users'], analysis_stats['total_words'],
        analysis_stats['total_media'], analysis_stats['total_links'],
        most_active_user, str(df['date'].iloc[0])[:10],
        str(df['date'].iloc[-1])[:10], df.to_json()
    ))
    conn.commit()

def get_user_analyses(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM whatsapp_analyses 
        WHERE user_id = ? 
        ORDER BY analysis_date DESC
    """, (user_id,))
    return cursor.fetchall()