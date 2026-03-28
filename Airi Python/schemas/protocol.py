import asyncio
import time
from typing import List, Optional, Dict, Any, Union, Literal, Generic, TypeVar

from pydantic import BaseModel, Field
from enum import Enum
from nanoid import generate

TType = TypeVar('TType', bound=str)
TPayload = TypeVar('TPayload')

class MessageHeartbeatKind(str, Enum):
    PING = "ping"
    PONG = "pong"

class PluginIdentity(BaseModel):
    id: str
    version: Optional[str] = None
    labels: Optional[Dict[str, str]] = None

class ModuleIdentity(BaseModel):
    id: str
    kind: Literal["plugin"]
    plugin: PluginIdentity
    labels: Optional[Dict[str, str]] = None

class EventPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class EventEnvelope(BaseModel):
    id: str = Field(default_factory=generate)
    type: str
    time: float = Field(default_factory=lambda: time.time() * 1000)
    priority: Optional[EventPriority] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    payload: Any

def create_event(
    event_type: str,
    payload: Any,
    priority: Optional[EventPriority] = None,
    source: Optional[str] = None,
    tags: Optional[List[str]] = None,
    event_id: Optional[str] = None,
    event_time: Optional[float] = None
) -> EventEnvelope:
    return EventEnvelope(
        id=event_id or generate(),
        type=event_type,
        time=event_time or time.time() * 1000,
        priority=priority,
        source=source,
        tags=tags,
        payload=payload
    )

class EventStream(Generic[TPayload]):
    def __init__(self, queue: Optional[asyncio.Queue] = None):
        self.queue = queue or asyncio.Queue()
        self.closed = False

    async def emit(self, event: TPayload):
        if not self.closed:
            await self.queue.put(event)

    def close(self):
        self.closed = True

    async def __aiter__(self):
        while not (self.closed and self.queue.empty()):
            try:
                event = await self.queue.get()
                yield event
                self.queue.task_done()
            except asyncio.CancelledError:
                break

def create_event_stream() -> EventStream[TPayload]:
    return EventStream()

class EventBaseMetadata(BaseModel):
    source: Optional[ModuleIdentity] = None
    id: Optional[str] = None
    parent_id: Optional[str] = Field(None, alias="parentId")

class WebSocketEventMetadata(BaseModel):
    source: ModuleIdentity
    event: Dict[str, Any] # Contains id and parentId

class RouteConfig(BaseModel):
    destinations: Optional[List[Union[str, Dict[str, Any]]]] = None
    bypass: Optional[bool] = None

class WebSocketBaseEvent(BaseModel):
    type: str
    data: Dict[str, Any]
    metadata: WebSocketEventMetadata
    route: Optional[RouteConfig] = None

class SparkNotifyEvent(BaseModel):
    id: str
    event_id: str = Field(..., alias="eventId")
    lane: Optional[str] = None
    kind: Literal["alarm", "ping", "reminder"]
    urgency: Literal["immediate", "soon", "later"]
    headline: str
    note: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    ttl_ms: Optional[int] = Field(None, alias="ttlMs")
    requires_ack: Optional[bool] = Field(None, alias="requiresAck")
    destinations: List[str]
    metadata: Optional[Dict[str, Any]] = None

class SparkEmitEvent(BaseModel):
    id: str
    event_id: Optional[str] = Field(None, alias="eventId")
    state: Literal["queued", "working", "done", "dropped", "blocked", "expired"]
    note: Optional[str] = None
    destinations: List[str]
    metadata: Optional[Dict[str, Any]] = None

class SparkCommandGuidanceOption(BaseModel):
    label: str
    steps: List[str]
    rationale: Optional[str] = None
    possible_outcome: Optional[List[str]] = Field(None, alias="possibleOutcome")
    risk: Optional[Literal["high", "medium", "low", "none"]] = None
    fallback: Optional[List[str]] = None
    triggers: Optional[List[str]] = None

class SparkCommandGuidance(BaseModel):
    type: Literal["proposal", "instruction", "memory-recall"]
    persona: Optional[Dict[str, Literal["very-high", "high", "medium", "low", "very-low"]]] = None
    options: List[SparkCommandGuidanceOption]

class SparkCommandEvent(BaseModel):
    id: str
    event_id: Optional[str] = Field(None, alias="eventId")
    parent_event_id: Optional[str] = Field(None, alias="parentEventId")
    command_id: str = Field(..., alias="commandId")
    interrupt: Union[Literal["force", "soft"], bool]
    priority: Literal["critical", "high", "normal", "low"]
    intent: Literal["plan", "proposal", "action", "pause", "resume", "reroute", "context"]
    ack: Optional[str] = None
    guidance: Optional[SparkCommandGuidance] = None
    contexts: Optional[List[Dict[str, Any]]] = None
    destinations: List[str]

class TransportConnectionHeartbeatEvent(BaseModel):
    kind: MessageHeartbeatKind
    message: str
    at: Optional[float] = Field(default_factory=time.time)

class ModuleAuthenticateEvent(BaseModel):
    token: str

class ModuleAuthenticatedEvent(BaseModel):
    authenticated: bool

class RegistryModulesSyncEvent(BaseModel):
    modules: List[Dict[str, Any]]

class ModuleAnnounceEvent(BaseModel):
    name: str
    identity: ModuleIdentity
    possible_events: List[str] = Field(..., alias="possibleEvents")
    permissions: Optional[Dict[str, Any]] = None
    config_schema: Optional[Dict[str, Any]] = Field(None, alias="configSchema")
    dependencies: Optional[List[Dict[str, Any]]] = None

class ModuleAnnouncedEvent(BaseModel):
    name: str
    index: Optional[int] = None
    identity: ModuleIdentity

class ModuleDeAnnouncedEvent(BaseModel):
    name: str
    index: Optional[int] = None
    identity: ModuleIdentity
    reason: Optional[str] = None

class ErrorEvent(BaseModel):
    message: str
