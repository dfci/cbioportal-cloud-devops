import os
import hashlib
import shutil
import time
import subprocess
from .utils import content_hasher, SQL
from .FileSyncSource import FileSyncSource
from .Organization import OrganizationsRepo
from .Study import StudyRepo
from .StudyVersionValidation import StudyVersionValidationRepo
from .StudyVersionFile import StudyVersionFileRepo
from .StudyVersion import StudyVersionRepo
from .File import FileRepo


class StudySync(object):
    def __init__(self,
                 connection,
                 sync_class: type(FileSyncSource),
                 sync_class_args,
                 download_dir,
                 portal_home,
                 study_link_dir,
                 schema_sql_path):
        self._schema_sql_path = schema_sql_path
        self._portal_home = portal_home
        self._validator_path = os.path.join(self._portal_home,
                                            'core/src/main/scripts/importer/validateData.py')
        self._cbioportalimporter_path = os.path.join(self._portal_home,
                                                     'core/src/main/scripts/importer/cbioportalImporter.py')
        self._metaimport_path = os.path.join(self._portal_home,
                                             'core/src/main/scripts/importer/metaImport.py')
        self._study_link_dir = study_link_dir
        self._download_dir = download_dir
        self._sql = SQL(connection)
        self._sync = sync_class(**sync_class_args)
        self.StudyVersionValidationRepo = StudyVersionValidationRepo(self._sql)
        self.StudyVersionFileRepo = StudyVersionFileRepo(self._sql)
        self.StudyVersionRepo = StudyVersionRepo(self._sql)
        self.StudyRepo = StudyRepo(self._sql)
        self.OrganizationsRepo = OrganizationsRepo(self._sql)
        self.FileRepo = FileRepo(self._sql)

    def run(self):
        self._sync.run()
        self._run_local_db_init()
        self._run_files_download()
        self._run_update_orgs()
        self._run_update_studies()
        self._run_update_study_versions()
        self._run_study_version_validation()

    def _run_local_db_init(self):
        print("Running schema setup...")
        with open(self._schema_sql_path) as schema_file:
            statements = schema_file.read().split(';')
            for statement in statements:
                self._sql.connection.execute(statement)

    def _run_files_download(self):
        print("Running files download...")
        for content_hash, remote_path in self._sync.content_hash_to_remote_path.items():
            file_from_db = self.FileRepo.get_file_by_content_hash(content_hash)
            do_download = True if file_from_db is None or (
                not os.path.isfile(file_from_db.get_path())) or content_hash != content_hasher(
                file_from_db.get_path()) else False
            if file_from_db is None or do_download:
                self.FileRepo.delete_files_by_content_hash(content_hash)
            if do_download:
                file_download_path = os.path.join(self._download_dir, content_hash)
                if not (os.path.isfile(file_download_path) and content_hash == content_hasher(file_download_path)):
                    print("Downloading file {} with content_hash {}".format(remote_path, content_hash))
                    self._sync.do_download(local_path=file_download_path, remote_path=remote_path)
                    assert content_hash == content_hasher(file_download_path)
                self.FileRepo.insert_file_path_with_content_hash(content_hash, file_download_path)

    def _run_update_orgs(self):
        print("Running orgs update...")
        orgs_in_db = {org.get_name() for org in self.OrganizationsRepo.list_all_orgs()}
        new_orgs = [org for org in set(self._sync.all_entries.keys()) - orgs_in_db]
        for org_name in new_orgs:
            self.OrganizationsRepo.add_org(org_name)

    def _run_update_studies(self):
        print("Running studies update...")
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
        print("Running study versions update...")
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

    def _run_study_version_validation(self):
        print("Running study version validation...")
        study_versions_needing_validation = self.StudyVersionRepo.get_study_versions_needing_validation()
        for study_version in study_versions_needing_validation:
            study_version_tmp_path = os.path.join(self._study_link_dir, str(study_version.get_id()))
            if os.path.exists(study_version_tmp_path):
                shutil.rmtree(study_version_tmp_path)
            for study_version_file in study_version.get_study_version_files():
                file_path = self.FileRepo.get_file_from_study_version_file(study_version_file).get_path()
                link_path = study_version_file.get_file_path()
                full_link_path = os.path.join(study_version_tmp_path, link_path)
                os.makedirs(os.path.dirname(full_link_path), exist_ok=True)
                os.symlink(file_path, full_link_path)
            try:
                p = subprocess.check_output("python {} -s {} -n".format(self._validator_path, study_version_tmp_path),
                                            shell=True,
                                            stderr=subprocess.STDOUT)
                status_code = 0
                output = p.decode('utf-8')
            except subprocess.CalledProcessError as e:
                status_code = e.returncode
                output = e.output.decode('utf-8')
            if status_code in {0, 3}:
                success = True
            else:
                success = False
            study_version.add_study_version_validation(status_code, success, output, int(time.time()))
