#ДОП1!!!: GUI подобный windirstat (4 balla) (сортировка красивые квадратики блять че нахуй)
#ДОП2!!!: поддержка exclude patterns (ввод регулярки которая исключает что-то из подсчета, за вменяемое время)


import sys
import os
import time
from utils.formatter import Formatter
from core.sysplat import SystemInfoProvider
from core.diranalyze import DirectoryAnalyzer
from core.filters import RegexFilter
from gui import DiskUsageGUI
from PyQt6.QtWidgets import QApplication

def run_gui():
    app = QApplication(sys.argv)
    window = DiskUsageGUI()
    window.show()
    sys.exit(app.exec())
class DiskUsageApp:
    def __init__(self):
        self.analyzer = DirectoryAnalyzer()
        self.formatter = Formatter()
        self.sys_info = SystemInfoProvider()

    def run(self):
        raw_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
        target_path = os.path.abspath(raw_path)

        exclude_pattern = input("Введите регулярное выражение для исключения (или Enter для пропуска): ")
        file_filter = RegexFilter(exclude_pattern) if exclude_pattern else None

        print(f'Analyze {target_path}...')
        self.analyzer.path_scanned.connect(self.show_progress)

        start_time = time.time()
        scan = self.analyzer.analyze(target_path, file_filter=file_filter)

        end_time = time.time()
        disk = self.sys_info.get_disk_stat(target_path)

        self.print_report(target_path, scan, disk, end_time - start_time)

    def show_progress(self, path):
        print(f"Обработка: {os.path.basename(path)}", end='\r')

    def print_report(self, path, scan, disk, duration):
        f = self.formatter
        print(f"\n\n--- ОТЧЕТ ЗАВЕРШЕН ---")
        print(f"Время выполнения: {duration:.2f} сек.")
        print(f"Общий объем: {f.format_size(disk.total)}")
        print(f"Занято:      {f.format_size(disk.used)}")
        print(f"Найдено:     {f.format_number(scan.files)} файлов")
        print(f"Размер папки: {f.format_size(scan.size)}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        run_gui()
    else:
        app = DiskUsageApp()
        app.run()
