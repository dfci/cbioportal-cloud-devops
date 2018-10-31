import sqlite3
import time
import hashlib
import MySQLdb

__old_print__ = print


def print(*args, **kwargs):
    return __old_print__(time.time(), *args, **kwargs)


def content_hasher(file_name):
    block_size = 4 * 1024 * 1024
    with open(file_name, 'rb') as f:
        block_digests = [hashlib.sha256(block).digest()
                         for block in iter(lambda: f.read(block_size), b'')]
    return hashlib.sha256(b''.join(block_digests)).hexdigest()


class SQL_sqlite3(object):
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.connection.row_factory = sqlite3.Row

    def exec_sql(self, statement, *args, fetchall=True):
        result = self.connection.execute(statement, args)
        return result.fetchall() if fetchall else result.fetchone()

    def exec_sql_to_single_val(self, statement, *args):
        result = self.exec_sql(statement, *args)
        return result[0] if result is not None else result

    def exec_sql_to_column_set(self, statement, *args, col_no=0):
        results = self.exec_sql(statement, args)
        return {result[col_no] for result in results}

    def exec_sql_to_dict(self, statement, *args, fetchall=True):
        results = self.exec_sql(statement, *args, fetchall=fetchall)
        if not isinstance(results, list):
            results = [results]
        ret = [{k: result[k] for k in result.keys()} for result in results]
        if fetchall:
            return ret
        else:
            return ret[0] if ret else list()


class SQL_mysql(object):
    def __init__(self, connection: MySQLdb.Connection):
        self.connection = connection
        self.cursor = None

    def __enter__(self):
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cursor.close()
        if exc_type is not None:
            self.connection.rollback()
        else:
            self.connection.commit()

    def exec_sql(self, statement, *args, fetchall=True):
        self.cursor.execute(statement, args)
        return self.cursor.fetchall() if fetchall else self.cursor.fetchone()

    def exec_sql_to_single_val(self, statement, *args):
        result = self.exec_sql(statement, *args)
        return result[0] if result is not None else result

    def exec_sql_to_column_set(self, statement, *args, col_no=0):
        results = self.exec_sql(statement, args)
        return {result[col_no] for result in results}


def line_iter(content):
    content = '\n'.join(content.split('\r')).split('\n')
    return (line for line in content if line)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
