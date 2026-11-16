
import sys
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from handify.ui.main_window import MainWindow


def resource_path(relative_path):
    base_path = getattr(
        sys,
        "_MEIPASS",
        os.path.abspath(".")
    )
    return os.path.join(base_path, relative_path)


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("Handify")
    app.setDesktopFileName("Handify")
    app.setWindowIcon(QIcon(resource_path("handify_1024.png")))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
