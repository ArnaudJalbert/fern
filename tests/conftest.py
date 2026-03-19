"""Root conftest: patch frontmatter to use pure-Python YAML handlers.

PyYAML's C extensions (CSafeDumper / CSafeLoader) crash under coverage
instrumentation with ``EmitterError`` / ``ConstructorError``.  The
pure-Python equivalents work identically but aren't affected by the
coverage tracer, so we swap them in before any test imports frontmatter.
"""

import frontmatter.default_handlers as _fmh
from yaml.dumper import SafeDumper as _PureSafeDumper
from yaml.loader import SafeLoader as _PureSafeLoader

_fmh.SafeDumper = _PureSafeDumper  # type: ignore[assignment]
_fmh.SafeLoader = _PureSafeLoader  # type: ignore[assignment]
