from StudyManagementItemAccess import *
from StudyManagementItems import *
from Util import SQL_sqlite3, line_iter, print
import re
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class _User(object):
    def __init__(self, email, name, enabled, cbio_sql):
        self.email = email
        self.name = name
        self.enabled = enabled
        self.cbio_sql = cbio_sql

    def _exists(self):
        statement = 'SELECT TRUE FROM users WHERE email = %s'
        result = self.cbio_sql.exec_sql(statement, self.email)
        return True if result else None

    def _equals(self, other):
        if not isinstance(other, _User):
            return False
        else:
            return (self.email == other.email) and (self.name == other.name) and (self.enabled == other.enabled)

    def _needs_updating(self):
        statement = 'SELECT email, name, enabled FROM users WHERE email = %s'
        result = self.cbio_sql.exec_sql(statement, self.email, fetchall=False)
        user = _User(*result, self.cbio_sql) if result else None
        if self._equals(user):
            return False
        else:
            return True

    def _update(self):
        statement = "UPDATE users SET name = %s, enabled = %s WHERE email = %s"
        self.cbio_sql.exec_sql(statement, self.name, self.enabled, self.email)

    def _add(self):
        statement = 'INSERT INTO users (email, name, enabled) VALUES (%s, %s, %s)'
        self.cbio_sql.exec_sql(statement, self.email, self.name, self.enabled)


class AuthorizationManager(object):
    def __init__(self, local_sql: SQL_sqlite3, cbio_sql: SQL_sqlite3):
        self._local_sql = local_sql
        self._cbio_sql = cbio_sql
        self.StudyAccess = StudyAccess(local_sql)
        self.StudyVersionAccess = StudyVersionAccess(local_sql)
        self.FileAccess = FilesAccess(local_sql)
        self.email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

    def run(self):
        self._run_auth_sync()
        self._run_user_sync()

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
                         in [(line.split(':')[0], line.split(':')[1])
                             if ':' in line else (line, None)
                             for line in line_iter(meta_study_file.get_contents())]}
            cancer_study_name = meta_dict['cancer_study_identifier'].strip()
            print("Found meta study file for study '{}' at '{}' with cancer_study_identifier as '{}'".format(
                study.get_study_name(), meta_study_file.get_path(), cancer_study_name))
            if is_valid is not None:
                print("Current access.txt for study '{}' is not valid, please fix.".format(cancer_study_name))
                break
            print("Removing all authorizations...")
            self.unauthorize_all_for_study(cancer_study_name)
            for email in authorized_emails:
                print("Authorizing email '{}' for study '{}' with cancer_study_identifier '{}".format(email,
                                                                                                      study.get_study_name(),
                                                                                                      cancer_study_name))
                self.authorize_for_study(email, cancer_study_name)

    def _run_user_sync(self):
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        gcloud_creds = json.loads(os.environ['GCLOUD_CREDS'])
        service_account_creds = ServiceAccountCredentials.from_json_keyfile_dict(gcloud_creds, scope)
        gc = gspread.authorize(service_account_creds)
        spreadsheet = gc.open_by_key(os.environ['AUTH_SHEET_KEY'])
        worksheet = spreadsheet.worksheet(os.environ['AUTH_SHEET_WORKSHEET_NAME'])
        key_map = json.loads(os.environ['AUTH_SHEET_KEYMAP'])
        true_val = os.environ['AUTH_SHEET_TRUEVAL']
        user_records = worksheet.get_all_records()
        distinct_emails = set()
        for record in user_records:
            name = ' '.join(
                [record[key] for key in (key_map['name'] if isinstance(key_map['name'], list) else [key_map['name']])])
            email = record[key_map['email']]
            enabled = True if record[key_map['enabled']] == true_val else False
            self.user_handler(email, name, enabled)
        admin_emails = {email for email in os.environ['ADMIN_EMAILS'].split(',')}
        for email in admin_emails - distinct_emails:
            self.user_handler(email, email, True)

    def user_handler(self, email, name, enabled):
        user = _User(email, name, enabled, self._cbio_sql)
        if not user._exists():
            user._add()
        elif user._needs_updating():
            user._update()

    def unauthorize_all_for_study(self, study_name):
        statement = "DELETE FROM authorities WHERE authority LIKE 'cbioportal:{}'".format(study_name.upper())
        self._cbio_sql.exec_sql(statement)

    def authorize_for_study(self, email, study_name):
        statement = "INSERT INTO authorities (email, authority) VALUES (%s, 'cbioportal:{}')".format(study_name.upper())
        self._cbio_sql.exec_sql(statement, email)
