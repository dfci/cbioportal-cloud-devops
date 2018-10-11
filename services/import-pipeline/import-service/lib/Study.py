from .utils import SQL
from .Organization import Organization


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


class StudyRepo(object):
    def __init__(self, sql: SQL):
        self.sql = sql

    def new_study(self, organization: Organization, study_name, available):
        statement = 'INSERT INTO studies (study_name, org_id, available) VALUES (?, ?, ?)'
        self.sql.exec_sql(statement, study_name, organization.get_id(), available)
        return organization.get_study_by_name(study_name)
