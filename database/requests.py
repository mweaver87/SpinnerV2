import sqlite3
import logging 

    
def db_initialize():   
    conn = sqlite3.connect('spinner.db')
    c = conn.cursor()

    try:
        # URL can be the foreign key
        # Can remove play count from here
        # last played goes to the other table
        c.execute("""CREATE TABLE requests (
                server text,
                user text,
                url text,
                liked boolean,
                play_count integer,
                last_played text
            )""")
    except:
        logging.warn("Could not create table.")

    conn.commit()
    conn.close()


async def fetch_objects_server(server):
    conn = sqlite3.connect('spinner.db')
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM requests WHERE server=:server", {'server': server})
        query = c.fetchall()
    except:
        query = "NA"
    conn.commit()
    conn.close()
    return query


async def fetch_objects_user(server, user):
    conn = sqlite3.connect('spinner.db')
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM requests WHERE server=:server AND user=:user", {'server': server, 'user': user})
        query = c.fetchall()
    except:
        query = "NA"
    conn.commit()
    conn.close()
    return query


async def fetch_user_liked(server):
    conn = sqlite3.connect('spinner.db')
    c = conn.cursor()
    liked = 1
    try:
        c.execute("SELECT * FROM requests WHERE server=:server AND liked=:liked", {'server': server, 'liked': liked})
        query = c.fetchall()
    except:
        query = "NA"
    conn.commit()
    conn.close()
    return query
    

async def fetch_objects_user_song(server, user, url):
    conn = sqlite3.connect('spinner.db')
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM requests WHERE server=:server AND user=:user AND url=:url", {'server': server, 'user': user, 'url': url})
        query = c.fetchall()
    except:
        query = "NA"
    conn.commit()
    conn.close()
    return query


async def create_object(server, user, url, liked, play_count, last_played):
    conn = sqlite3.connect('spinner.db')
    c = conn.cursor()
    c.execute("INSERT INTO requests VALUES (:server, :user, :url, :liked, :play_count, :last_played)", {'server': server, 'user': user, 'url': url, 'liked': liked, 'play_count':play_count, 'last_played': last_played})
    conn.commit()
    conn.close()


async def update_likes(server, user, url, liked):
    conn = sqlite3.connect('spinner.db')
    c = conn.cursor()
    with conn:
        c.execute("""UPDATE requests SET liked = :liked
                    WHERE server = :server AND user = :user AND url = :url""",
                    {'server': server, 'user': user, 'url': url, 'liked': liked})
    conn.commit()
    conn.close()


async def update_played(server, user, url, liked, play_count, last_played):
    conn = sqlite3.connect('spinner.db')
    c = conn.cursor()
    with conn:
        c.execute("""UPDATE requests SET play_count = play_count+1
                    WHERE server = :server AND user = :user AND url = :url""",
                    {'server': server, 'user': user, 'url': url, 'liked':liked, 'play_count': play_count, 'last_played': last_played})
        c.execute("""UPDATE requests SET last_played = :last_played
                    WHERE server = :server AND user = :user AND url = :url""",
                    {'server': server, 'user': user, 'url': url, 'liked':liked, 'play_count': play_count, 'last_played': last_played})
    conn.commit()
    conn.close()

