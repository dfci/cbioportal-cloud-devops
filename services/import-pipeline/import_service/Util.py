import sqlite3
import time
import hashlib

__old_print__ = print


def print(*args, **kwargs):
    return __old_print__(time.time(), *args, **kwargs)


def content_hasher(file_name):
    block_size = 4 * 1024 * 1024
    with open(file_name, 'rb') as f:
        block_digests = [hashlib.sha256(block).digest()
                         for block in iter(lambda: f.read(block_size), b'')]
    return hashlib.sha256(b''.join(block_digests)).hexdigest()


class SQL(object):
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def exec_sql(self, statement, *args, fetchall=True):
        result = self.connection.execute(statement, args)
        return result.fetchall() if fetchall else result.fetchone()

    def exec_sql_to_single_val(self, statement, *args):
        result = self.exec_sql(statement, *args)
        return result[0] if result is not None else result

    def exec_sql_to_column_set(self, statement, *args, col_no=0):
        results = self.exec_sql(statement, args)
        return {result[col_no] for result in results}


def line_iter(content):
    content = '\n'.join(content.split('\r')).split('\n')
    return (line for line in content if line)
