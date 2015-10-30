import logging
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QGuiApplication, QPainter
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
import sys
from gui import Ui_MainWindow

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class ScreenShooter(Ui_MainWindow, QMainWindow):
    def __init__(self, parent=None):
        Ui_MainWindow.__init__(self)
        QMainWindow.__init__(self)
        self.setupUi(self)

        self.btn_take_screenshot.clicked.connect(self.btn_take_screenshot_clicked)

    def btn_take_screenshot_clicked(self):
        """
        Action performed after clicking "Take screenshot"
        """
        # hide main window
        self.hide()

        QTimer.singleShot(25 + 1000 * self.spin_delay.value(), self._take_screenshot)

    def _take_screenshot(self):
        """
        Grabs the contents of screen and store it, update preview widget and show main window
        """
        screen = QGuiApplication.instance().primaryScreen()
        if screen:
            screenshot = screen.grabWindow(0)
            self.preview_widget.set_image(screenshot)

        if not self.isVisible():
            self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    program = ScreenShooter()
    program.show()

    sys.exit(app.exec_())