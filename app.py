import sys
import re
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTreeView, QVBoxLayout, QHBoxLayout,
                             QWidget, QProgressBar, QPushButton, QFileDialog, QTabWidget,
                             QLabel, QLineEdit, QSplitter, QMessageBox, QSpinBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QSortFilterProxyModel, QModelIndex
from core.diranalyze import DirectoryAnalyzer
from core.treemodel import ScanTreeModel
from core.sysplat import SystemInfoProvider
from core.filters import RegexFilter
from core.analytics import DataAggregator
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
        self.setWindowTitle("Disk Usage Analyzer (WinDirStat Analytics Edition)")
        self.setGeometry(50, 50, 1150, 750)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)

        self.label_path = QLabel("Выберите папку для начала сканирования")
        self.input_exclude = QLineEdit()
        self.input_exclude.setPlaceholderText(r"Исключить файлы по regex (например: \.tmp$|node_modules)")
        self.btn = QPushButton("Выбрать папку и начать")
        self.progress_bar = QProgressBar()

        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Макс. уровень вложенности в дереве:"))
        self.level_spin = QSpinBox()
        self.level_spin.setRange(0, 200)
        self.level_spin.setValue(100)
        self.level_spin.valueChanged.connect(self.update_level_filter)
        level_layout.addWidget(self.level_spin)

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.tree = QTreeView()
        self.tree.setSortingEnabled(True)

        self.treemap = TreeMapWidget()
        self.treemap.clicked_node.connect(self.on_treemap_clicked)

        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.treemap)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 1)

        self.stats_label = QLabel("Статистика диска: ожидание...")
        self.stats_label.setWordWrap(True)
        left_layout.addWidget(self.label_path)
        left_layout.addWidget(QLabel("Фильтр исключений (Regex):"))
        left_layout.addWidget(self.input_exclude)
        left_layout.addWidget(self.btn)
        left_layout.addWidget(self.progress_bar)
        left_layout.addLayout(level_layout)
        left_layout.addWidget(self.splitter)
        left_layout.addWidget(self.stats_label)

        self.tabs = QTabWidget()
        self.tabs.setMinimumWidth(420)

        self.table_ext = QTableWidget()
        self.table_owner = QTableWidget()
        self.table_time = QTableWidget()

        self._init_analytics_table(self.table_ext, ["Расширение", "Размер", "Кол-во"])
        self._init_analytics_table(self.table_owner, ["Владелец", "Размер", "Объектов"])
        self._init_analytics_table(self.table_time, ["Период изм.", "Размер", "Кол-во"])

        self.tabs.addTab(self.table_ext, "По расширениям")
        self.tabs.addTab(self.table_owner, "По владельцам")
        self.tabs.addTab(self.table_time, "По времени")

        main_layout.addWidget(left_container, stretch=2)
        main_layout.addWidget(self.tabs, stretch=1)

        self.btn.clicked.connect(self.start_scan)

    def _init_analytics_table(self, table, headers):
        """Красивая табличная сетка"""
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

    def start_scan(self):
        pattern = self.input_exclude.text()
        if pattern:
            try:
                re.compile(pattern)
            except re.error:
                QMessageBox.critical(self, "Ошибка", "Некорректное регулярное выражение!")
                return

        dir_path = QFileDialog.getExistingDirectory(self, "Выберите папку для сканирования")
        if not dir_path:
            return

        self.label_path.setText(f"Сканирую: {dir_path}")
        self.progress_bar.setRange(0, 0)
        self.btn.setEnabled(False)

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
        disk = sys_info.get_disk_stat(self.thread.path)
        total_gb = round(disk.total / (1024 ** 3), 2)
        used_gb = round(disk.used / (1024 ** 3), 2)
        free_gb = round(disk.free / (1024 ** 3), 2)

        disk_name = self.thread.path
        stats_text = (
            f"DISK USAGE REPORT:\n\n"
            f"--Info about disk [{disk_name}] --\n"
            f"Общий объем диска: {total_gb} GB\n"
            f"Занято на диске: {used_gb} GB\n"
            f"Свободно на диске: {free_gb} GB"
        )

        self.stats_label.setText(stats_text)
        self.model = ScanTreeModel(result)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortRole(Qt.ItemDataRole.UserRole)

        self.tree.setModel(self.proxy_model)
        self.tree.sortByColumn(1, Qt.SortOrder.DescendingOrder)
        self.treemap.set_data(result)

        self.calculate_analytics(result)
        self.label_path.setText(f"Анализ завершен для: {self.thread.path}")

    def _fill_table_data(self, table, data_dict):
        """Заполнение строк с умной числовой сортировкой ячеек"""
        table.setSortingEnabled(False)
        table.setRowCount(len(data_dict))
        formatter = Formatter()

        for row, (key, (size, cnt)) in enumerate(data_dict.items()):
            item_key = QTableWidgetItem(str(key))

            item_size = QTableWidgetItem(formatter.format_size(size))
            item_size.setData(Qt.ItemDataRole.UserRole, size)
            item_size.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            item_cnt = QTableWidgetItem(f"{cnt} ф.")
            item_cnt.setData(Qt.ItemDataRole.UserRole, cnt)
            item_cnt.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            table.setItem(row, 0, item_key)
            table.setItem(row, 1, item_size)
            table.setItem(row, 2, item_cnt)

        table.setSortingEnabled(True)
        table.sortByColumn(1, Qt.SortOrder.DescendingOrder)

    def calculate_analytics(self, root_node):
        self._fill_table_data(self.table_ext, DataAggregator.group_by_extension(root_node))
        self._fill_table_data(self.table_owner, DataAggregator.group_by_owner(root_node))
        self._fill_table_data(self.table_time, DataAggregator.group_by_time(root_node))

    def update_level_filter(self):
        """Интерактивное скрытие строк глубже заданного уровня (ДОП)"""
        if hasattr(self, 'proxy_model'):
            max_level = self.level_spin.value()
            self._apply_level_visibility(QModelIndex(), max_level)

    def _apply_level_visibility(self, parent_idx, max_level):
        rows = self.proxy_model.rowCount(parent_idx)
        for r in range(rows):
            child_idx = self.proxy_model.index(r, 0, parent_idx)
            source_idx = self.proxy_model.mapToSource(child_idx)
            node = source_idx.internalPointer()

            if node:
                self.tree.setRowHidden(r, parent_idx, node.level > max_level)
                if node.children:
                    self._apply_level_visibility(child_idx, max_level)

    def on_treemap_clicked(self, node):
        formatter = Formatter()
        self.stats_label.setText(f"Выбран объект: {node.path} ({formatter.format_size(node.size)}) | Файлов: {node.files}")

        if hasattr(self, 'proxy_model'):
            source_index = self._get_index_for_node(node)
            if source_index.isValid():
                proxy_index = self.proxy_model.mapFromSource(source_index)
                if proxy_index.isValid():
                    self.tree.setCurrentIndex(proxy_index)
                    self.tree.scrollTo(proxy_index, QTreeView.ScrollHint.PositionAtCenter)

    def _get_index_for_node(self, node):
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