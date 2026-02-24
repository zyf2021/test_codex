"""Backward-compatible storage import path."""

from app.data.storage import MAX_TASKS, InventoryRow, SessionRow, Storage, TaskRow

__all__ = ["Storage", "SessionRow", "TaskRow", "InventoryRow", "MAX_TASKS"]
