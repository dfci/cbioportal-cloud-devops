from .utils import SQL
from .File import File
from .StudyVersion import StudyVersion


class StudyVersionFile(object):
    def __init__(self, study_version_id, file_id, file_path, file_modified_date, sql: SQL):
        self.sql = sql
        self.study_version_id = study_version_id
        self.file_id = file_id
        self.file_path = file_path
        self.file_modified_date = file_modified_date

    def get_study_version_id(self):
        return self.study_version_id

    def get_file_id(self):
        return self.file_id

    def get_file_path(self):
        return self.file_path

    def get_file_modified_date(self):
        return self.file_modified_date


class StudyVersionFileRepo(object):
    def __init__(self, sql: SQL):
        self.sql = sql

    def add_new_study_version_file(self, study_version: StudyVersion, file: File, path, modified_date):
        statement = ('INSERT INTO study_version_files (study_version_id, file_id, file_path, file_modified_date)'
                     'VALUES (?, ?, ?, ?)')
        self.sql.exec_sql(statement, study_version.get_id(), file.get_id(), path, modified_date)
