import sys
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTreeView, QVBoxLayout,
                             QWidget, QProgressBar, QPushButton, QFileDialog,
                             QLabel, QLineEdit, QSplitter, QMessageBox)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSortFilterProxyModel, \
    QModelIndex
from core.diranalyze import DirectoryAnalyzer
from core.treemodel import ScanTreeModel
from core.sysplat import SystemInfoProvider
from core.filters import RegexFilter
from utils.formatter import Formatter
from gui.treemap import TreeMapWidget


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
        self.setWindowTitle("Disk Usage Analyzer (WinDirStat Edition)")
        self.setGeometry(100, 100, 900, 700)

        self.layout = QVBoxLayout()
        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.label_path = QLabel("Выберите папку для начала сканирования")
        self.input_exclude = QLineEdit()
        self.input_exclude.setPlaceholderText(
            "Исключить файлы по regex (например: \.tmp$|node_modules)")
        self.btn = QPushButton("Выбрать папку и начать")
        self.progress_bar = QProgressBar()
        self.stats_label = QLabel("Статистика диска: ожидание...")

        self.splitter = QSplitter(Qt.Orientation.Vertical)

        self.tree = QTreeView()
        self.tree.setSortingEnabled(True)

        self.treemap = TreeMapWidget()
        self.treemap.clicked_node.connect(self.on_treemap_clicked)

        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.treemap)

        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)

        self.layout.addWidget(self.label_path)
        self.layout.addWidget(QLabel("Фильтр исключений (Regex):"))
        self.layout.addWidget(self.input_exclude)
        self.layout.addWidget(self.btn)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.splitter)
        self.layout.addWidget(self.stats_label)

        self.btn.clicked.connect(self.start_scan)

    def start_scan(self):
        pattern = self.input_exclude.text()

        if pattern:
            try:
                re.compile(pattern)
            except re.error:
                QMessageBox.critical(self, "Ошибка",
                                     "Некорректное регулярное выражение!\nПроверьте синтаксис.")
                return

        dir_path = QFileDialog.getExistingDirectory(self,
                                                    "Выберите папку для сканирования")
        if not dir_path:
            return

        self.label_path.setText(f"Сканирую: {dir_path}")
        self.progress_bar.setRange(0, 0)
        self.btn.setEnabled(False)

        self.thread = ScanThread(dir_path, pattern)
        self.thread.progress.connect(
            lambda p: self.progress_bar.setFormat(f"Обработка: {p}"))
        self.thread.finished.connect(self.on_finished)
        self.thread.start()

    def on_finished(self, result):
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("Готово!")
        self.btn.setEnabled(True)

        # Считаем и выводим общую статистику диска
        sys_info = SystemInfoProvider()
        formatter = Formatter()
        disk = sys_info.get_disk_stat(self.thread.path)

        stats_text = (f"Всего: {formatter.format_size(disk.total)} | "
                      f"Занято: {formatter.format_size(disk.used)} | "
                      f"Свободно: {formatter.format_size(disk.free)}")
        self.stats_label.setText(stats_text)

        self.model = ScanTreeModel(result)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortRole(Qt.ItemDataRole.UserRole)

        self.tree.setModel(self.proxy_model)
        self.tree.sortByColumn(1, Qt.SortOrder.DescendingOrder)

        self.treemap.set_data(result)
        self.label_path.setText(f"Анализ завершен для: {self.thread.path}")

    def on_treemap_clicked(self, node):
        """Слот обработки клика по прямоугольнику в TreeMap"""
        formatter = Formatter()
        self.stats_label.setText(
            f"Выбран объект: {node.path} ({formatter.format_size(node.size)})")

        if hasattr(self, 'proxy_model'):
            source_index = self._get_index_for_node(node)
            if source_index.isValid():
                proxy_index = self.proxy_model.mapFromSource(source_index)
                if proxy_index.isValid():
                    self.tree.setCurrentIndex(proxy_index)
                    self.tree.scrollTo(proxy_index,
                                       QTreeView.ScrollHint.PositionAtCenter)

    def _get_index_for_node(self, node):
        """Быстрое получение QModelIndex без рекурсивного перебора всего дерева"""
        if node == self.model.root_item or node.parent is None:
            return QModelIndex()

        parent_node = node.parent
        try:
            row = parent_node.children.index(node)
        except ValueError:
            return QModelIndex()

        parent_index = self._get_index_for_node(parent_node)
        return self.model.index(row, 0, parent_index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiskUsageGUI()
    window.show()
    sys.exit(app.exec())