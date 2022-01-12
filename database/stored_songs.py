import sqlite3
import logging 

    
def db_initialize_songs():   
    conn = sqlite3.connect('spinner.db')
    c = conn.cursor()

    try:
        c.execute("""CREATE TABLE songs (
                artist text,
                track text,
                duration text,
                url text,
                last_played datetime,
                play_count integer
            )""")
    except:
        logging.warn("Could not create table.")

    conn.commit()
    conn.close()