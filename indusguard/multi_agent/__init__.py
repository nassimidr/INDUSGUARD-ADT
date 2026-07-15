"""Phase 6: système multi-agents SPADE/XMPP d'INDUSGUARD-ADT."""

from .config import MultiAgentConfig, load_multi_agent_config
from .schemas import AgentMessage
from .runtime import MultiAgentRuntime

__all__ = ["AgentMessage", "MultiAgentConfig", "MultiAgentRuntime", "load_multi_agent_config"]
