#для каждой вложенной папки в диске, прогресс бар по работе, убрать GetDiskFreeSpaceExW, расширение, время, вложенность указать для работы кода

#ДОП1!!!: GUI подобный windirstat (4 balla)
#ДОП2!!!: поддержка exclude patterns (ввод регулярки которая исключает что-то из подсчета, за вменяемое время)

import sys
import os
from utils.formatter import Formatter
from core.sysplat import SystemInfoProvider
from core.diranalyze import DirectoryAnalyzer

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
