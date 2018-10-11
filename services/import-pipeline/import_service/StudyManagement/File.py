from import_service.StudyUtil.utils import SQL
from import_service.StudyManagement.StudyVersionFile import StudyVersionFile


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


class FileRepo(object):

    def __init__(self, sql: SQL):
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
