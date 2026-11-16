
import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from handify.ui.main_window import MainWindow


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("Handify")
    app.setWindowIcon(QIcon(resource_path("handify.ico")))

    window = MainWindow()
    window.setWindowIcon(QIcon(resource_path("handify.ico")))
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
