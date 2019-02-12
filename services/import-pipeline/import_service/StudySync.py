import os
import json
import hashlib
import shutil
import time
import subprocess
from Util import content_hasher, SQL_sqlite3, print, is_valid_access_file
from FileSyncSource import *
from StudyManagementAccess import *


class StudySync(object):
    UNVERSIONED_FILE_NAMES = {'access.txt'}

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
        self._sql = connection
        self._sync = sync_class(**sync_class_args)
        self.StudyVersionValidationAccess = StudyVersionValidationAccess(self._sql)
        self.StudyVersionFileAccess = StudyVersionFileAccess(self._sql)
        self.StudyVersionAccess = StudyVersionAccess(self._sql)
        self.StudyAccess = StudyAccess(self._sql)
        self.OrganizationsAccess = TopLevelFoldersAccess(self._sql)
        self.FileAccess = FilesAccess(self._sql)
        self.StudyAccessAccess = StudyFileAccess(self._sql)

    def perform_db_sync(self):
        self._run_local_db_init()
        self._run_db_sync()

    def perform_study_validation(self):
        self._run_study_version_validation()

    def perform_study_import(self):
        self._run_study_version_import()

    def _run_db_sync(self):
        self._sync.run()
        self._run_files_download()
        self._run_update_orgs()
        self._run_update_studies()
        self._run_update_study_versions()
        self._sync.register_all_entries_registered()
        self._run_update_dashboard_json()

    def _run_update_dashboard_json(self):
        print("Running update dashboard json...")
        tables_and_files = {
            "top_level_dashboard": "top_level.json",
            "second_level_dashboard": "second_level.json"
        }
        os.makedirs('/dashboard/data', exist_ok=True)
        for k, v in tables_and_files.items():
            with open(os.path.join('/dashboard/data', v), 'w') as f:
                json.dump(self._sql.exec_sql_to_dict('SELECT * FROM {}'.format(k)), f)

    def _run_local_db_init(self):
        print("Running schema setup...")
        with open(self._schema_sql_path) as schema_file:
            statements = schema_file.read().split(';')
        for statement in statements:
            self._sql.connection.execute(statement)

    def _run_files_download(self):
        print("Running files download...")
        for content_hash, remote_path in self._sync.content_hash_to_remote_path.items():
            file_from_db = self.FileAccess.get_file_by_content_hash(content_hash)
            do_download = True if file_from_db is None or (
                not os.path.isfile(file_from_db.get_path())) or content_hash != content_hasher(
                file_from_db.get_path()) else False
            if file_from_db is None or do_download:
                self.FileAccess.delete_files_by_content_hash(content_hash)
            if do_download:
                file_download_path = os.path.join(self._download_dir, content_hash)
                if not (os.path.isfile(file_download_path) and content_hash == content_hasher(file_download_path)):
                    print("Downloading file {} with content_hash {}".format(remote_path, content_hash))
                    self._sync.do_download(local_path=file_download_path, remote_path=remote_path)
                    assert content_hash == content_hasher(file_download_path)
                self.FileAccess.insert_file_path_with_content_hash(content_hash, file_download_path)

    def _run_update_orgs(self):
        print("Running orgs update...")
        orgs_in_db = {org.get_name() for org in self.OrganizationsAccess.list_all_orgs()}
        new_orgs = [org for org in set(self._sync.all_entries.keys()) - orgs_in_db]
        for org_name in new_orgs:
            self.OrganizationsAccess.add_org(org_name)

    def _run_update_studies(self):
        print("Running studies update...")
        for org_name, study_entries in self._sync.all_entries.items():
            org = self.OrganizationsAccess.get_org_by_name(org_name)
            studies_in_db = org.get_studies()
            incoming_study_names = set(study_entries.keys())
            for study in studies_in_db:
                if study.get_study_name() not in incoming_study_names:
                    study.mark_unavailable()
                elif not study.is_available():
                    study.mark_available()
            for study_name in incoming_study_names:
                if not org.study_name_exists(study_name):
                    self.StudyAccess.new_study(org, study_name, available=True)

    def _run_update_study_versions(self):
        print("Running study versions update...")
        for org_name, study_entries in self._sync.all_entries.items():
            org = self.OrganizationsAccess.get_org_by_name(org_name)
            for study_name, path_entries in study_entries.items():
                study = org.get_study_by_name(study_name)
                aggregate_list = [path.encode('utf-8') + content_hash.encode('utf-8')
                                  for path, content_hash_entries in path_entries.items()
                                  for content_hash in content_hash_entries.keys()
                                  if os.path.basename(path) not in self.UNVERSIONED_FILE_NAMES]
                aggregate_hash = hashlib.sha256(b''.join(sorted(aggregate_list))).hexdigest()
                for path, content_hash_entries in filter(lambda x: os.path.basename(x[0]) == "access.txt",
                                                         path_entries.items()):
                    print(1, path)
                    for content_hash in content_hash_entries:
                        print(2, content_hash)
                        file = self.FileAccess.get_file_by_content_hash(content_hash)
                        print(3, is_valid_access_file(file))
                        print(4, self.StudyAccessAccess.study_access_exists(study, file))
                        if is_valid_access_file(file) and not self.StudyAccessAccess.study_access_exists(study, file):
                            self.StudyAccessAccess.add_new_study_access(study, file)
                if not self.StudyVersionAccess.study_version_exists(study, aggregate_hash):
                    study_version = self.StudyVersionAccess.new_study_version(study, aggregate_hash)
                    for path, content_hash_entries in path_entries.items():
                        for content_hash, server_modified in content_hash_entries.items():
                            file = self.FileAccess.get_file_by_content_hash(content_hash)
                            self.StudyVersionFileAccess.add_new_study_version_file(study_version,
                                                                                   file,
                                                                                   path,
                                                                                   server_modified)

    def _run_study_version_validation(self):
        print("Running study version validation...")
        os.makedirs("/dashboard/validation", exist_ok=True)
        study_versions_needing_validation = self.StudyVersionAccess.get_study_versions_needing_validation()
        for study_version in study_versions_needing_validation:
            print("Validating study '{}' @ study_version_id '{}'".format(study_version.get_study().get_study_name(),
                                                                         study_version.get_id()))
            study_version_tmp_path = os.path.join(self._study_link_dir, str(study_version.get_id()))
            if os.path.exists(study_version_tmp_path):
                shutil.rmtree(study_version_tmp_path)
            for study_version_file in study_version.get_study_version_files():
                file_path = self.FileAccess.get_file_from_study_version_file(study_version_file).get_path()
                link_path = study_version_file.get_file_path()
                full_link_path = os.path.join(study_version_tmp_path, link_path)
                print("{} -> {}".format(file_path, full_link_path))
                os.makedirs(os.path.dirname(full_link_path), exist_ok=True)
                os.symlink(file_path, full_link_path)
            try:
                cmd = "python {} -s {} -n -html {}.html".format(self._validator_path,
                                                                study_version_tmp_path,
                                                                os.path.join("/dashboard/validation",
                                                                             str(study_version.get_id())))
                print("Running command '{}'".format(cmd))
                p = subprocess.check_output(cmd,
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
            print("Command exited with code '{}', marking as a {}.".format(status_code,
                                                                           'success' if success else 'failure'))
            study_version.add_study_version_validation(status_code, success, output, int(time.time()))

    def _run_study_version_import(self):
        print("Running study version import...")
        os.makedirs("/dashboard/import", exist_ok=True)
        study_versions_needing_import_test = self.StudyVersionAccess.get_study_versions_needing_import_test()
        while study_versions_needing_import_test:
            for study_version in study_versions_needing_import_test:
                print("Importing study '{}' @ study_version_id '{}'".format(study_version.get_study().get_study_name(),
                                                                            study_version.get_id()))
                study_version_tmp_path = os.path.join(self._study_link_dir, str(study_version.get_id()))
                if os.path.exists(study_version_tmp_path):
                    shutil.rmtree(study_version_tmp_path)
                for study_version_file in study_version.get_study_version_files():
                    file_path = self.FileAccess.get_file_from_study_version_file(study_version_file).get_path()
                    link_path = study_version_file.get_file_path()
                    full_link_path = os.path.join(study_version_tmp_path, link_path)
                    print("{} -> {}".format(file_path, full_link_path))
                    os.makedirs(os.path.dirname(full_link_path), exist_ok=True)
                    os.symlink(file_path, full_link_path)
                cmd = "python {} --command import-study --study_directory {}".format(
                    self._cbioportalimporter_path,
                    study_version_tmp_path)
                try:
                    study_version.set_currently_loaded(False)
                    self.StudyVersionAccess.set_all_study_versions_in_study_currently_loaded(study_version.get_study(),
                                                                                             False)
                    print("Running command '{}'".format(cmd))
                    p = subprocess.check_output(cmd,
                                                shell=True,
                                                stderr=subprocess.STDOUT)
                    status_code = 0
                    output = p.decode('utf-8')
                except subprocess.CalledProcessError as e:
                    status_code = e.returncode
                    output = e.output.decode('utf-8')
                if status_code in {0, 3}:
                    success = True
                    study_version.set_currently_loaded(True)
                else:
                    success = False
                print("Command exited with code '{}', marking as a {}.".format(status_code,
                                                                               'success' if success else 'failure'))
                with open(os.path.join("/dashboard/import", "{}.txt".format(study_version.get_id())), 'a') as wf:
                    wf.write("===================================\n")
                    wf.write(str(time.time()) + "\n")
                    wf.write(cmd + "\n")
                    wf.write(output)
                    wf.write("\n===================================\n")

                if not success:
                    try:
                        print("Removing study version as import failed")
                        meta_file = self.FileAccess.get_meta_study_version_file_from_study_version(study_version)
                        if meta_file:
                            print("Found meta study file '{}'".format(meta_file))
                            meta_file_path = os.path.join(study_version_tmp_path, meta_file.get_file_path())
                            print("Meta study file complete path '{}'".format(meta_file_path))
                            cmd = 'python  {} --command remove-study --meta_filename="{}"'.format(
                                self._cbioportalimporter_path, meta_file_path)
                            print("Running command '{}' to remove the study version".format(cmd))
                            p = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
                            print("Command output {}".format(p.decode('utf-8')))
                    except subprocess.CalledProcessError as e:
                        print("ERROR: '{}'".format(e.output))
                study_version.add_study_version_import(status_code, success, output, int(time.time()))
            study_versions_needing_import_test = self.StudyVersionAccess.get_study_versions_needing_import_test()
