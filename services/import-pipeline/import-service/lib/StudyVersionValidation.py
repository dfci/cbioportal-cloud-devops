from .utils import SQL


class StudyVersionValidationRepo(object):
    def __init__(self, sql: SQL):
        self.sql = sql
