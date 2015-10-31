import logging
import sys
import os
from tempfile import NamedTemporaryFile
import webbrowser

from PyQt5.QtCore import QSettings, Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QLineEdit, QLabel, \
    QDialog, QVBoxLayout
from imgurpython.client import ImgurClient

from gui import Ui_MainWindow

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

with open('imgur_api_secret.txt') as file_:
    IMGUR_API_SECRET = file_.read().strip()

class ImgurAuthenticationDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        self.setWindowModality(Qt.ApplicationModal)

        layout = QVBoxLayout(self)

        self.url = QLabel(self)
        self.input = QLineEdit(self)
        layout.addWidget(self.url)
        layout.addWidget(self.input)

        self.url.setWordWrap(True)
        self.url.setOpenExternalLinks(True)

        self.input.editingFinished.connect(self.accept)

    @staticmethod
    def getImgurPin(parent=None, window_title="", label_text=""):
        dialog = ImgurAuthenticationDialog(parent)
        dialog.setWindowTitle(window_title)
        dialog.url.setText(label_text)
        result = dialog.exec_()
        return result, dialog.input.text()

class UploadThread(QThread):
    file_uploaded = pyqtSignal(object)

    def __init__(self, client, image):
        QThread.__init__(self)
        self.client = client
        self.image = image

    def run(self):
        """
        Create temporary image and upload it using provided credentials, after this emit
        `file_uploaded` signal
        :return:
        """

        response = None
        with NamedTemporaryFile(suffix='.png') as temp_file:
            self.image.save(temp_file.name)
            response = self.client.upload_from_path(temp_file.name, anon=False)
            logger.debug("Upload completed")

        self.file_uploaded.emit(response)


class ScreenShooter(Ui_MainWindow, QMainWindow):
    def __init__(self, parent=None):
        Ui_MainWindow.__init__(self)
        QMainWindow.__init__(self)
        self.setupUi(self)

        self.btn_take_screenshot.clicked.connect(self.btn_take_screenshot_clicked)
        self.btn_save.clicked.connect(self.btn_save_clicked)
        self.btn_upload.clicked.connect(self.btn_upload_clicked)

        self.progress_bar.hide()

        self.screenshot = None

        self.supported_extensions = ['png', 'bmp', 'jpeg', 'jpg']
        # create filter
        self.filter = "Images ({})".format(' '.join(
            ("*." + extension) for extension in self.supported_extensions))

        # load app settings
        self.settings = QSettings('ppkt', 'python_uploader')

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

    def _get_imgur_client(self):
        """
        Returns imgur client instance with authorized user. If user was not authorized previously,
        will be asked for authentication on imgur site.

        :return: instance of Imgur client with all tokens present or `None`
        :rtype ImgurClient:
        """

        # check if credentials are present
        access_token = self.settings.value('imgur_access_token', type=str)
        refresh_token = self.settings.value('imgur_refresh_token', type=str)

        if access_token and refresh_token:
            client = ImgurClient('6ba31a58e98608d', IMGUR_API_SECRET, access_token, refresh_token)
        else:
            client = ImgurClient('6ba31a58e98608d', IMGUR_API_SECRET)
            logger.debug("Authorization required")
            authorization_url = client.get_auth_url()
            logger.debug("Authorization url: %s", authorization_url)

            (accepted, pin) = ImgurAuthenticationDialog().getImgurPin(
                None, "User not authenticated",
                ("Please open this <a href=\"{}\">URL</a> and log in using imgur credentials. Then "
                 "paste autorization pin in form below").format(authorization_url))

            if not accepted or not pin:
                return None

            logger.debug("Authorization pin: %s", pin)

            credentials = client.authorize(pin)
            client.set_user_auth(credentials['access_token'], credentials['refresh_token'])

            # save tokens
            self.settings.setValue('imgur_access_token', credentials['access_token'])
            self.settings.setValue('imgur_refresh_token', credentials['refresh_token'])

            logger.debug("Credentials are correct")

        return client

    def btn_upload_clicked(self):

        client = self._get_imgur_client()
        if not client:
            return

        self.progress_bar.show()
        self.btn_upload.setDisabled(True)

        # upload in separate thread (to not freeze gui)
        self.upload_thread = UploadThread(client, self.screenshot)
        self.upload_thread.file_uploaded.connect(self._upload_finished)
        self.upload_thread.start()


    def _upload_finished(self, response):
        """
        Slot triggered when uploader thread finishes its execution (and image is present on Imgur)
        """

        if response:
            logger.debug(response)
            url = "https://imgur.com/{}".format(response['id'])
            webbrowser.open(url)

        self.progress_bar.hide()
        self.btn_upload.setEnabled(True)

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
