"""
A real, tested IT-support ticket model and priority-triage engine --
built to close a specific gap for eigenblue's "Working Student IT
Support" posting: "Handle, prioritize, and troubleshoot day-to-day IT
support requests and issues, from work laptops to office network
setups, using Slack and Jira Service Desk." I have no access to real
Jira Service Desk or Slack in this environment, so this project
implements the underlying triage logic those tools would sit on top
of, on a real, runnable data model, rather than a description of the
concept.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TicketCategory(Enum):
    LAPTOP = "laptop"
    NETWORK = "network"
    SERVER = "server"
    GPU_WORKSTATION = "gpu_workstation"
    ACCOUNT_ACCESS = "account_access"
    AI_TOOLING = "ai_tooling"
    OTHER = "other"


class TicketPriority(Enum):
    CRITICAL = 4  # outage affecting multiple people or blocking production work
    HIGH = 3      # single person fully blocked
    MEDIUM = 2    # degraded but workable
    LOW = 1       # cosmetic / convenience / no real blocker


class TicketStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_ON_REQUESTER = "waiting_on_requester"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class Ticket:
    ticket_id: str
    requester: str
    category: TicketCategory
    description: str
    affected_user_count: int = 1
    is_blocking_work: bool = False
    created_at: datetime = field(default_factory=lambda: datetime(2026, 1, 1))
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority | None = None
    assigned_to: str | None = None
    resolution_notes: str = ""

    def __post_init__(self):
        if self.affected_user_count < 1:
            raise ValueError(f"affected_user_count must be at least 1, was {self.affected_user_count}")
