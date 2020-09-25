from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QStyle


class RangeSlider(QtWidgets.QWidget):
    sliderMoved = QtCore.pyqtSignal(int, int, int)

    def __init__(self, parent=None, other=None):
        super().__init__(parent)
        self.other = other

        self.opt = QtWidgets.QStyleOptionSlider()
        self.opt.minimum = 0
        self.opt.maximum = 10

        self.first_position = self.opt.minimum
        self.second_position = self.opt.maximum

        self.setTickPosition(QtWidgets.QSlider.TicksAbove)
        self.setTickInterval(1)
        self.setSizePolicy(
            QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Fixed,
                QtWidgets.QSizePolicy.Slider,
            )
        )
        self.range_slider_handle = QStyle.SC_SliderHandle

    def setRangeLimit(self, minimum: int, maximum: int):
        self.opt.minimum = minimum
        self.opt.maximum = maximum

    def setRange(self, start: int, end: int):
        self.first_position = start
        self.second_position = end

    def getRange(self):
        return (self.first_position, self.second_position)

    def setTickPosition(self, position: QtWidgets.QSlider.TickPosition):
        self.opt.tickPosition = position

    def setTickInterval(self, ti: int):
        self.opt.tickInterval = ti

    def paintEvent(self, event: QtGui.QPaintEvent):
        painter = QtGui.QPainter(self)

        # Draw rule
        self.opt.initFrom(self)
        self.opt.rect = self.rect()
        self.opt.sliderPosition = 0
        self.opt.subControls = QStyle.SC_SliderGroove | QStyle.SC_SliderTickmarks

        #   Draw GROOVE
        self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)

        #  Draw INTERVAL
        if self.other is None:
            color = self.palette().color(QtGui.QPalette.Highlight)
        else:
            color = self.other.palette().color(QtGui.QPalette.Highlight)
        color.setAlpha(128)
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QtCore.Qt.NoPen)

        self.opt.sliderPosition = self.first_position
        x_left_handle = (
            self.style().subControlRect(QStyle.CC_Slider, self.opt,
                                        self.range_slider_handle).right()
        )

        self.opt.sliderPosition = self.second_position
        x_right_handle = (
            self.style().subControlRect(QStyle.CC_Slider, self.opt,
                                        self.range_slider_handle).left()
        )

        groove_rect = self.style().subControlRect(
            QStyle.CC_Slider, self.opt, QStyle.SC_SliderGroove
        )

        selection = QtCore.QRect(
            x_left_handle,
            groove_rect.y(),
            x_right_handle - x_left_handle,
            groove_rect.height(),
        ).adjusted(-1, 1, 1, -1)

        painter.drawRect(selection)

        # Draw first handle
        self.opt.subControls = self.range_slider_handle
        self.opt.sliderPosition = self.first_position
        self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)

        # Draw second handle
        self.opt.sliderPosition = self.second_position
        self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        self.opt.sliderPosition = self.first_position
        self._first_sc = self.style().hitTestComplexControl(
            QStyle.CC_Slider, self.opt, event.pos(), self
        )

        self.opt.sliderPosition = self.second_position
        self._second_sc = self.style().hitTestComplexControl(
            QStyle.CC_Slider, self.opt, event.pos(), self
        )

    def setFirstPosition(self, pos):
        if pos < self.second_position:
            self.first_position = pos
            self.update()
            self.sliderMoved.emit(self.first_position, self.second_position, 0)

    def setSecondPosition(self, pos):
        if pos > self.first_position:
            self.second_position = pos
            self.update()
            self.sliderMoved.emit(self.first_position, self.second_position, 1)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        distance = self.opt.maximum - self.opt.minimum

        pos = self.style().sliderValueFromPosition(
            0, distance,
            event.pos().x(),
            self.rect().width()
        )

        if (self._first_sc == self.range_slider_handle):
            if (pos <= self.second_position) or (self.last_clicked == 0):
                self.first_position = pos
                self.update()
                self.sliderMoved.emit(self.first_position, self.second_position, 0)
                return

        if (self._second_sc == self.range_slider_handle):
            if (pos >= self.first_position) or (self.second_position == 1):
                self.second_position = pos
                self.update()
                self.sliderMoved.emit(self.first_position, self.second_position, 1)
                return

    def sizeHint(self):
        """ override """
        SliderLength = 84
        TickSpace = 5

        w = SliderLength
        h = self.style().pixelMetric(QStyle.PM_SliderThickness, self.opt, self)

        if (
            self.opt.tickPosition & QtWidgets.QSlider.TicksAbove
            or self.opt.tickPosition & QtWidgets.QSlider.TicksBelow
        ):
            h += TickSpace

        return (
            self.style().sizeFromContents(QStyle.CT_Slider, self.opt,
                                          QtCore.QSize(w, h)).expandedTo(
                                              QtWidgets.QApplication.globalStrut()
                                          )
        )
