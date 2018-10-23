from collections import defaultdict
import dropbox


class FileSyncSource(object):
    def __init__(self):
        super().__init__()
        self.all_entries = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        self.content_hash_to_remote_path = dict()

    def run(self) -> None:
        pass

    def do_download(self, local_path: str, remote_path: str) -> None:
        pass


class DropBoxSyncSource(FileSyncSource):
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
