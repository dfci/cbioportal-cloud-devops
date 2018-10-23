from Util import SQL


class File(object):
    def __init__(self, _id, content_hash, path, sql: SQL):
        self.sql = sql
        self._id = _id
        self._content_hash = content_hash
        self._path = path

    def get_id(self):
        return self._id

    def get_path(self):
        return self._path


class TopLevelFolder(object):
    def __init__(self, _id, org_name, sql):
        self._id = _id
        self._org_name = org_name
        self.sql = sql

    def get_name(self):
        return self._org_name

    def get_studies(self, available=None):
        statement = ('SELECT id, org_id, study_name, available '
                     'FROM studies '
                     'WHERE org_id = ? ')
        if available is not None:
            statement += 'AND available = ?'
            results = self.sql.exec_sql(statement, self.get_id(), available)
        else:
            results = self.sql.exec_sql(statement, self.get_id())
        return [Study(*result, self.sql) for result in results] if results else list()

    def get_study_by_name(self, study_name):
        statement = ('SELECT id, org_id, study_name, available '
                     'FROM studies '
                     'WHERE org_id = ? '
                     'AND study_name = ?')
        result = self.sql.exec_sql(statement, self.get_id(), study_name, fetchall=False)
        return Study(*result, self.sql) if result else None

    def get_id(self):
        return self._id

    def study_name_exists(self, study_name):
        return True if self.get_study_by_name(study_name) is not None else False


class Study(object):
    def __init__(self, _id, org_id, study_name, available, sql: SQL):
        self.sql = sql
        self._id = _id
        self._org_id = org_id
        self._study_name = study_name
        self._available = available

    def get_id(self):
        return self._id

    def get_study_name(self):
        return self._study_name

    def is_available(self):
        return self._available

    def _set_available(self, available):
        statement = 'UPDATE studies SET available = ? WHERE id = ?'
        self.sql.exec_sql(statement, self._id, available)
        self._available = available

    def mark_available(self):
        self._set_available(True)

    def mark_unavailable(self):
        self._set_available(False)


class StudyVersion(object):
    def __init__(self, _id, study_id, aggregate_hash, passes_validation, loads_successfully, currently_loaded,
                 sql: SQL):
        self.sql = sql
        self._currently_loaded = currently_loaded
        self._passes_validation = passes_validation
        self._loads_successfully = loads_successfully
        self._id = _id
        self._study_id = study_id
        self._aggregate_hash = aggregate_hash

    def _set_passes_validation(self, passes_validation):
        statement = ('UPDATE study_versions '
                     'SET passes_validation = ? '
                     'WHERE id = ?')
        self.sql.exec_sql(statement, passes_validation, self.get_id())

    def _set_loads_successfully(self, loads_successfully):
        statement = ('UPDATE study_versions '
                     'SET loads_successfully = ? '
                     'WHERE id = ?')
        self.sql.exec_sql(statement, loads_successfully, self.get_id())

    def set_currently_loaded(self, currently_loaded):
        statement = ('UPDATE study_versions '
                     'SET currently_loaded = ? '
                     'WHERE id = ?')
        self.sql.exec_sql(statement, currently_loaded, self.get_id())

    def get_id(self):
        return self._id

    def add_study_version_validation(self, status_code, succeeded, output, time_added):
        statement = (
            'INSERT INTO study_version_validation (study_version_id, status_code, success, output, time_added) '
            'VALUES (?, ?, ?, ?, ?)')
        self.sql.exec_sql(statement, self.get_id(), status_code, succeeded, output, time_added)
        self._set_passes_validation(succeeded)

    def add_study_version_import(self, status_code, succeeded, output, time_added):
        statement = (
            'INSERT INTO study_version_import (study_version_id, status_code, success, output, time_added) '
            'VALUES (?, ?, ?, ?, ?)')
        self.sql.exec_sql(statement, self.get_id(), status_code, succeeded, output, time_added)
        self._set_loads_successfully(succeeded)

    def get_study_version_files(self):
        statement = ('SELECT f.study_version_id, f.file_id, f.file_path, f.file_modified_date '
                     'FROM study_versions sv '
                     'INNER JOIN study_version_files f ON sv.id = f.study_version_id '
                     'WHERE sv.id = ?')
        results = self.sql.exec_sql(statement, self.get_id())
        return [StudyVersionFile(*result, self.sql) for result in results] if results is not None else list()

    def get_study(self):
        statement = ('SELECT s.id, s.org_id, s.study_name, s.available '
                     'FROM study_versions sv '
                     'INNER JOIN studies s on s.id = sv.study_id '
                     'WHERE sv.id = ? ')
        result = self.sql.exec_sql(statement, self._id, fetchall=False)
        return Study(*result, self.sql) if result else None


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


class StudyVersionValidation(object):
    pass
