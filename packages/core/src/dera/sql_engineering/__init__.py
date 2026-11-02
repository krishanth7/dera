"""Deterministic offline SQL engineering foundation; no database access."""

from .analyzer import analyze
from .models import Analysis

__all__ = ["Analysis", "analyze"]
