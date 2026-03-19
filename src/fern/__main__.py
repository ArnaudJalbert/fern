import sys

from PySide6.QtWidgets import QApplication

from fern.infrastructure import ControllerFactory
from fern.infrastructure.pyside import MainWindow
from fern.infrastructure.pyside.theme import load_global_stylesheet


def main() -> None:
    app = QApplication(sys.argv)
    load_global_stylesheet(app)
    factory = ControllerFactory()
    recent_controller = factory.create_recent_vaults_controller()
    window = MainWindow(recent_controller=recent_controller, controller_factory=factory)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
