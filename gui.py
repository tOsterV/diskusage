import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTreeView, QVBoxLayout,
                             QWidget, QProgressBar, QPushButton, QFileDialog, QLabel, QLineEdit)
from PyQt6.QtCore import QThread, pyqtSignal, QDir
from core.diranalyze import DirectoryAnalyzer
from core.treemodel import ScanTreeModel
from core.sysplat import SystemInfoProvider
from core.filters import RegexFilter
from utils.formatter import Formatter


class ScanThread(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)

    def __init__(self, path, pattern=""):
        super().__init__()
        self.path = path
        self.pattern = pattern

    def run(self):
        analyzer = DirectoryAnalyzer()
        file_filter = RegexFilter(self.pattern) if self.pattern else None
        analyzer.path_scanned.connect(lambda p: self.progress.emit(p))
        result = analyzer.analyze(self.path, file_filter=file_filter)
        self.finished.emit(result)


class DiskUsageGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Disk Usage Analyzer")
        self.setGeometry(100, 100, 800, 650)

        self.layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.label_path = QLabel("Выберите папку для начала сканирования")
        self.input_exclude = QLineEdit()
        self.input_exclude.setPlaceholderText("Исключить файлы по regex (например: .tmp|node_modules)")
        self.btn = QPushButton("Выбрать папку и начать")
        self.progress_bar = QProgressBar()
        self.tree = QTreeView()
        self.stats_label = QLabel("Статистика диска: ожидание...")

        self.layout.addWidget(self.label_path)
        self.layout.addWidget(QLabel("Фильтр исключений:"))
        self.layout.addWidget(self.input_exclude)
        self.layout.addWidget(self.btn)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.tree)
        self.layout.addWidget(self.stats_label)

        self.btn.clicked.connect(self.start_scan)

    def start_scan(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Выберите папку для сканирования")
        if not dir_path:
            return

        self.label_path.setText(f"Сканирую: {dir_path}")
        self.progress_bar.setRange(0, 0)
        self.btn.setEnabled(False)

        pattern = self.input_exclude.text()

        self.thread = ScanThread(dir_path, pattern)
        self.thread.progress.connect(lambda p: self.progress_bar.setFormat(f"Обработка: {p}"))
        self.thread.finished.connect(self.on_finished)
        self.thread.start()

    def on_finished(self, result):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Готово!")
        self.btn.setEnabled(True)

        sys_info = SystemInfoProvider()
        formatter = Formatter()
        disk = sys_info.get_disk_stat(self.thread.path)

        stats_text = (f"Всего: {formatter.format_size(disk.total)} | "
                      f"Занято: {formatter.format_size(disk.used)} | "
                      f"Свободно: {formatter.format_size(disk.free)}")
        self.stats_label.setText(stats_text)

        self.model = ScanTreeModel(result)
        self.tree.setModel(self.model)
        self.label_path.setText(f"Анализ завершен для: {self.thread.path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiskUsageGUI()
    window.show()
    sys.exit(app.exec())