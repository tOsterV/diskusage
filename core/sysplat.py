import platform
import os
from diskstat import DiskStats
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
