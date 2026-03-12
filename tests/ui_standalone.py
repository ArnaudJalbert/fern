"""
Run the Fern UI for local testing.

Usage (from project root):

    uv run python -m tests.ui_standalone

The window opens on the welcome page. Use Vault > Open... to open a vault.
Fake data for testing is in tests/standalone/ (open that folder as a vault).
"""

import sys

from PySide6.QtWidgets import QApplication


def main() -> None:
    app = QApplication(sys.argv)
    from fern.infrastructure import ControllerFactory
    from fern.infrastructure.pyside import MainWindow
    from fern.infrastructure.pyside.theme import load_global_stylesheet

    load_global_stylesheet(app)
    factory = ControllerFactory()
    controller = factory.get_controller()
    window = MainWindow(controller)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
