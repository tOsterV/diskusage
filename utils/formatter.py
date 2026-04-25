class Formatter:
    @staticmethod
    def format_size(bytes_size):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_size < 1024:
                return f"{bytes_size:>8.2f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:>8.2f} PB"

    @staticmethod
    def format_number(number):
        return f"{number:,}".replace(",", " ")
