from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtCore import Qt, QRectF, pyqtSignal


class TreeMapWidget(QWidget):
    # Сигнал, который будет передавать объект ScanResult при клике
    clicked_node = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.root_node = None
        self.selected_node = None  # Сюда сохраняем узел, на который нажали
        self.setMinimumHeight(250)
        # Список для хранения отрисованных прямоугольников и ссылок на узлы
        self.rects_map = []
        # Разрешаем виджету принимать фокус мыши
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_data(self, root_node):
        self.root_node = root_node
        self.selected_node = None  # Сбрасываем выделение при новом сканировании
        self.rects_map.clear()
        self.update()

    def paintEvent(self, event):
        if not self.root_node or self.root_node.size == 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()

        # Очищаем старую карту перед перерисовкой
        self.rects_map.clear()

        # Запускаем отрисовку дерева прямоугольников
        self._draw_node(painter, self.root_node, rect.x(), rect.y(),
                        rect.width(), rect.height())

        # Вторым слоем поверх рисуем рамку выделения, чтобы её не перекрыли соседние квадраты
        if self.selected_node:
            for rect_obj, node in self.rects_map:
                if node == self.selected_node:
                    # Жирная контрастная рамка (например, желтая или белая)
                    highlight_pen = QPen(QColor(255, 255, 0),
                                         3)  # Желтый цвет, толщина 3px
                    painter.setPen(highlight_pen)
                    painter.setBrush(
                        Qt.BrushStyle.NoBrush)  # Не закрашиваем внутренность

                    # Рисуем рамку чуть-чуть отступив внутрь, чтобы углы не срезались
                    painter.drawRect(rect_obj.adjusted(1, 1, -1, -1))
                    break

    def _draw_node(self, painter, node, x, y, w, h):
        if w < 3 or h < 3 or not node.children:
            rect_obj = QRectF(x, y, w, h)
            self.rects_map.append((rect_obj, node))

            hue = hash(node.name) % 360
            color = QColor.fromHsv(hue, 180, 200)

            painter.setBrush(QBrush(color))
            # Обычная тонкая белая рамка-сетка между квадратами
            painter.setPen(QPen(QColor(40, 40, 40), 1))
            painter.drawRect(rect_obj)
            return

        children = sorted([c for c in node.children if c.size > 0],
                          key=lambda c: c.size, reverse=True)
        total_size = sum(c.size for c in children)

        if total_size == 0:
            return

        current_x = x
        current_y = y
        horizontal_split = w > h

        for child in children:
            ratio = child.size / total_size
            if horizontal_split:
                child_w = w * ratio
                child_h = h
                self._draw_node(painter, child, current_x, current_y, child_w,
                                child_h)
                current_x += child_w
            else:
                child_w = w
                child_h = h * ratio
                self._draw_node(painter, child, current_x, current_y, child_w,
                                child_h)
                current_y += child_h

    # Обработка клика мыши
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()

            # Ищем, в какой прямоугольник попал клик
            for rect_obj, node in reversed(self.rects_map):
                if rect_obj.contains(pos):
                    self.selected_node = node  # Запоминаем, что выделили
                    self.clicked_node.emit(
                        node)  # Пытаемся синхронизировать с деревом
                    self.update()  # Вызываем принудительный repaint виджета
                    break