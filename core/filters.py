import re


class RegexFilter:
    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern) if pattern else None

    def should_exclude(self, path: str) -> bool:
        if not self.pattern:
            return False
        return bool(self.pattern.search(path))
