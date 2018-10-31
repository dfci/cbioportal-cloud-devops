import os
import sqlite3
import time
import MySQLdb
from FileSyncSource import DropBoxSyncSource
from StudyManagementAccess import AuthorizationManager
from StudySync import StudySync
from Util import SQL_sqlite3, SQL_mysql, print
from apscheduler.schedulers.blocking import BlockingScheduler


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


def create_sync_obj(initialization: Initialization, connection: sqlite3.Connection):
    return StudySync(connection=SQL_sqlite3(connection),
                     sync_class=DropBoxSyncSource,
                     sync_class_args={'dbx_access_token': initialization.ACCESS_TOKEN,
                                      'allowed_folders': initialization.ALLOWED_FOLDERS},
                     download_dir=initialization.DOWNLOAD_DIR,
                     portal_home=initialization.PORTAL_HOME,
                     study_link_dir=initialization.STUDY_LINK_DIR,
                     schema_sql_path=initialization.SCHEMA_SQL_PATH)


def auth_sync(initialization: Initialization = Initialization()):
    print("Running auth_sync")
    try:
        with sqlite3.connect(initialization.DB_LOCATION) as sqlite_connection:
            sync_obj = create_sync_obj(initialization, sqlite_connection)
            sync_obj.perform_db_sync()
    except sqlite3.IntegrityError as e:
        print(time.time(), e)
    try:
        cbio_con = MySQLdb.connect(**initialization.CBIOPORTAL_DB_CONNECTION_INFO)
        with SQL_mysql(cbio_con) as cbioportal_sql, sqlite3.connect(initialization.DB_LOCATION) as sqlite_connection:
            auth_sync_obj = AuthorizationManager(SQL_sqlite3(sqlite_connection), cbioportal_sql)
            auth_sync_obj.run()
    except sqlite3.IntegrityError as e:
        print(time.time(), e)


def study_validation(initialization: Initialization = Initialization()):
    auth_sync(initialization)
    print("Running study_validation")
    try:
        with sqlite3.connect(initialization.DB_LOCATION) as sqlite_connection:
            sync_obj = create_sync_obj(initialization, sqlite_connection)
            sync_obj.perform_study_validation()
    except sqlite3.IntegrityError as e:
        print(time.time(), e)


def study_import(initialization: Initialization = Initialization()):
    study_validation(initialization)
    print("Running study_import")
    try:
        with sqlite3.connect(initialization.DB_LOCATION) as sqlite_connection:
            sync_obj = create_sync_obj(initialization, sqlite_connection)
            sync_obj.perform_study_import()
    except sqlite3.IntegrityError as e:
        print(time.time(), e)


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(auth_sync, trigger='cron', hour='*', minute='0,15,30,45', second='0')
    scheduler.add_job(study_validation, trigger='cron', hour='*', minute='5')
    scheduler.add_job(study_import, trigger='cron', hour='23', minute='10')
    scheduler.start()
