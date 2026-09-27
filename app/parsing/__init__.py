"""Docling-backed document parsing.

``parse_document`` is the one entry point; nothing Docling-specific crosses this boundary
— callers see only the ``app.models`` wire contract.
"""

from __future__ import annotations

from .converter import is_model_loaded, load_models
from .service import parse_document

__all__ = ["is_model_loaded", "load_models", "parse_document"]
