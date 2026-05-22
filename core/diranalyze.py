import os
from core.scanresult import ScanResult
from core.signals import Signal


class DirectoryAnalyzer:
    def __init__(self):
        self.path_scanned = Signal()

    def analyze(self, path, file_filter=None):
        root_result = ScanResult(name=os.path.basename(path), path=path)
        self._walk_recursive(path, root_result, file_filter)
        return root_result

    def _walk_recursive(self, current_path, current_result, file_filter):
        try:
            self.path_scanned.emit(current_path)

            with os.scandir(current_path) as it:
                for entry in it:
                    if file_filter and file_filter.should_exclude(entry.path):
                        continue

                    if entry.is_symlink(): continue

                    if entry.is_file():
                        current_result.size += entry.stat().st_size
                        current_result.files += 1
                    elif entry.is_dir():
                        sub_folder_result = ScanResult(name=entry.name, path=entry.path)
                        current_result.add_child(sub_folder_result)
                        self._walk_recursive(entry.path, sub_folder_result, file_filter)
                        current_result.size += sub_folder_result.size
                        current_result.files += sub_folder_result.files
        except (PermissionError, OSError):
            current_result.skipped += 1