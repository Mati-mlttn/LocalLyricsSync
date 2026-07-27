import sqlite3
import threading

class Database:

    def __init__(self, filename):

        self.filename = filename

        self.lock = threading.Lock()

        self.conn = sqlite3.connect(
            filename,
            check_same_thread=False
        )

        self.conn.execute("PRAGMA journal_mode=WAL")

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS cache(
            file TEXT PRIMARY KEY,
            artist TEXT,
            title TEXT,
            album TEXT,
            status TEXT,
            provider TEXT,
            searched_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()

    def get_status(self, file):
        """Devuelve el status cacheado para este archivo, o None si no existe."""
        with self.lock:
            cur = self.conn.execute(
                "SELECT status FROM cache WHERE file = ?",
                (str(file),)
            )
            row = cur.fetchone()
            return row[0] if row else None

    def upsert(self, file, artist, title, album, status, provider):
        """Inserta o actualiza el resultado del procesamiento de un archivo."""
        with self.lock:
            self.conn.execute("""
                INSERT INTO cache (file, artist, title, album, status, provider)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(file) DO UPDATE SET
                    artist=excluded.artist,
                    title=excluded.title,
                    album=excluded.album,
                    status=excluded.status,
                    provider=excluded.provider,
                    searched_at=CURRENT_TIMESTAMP
            """, (str(file), artist, title, album, status, provider))
            self.conn.commit()