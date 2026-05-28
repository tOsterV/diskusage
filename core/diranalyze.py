import os
import sys
from core.scanresult import ScanResult
from core.signals import Signal

if sys.platform != "win32":
    import pwd
else:
    pwd = None


class DirectoryAnalyzer:
    def __init__(self):
        self.path_scanned = Signal()

    def _get_owner(self, stat_res):
        """Безопасное получение владельца (ДОП)"""
        if sys.platform == "win32":
            return os.environ.get("USERNAME", "Система")
        else:
            try:
                return pwd.getpwuid(stat_res.st_uid).pw_name
            except Exception:
                return f"UID-{stat_res.st_uid}"

    def analyze(self, path, file_filter=None):
        root_result = ScanResult(name=os.path.basename(path), path=path)
        root_result.extension = "Папка"
        try:
            stat_res = os.stat(path)
            root_result.mtime = stat_res.st_mtime
            root_result.owner = self._get_owner(stat_res)
        except Exception:
            pass

        self._walk_recursive(path, root_result, file_filter)
        return root_result

    def _walk_recursive(self, current_path, current_result, file_filter):
        try:
            self.path_scanned.emit(current_path)

            with os.scandir(current_path) as it:
                for entry in it:
                    if file_filter and file_filter.should_exclude(entry.path):
                        continue

                    if entry.is_symlink():
                        continue

                    try:
                        stat_res = entry.stat(follow_symlinks=False)
                        mtime = stat_res.st_mtime
                        owner = self._get_owner(stat_res)
                    except (PermissionError, OSError):
                        continue

                    if entry.is_file():
                        file_node = ScanResult(name=entry.name, path=entry.path, parent=current_result)
                        file_node.size = stat_res.st_size
                        file_node.files = 1
                        file_node.mtime = mtime
                        file_node.owner = owner

                        current_result.children.append(file_node)
                        current_result.size += file_node.size
                        current_result.files += 1


                    elif entry.is_dir():
                        sub_folder_result = ScanResult(name=entry.name, path=entry.path)
                        sub_folder_result.extension = "Папка"
                        sub_folder_result.mtime = mtime
                        sub_folder_result.owner = owner
                        current_result.add_child(sub_folder_result)
                        self._walk_recursive(entry.path, sub_folder_result, file_filter)
                        current_result.size += sub_folder_result.size
                        current_result.files += sub_folder_result.files
        except (PermissionError, OSError):
            current_result.skipped += 1
