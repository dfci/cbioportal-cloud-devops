import shutil
import subprocess
import time
import os
from .classes import *

DOWNLOAD_DIR = os.environ['DOWNLOAD_DIR']
PORTAL_HOME = os.environ['PORTAL_HOME']
DB_LOCATION = 'test2.db'
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
ALLOWED_FOLDERS = set(os.environ['ALLOWED_FOLDER'].split(','))
STUDY_LINK_DIR = "/study_link_dir"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(STUDY_LINK_DIR, exist_ok=True)

DB_CONNECTION = sqlite3.connect(DB_LOCATION)

connection = sqlite3.connect(DB_LOCATION)
sql = SQL(connection)
dbx = DropBoxSync(ACCESS_TOKEN, sql)
syncer = StudySync(sql, dbx, DOWNLOAD_DIR)
syncer.run()
validator_path = os.path.join(PORTAL_HOME, 'core/src/main/scripts/importer/validateData.py')
study_versions_needing_validation = syncer.StudyVersionRepo.get_study_versions_needing_validation()
for study_version in study_versions_needing_validation:
    study_version_tmp_path = os.path.join(STUDY_LINK_DIR, str(study_version.get_id()))
    if os.path.exists(study_version_tmp_path):
        shutil.rmtree(study_version_tmp_path)
    for study_version_file in study_version.get_study_version_files():
        file_path = syncer.FileRepo.get_file_from_study_version_file(study_version_file).get_path()
        link_path = study_version_file.get_file_path()
        full_link_path = os.path.join(study_version_tmp_path, link_path)
        os.makedirs(os.path.dirname(full_link_path), exist_ok=True)
        os.symlink(file_path, full_link_path)
    try:
        p = subprocess.check_output("python {} -s {} -n".format(validator_path, study_version_tmp_path), shell=True,
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
connection.close()
