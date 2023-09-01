import sqlite3
from sqlite3 import Error

class TorrentCacheObject():
    torrent_id = None
    type = ""
    tmdb_id = None
    def __init__(self, obj: list) -> None:
        self.torrent_id = obj[1]
        self.type = obj[2]
        self.tmdb_id = obj[3]

class Cache():
    conn = None

    def __init__(self) -> None:
        self.create_connection(r".\cache\managed_list.db")
        self.create_table()

    def create_connection(self, db_file):
        """ create a database connection to a SQLite database """
        try:
            self.conn = sqlite3.connect(db_file)
        except Error as e:
            print(e)

    def create_table(self):
        try:
            c = self.conn.cursor()
            with open(r"create_cache_tables.sql") as sql_file:
                sql = sql_file.read()
                c.executescript(sql)
        except Error as e:
            print(e)

    def save(self, torrent_id, type, tmdb_id, folder_name):
        try:
            c = self.conn.cursor()
            c.execute("INSERT OR IGNORE INTO list (torrent_id, type, tmdb_id) VALUES(?,?,?)", (torrent_id, type, tmdb_id))
            c.execute("INSERT OR IGNORE INTO torrents (id, folder) VALUES (?,?)", (torrent_id, folder_name))
            self.conn.commit()
        except Error as e:
            print(e)

    def fetch(self, torrent_id):
        try:
            c = self.conn.cursor()
            c.execute("SELECT * FROM list WHERE torrent_id=?", (torrent_id,))
            result = c.fetchone()
            if result:
                return TorrentCacheObject(result)
            else:
                return None
        except Error as e:
            print(e)

    def get_torrent_id(self, folder_name):
        try:
            c = self.conn.cursor()
            c.execute("SELECT id FROM torrents WHERE folder=?", (folder_name,))
            result = c.fetchone()
            if result:
                return result[0]
            else:
                return None
        except Error as e:
            print(e)

    def get_dest_folder(self, torrent_id):
        try:
            c = self.conn.cursor()
            c.execute("SELECT dest_folder FROM torrents WHERE id=?", (torrent_id,))
            result = c.fetchone()
            if result:
                return result[0]
            else:
                return None
        except Error as e:
            print(e)

    def save_dest_folder(self, torrent_id, dest_folder):
        try:
            c = self.conn.cursor()
            c.execute("UPDATE torrents SET dest_folder=? WHERE id=?", (dest_folder, torrent_id))
            self.conn.commit()
        except Error as e:
            print(e)