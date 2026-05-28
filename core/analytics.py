import time


class DataAggregator:
    @staticmethod
    def get_flat_nodes(root_node):
        """Разворачивает дерево папок в один плоский список для быстрой фильтрации"""
        nodes = [root_node]
        for child in root_node.children:
            nodes.extend(DataAggregator.get_flat_nodes(child))
        return nodes

    @staticmethod
    def group_by_extension(root_node):
        """Группировка: Расширение -> (Суммарный размер, Количество файлов)"""
        flat = DataAggregator.get_flat_nodes(root_node)
        ext_map = {}
        for n in flat:
            if n.children:
            ext = n.extension if n.extension else "без расширения"
            size, count = ext_map.get(ext, (0, 0))
            ext_map[ext] = (size + n.size, count + 1)
        return ext_map

    @staticmethod
    def group_by_owner(root_node):
        """Группировка: Владелец -> (Суммарный размер, Количество объектов)"""
        flat = DataAggregator.get_flat_nodes(root_node)
        owner_map = {}
        for n in flat:
            size, count = owner_map.get(n.owner, (0, 0))
            owner_map[n.owner] = (size + n.size, count + 1)
        return owner_map

    @staticmethod
    def group_by_time(root_node):
        """Группировка по временным категориям"""
        flat = DataAggregator.get_flat_nodes(root_node)
        now = time.time()
        time_categories = {
            "Последние 24 часа": (0, 0),
            "Последняя неделя": (0, 0),
            "Последний месяц": (0, 0),
            "Старее месяца": (0, 0)
        }

        for n in flat:
            if n.children:
                continue
            diff = now - n.mtime
            if diff <= 86400:
                cat = "Последние 24 часа"
            elif diff <= 604800:
                cat = "Последняя неделя"
            elif diff <= 2592000:
                cat = "Последний месяц"
            else:
                cat = "Старее месяца"

            size, count = time_categories[cat]
            time_categories[cat] = (size + n.size, count + 1)
        return time_categories