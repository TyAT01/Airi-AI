import time
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from nanoid import generate

class NotebookEntry(BaseModel):
    id: str = Field(default_factory=generate)
    kind: Literal["note", "diary", "focus"]
    text: str
    created_at: float = Field(default_factory=time.time)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ScheduledTask(BaseModel):
    id: str = Field(default_factory=generate)
    title: str
    details: Optional[str] = None
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    status: Literal["queued", "scheduled", "done", "dropped"] = "queued"
    due_at: Optional[float] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    last_notified_at: Optional[float] = None
    next_notify_at: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class CharacterNotebook:
    def __init__(self):
        self.entries: List[NotebookEntry] = []
        self.tasks: List[ScheduledTask] = []

    def add_entry(self, kind: Literal["note", "diary", "focus"], text: str, tags: List[str] = None, metadata: Dict[str, Any] = None) -> NotebookEntry:
        entry = NotebookEntry(kind=kind, text=text, tags=tags, metadata=metadata)
        self.entries.append(entry)
        return entry

    def add_note(self, text: str, tags: List[str] = None, metadata: Dict[str, Any] = None) -> NotebookEntry:
        return self.add_entry("note", text, tags, metadata)

    def schedule_task(self, title: str, details: str = None, priority: str = "normal", due_at: float = None, metadata: Dict[str, Any] = None) -> ScheduledTask:
        task = ScheduledTask(
            title=title,
            details=details,
            priority=priority,
            due_at=due_at,
            status="scheduled" if due_at else "queued",
            metadata=metadata
        )
        self.tasks.append(task)
        return task

    def mark_task_done(self, task_id: str):
        for task in self.tasks:
            if task.id == task_id:
                task.status = "done"
                task.updated_at = time.time()
                break

    def mark_task_notified(self, task_id: str, next_notify_at: float = None):
        for task in self.tasks:
            if task.id == task_id:
                task.last_notified_at = time.time()
                task.next_notify_at = next_notify_at
                task.updated_at = time.time()
                break

    def get_due_tasks(self, now: float, window_ms: float) -> List[ScheduledTask]:
        due_tasks = []
        window_seconds = window_ms / 1000.0
        for task in self.tasks:
            if task.status in ["done", "dropped"]:
                continue
            due_at = task.due_at if task.due_at is not None else now
            if due_at > now + window_seconds:
                continue
            if task.next_notify_at is not None and task.next_notify_at > now:
                continue
            due_tasks.append(task)
        return due_tasks
