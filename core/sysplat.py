import shutil
from core.diskstat import DiskStats

class SystemInfoProvider:
    def get_disk_stat(self, path):
        usage = shutil.disk_usage(path)
        return DiskStats(usage.total, usage.free)