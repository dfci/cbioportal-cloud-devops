import os
import sqlite3
import time
from FileSyncSource import DropBoxSyncSource
from StudySync import StudySync

DOWNLOAD_DIR = os.environ['DOWNLOAD_DIR']
PORTAL_HOME = os.environ['PORTAL_HOME']
VALIDATOR_PATH = os.path.join(PORTAL_HOME, 'core/src/main/scripts/importer/validateData.py')
CBIOIMPORTER_PATH = os.path.join(PORTAL_HOME, 'core/src/main/scripts/importer/cbioportalImporter.py')
METAIMPORT_PATH = os.path.join(PORTAL_HOME, 'core/src/main/scripts/importer/metaImport.py')
DB_LOCATION = os.environ['DB_LOCATION']
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
ALLOWED_FOLDERS = set(os.environ['ALLOWED_FOLDER'].split(','))
STUDY_LINK_DIR = os.environ['STUDY_LINK_DIR']
SLEEP_DURATION = int(os.environ['SLEEP_DURATION'])
SCHEMA_SQL_PATH = os.environ['SCHEMA_SQL_PATH']

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(STUDY_LINK_DIR, exist_ok=True)

connection = sqlite3.connect(DB_LOCATION)
try:
    with connection:
        sync = StudySync(connection=connection,
                         sync_class=DropBoxSyncSource,
                         sync_class_args={'dbx_access_token': ACCESS_TOKEN,
                                          'allowed_folders': ALLOWED_FOLDERS},
                         download_dir=DOWNLOAD_DIR,
                         portal_home=PORTAL_HOME,
                         study_link_dir=STUDY_LINK_DIR,
                         schema_sql_path=SCHEMA_SQL_PATH)
        sync.run()
except sqlite3.IntegrityError as e:
    print(time.time(), e)

connection.close()
