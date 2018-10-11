from collections import defaultdict


class FileSyncSource(object):
    def __init__(self):
        super().__init__()
        self.all_entries = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        self.content_hash_to_remote_path = dict()

    def run(self) -> None:
        pass

    def do_download(self, local_path: str, remote_path: str) -> None:
        pass
