import os
import sqlite3
import time
import MySQLdb
from FileSyncSource import DropBoxSyncSource
from StudyManagementAccess import AuthorizationManager
from StudySync import StudySync
from Util import SQL_sqlite3, SQL_mysql, print
from apscheduler.schedulers.background import BackgroundScheduler


class Initialization:
    def __init__(self):
        self.DOWNLOAD_DIR = os.environ['DOWNLOAD_DIR']
        self.PORTAL_HOME = os.environ['PORTAL_HOME']
        self.VALIDATOR_PATH = os.path.join(self.PORTAL_HOME, 'core/src/main/scripts/importer/validateData.py')
        self.CBIOIMPORTER_PATH = os.path.join(self.PORTAL_HOME, 'core/src/main/scripts/importer/cbioportalImporter.py')
        self.METAIMPORT_PATH = os.path.join(self.PORTAL_HOME, 'core/src/main/scripts/importer/metaImport.py')
        self.DB_LOCATION = os.environ['DB_LOCATION']
        self.ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
        self.ALLOWED_FOLDERS = set(os.environ['ALLOWED_FOLDER'].split(','))
        self.STUDY_LINK_DIR = os.environ['STUDY_LINK_DIR']
        self.SCHEMA_SQL_PATH = os.environ['SCHEMA_SQL_PATH']
        self.CBIOPORTAL_DB_CONNECTION_INFO = {
            "host": os.environ['DB_HOST'],
            "db": os.environ['DB_NAME'],
            "user": os.environ["DB_USER"],
            "passwd": os.environ["DB_PASSWORD"]
        }

        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)
        os.makedirs(self.STUDY_LINK_DIR, exist_ok=True)

        self.sqlite_connection = sqlite3.connect(self.DB_LOCATION)
        self.cbio_con = MySQLdb.connect(**self.CBIOPORTAL_DB_CONNECTION_INFO)


def study_sync():
    print("Running study_sync")
    initialization = Initialization()
    try:
        with initialization.sqlite_connection:
            sync = StudySync(connection=SQL_sqlite3(initialization.sqlite_connection),
                             sync_class=DropBoxSyncSource,
                             sync_class_args={'dbx_access_token': initialization.ACCESS_TOKEN,
                                              'allowed_folders': initialization.ALLOWED_FOLDERS},
                             download_dir=initialization.DOWNLOAD_DIR,
                             portal_home=initialization.PORTAL_HOME,
                             study_link_dir=initialization.STUDY_LINK_DIR,
                             schema_sql_path=initialization.SCHEMA_SQL_PATH)
            sync.run()
    except sqlite3.IntegrityError as e:
        print(time.time(), e)


def auth_sync():
    print("Running auth_sync")
    initialization = Initialization()
    try:
        with SQL_mysql(initialization.cbio_con) as cbioportal_sql, initialization.sqlite_connection:
            auth_sync = AuthorizationManager(SQL_sqlite3(initialization.sqlite_connection), cbioportal_sql)
            auth_sync.run()
    except sqlite3.IntegrityError as e:
        print(time.time(), e)
    initialization.sqlite_connection.close()


if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(auth_sync, trigger='cron', hour='*', minute='0', second='0')
    scheduler.add_job(study_sync, trigger='cron', hour='23', minute='30')
    scheduler.start()
    while True:
        time.sleep(10)
