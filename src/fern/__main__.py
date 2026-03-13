import sys

from PySide6.QtWidgets import QApplication

from fern.infrastructure.pyside.theme import load_global_stylesheet


def main() -> None:
    app = QApplication(sys.argv)
    load_global_stylesheet(app)

    from fern.infrastructure.pyside.splash import SplashScreen

    splash = SplashScreen()
    splash.show()
    splash.set_progress(10, "Loading workspace…")

    from fern.infrastructure import ControllerFactory

    splash.set_progress(30, "Initializing controller…")
    factory = ControllerFactory()
    controller = factory.get_controller()

    splash.set_progress(60, "Building interface…")

    from fern.infrastructure.pyside import MainWindow

    window = MainWindow(controller)

    splash.set_progress(85, "Almost ready…")
    splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
