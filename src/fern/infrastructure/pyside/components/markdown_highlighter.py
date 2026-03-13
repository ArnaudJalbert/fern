"""
Markdown syntax highlighter for QPlainTextEdit.

Provides a QSyntaxHighlighter that applies colors and styles to markdown
constructs (headers, bold, italic, code, links, lists, blockquotes, etc.)
inside a QTextDocument.
"""

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class MarkdownHighlighter(QSyntaxHighlighter):
    """
    Applies markdown syntax highlighting to a QTextDocument.

    Supports: headers (# ...), bold (**...**), italic (*...*), inline code (`...`),
    links ([text](url)), list markers (-, *, 1.), blockquotes (>) and horizontal rules (---).
    """

    def __init__(self, parent=None):
        """
        Initialize the highlighter and build format/rule sets.

        Args:
            parent: A QTextDocument to highlight (typically from QPlainTextEdit.document()).
        """
        super().__init__(parent)
        self._formats: dict[str, QTextCharFormat] = {}
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []
        self._setup_formats()
        self._setup_rules()

    def _setup_formats(self) -> None:
        """Create QTextCharFormat instances for each markdown element type."""
        header = QTextCharFormat()
        header.setForeground(QColor("#6a9955"))
        header.setFontWeight(QFont.Weight.Bold)
        self._formats["header"] = header

        bold = QTextCharFormat()
        bold.setFontWeight(QFont.Weight.Bold)
        bold.setForeground(QColor("#d4d4d4"))
        self._formats["bold"] = bold

        italic = QTextCharFormat()
        italic.setFontItalic(True)
        italic.setForeground(QColor("#d4d4d4"))
        self._formats["italic"] = italic

        code = QTextCharFormat()
        code.setForeground(QColor("#ce9178"))
        code.setBackground(QColor("#2d2d2d"))
        self._formats["code"] = code

        link = QTextCharFormat()
        link.setForeground(QColor("#3794ff"))
        try:
            link.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)
        except AttributeError:
            pass
        self._formats["link"] = link

        list_marker = QTextCharFormat()
        list_marker.setForeground(QColor("#808080"))
        self._formats["list"] = list_marker

        blockquote = QTextCharFormat()
        blockquote.setForeground(QColor("#6a9955"))
        self._formats["blockquote"] = blockquote

        horizontal_rule = QTextCharFormat()
        horizontal_rule.setForeground(QColor("#808080"))
        horizontal_rule.setFontWeight(QFont.Weight.Bold)
        self._formats["hr"] = horizontal_rule

    def _setup_rules(self) -> None:
        """Build the list of (regex, format) rules applied in highlightBlock."""
        # Headers: # ## ### etc. at start of line
        self._rules.append(
            (
                QRegularExpression(r"^#{1,6}\s+.+$"),
                self._formats["header"],
            )
        )
        # Bold: **text** or __text__
        self._rules.append(
            (
                QRegularExpression(r"\*\*[^*]+\*\*|__[^_]+__"),
                self._formats["bold"],
            )
        )
        # Italic: *text* or _text_ (single, not double)
        self._rules.append(
            (
                QRegularExpression(r"(?<!\*)\*[^*]+\*(?!\*)|(?<!_)_[^_]+_(?!_)"),
                self._formats["italic"],
            )
        )
        # Inline code: `code`
        self._rules.append(
            (
                QRegularExpression(r"`[^`]+`"),
                self._formats["code"],
            )
        )
        # Links: [text](url) or [text](url "title")
        self._rules.append(
            (
                QRegularExpression(r"\[([^\]]+)\]\([^)]+\)"),
                self._formats["link"],
            )
        )
        # Unordered list: - or * or + at start of line
        self._rules.append(
            (
                QRegularExpression(r"^(\s*)[-*+]\s"),
                self._formats["list"],
            )
        )
        # Ordered list: 1. 2. etc.
        self._rules.append(
            (
                QRegularExpression(r"^(\s*)\d+\.\s"),
                self._formats["list"],
            )
        )
        # Blockquote: > at start
        self._rules.append(
            (
                QRegularExpression(r"^>\s?.+$"),
                self._formats["blockquote"],
            )
        )
        # Horizontal rule: --- or *** or ___
        self._rules.append(
            (
                QRegularExpression(r"^[-*_]{3,}\s*$"),
                self._formats["hr"],
            )
        )

    def highlightBlock(self, text: str) -> None:
        """Apply formatting to the given line of text. Called by Qt for each block."""
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
