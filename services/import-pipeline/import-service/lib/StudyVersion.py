from .utils import SQL
from .StudyVersionFile import StudyVersionFile
from .Study import Study


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

    def get_id(self):
        return self._id

    def add_study_version_validation(self, status_code, succeeded, output, time_added):
        statement = (
            'INSERT INTO study_version_validation (study_version_id, status_code, success, output, time_added) '
            'VALUES (?, ?, ?, ?, ?)')
        self.sql.exec_sql(statement, self.get_id(), status_code, succeeded, output, time_added)
        self._set_passes_validation(succeeded)

    def get_study_version_files(self):
        statement = ('SELECT f.study_version_id, f.file_id, f.file_path, f.file_modified_date '
                     'FROM study_versions sv '
                     'INNER JOIN study_version_files f ON sv.id = f.study_version_id '
                     'WHERE sv.id = ?')
        results = self.sql.exec_sql(statement, self.get_id())
        return [StudyVersionFile(*result, self.sql) for result in results] if results is not None else list()


class StudyVersionRepo(object):
    def __init__(self, sql: SQL):
        self.sql = sql

    def get_study_version(self, study: Study, aggregate_hash):
        statement = ('SELECT id, study_id, aggregate_hash, passes_validation, loads_successfully, currently_loaded '
                     'FROM study_versions '
                     'WHERE study_id = ? '
                     'AND aggregate_hash = ?')
        result = self.sql.exec_sql(statement, study.get_id(), aggregate_hash, fetchall=False)
        return StudyVersion(*result, self.sql) if result else None

    def study_version_exists(self, study: Study, aggregate_hash):
        return True if self.get_study_version(study, aggregate_hash) is not None else False

    def new_study_version(self, study: Study, aggregate_hash):
        statement = ('INSERT INTO study_versions (study_id, aggregate_hash)'
                     'VALUES (?, ?)')
        self.sql.exec_sql(statement, study.get_id(), aggregate_hash)
        return self.get_study_version(study, aggregate_hash)

    def get_study_versions_needing_validation(self, study: Study = None):
        statement = ('SELECT sv.id, sv.study_id, sv.aggregate_hash, '
                     'sv.passes_validation, sv.loads_successfully, sv.currently_loaded '
                     'FROM study_versions sv '
                     'INNER JOIN studies s ON s.id = sv.study_id '
                     'WHERE sv.passes_validation IS NULL ')
        if study is not None:
            statement += 'AND study_id = ?'
            results = self.sql.exec_sql(statement, study.get_id())
        else:
            results = self.sql.exec_sql(statement)
        return [StudyVersion(*result, self.sql) for result in results] if results is not None else list()

    def get_study_versions_needing_import_test(self, study: Study = None):
        statement = ('SELECT sv.id, sv.study_id, sv.aggregate_hash, '
                     'sv.passes_validation, sv.loads_successfully, sv.currently_loaded '
                     'FROM study_versions sv '
                     'INNER JOIN studies s ON s.id = sv.study_id '
                     'WHERE v.loads_successfully IS NULL ')
        if study is not None:
            statement += 'AND study_id = ?'
        if study is not None:
            results = self.sql.exec_sql(statement, study.get_id())
        else:
            results = self.sql.exec_sql(statement, statement)
        return [StudyVersion(*result, self.sql) for result in results] if results is not None else list()
