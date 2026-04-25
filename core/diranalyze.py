from scanresult import ScanResult
import os
class DirectoryAnalyzer:
    def analyze(self, path):
        result = ScanResult()
        self._walk_recursive(path, result)
        return result

    def _walk_recursive(self, current_path, result):
        try:
            with os.scandir(current_path) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_file():
                            result.size += entry.stat().st_size
                            result.files += 1
                        elif entry.is_dir():
                            self._walk_recursive(entry.path, result)
                    except (PermissionError, OSError):
                        result.skipped += 1
        except (PermissionError, OSError):
            result.skipped += 1
