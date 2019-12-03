from Util import SQL_sqlite3, line_iter
from StudyManagementItems import *


class FilesAccess(object):

    def __init__(self, sql: SQL_sqlite3):
        self.sql = sql
        pass

    def get_file_by_content_hash(self, content_hash):
        statement = 'SELECT id, content_hash, path FROM files WHERE content_hash = ?'
        result = self.sql.exec_sql(statement, content_hash)
        return File(*result[0], self.sql) if result else None

    def delete_files_by_content_hash(self, content_hash):
        statement = 'DELETE FROM files WHERE content_hash = ?'
        self.sql.exec_sql(statement, content_hash)

    def insert_file_path_with_content_hash(self, content_hash, file_path):
        statement = 'INSERT INTO files (content_hash, path) VALUES (?, ?)'
        self.sql.exec_sql(statement, content_hash, file_path)

    def get_files_by_content_hashes(self, content_hashes):
        return [self.get_file_by_content_hash(content_hash) for content_hash in content_hashes]

    def get_file_from_study_version_file(self, study_version_file: StudyVersionFile):
        statement = ('SELECT f.content_hash '
                     'FROM study_version_files svf '
                     'INNER JOIN files f '
                     'ON f.id = svf.file_id '
                     'WHERE svf.study_version_id = ? '
                     'AND svf.file_id = ?')
        result = self.sql.exec_sql_to_single_val(statement, study_version_file.get_study_version_id(),
                                                 study_version_file.get_file_id())
        return self.get_file_by_content_hash(result[0]) if result is not None else result

    def get_file_by_id(self, file_id):
        statement = 'SELECT id, content_hash, path FROM files WHERE id = ?'
        result = self.sql.exec_sql(statement, file_id, fetchall=False)
        return File(*result, self.sql) if result else None

    def get_meta_study_file_from_study_version(self, study_version: StudyVersion):
        study_version_files = study_version.get_study_version_files()
        for study_version_file in study_version_files:
            file_name = study_version_file.get_file_path().lower()
            if "meta" in file_name:
                file = self.get_file_from_study_version_file(study_version_file)
                meta_dict = {k: v for k, v in
                             [(line.split(':')[0], ''.join(line.split(':')[1::])) if ':' in line else (line, None)
                              for line in line_iter(file.get_contents())]}
                if 'cancer_study_identifier' in meta_dict and 'type_of_cancer' in meta_dict:
                    return study_version_file
        return None


class TopLevelFoldersAccess(object):
    def __init__(self, sql: SQL_sqlite3):
        self.sql = sql

    def list_all_orgs(self):
        statement = 'SELECT id, org_name FROM orgs'
        results = self.sql.exec_sql(statement)
        return [TopLevelFolder(*result, self.sql) for result in results] if results else list()

    def add_org(self, org_name):
        statement = 'INSERT INTO orgs (org_name) VALUES (?)'
        self.sql.exec_sql(statement, org_name)

    def get_org_by_name(self, org_name):
        statement = 'SELECT id, org_name FROM orgs WHERE org_name = ?'
        result = self.sql.exec_sql(statement, org_name, fetchall=False)
        return TopLevelFolder(*result, self.sql) if result else None


class StudyAccess(object):
    def __init__(self, sql: SQL_sqlite3):
        self.sql = sql

    def new_study(self, organization: TopLevelFolder, study_name, available):
        statement = 'INSERT INTO studies (study_name, org_id, available) VALUES (?, ?, ?)'
        self.sql.exec_sql(statement, study_name, organization.get_id(), available)
        return organization.get_study_by_name(study_name)

    def get_study_by_id(self, id):
        statement = ('SELECT id, org_id, study_name, available '
                     'FROM studies s '
                     'WHERE id = ?')
        result = self.sql.exec_sql(statement, id, fetchall=False)
        return Study(*result, self.sql) if result else None


class StudyVersionFileAccess(object):
    def __init__(self, sql: SQL_sqlite3):
        self.sql = sql

    def add_new_study_version_file(self, study_version: StudyVersion, file: File, path, modified_date):
        statement = ('INSERT INTO study_version_files (study_version_id, file_id, file_path, file_modified_date)'
                     'VALUES (?, ?, ?, ?)')
        self.sql.exec_sql(statement, study_version.get_id(), file.get_id(), path, modified_date)


class StudyVersionAccess(object):
    def __init__(self, sql: SQL_sqlite3):
        self.sql = sql

    def get_active_study_version(self, study: Study):
        statement = ('SELECT id, study_id, aggregate_hash, passes_validation, loads_successfully, currently_loaded '
                     'FROM study_versions '
                     'WHERE study_id = ? '
                     'AND currently_loaded '
                     'LIMIT 1')
        result = self.sql.exec_sql(statement, study.get_id(), fetchall=False)
        return StudyVersion(*result, self.sql) if result else None

    def get_study_version_by_id(self, study_version_id):
        statement = ('SELECT id, study_id, aggregate_hash, passes_validation, loads_successfully, currently_loaded '
                     'FROM study_versions '
                     'WHERE id = ? '
                     'LIMIT 1')
        result = self.sql.exec_sql(statement, study_version_id, fetchall=False)
        return StudyVersion(*result, self.sql) if result else None

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

    def set_all_study_versions_in_study_currently_loaded(self, study: Study, currently_loaded):
        statement = ('UPDATE study_versions '
                     'SET currently_loaded = ? '
                     'WHERE study_id = ? '
                     'AND currently_loaded IS NOT NULL ')
        self.sql.exec_sql(statement, currently_loaded, study.get_id())

    def get_study_versions_needing_import_test(self):
        statement = (
            'WITH  q AS (SELECT sv.id, '
            'row_number() OVER (PARTITION BY s.id ORDER BY sv.id DESC, s.id DESC) AS _id '
            'FROM study_versions sv '
            'INNER JOIN study_version_validation v ON sv.id = v.study_version_id '
            'INNER JOIN studies s ON sv.study_id = s.id '
            'WHERE s.available '
            '  AND ((sv.loads_successfully IS NULL) '
            '      OR (sv.loads_successfully))) '
            'SELECT sv.* '
            'FROM q '
            'INNER JOIN study_versions sv ON sv.id = q.id '
            'WHERE ((currently_loaded IS NULL) '
            '   OR (NOT currently_loaded)) AND q._id = 1')
        results = self.sql.exec_sql(statement)
        return [StudyVersion(*result, self.sql) for result in results] if results is not None else list()


class StudyVersionValidationAccess(object):
    def __init__(self, sql: SQL_sqlite3):
        self.sql = sql
