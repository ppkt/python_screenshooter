import logging
import sys
import os

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog

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
        self.btn_save.clicked.connect(self.btn_save_clicked)

        self.screenshot = None

        self.supported_extensions = ['png', 'bmp', 'jpeg', 'jpg']
        # create filter
        self.filter = "Images ({})".format(' '.join(
            ("*." + extension) for extension in self.supported_extensions))

        self._take_screenshot()

    def btn_take_screenshot_clicked(self):
        """
        Action performed after clicking "Take screenshot"
        """
        # hide main window
        self.hide()

        # schedule taking screenshot
        QTimer.singleShot(25 + 1000 * self.spin_delay.value(), self._take_screenshot)

    def btn_save_clicked(self):
        """
        Action performed after clicking "Save as..."
        """

        if not self.screenshot:
            return

        # display dialog with path to image
        (path, _) = QFileDialog.getSaveFileName(parent=self,
                                                caption="Path to store image",
                                                filter=self.filter)

        if not path:
            # cancel clicked
            return

        _, extension = os.path.splitext(path)
        extension = extension[1:]  # ignore dot at the beginning of extension

        format = ''
        if extension not in self.supported_extensions:
            # unexpected extension, fallback to png
            format = 'png'
        self.screenshot.save(path, format=format)


    def _take_screenshot(self):
        """
        Grabs the contents of screen and store it, update preview widget and show main window
        """
        screen = QGuiApplication.instance().primaryScreen()
        if screen:
            self.screenshot = screen.grabWindow(0)
            self.preview_widget.set_image(self.screenshot)

        if not self.isVisible():
            self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    program = ScreenShooter()
    program.show()

    sys.exit(app.exec_())
