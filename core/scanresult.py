class ScanResult:
    def __init__(self, name="root", path="", parent=None):
        self.name = name
        self.path = path
        self.parent = parent
        self.size = 0
        self.files = 0
        self.skipped = 0
        self.children = []

    def add_child(self, child_result):
        child_result.parent = self
        self.children.append(child_result)