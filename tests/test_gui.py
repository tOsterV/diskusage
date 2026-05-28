import os
import sys

# Динамически находим путь к корню (папке ddd) и добавляем в sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from PyQt6.QtCore import Qt
from app import DiskUsageGUI
from core.scanresult import ScanResult


@pytest.fixture
def app_instance(qtbot):
    """Фикстура для инициализации и отслеживания окна GUI"""
    gui_window = DiskUsageGUI()
    qtbot.addWidget(gui_window)
    return gui_window


def test_gui_initial_state(app_instance):
    """Проверяем базовое состояние элементов при запуске приложения"""
    assert app_instance.windowTitle() == "Disk Usage Analyzer (WinDirStat Analytics Edition)"
    assert app_instance.btn.text() == "Выбрать папку и начать"
    assert app_instance.table_ext.columnCount() == 3
    assert app_instance.table_owner.columnCount() == 3
    assert app_instance.table_time.columnCount() == 3


def test_table_population(app_instance):
    """Проверяем, корректно ли данные ложатся в ячейки QTableWidget"""
    root = ScanResult("root", "/dummy")
    root.extension = "Папка"  # Явно помечаем корень как Папку, чтобы он не попадал в аналитику расширений файлов

    f1 = ScanResult("test.py", "/dummy/test.py")
    f1.size = 1024
    f1.files = 1
    root.add_child(f1)

    app_instance.calculate_analytics(root)

    # Теперь в таблице будет ровно 1 строка с расширением ".py"
    assert app_instance.table_ext.rowCount() == 1
    assert app_instance.table_ext.item(0, 0).text() == ".py"
    assert "1.00 KB" in app_instance.table_ext.item(0, 1).text()
    assert app_instance.table_ext.item(0, 1).data(Qt.ItemDataRole.UserRole) == 1024
    assert app_instance.table_ext.item(0, 2).text() == "1 ф."


def test_level_filter_logic(app_instance):
    """Проверяем, что изменение спинбокса вложенности не роняет систему"""
    app_instance.level_spin.setValue(2)
    app_instance.update_level_filter()
    assert app_instance.level_spin.value() == 2