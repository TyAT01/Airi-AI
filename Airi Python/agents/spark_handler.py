import logging
import json
import asyncio
from typing import List, Dict, Any, Optional, Union, Literal
from nanoid import generate
from pydantic import BaseModel, Field

from schemas.protocol import SparkNotifyEvent, SparkCommandEvent, SparkCommandGuidance, SparkCommandGuidanceOption
from llm.client import LLMClient
from core.character import CharacterStore as CharacterState

logger = logging.getLogger(__name__)

class SparkCommandDraftPersona(BaseModel):
    strength: Literal['very-high', 'high', 'medium', 'low', 'very-low']
    traits: str

class SparkCommandDraftGuidanceOption(BaseModel):
    label: str
    steps: List[str]
    rationale: Optional[str] = None
    possibleOutcome: Optional[List[str]] = None
    risk: Optional[Literal['high', 'medium', 'low', 'none']] = None
    fallback: Optional[List[str]] = None
    triggers: Optional[List[str]] = None

class SparkCommandDraftGuidance(BaseModel):
    type: Literal['proposal', 'instruction', 'memory-recall']
    persona: Optional[List[SparkCommandDraftPersona]] = None
    options: List[SparkCommandDraftGuidanceOption]

class SparkCommandDraft(BaseModel):
    destinations: List[str]
    interrupt: Optional[Union[Literal['force', 'soft', 'false'], bool]] = None
    priority: Optional[Literal['critical', 'high', 'normal', 'low']] = None
    intent: Optional[Literal['plan', 'proposal', 'action', 'pause', 'resume', 'reroute', 'context']] = None
    ack: Optional[str] = None
    guidance: Optional[SparkCommandDraftGuidance] = None

class SparkCommandSchema(BaseModel):
    commands: List[SparkCommandDraft]

class SparkNotifyResponse(BaseModel):
    reaction: Optional[str] = None
    commands: List[SparkCommandDraft] = []

