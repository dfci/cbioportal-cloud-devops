from time import sleep
from .classes import *

DOWNLOAD_DIR = os.environ['DOWNLOAD_DIR']
PORTAL_HOME = os.environ['PORTAL_HOME']
VALIDATOR_PATH = os.path.join(PORTAL_HOME, 'core/src/main/scripts/importer/validateData.py')
DB_LOCATION = os.environ['DB_LOCATION']
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
ALLOWED_FOLDERS = set(os.environ['ALLOWED_FOLDER'].split(','))
STUDY_LINK_DIR = os.environ['STUDY_LINK_DIR']
SLEEP_DURATION = int(os.environ['SLEEP_DURATION'])

while True:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(STUDY_LINK_DIR, exist_ok=True)

    connection = sqlite3.connect(DB_LOCATION)
    sync = StudySync(connection=connection,
                     sync_class=DropBoxSync,
                     sync_class_args={'dbx_access_token': ACCESS_TOKEN,
                                      'allowed_folders': ALLOWED_FOLDERS},
                     download_dir=DOWNLOAD_DIR,
                     validator_path=VALIDATOR_PATH,
                     study_link_dir=STUDY_LINK_DIR)
    sync.run()
    connection.close()
    sleep(SLEEP_DURATION)
