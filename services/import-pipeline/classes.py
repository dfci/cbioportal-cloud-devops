import dropbox
import sqlite3
import hashlib
from collections import defaultdict


def content_hasher(file_name):
    block_size = 4 * 1024 * 1024
    with open(file_name, 'rb') as f:
        block_digests = [hashlib.sha256(block).digest()
                         for block in iter(lambda: f.read(block_size), b'')]
    return hashlib.sha256(b''.join(block_digests)).hexdigest()


class FileSyncSource(object):
    def __init__(self):
        super().__init__()
        self.all_entries = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        self.content_hash_to_remote_path = dict()

    def run(self) -> None:
        pass

    def do_download(self, local_path: str, remote_path: str) -> None:
        pass


class DropBoxSync(FileSyncSource):
    def __init__(self, dbx_access_token, allowed_folders):
        super().__init__()
        self.dbx = dropbox.Dropbox(dbx_access_token)
        self.allowed_folders = allowed_folders

    def run(self):
        self.all_entries = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        self.content_hash_to_remote_path = dict()
        self._run_dbx_files_init()

    def _run_dbx_files_init(self):

        cursors = list()

        def process_list_folder_result(list_folder_result):
            for entry in list_folder_result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    split_path = entry.path_display.split('/')
                    org = split_path[1]
                    study = split_path[2]
                    path = '/'.join(split_path[3::])
                    self.all_entries[org][study][path][entry.content_hash] = str(entry.server_modified)
                    self.content_hash_to_remote_path[entry.content_hash] = entry.path_display
            if hasattr(list_folder_result, 'cursor') and list_folder_result.has_more:
                cursors.append(list_folder_result.cursor)

        for folder in self.allowed_folders:
            process_list_folder_result(self.dbx.files_list_folder("/" + folder, recursive=True))
        while cursors:
            process_list_folder_result(self.dbx.files_list_folder_continue(cursors.pop()))

    def do_download(self, local_path, remote_path):
        self.dbx.files_download_to_file(path=remote_path, download_path=local_path)


class SQL(object):
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def exec_sql(self, statement, *args, fetchall=True):
        result = self.connection.execute(statement, args)
        return result.fetchall() if fetchall else result.fetchone()

    def exec_sql_to_single_val(self, statement, *args):
        result = self.exec_sql(statement, *args)
        return result[0] if result is not None else result

    def exec_sql_to_column_set(self, statement, *args, col_no=0):
        results = self.exec_sql(statement, args)
        return {result[col_no] for result in results}


class Organization(object):
    def __init__(self, _id, org_name, sql):
        self._id = _id
        self._org_name = org_name
        self.sql = sql

    def get_studies(self, available=None):
        statement = ('SELECT id, org_id, study_name, available '
                     'FROM studies '
                     'WHERE org_id = ? '
                     'AND available = ?' if available else '')
        results = self.sql.exec_sql(statement, self.get_id(), available if available is not None else ())
        return [Study(*result, self.sql) for result in results] if results else None

    def get_study_by_name(self, study_name):
        statement = ('SELECT id, org_id, study_name, available '
                     'FROM studies '
                     'WHERE org_id = ? '
                     'AND study_name = ?')
        result = self.sql.exec_sql(statement, self.get_id(), study_name, fetchall=False)
        return Study(*result[0], self.sql) if result else None

    def get_id(self):
        return self._id

    def study_name_exists(self, study_name):
        return True if self.get_study_by_name(study_name) is not None else False


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
        return [StudyVersionFile(*result, self.sql) for result in results] if results is not None else results


class StudyVersionValidationRepo(object):
    def __init__(self, sql: SQL):
        self.sql = sql


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


class StudyVersionRepo(object):
    def __init__(self, sql: SQL):
        self.sql = sql

    def get_study_version(self, study: Study, aggregate_hash):
        statement = ('SELECT id, study_id, aggregate_hash, passes_validation, loads_successfully, currently_loaded '
                     'FROM study_verions '
                     'WHERE study_id = ? '
                     'AND aggregate_hash = ?')
        result = self.sql.exec_sql(statement, study.get_id(), aggregate_hash, fetchall=False)
        return StudyVersion(*result[0], self.sql) if result else None

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
                     'FROM study_verions sv '
                     'INNER JOIN studies s ON s.id = sv.study_id '
                     'WHERE v.passes_validation IS NULL '
                     'AND study_id = ?' if study is not None else '')
        results = self.sql.exec_sql(statement, study.get_id() if study is not None else ())
        return [StudyVersion(*result, self.sql) for result in results] if results is not None else results

    def get_study_versions_needing_import_test(self, study: Study = None):
        statement = ('SELECT sv.id, sv.study_id, sv.aggregate_hash, '
                     'sv.passes_validation, sv.loads_successfully, sv.currently_loaded '
                     'FROM study_verions sv '
                     'INNER JOIN studies s ON s.id = sv.study_id '
                     'WHERE v.loads_successfully IS NULL '
                     'AND study_id = ?' if study is not None else '')
        results = self.sql.exec_sql(statement, study.get_id() if study is not None else ())
        return [StudyVersion(*result, self.sql) for result in results] if results is not None else results


