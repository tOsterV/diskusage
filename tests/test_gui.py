import pytest
from PyQt6.QtCore import Qt
from app import DiskUsageGUI
from core.scanresult import ScanResult


@pytest.fixture
def app(qtbot):
    """Фикстура для инициализации и отслеживания окна GUI"""
    gui = DiskUsageGUI()
    qtbot.addWidget(gui)
    return gui


def test_gui_initial_state(app):
    """Проверяем базовое состояние элементов при запуске приложения"""
    assert app.windowTitle() == "Disk Usage Analyzer (WinDirStat Analytics Edition)"
    assert app.btn.text() == "Выбрать папку и начать"
    assert app.table_ext.columnCount() == 3
    assert app.table_owner.columnCount() == 3
    assert app.table_time.columnCount() == 3


def test_table_population(app):
    """Проверяем, корректно ли данные ложатся в ячейки QTableWidget"""
    root = ScanResult("root", "/dummy")
    f1 = ScanResult("test.py", "/dummy/test.py")
    f1.size = 1024
    f1.files = 1
    root.add_child(f1)

    app.calculate_analytics(root)

    assert app.table_ext.rowCount() == 1

    assert app.table_ext.item(0, 0).text() == ".py"

    assert "1.00 KB" in app.table_ext.item(0, 1).text()
    assert app.table_ext.item(0, 1).data(Qt.ItemDataRole.UserRole) == 1024

    assert app.table_ext.item(0, 2).text() == "1 ф."
    assert app.table_ext.item(0, 2).data(Qt.ItemDataRole.UserRole) == 1


def test_level_filter_logic(app):
    """Проверяем, что изменение спинбокса вложенности не роняет систему"""
    app.level_spin.setValue(2)

    app.update_level_filter()
    assert app.level_spin.value() == 2