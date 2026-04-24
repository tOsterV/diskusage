#для каждой вложенной папки в диске, прогресс бар по работе, в несколько файлов, убрать GetDiskFreeSpaceExW, расширение, время, вложенность указать для работы кода

#ДОП1!!!: GUI подобный windirstat (4 balla)
#ДОП2!!!: поддержка exclude patterns (ввод регулярки которая исключает что-то из подсчета, за вменяемое время)




import os
import sys
import platform
from scanresult import ScanResult
from diskstat import DiskStats



class Formatter:
    @staticmethod
    def format_size(bytes_size):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_size < 1024:
                return f"{bytes_size:<.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:,.2f} PB"

    @staticmethod
    def format_number(number):
        return f"{number:,}".replace(",", " ")


class SystemInfoProvider:
    def get_disk_stat(self, path):
        current_os = platform.system()
        if current_os == "Windows":
            return self._get_windows_stats(path)
        else:
            return self._get_unix_stats(path)

    def _get_unix_stats(self, path):
        st = os.statvfs(path)
        total = st.f_frsize * st.f_blocks
        free = st.f_frsize * st.f_bavail
        return DiskStats(total, free)

    def _get_windows_stats(self, path):
        import ctypes
        free_bytes = ctypes.c_ulonglong(0)
        total_bytes = ctypes.c_ulonglong(0)
        total_free_bytes = ctypes.c_ulonglong(0)

        full_path = os.path.abspath(path)

        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            ctypes.c_wchar_p(full_path),
            ctypes.pointer(free_bytes),
            ctypes.pointer(total_bytes),
            ctypes.pointer(total_free_bytes)
        )
        return DiskStats(total_bytes.value, total_free_bytes.value)


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


# main app

class DiskUsageApp:
    def __init__(self):
        self.analyzer = DirectoryAnalyzer()
        self.formatter = Formatter()
        self.sys_info = SystemInfoProvider()

    def run(self) -> object:
        raw_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
        target_path = os.path.abspath(raw_path)
        if not os.path.exists(target_path):
            print(f'Error: path {target_path} doesnt exist')
            return
        print(f'Analyze {target_path}...')

        scan = self.analyzer.analyze(target_path)
        disk = self.sys_info.get_disk_stat(target_path)

        self.print_report(target_path, scan, disk)

    def print_report(self, path, scan, disk):
        f = self.formatter
        print(f"\n DISK USAGE REPORT:")
        print(f"-- Info about disk for path [{path}] --")
        print(f"Общий объем диска: {f.format_size(disk.total)}")
        print(f"Занято на диске: {f.format_size(disk.used)}")
        print(f"Свободно на диске: {f.format_size(disk.free)}")
        print(f"Найдено файлов:  {f.format_number(scan.files)}")
        print(f"Размер папки:    {f.format_size(scan.size)}")
        if scan.skipped > 0:
            print(f"Пропущено(нет доступа): {scan.skipped}")


if __name__ == "__main__":
    app = DiskUsageApp()
    app.run()
