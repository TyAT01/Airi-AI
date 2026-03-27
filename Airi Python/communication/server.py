import json
import time
import uuid
import asyncio
import logging
from typing import Dict, Set, Optional, Any, List, Callable, Awaitable
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from nanoid import generate

from schemas.protocol import (
    WebSocketBaseEvent,
    WebSocketEventMetadata,
    ModuleIdentity,
    MessageHeartbeatKind,
    ModuleAnnouncedEvent,
    ModuleDeAnnouncedEvent,
    RegistryModulesSyncEvent,
    ErrorEvent
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticatedPeer:
    def __init__(self, websocket: WebSocket, peer_id: str):
        self.websocket = websocket
        self.id = peer_id
        self.authenticated = False
        self.name: Optional[str] = ""
        self.index: Optional[int] = None
        self.identity: Optional[ModuleIdentity] = None
        self.last_heartbeat_at = time.time()
        self.missed_heartbeats = 0
        self.healthy = True

class RoutingPolicy(BaseModel):
    allow_plugins: Optional[List[str]] = None
    deny_plugins: Optional[List[str]] = None

class AiriServer:
    def __init__(self, instance_id: str = None, auth_token: str = ""):
        self.instance_id = instance_id or generate()
        self.auth_token = auth_token
        self.peers: Dict[str, AuthenticatedPeer] = {}
        self.peers_by_module: Dict[str, Dict[Optional[int], AuthenticatedPeer]] = {}
        self.app = FastAPI()
        self.on_event_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
        self.routing_policy: Optional[RoutingPolicy] = None
        self.setup_routes()

    def set_on_event_callback(self, callback: Callable[[Dict[str, Any]], Awaitable[None]]):
        self.on_event_callback = callback

    def set_routing_policy(self, policy: RoutingPolicy):
        self.routing_policy = policy

    def setup_routes(self):
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            peer_id = str(uuid.uuid4())
            peer = AuthenticatedPeer(websocket, peer_id)
            self.peers[peer_id] = peer

            if not self.auth_token:
                peer.authenticated = True
                await self.send_authenticated(peer)
                await self.send_registry_sync(peer)

            logger.info(f"Peer {peer_id} connected")

            try:
                while True:
                    data = await websocket.receive_text()
                    await self.handle_message(peer, data)
            except WebSocketDisconnect:
                logger.info(f"Peer {peer_id} disconnected")
                await self.unregister_peer(peer)

    async def handle_message(self, peer: AuthenticatedPeer, message: str):
        try:
            event_dict = json.loads(message)
            event_type = event_dict.get("type")
            if not event_type:
                return

            peer.last_heartbeat_at = time.time()
            if "metadata" in event_dict and "source" in event_dict["metadata"]:
                peer.identity = ModuleIdentity(**event_dict["metadata"]["source"])

            if event_type == "transport:connection:heartbeat":
                peer.missed_heartbeats = 0
                if event_dict["data"].get("kind") == "ping":
                    await self.send(peer, {
                        "type": "transport:connection:heartbeat",
                        "data": {"kind": "pong", "message": "💛", "at": time.time()},
                        "metadata": self.create_server_metadata()
                    })
                return

            if event_type == "module:authenticate":
                token = event_dict["data"].get("token", "")
                if self.auth_token and token != self.auth_token:
                    await self.send_error(peer, "Invalid token")
                    return
                peer.authenticated = True
                await self.send_authenticated(peer)
                await self.send_registry_sync(peer)
                return

            if not peer.authenticated:
                await self.send_error(peer, "Not authenticated")
                return

            if event_type == "module:announce":
                await self.handle_announce(peer, event_dict)
                return

            if self.on_event_callback:
                await self.on_event_callback(event_dict)

            # Routing Decision
            target_ids = self.decide_routing(peer, event_dict)
            if target_ids is not None:
                await self.broadcast(event_dict, exclude_peer=peer, target_ids=target_ids)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(peer, str(e))

    def decide_routing(self, from_peer: AuthenticatedPeer, event: Dict[str, Any]) -> Optional[Set[str]]:
        # Porting policy-based routing logic
        if event.get("route", {}).get("bypass"):
            return None

        destinations = event.get("route", {}).get("destinations")
        if destinations:
            targets = set()
            for d in destinations:
                if isinstance(d, str):
                    if d in self.peers:
                        targets.add(d)
                    elif d in self.peers_by_module:
                        for p in self.peers_by_module[d].values():
                            targets.add(p.id)
            return targets

        if self.routing_policy:
            targets = set()
            for pid, p in self.peers.items():
                if self.matches_policy(p, self.routing_policy):
                    targets.add(pid)
            return targets

        return None # Broadcast to all

    def matches_policy(self, peer: AuthenticatedPeer, policy: RoutingPolicy) -> bool:
        plugin_id = peer.identity.plugin.id if peer.identity and peer.identity.plugin else ""
        if policy.allow_plugins and plugin_id not in policy.allow_plugins:
            return False
        if policy.deny_plugins and plugin_id in policy.deny_plugins:
            return False
        return True

    async def handle_announce(self, peer: AuthenticatedPeer, event_dict: Dict[str, Any]):
        data = event_dict["data"]
        name = data.get("name")
        index = data.get("index")
        identity = data.get("identity")

        if not name:
            await self.send_error(peer, "Module name required")
            return

        await self.unregister_module_peer(peer, reason="re-announcing")

        peer.name = name
        peer.index = index
        if identity:
            peer.identity = ModuleIdentity(**identity)

        if name not in self.peers_by_module:
            self.peers_by_module[name] = {}
        self.peers_by_module[name][index] = peer

        logger.info(f"Module {name} announced")

        await self.broadcast({
            "type": "module:announced",
            "data": {"name": name, "index": index, "identity": peer.identity.dict() if peer.identity else None},
            "metadata": self.create_server_metadata(event_dict.get("metadata", {}).get("event", {}).get("id"))
        })
        await self.broadcast_registry_sync()

    async def unregister_peer(self, peer: AuthenticatedPeer):
        if peer.id in self.peers:
            del self.peers[peer.id]
        await self.unregister_module_peer(peer, reason="connection closed")

    async def unregister_module_peer(self, peer: AuthenticatedPeer, reason: str = None):
        if peer.name and peer.name in self.peers_by_module:
            if peer.index in self.peers_by_module[peer.name]:
                del self.peers_by_module[peer.name][peer.index]
                if not self.peers_by_module[peer.name]:
                    del self.peers_by_module[peer.name]

        if peer.identity:
            await self.broadcast({
                "type": "module:de-announced",
                "data": {
                    "name": peer.name,
                    "index": peer.index,
                    "identity": peer.identity.dict(),
                    "reason": reason
                },
                "metadata": self.create_server_metadata()
            })
        await self.broadcast_registry_sync()

    def create_server_metadata(self, parent_id: str = None) -> Dict[str, Any]:
        return {
            "event": {
                "id": generate(),
                "parentId": parent_id
            },
            "source": {
                "id": self.instance_id,
                "kind": "plugin",
                "plugin": {"id": "proj-airi:server-runtime", "version": "python-0.1.0"}
            }
        }

    async def send(self, peer: AuthenticatedPeer, event: Dict[str, Any]):
        await peer.websocket.send_text(json.dumps(event))

    async def send_authenticated(self, peer: AuthenticatedPeer):
        await self.send(peer, {
            "type": "module:authenticated",
            "data": {"authenticated": True},
            "metadata": self.create_server_metadata()
        })

    async def send_error(self, peer: AuthenticatedPeer, message: str):
        await self.send(peer, {
            "type": "error",
            "data": {"message": message},
            "metadata": self.create_server_metadata()
        })

    async def send_registry_sync(self, peer: AuthenticatedPeer):
        modules = []
        for p in self.peers.values():
            if p.name and p.identity:
                modules.append({
                    "name": p.name,
                    "index": p.index,
                    "identity": p.identity.dict()
                })
        await self.send(peer, {
            "type": "registry:modules:sync",
            "data": {"modules": modules},
            "metadata": self.create_server_metadata()
        })

    async def broadcast_registry_sync(self):
        for peer in list(self.peers.values()):
            if peer.authenticated:
                await self.send_registry_sync(peer)

    async def broadcast(self, event: Dict[str, Any], exclude_peer: AuthenticatedPeer = None, target_ids: Set[str] = None):
        payload = json.dumps(event)

        for peer_id, peer in self.peers.items():
            if not peer.authenticated:
                continue
            if exclude_peer and peer_id == exclude_peer.id:
                continue
            if target_ids is not None and peer_id not in target_ids:
                continue

            try:
                await peer.websocket.send_text(payload)
            except Exception as e:
                logger.error(f"Broadcast error to {peer.id}: {e}")
                await self.unregister_peer(peer)

    def run(self, host="0.0.0.0", port=8000):
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)

if __name__ == "__main__":
    server = AiriServer()
    server.run()