class SparkNotifyAgent:
    """
    Agent that handles spark:notify events.
    Mimics packages/stage-ui/src/stores/character/orchestrator/agents/event-handler-spark-notify/index.ts.
    """
    def __init__(self, character: CharacterState, llm: LLMClient, active_model: str = "gpt-4o"):
        self.character = character
        self.llm = llm
        self.active_model = active_model
        self.processing = False
        self.pending: List[SparkNotifyEvent] = []

    def get_spark_notify_handling_agent_instruction(self, module_name: str) -> str:
        return "\n".join([
            'This is AIRI system, the life pod hosting your consciousness. You don\'t need to respond to me or every spark:notify event directly.',
            f'Another module "{module_name}" triggered spark:notify event for you to checkout.',
            'You may call the built-in tool "builtIn_sparkCommand" to issue spark:command to sub-agents as needed.',
            'For any of the output that is not a tool call, it will be streamed to user\'s interface and maybe processed with text to speech system ',
            'to be played out loud as your actual reaction to the spark:notify event.',
        ])

    async def run_notify_agent(self, event: SparkNotifyEvent, source_key: str = "unknown") -> SparkNotifyResponse:
        system_prompt = "\n\n".join(filter(None, [
            self.character.system_prompt,
            self.get_spark_notify_handling_agent_instruction(source_key)
        ]))

        user_msg = json.dumps({
            "notify": event.dict(by_alias=True),
            "source": source_key,
        }, indent=2)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]

        # Define tools matching the TypeScript implementation
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "builtIn_sparkNoResponse",
                    "description": "Indicate that no response or action is needed for the current spark:notify event.",
                    "parameters": {"type": "object", "properties": {}, "additionalProperties": False}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "builtIn_sparkCommand",
                    "description": "Issue a spark:command to sub-agents. You can call this tool multiple times to issue matrices of commands to different sub-agents as needed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "commands": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "destinations": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                                        "interrupt": {"type": "string", "enum": ["force", "soft", "false"], "nullable": True},
                                        "priority": {"type": "string", "enum": ["critical", "high", "normal", "low"], "nullable": True},
                                        "intent": {"type": "string", "enum": ["plan", "proposal", "action", "pause", "resume", "reroute", "context"], "nullable": True},
                                        "ack": {"type": "string"},
                                        "guidance": {
                                            "type": "object",
                                            "properties": {
                                                "type": {"type": "string", "enum": ["proposal", "instruction", "memory-recall"]},
                                                "persona": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "strength": {"type": "string", "enum": ["very-high", "high", "medium", "low", "very-low"]},
                                                            "traits": {"type": "string"}
                                                        },
                                                        "required": ["strength", "traits"],
                                                        "additionalProperties": False
                                                    },
                                                    "nullable": True
                                                },
                                                "options": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "label": {"type": "string"},
                                                            "steps": {"type": "array", "items": {"type": "string"}},
                                                            "rationale": {"type": "string", "nullable": True},
                                                            "possibleOutcome": {"type": "array", "items": {"type": "string"}, "nullable": True},
                                                            "risk": {"type": "string", "enum": ["high", "medium", "low", "none"], "nullable": True},
                                                            "fallback": {"type": "array", "items": {"type": "string"}, "nullable": True},
                                                            "triggers": {"type": "array", "items": {"type": "string"}, "nullable": True}
                                                        },
                                                        "required": ["label", "steps"],
                                                        "additionalProperties": False
                                                    }
                                                }
                                            },
                                            "required": ["type", "options"],
                                            "additionalProperties": False,
                                            "nullable": True
                                        }
                                    },
                                    "required": ["destinations", "ack"],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": ["commands"],
                        "additionalProperties": False
                    }
                }
            }
        ]

        full_text = [""]
        command_drafts: List[SparkCommandDraft] = []
        no_response = [False]

        async def on_delta(delta: str):
            if no_response[0]:
                return
            full_text[0] += delta
            # In a real system, you'd call character.on_spark_notify_reaction_stream_event here

        response = await self.llm.stream_chat(
            model=self.active_model,
            messages=messages,
            on_delta=on_delta,
            tools=tools
        )

        for tc in response.get("tool_calls", []):
            if tc["function"]["name"] == "builtIn_sparkNoResponse":
                no_response[0] = True
            elif tc["function"]["name"] == "builtIn_sparkCommand":
                try:
                    args = json.loads(tc["function"]["arguments"])
                    validated = SparkCommandSchema(**args)
                    command_drafts.extend(validated.commands)
                except Exception as e:
                    logger.error(f"Failed to parse spark command tools: {e}")

        return SparkNotifyResponse(
            reaction="" if no_response[0] else full_text[0].strip(),
            commands=command_drafts
        )

    async def handle(self, event: SparkNotifyEvent, source_key: str = "unknown"):
        if event.urgency != 'immediate' and len(self.pending) > 0:
            self.pending.append(event)
            return None

        if self.processing:
            self.pending.append(event)
            return None

        self.processing = True
        try:
            response = await self.run_notify_agent(event, source_key)
            if not response:
                return None

            commands = []
            for draft in response.commands:
                if not draft.destinations:
                    continue

                guidance = None
                if draft.guidance:
                    persona_map = {}
                    if draft.guidance.persona:
                        for p in draft.guidance.persona:
                            persona_map[p.traits] = p.strength

                    options = []
                    for opt in draft.guidance.options:
                        options.append(SparkCommandGuidanceOption(
                            label=opt.label,
                            steps=opt.steps,
                            rationale=opt.rationale,
                            possibleOutcome=opt.possibleOutcome,
                            risk=opt.risk,
                            fallback=opt.fallback,
                            triggers=opt.triggers
                        ))

                    guidance = SparkCommandGuidance(
                        type=draft.guidance.type,
                        persona=persona_map if persona_map else None,
                        options=options
                    )

                interrupt_val = draft.interrupt
                if interrupt_val is True:
                    interrupt_val = 'force'
                elif interrupt_val is False or interrupt_val == 'false':
                    interrupt_val = False

                command = SparkCommandEvent(
                    id=generate(),
                    eventId=generate(),
                    parentEventId=event.id,
                    commandId=generate(),
                    interrupt=interrupt_val or False,
                    priority=draft.priority or 'normal',
                    intent=draft.intent or 'action',
                    ack=draft.ack,
                    guidance=guidance,
                    destinations=draft.destinations
                )
                commands.append(command)

            return {
                "reaction": response.reaction,
                "commands": commands
            }
        finally:
            self.processing = False
