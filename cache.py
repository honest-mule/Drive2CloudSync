from pathlib import Path
import sqlite3
from sqlite3 import Error
from utils import Correction

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
    logger = None

    def __init__(self, logger = None) -> None:
        db_file_path = Path(r".\cache\managed_list.db")
        db_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.create_connection(db_file_path)
        self.create_table()
        self.logger = logger

    def create_connection(self, db_file):
        """ create a database connection to a SQLite database """
        try:
            self.conn = sqlite3.connect(db_file)
        except Error as e:
            self.__log_error(e)

    def create_table(self):
        try:
            c = self.conn.cursor()
            with open(r"create_cache_tables.sql") as sql_file:
                sql = sql_file.read()
                c.executescript(sql)
        except Error as e:
            self.__log_error(e)

    def save(self, torrent_id, type, tmdb_id, folder_name, hash):
        try:
            c = self.conn.cursor()
            c.execute("INSERT OR IGNORE INTO list (torrent_id, type, tmdb_id) VALUES(?,?,?)", (torrent_id, type, tmdb_id))
            c.execute("INSERT OR IGNORE INTO torrents (id, hash, folder) VALUES (?,?,?)", (torrent_id, hash, folder_name))
            self.conn.commit()
        except Error as e:
            self.__log_error(e)

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
            self.__log_error(e)
            return None

    def get_torrent_id(self, hash: str):
        try:
            c = self.conn.cursor()
            c.execute("SELECT id FROM torrents WHERE hash=?", (hash,))
            result = c.fetchone()
            if result:
                return result[0]
            else:
                return None
        except Error as e:
            self.__log_error(e)
            return None
        
    def get_torrent_media_type(self, hash: str):
        try:
            c = self.conn.cursor()
            c.execute("SELECT type FROM list WHERE torrent_id=(SELECT id FROM torrents WHERE hash=?)", (hash,))
            result = c.fetchone()
            if not result:
                return None
            return result[0]
        except Error as e:
            self.__log_error(e)
            return None

    def get_dest_folder(self, torrent_id=""):
        try:
            c = self.conn.cursor()
            c.execute("SELECT dest_folder FROM torrents WHERE id=?", (torrent_id,))
            result = c.fetchone()
            if result:
                return result[0]
            else:
                return None
        except Error as e:
            self.__log_error(e)
            return None

    def get_dest_folder2(self, hash=""):
        try:
            c = self.conn.cursor()
            c.execute("SELECT dest_folder FROM torrents WHERE hash=?", (hash,))
            result = c.fetchone()
            if result:
                return result[0]
            else:
                return None
        except Error as e:
            self.__log_error(e)
            return None

    def get_dest_folder_by_torrent_hash(self, hash):
        try:
            c = self.conn.cursor()
            c.execute("SELECT dest_folder FROM torrents WHERE hash=?", (hash,))
            result = c.fetchone()
            if result:
                return result[0]
            else:
                return None
        except Error as e:
            self.__log_error(e)
            return None

    def save_dest_folder(self, torrent_id, dest_folder):
        try:
            c = self.conn.cursor()
            c.execute("UPDATE torrents SET dest_folder=? WHERE id=?", (dest_folder, torrent_id))
            self.conn.commit()
            return True
        except Error as e:
            self.__log_error(e)
            return False
    
    def update_torrent_id(self, torrent_id, hash = None, old_torrent_id = None):
        try:
            c = self.conn.cursor()
            if not old_torrent_id and hash:
                old_torrent_id = self.get_torrent_id(hash)
            if not old_torrent_id:
                return False
            c.execute("UPDATE list SET torrent_id=? WHERE torrent_id=?", (torrent_id, old_torrent_id))
            c.execute("UPDATE torrents SET id=? WHERE id=?", (torrent_id, old_torrent_id))
            self.conn.commit()
        except Error as e:
            self.__log_error(e)
            return False

    def fix_entry(self, correction: Correction):
        try:
            c = self.conn.cursor()
            c.execute("SELECT id FROM torrents WHERE hash=?", (correction.hash,))
            torrent_id = c.fetchone()
            if not torrent_id:
                return False
            torrent_id = torrent_id[0]
            c.execute("UPDATE list SET type=?,tmdb_id=? WHERE torrent_id=?", (correction.type, correction.tmdb_id, torrent_id))
            c.execute("UPDATE torrents SET dest_folder=NULL WHERE id=?", (torrent_id,))
            self.conn.commit()
            return True
        except Error as e:
            self.__log_error(e)
            return False

    def get_saved_torrent_ids(self):
        results = []
        try:
            c = self.conn.cursor()
            c.execute("SELECT id FROM torrents")
            return [row[0] for row in c]
        except Error as e:
            self.__log_error(e)
            return []

    def __log_error(self, e):
        if self.logger:
            self.logger.error(f"DB issue: {e}")
        else:
            print(e)