import time
import logging
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from nanoid import generate

logger = logging.getLogger(__name__)

NotebookEntryKind = Literal['note', 'diary', 'focus']

class NotebookEntry(BaseModel):
    id: str = Field(default_factory=generate)
    kind: NotebookEntryKind
    text: str
    created_at: float = Field(default_factory=time.time, alias="createdAt")
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

TaskPriority = Literal['low', 'normal', 'high', 'critical']
TaskStatus = Literal['queued', 'scheduled', 'done', 'dropped']

class ScheduledTask(BaseModel):
    id: str = Field(default_factory=generate)
    title: str
    details: Optional[str] = None
    priority: TaskPriority = 'normal'
    status: TaskStatus = 'queued'
    due_at: Optional[float] = Field(None, alias="dueAt")
    created_at: float = Field(default_factory=time.time, alias="createdAt")
    updated_at: float = Field(default_factory=time.time, alias="updatedAt")
    last_notified_at: Optional[float] = Field(None, alias="lastNotifiedAt")
    next_notify_at: Optional[float] = Field(None, alias="nextNotifyAt")
    metadata: Optional[Dict[str, Any]] = None

class CharacterNotebook:
    def __init__(self):
        self.entries: List[NotebookEntry] = []
        self.tasks: List[ScheduledTask] = []

    @property
    def diary_entries(self) -> List[NotebookEntry]:
        return [e for e in self.entries if e.kind == 'diary']

    @property
    def focus_entries(self) -> List[NotebookEntry]:
        return [e for e in self.entries if e.kind == 'focus']

    def add_entry(self, kind: NotebookEntryKind, text: str, tags: List[str] = None, metadata: Dict[str, Any] = None) -> NotebookEntry:
        entry = NotebookEntry(kind=kind, text=text, tags=tags, metadata=metadata)
        self.entries.append(entry)
        logger.info(f"Added notebook entry of kind: {kind}")
        return entry

    def add_note(self, text: str, tags: List[str] = None, metadata: Dict[str, Any] = None) -> NotebookEntry:
        return self.add_entry('note', text, tags, metadata)

    def add_diary_entry(self, text: str, tags: List[str] = None, metadata: Dict[str, Any] = None) -> NotebookEntry:
        return self.add_entry('diary', text, tags, metadata)

    def add_focus_entry(self, text: str, tags: List[str] = None, metadata: Dict[str, Any] = None) -> NotebookEntry:
        return self.add_entry('focus', text, tags, metadata)

    def schedule_task(self, title: str, details: str = None, priority: TaskPriority = 'normal', due_at: float = None, metadata: Dict[str, Any] = None) -> ScheduledTask:
        now = time.time()
        status: TaskStatus = 'scheduled' if due_at else 'queued'
        task = ScheduledTask(
            title=title,
            details=details,
            priority=priority,
            status=status,
            dueAt=due_at,
            createdAt=now,
            updatedAt=now,
            metadata=metadata
        )
        self.tasks.append(task)
        logger.info(f"Scheduled task: {title} (priority={priority})")
        return task

    def mark_task_done(self, task_id: str):
        for task in self.tasks:
            if task.id == task_id:
                task.status = 'done'
                task.updated_at = time.time()
                logger.info(f"Task {task_id} marked as done")
                return

    def requeue_task(self, task_id: str, due_at: float = None, reason: str = None):
        for task in self.tasks:
            if task.id == task_id:
                task.status = 'queued'
                task.due_at = due_at
                task.updated_at = time.time()
                if not task.metadata:
                    task.metadata = {}
                task.metadata['requeueReason'] = reason
                logger.info(f"Task {task_id} re-queued")
                return

    def mark_task_notified(self, task_id: str, next_notify_at: float = None):
        for task in self.tasks:
            if task.id == task_id:
                now = time.time()
                task.last_notified_at = now
                task.next_notify_at = next_notify_at
                task.updated_at = now
                logger.info(f"Task {task_id} notification marked")
                return

    def get_due_tasks(self, now: float, window_ms: float) -> List[ScheduledTask]:
        due_tasks = []
        for task in self.tasks:
            if task.status in ('done', 'dropped'):
                continue

            due_at = task.due_at if task.due_at is not None else now
            if due_at > now + (window_ms / 1000.0):
                continue

            if task.next_notify_at is not None and task.next_notify_at > now:
                continue

            due_tasks.append(task)
        return due_tasks
