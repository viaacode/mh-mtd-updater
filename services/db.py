from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from psycopg_pool import ConnectionPool
from psycopg.rows import class_row
from psycopg.types.json import Jsonb


class RecordStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    ERROR = "ERROR"


@dataclass
class MhCleanupRecord:
    fragment_id: str
    cp_id: str
    jira_ticket: str
    original_metadata: str
    update_object: str
    transformations: Jsonb
    status: str
    error: str
    error_msg: str
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

    # TODO: check Pyscopg docs to verify if both statements are executed within
    # one and the same transaction!
    def get_item_to_process(self) -> Optional[MhCleanupRecord]:
        with self.pool.connection() as conn:
            with conn.cursor(row_factory=class_row(MhCleanupRecord)) as cur:
                item = cur.execute(
                    f"SELECT * FROM public.{self.table} WHERE status = 'TODO' LIMIT 1"
                ).fetchone()
                if item:
                    cur.execute(
                        f"UPDATE public.{self.table} SET status = %s WHERE fragment_id = %s;",
                        (RecordStatus.IN_PROGRESS.value, item.fragment_id),
                    )
                    conn.commit()
                return item

    def update_db_status(self, fragment_id: str, status: str):
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE public.{self.table} SET status = %s WHERE fragment_id = %s;",
                    (status, fragment_id),
                )
                conn.commit()

    def update_with_result(self, item: MhCleanupRecord):
        """Convenience method to update this record's state after a cleanup-run."""
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""UPDATE public.{self.table} SET
                        original_metadata = %s, update_object = %s, status = %s, error = %s, error_msg = %s
                    WHERE fragment_id = %s;""",
                    (
                        item.original_metadata,
                        item.update_object,
                        item.status,
                        item.error,
                        item.error_msg,
                        item.fragment_id,
                    ),
                )
                conn.commit()