class StudyRepo(object):
    def __init__(self, sql: SQL):
        self.sql = sql

    def new_study(self, organization: Organization, study_name, available):
        statement = 'INSERT INTO studies (study_name, org_id, available) VALUES (?, ?, ?)'
        self.sql.exec_sql(statement, study_name, organization.get_id(), available)
        return organization.get_study_by_name(study_name)


class OrganizationsRepo(object):
    def __init__(self, sql: SQL):
        self.sql = sql

    def list_all_orgs(self):
        statement = 'SELECT id, org_name FROM orgs'
        results = self.sql.exec_sql(statement)
        return [Organization(*result, self.sql) for result in results] if results else None

    def add_org(self, org_name):
        statement = 'INSERT INTO orgs (org_name) VALUES (?)'
        self.sql.exec_sql(statement, org_name)

    def get_org_by_name(self, org_name):
        statement = 'SELECT id, org_name FROM orgs WHERE org_name = ?'
        result = self.sql.exec_sql(statement, org_name, fetchall=False)
        return Organization(*result[0], self.sql) if result else None


class FileRepo(object):

    def __init__(self, sql: SQL):
        self.sql = sql
        pass

    def get_file_by_content_hash(self, content_hash):
        statement = 'SELECT id, content_hash, path FROM files WHERE content_hash = ?'
        result = self.sql.exec_sql(statement, content_hash)
        return File(*result, self.sql) if result else None

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
        return self.get_file_by_content_hash(result) if result is not None else result


class StudySync(object):
    def __init__(self, sql: SQL, sync: FileSyncSource, download_dir):
        self._download_dir = download_dir
        self._sql = sql
        self._sync = sync
        self.StudyVersionValidationRepo = StudyVersionValidationRepo(sql)
        self.StudyVersionFileRepo = StudyVersionFileRepo(sql)
        self.StudyVersionRepo = StudyVersionRepo(sql)
        self.StudyRepo = StudyRepo(sql)
        self.OrganizationsRepo = OrganizationsRepo(sql)
        self.FileRepo = FileRepo(sql)

    def run(self):
        self._sync.run()
        self._run_local_db_init()
        self._run_files_download()
        self._run_update_orgs()
        self._run_update_studies()
        self._run_update_study_versions()

    def _run_local_db_init(self):
        with open('/schema.sql') as schema_file:
            statements = schema_file.read().split(';')
            for statement in statements:
                self._sql.connection.execute(statement)

    def _run_files_download(self):
        for content_hash, remote_path in self._sync.content_hash_to_remote_path.items():
            file_from_db = self.FileRepo.get_file_by_content_hash(content_hash)
            do_download = any((file_from_db is None,
                               not os.path.isfile(file_from_db.path),
                               content_hash == content_hasher(file_from_db.path)))
            if file_from_db is None:
                self.FileRepo.delete_files_by_content_hash(content_hash)
            if do_download:
                file_download_path = os.path.join(self._download_dir, content_hash)
                print("Downloading file {} with content_hash {}".format(remote_path, content_hash))
                self._sync.do_download(local_path=file_download_path, remote_path=remote_path)
                assert content_hash == content_hasher(file_download_path)
                self.FileRepo.insert_file_path_with_content_hash(content_hash, file_download_path)

    def _run_update_orgs(self):
        orgs_in_db = {org.org_name for org in self.OrganizationsRepo.list_all_orgs()}
        new_orgs = [org for org in set(self._sync.all_entries.keys()) - orgs_in_db]
        for org_name in new_orgs:
            self.OrganizationsRepo.add_org(org_name)

    def _run_update_studies(self):
        for org_name, study_entries in self._sync.all_entries.items():
            org = self.OrganizationsRepo.get_org_by_name(org_name)
            studies_in_db = org.get_studies()
            incoming_study_names = set(study_entries.keys())
            for study in studies_in_db:
                if study.get_study_name() not in incoming_study_names:
                    study.mark_unavailable()
                elif not study.is_available():
                    study.mark_available()
            for study_name in incoming_study_names:
                if not org.study_name_exists(study_name):
                    self.StudyRepo.new_study(org, study_name, available=True)

    def _run_update_study_versions(self):
        for org_name, study_entries in self._sync.all_entries.items():
            org = self.OrganizationsRepo.get_org_by_name(org_name)
            for study_name, path_entries in study_entries.items():
                study = org.get_study_by_name(study_name)
                aggregate_list = [path.encode('utf-8') + content_hash.encode('utf-8')
                                  for path, content_hash_entries in path_entries.items()
                                  for content_hash in content_hash_entries.keys()]
                aggregate_hash = hashlib.sha256(b''.join(sorted(aggregate_list))).hexdigest()
                if not self.StudyVersionRepo.study_version_exists(study, aggregate_hash):
                    study_version = self.StudyVersionRepo.new_study_version(study, aggregate_hash)
                    for path, content_hash_entries in path_entries.items():
                        for content_hash, server_modified in content_hash_entries.items():
                            file = self.FileRepo.get_file_by_content_hash(content_hash)
                            self.StudyVersionFileRepo.add_new_study_version_file(study_version,
                                                                                 file,
                                                                                 path,
                                                                                 server_modified)
