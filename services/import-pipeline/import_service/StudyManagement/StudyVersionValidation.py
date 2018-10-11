from import_service.StudyUtil.utils import SQL


class StudyVersionValidationRepo(object):
    def __init__(self, sql: SQL):
        self.sql = sql
