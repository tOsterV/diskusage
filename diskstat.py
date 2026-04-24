class DiskStats:
    def __init__(self, total, free):
        self.total = total
        self.free = free
        self.used = total - free