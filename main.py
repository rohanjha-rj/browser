import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from src.browser_window import MainWindow


def main():
    # Enable High DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    QApplication.setApplicationName('My Cool Browser')
    QApplication.setOrganizationName('MyCoolBrowser')

    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()