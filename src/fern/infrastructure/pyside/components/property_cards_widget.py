"""
Widget that stacks PropertyCards vertically (one card per row).
"""

from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from fern.infrastructure.pyside.components.property_card import PropertyCard


class PropertyCardsWidget(QWidget):
    """
    Container that stacks PropertyCards on top of each other (label left, modifier right in each card).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("propertyCardsWidget")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._cards: list[PropertyCard] = []

    def add_card(self, card: PropertyCard) -> None:
        """Append a card to the stack."""
        self._layout.addWidget(card)
        self._cards.append(card)

    def clear(self) -> None:
        """Remove all cards from the stack and delete them."""
        for card in self._cards:
            self._layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

    def cards(self) -> list[PropertyCard]:
        """Return the list of cards (read-only)."""
        return list(self._cards)
