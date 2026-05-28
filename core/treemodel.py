from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt


class ScanTreeModel(QAbstractItemModel):
    def __init__(self, root_result):
        super().__init__()
        self.root_item = root_result

    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_item = parent.internalPointer() if parent.isValid() else self.root_item

        if row < len(parent_item.children):
            child = parent_item.children[row]
            return self.createIndex(row, column, child)

        return QModelIndex()

    def hasChildren(self, parent=QModelIndex()):
        if not parent.isValid():
            return True
        parent_item = parent.internalPointer()
        return len(parent_item.children) > 0
    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent

        if parent_item is None or parent_item == self.root_item:
            return QModelIndex()
        grandparent = parent_item.parent
        row = grandparent.children.index(parent_item)

        return self.createIndex(row, 0, parent_item)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return "Имя файла" if section == 0 else "Размер"
        return None

    def rowCount(self, parent=QModelIndex()):
        if parent.column() > 0:
            return 0
        parent_item = parent.internalPointer() if parent.isValid() else self.root_item
        return len(parent_item.children)

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return item.name
            if index.column() == 1:
                from utils.formatter import Formatter
                return Formatter().format_size(item.size)
        if role == Qt.ItemDataRole.UserRole:
            if index.column() == 0:
                return item.name
            if index.column() == 1:
                return item.size
        
        return None