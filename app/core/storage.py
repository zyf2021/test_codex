"""Backward-compatible storage import path."""

from app.data.storage import InventoryRow, SessionRow, Storage, TaskRow

__all__ = ["Storage", "SessionRow", "TaskRow", "InventoryRow"]
