from StudyManagementItemAccess import *
from StudyManagementItems import *
from Util import SQL, line_iter, print
import re
import os


class AuthorizationManager(object):
    def __init__(self, local_sql: SQL, cbio_sql: SQL):
        self._local_sql = local_sql
        self._cbio_sql = cbio_sql
        self.StudyAccess = StudyAccess(local_sql)
        self.StudyVersionAccess = StudyVersionAccess(local_sql)
        self.FileAccess = FilesAccess(local_sql)
        self.email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

    def run(self):
        self._run_auth_sync()

    def _run_auth_sync(self):
        statement = ('WITH q AS (SELECT s.id         study_id,'
                     '                  sv.id        study_version_id,'
                     '                  f.file_id    file_id,'
                     '                  row_number() OVER (PARTITION BY s.id ORDER BY sv.id DESC, s.id DESC) AS _id '
                     '           FROM study_versions sv'
                     '                  INNER JOIN studies s ON sv.study_id = s.id'
                     '                  INNER JOIN study_version_files f ON sv.id = f.study_version_id'
                     "           WHERE f.file_path = 'access.txt')"
                     'SELECT study_id, study_version_id, file_id '
                     'FROM q '
                     'WHERE _id = 1')
        results = self._local_sql.exec_sql(statement)
        for result in results:
            study = self.StudyAccess.get_study_by_id(result[0])
            study_version = self.StudyVersionAccess.get_study_version_by_id(result[1])
            access_file = self.FileAccess.get_file_by_id(result[2])
            is_valid = None
            authorized_emails = set() | {email for email in os.environ['ADMIN_EMAILS'].split(',')}
            for line in line_iter(access_file.get_contents()):
                if re.match(self.email_regex, line.strip()) is None:
                    is_valid = False
                    break
                else:
                    authorized_emails.add(line.strip())
            meta_study_file = self.FileAccess.get_file_from_study_version_file(
                self.FileAccess.get_meta_study_file_from_study_version(study_version))
            meta_dict = {k: v
                         for k, v
                         in [line.split(':')
                             if ':' in line else (line, None)
                             for line in line_iter(meta_study_file.get_contents())]}
            cancer_study_name = meta_dict['cancer_study_identifier']
            if is_valid is not None:
                print("Current access.txt for study '{}' is not valid, please fix.".format(cancer_study_name))
                break
            self.unauthorize_all_for_study(cancer_study_name)
            for email in authorized_emails:
                if not self.user_exists(email):
                    self.add_user(email)

    def user_exists(self, email):
        statement = 'SELECT TRUE FROM users WHERE email = ?'
        result = self._cbio_sql.exec_sql(statement, email)
        return True if result else None

    def add_user(self, email):
        statement = 'INSERT INTO users (email, name, enabled) VALUES (?, ?, ?)'
        self._cbio_sql.exec_sql(statement, email, email, True)

    def unauthorize_all_for_study(self, study_name):
        statement = "DELETE FROM authorities WHERE authority LIKE 'cbioportal:?'"
        self._cbio_sql.exec_sql(statement, study_name.upper())

    def authorize_for_study(self, email, study_name):
        statement = "INSERT INTO authorities (email, authority) VALUES (?, 'cbioportal:?')"
        self._cbio_sql.exec_sql(statement, email, study_name.upper())
