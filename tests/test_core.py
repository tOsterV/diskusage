import os
import sys

# Динамически находим путь к корню (папке ddd) и добавляем в sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import time
import pytest
from core.scanresult import ScanResult
from core.analytics import DataAggregator
from core.diranalyze import DirectoryAnalyzer


def test_scan_result_extension_handling():
    """Проверка, что ScanResult правильно определяет расширения"""
    file_node = ScanResult(name="script.py", path="/dummy/script.py")
    assert file_node.extension == ".py"

    folder_node = ScanResult(name="src", path="/dummy/src")
    assert folder_node.extension == "без расширения"

    folder_node.extension = "Папка"
    assert folder_node.extension == "Папка"


def test_directory_analyzer_and_aggregations(tmp_path):
    """Интеграционный тест: создание структуры на диске и проверка агрегации"""
    dir_a = tmp_path / "dir_a"
    dir_a.mkdir()

    file1 = tmp_path / "file1.txt"
    file1.write_text("12345")

    file2 = dir_a / "file2.txt"
    file2.write_text("abc")

    file3 = dir_a / "image.png"
    file3.write_text("png_data_here")

    analyzer = DirectoryAnalyzer()
    root_node = analyzer.analyze(str(tmp_path))

    assert root_node.size == 5 + 3 + 13
    assert root_node.files == 3

    ext_data = DataAggregator.group_by_extension(root_node)
    assert ".txt" in ext_data
    assert ".png" in ext_data
    assert ext_data[".txt"][0] == 8
    assert ext_data[".txt"][1] == 2
    assert ext_data[".png"][0] == 13

    time_data = DataAggregator.group_by_time(root_node)
    assert time_data["Последние 24 часа"][1] == 3


def test_flat_nodes_generation():
    """Проверка правильности развертки дерева в плоский список"""
    root = ScanResult("root", "/root")
    child1 = ScanResult("child1", "/root/child1")
    child2 = ScanResult("child2", "/root/child2")
    root.add_child(child1)
    root.add_child(child2)

    flat = DataAggregator.get_flat_nodes(root)
    assert len(flat) == 3
    assert root in flat
    assert child1 in flat
    assert child2 in flat
    assert child1.level == 1