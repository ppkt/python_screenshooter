from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QWidget

class PreviewWidget(QWidget):
    """
    Widget displays preview of image (QPixmap)
    """
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.image = None

    def set_image(self, image):
        """
        :param image: image to draw in preview
        :return:
        """
        self.image = image


    def paintEvent(self, paint_event):
        """
        :param paint_event:
        :return:
        """
        painter = QPainter(self)
        if self.image:
            # scale image to fit on widget
            scaled = self.image.scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            d_x = (self.width() - scaled.width()) / 2
            d_y = (self.height() - scaled.height()) / 2
            painter.drawPixmap(d_x, d_y, scaled)