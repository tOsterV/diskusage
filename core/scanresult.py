import os


class ScanResult:
    def __init__(self, name="root", path="", parent=None):
        self.name = name
        self.path = path
        self.parent = parent
        self.level = 0
        self.size = 0
        self.files = 0
        self.skipped = 0
        self.children = []

        self.mtime = 0.0
        self.owner = "Unknown"

        _, ext = os.path.splitext(name)
        self.extension = ext.lower() if ext else "без расширения"

    def add_child(self, child_result):
        child_result.parent = self
        child_result.level = self.level + 1
        self.children.append(child_result)