import os
import sqlite3
import time
import MySQLdb
from FileSyncSource import DropBoxSyncSource
from StudyManagementAccess import AuthorizationManager
from StudySync import StudySync
from Util import SQL

DOWNLOAD_DIR = os.environ['DOWNLOAD_DIR']
PORTAL_HOME = os.environ['PORTAL_HOME']
VALIDATOR_PATH = os.path.join(PORTAL_HOME, 'core/src/main/scripts/importer/validateData.py')
CBIOIMPORTER_PATH = os.path.join(PORTAL_HOME, 'core/src/main/scripts/importer/cbioportalImporter.py')
METAIMPORT_PATH = os.path.join(PORTAL_HOME, 'core/src/main/scripts/importer/metaImport.py')
DB_LOCATION = os.environ['DB_LOCATION']
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
ALLOWED_FOLDERS = set(os.environ['ALLOWED_FOLDER'].split(','))
STUDY_LINK_DIR = os.environ['STUDY_LINK_DIR']
SCHEMA_SQL_PATH = os.environ['SCHEMA_SQL_PATH']
CBIOPORTAL_DB_CONNECTION_INFO = {
    "host": os.environ['DB_HOST'],
    "db": os.environ['DB_NAME'],
    "user": os.environ["DB_USER"],
    "passwd": os.environ["DB_PASSWORD"]
}

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(STUDY_LINK_DIR, exist_ok=True)

connection = sqlite3.connect(DB_LOCATION)
cbio_con = MySQLdb.connect(**CBIOPORTAL_DB_CONNECTION_INFO)
try:
    with connection:
        sync = StudySync(connection=SQL(connection),
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

try:
    with cbio_con, connection:
        auth_sync = AuthorizationManager(SQL(connection), SQL(cbio_con))
        auth_sync.run()
except sqlite3.IntegrityError as e:
    print(time.time(), e)
connection.close()
