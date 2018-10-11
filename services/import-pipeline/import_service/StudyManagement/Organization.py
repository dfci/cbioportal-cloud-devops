from import_service.StudyUtil.utils import SQL
from import_service.StudyManagement.Study import Study


class OrganizationsRepo(object):
    def __init__(self, sql: SQL):
        self.sql = sql

    def list_all_orgs(self):
        statement = 'SELECT id, org_name FROM orgs'
        results = self.sql.exec_sql(statement)
        return [Organization(*result, self.sql) for result in results] if results else list()

    def add_org(self, org_name):
        statement = 'INSERT INTO orgs (org_name) VALUES (?)'
        self.sql.exec_sql(statement, org_name)

    def get_org_by_name(self, org_name):
        statement = 'SELECT id, org_name FROM orgs WHERE org_name = ?'
        result = self.sql.exec_sql(statement, org_name, fetchall=False)
        return Organization(*result, self.sql) if result else None


class Organization(object):
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
