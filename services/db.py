from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from psycopg_pool import ConnectionPool
from psycopg.rows import class_row
from psycopg.types.json import Jsonb


@dataclass
class MhCleanupRecord:
    fragment_id: str
    original_metadata: str
    transformed_metadata: str
    transformations: Jsonb
    status: str
    error: str
    created_at: datetime
    modified_at: datetime


class DatabaseService(object):
    def __init__(self, config: dict, table: str):
        self.pool = ConnectionPool(
            f"host={config['database']['host']} port={config['database']['port']} dbname={config['database']['dbname']} user={config['database']['user']} password={config['database']['password']}"
        )
        self.table = table

    def count_items_to_process(self) -> int:
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                return cur.execute(
                    f"SELECT count(*) FROM public.{self.table} WHERE status = 'TODO'"
                ).fetchone()[0]

    def get_item_to_process(self) -> Optional[MhCleanupRecord]:
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=class_row(MhCleanupRecord)) as cur:
                return cur.execute(
                    f"SELECT * FROM public.{self.table} WHERE status = 'TODO' LIMIT 1"
                ).fetchone()

    def update_db_status(self, fragment_id: str, status: str):
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE public.{self.table} SET status = %s WHERE fragment_id = %s;",
                    (status, fragment_id),
                )
                conn.commit()
