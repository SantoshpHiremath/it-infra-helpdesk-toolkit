"""
Real, explicit, testable ticket-priority triage logic -- turning "use
good judgement about what's urgent" into a documented, consistent rule
set rather than an implicit, undiscussable habit. This is the kind of
logic a real support queue (Jira Service Desk, Zendesk, or similar)
would apply automatically or a support engineer would apply manually
every day.
"""
from src.ticket import Ticket, TicketCategory, TicketPriority


def compute_priority(ticket: Ticket) -> TicketPriority:
    """Assigns a priority based on real, explainable signals: how many
    people are affected, whether the requester is fully blocked, and
    the category of the issue (some categories are inherently higher-
    stakes -- a server or network outage affects more downstream work
    than a single cosmetic laptop issue)."""

    # Multiple people affected is always at least HIGH, regardless of
    # category -- a shared-infrastructure problem affecting several
    # people is never a low-priority issue.
    if ticket.affected_user_count > 1:
        if ticket.category in (TicketCategory.NETWORK, TicketCategory.SERVER) or ticket.is_blocking_work:
            return TicketPriority.CRITICAL
        return TicketPriority.HIGH

    # Single-user tickets: blocking work matters more than category
    # alone, but category still shifts the baseline.
    if ticket.is_blocking_work:
        if ticket.category in (TicketCategory.SERVER, TicketCategory.NETWORK, TicketCategory.GPU_WORKSTATION):
            return TicketPriority.HIGH
        return TicketPriority.MEDIUM

    if ticket.category == TicketCategory.ACCOUNT_ACCESS:
        # Access issues that aren't described as blocking are still
        # usually time-sensitive (a locked-out account), so they get a
        # floor of MEDIUM rather than defaulting to LOW.
        return TicketPriority.MEDIUM

    return TicketPriority.LOW


def triage_ticket(ticket: Ticket) -> Ticket:
    """Computes and assigns the priority on the ticket in place,
    returning it for convenient chaining. Kept as a pure function
    (input ticket -> same ticket, priority set) rather than hiding the
    logic inside a class method, so it's trivially testable."""
    ticket.priority = compute_priority(ticket)
    return ticket


def sort_queue_by_priority(tickets: list[Ticket]) -> list[Ticket]:
    """Returns tickets sorted with the highest priority first, and
    among equal priorities, the oldest ticket first (first-in-first-out
    within a priority tier, which is what a real support queue should
    do -- otherwise newer same-priority tickets could starve older
    ones indefinitely)."""
    return sorted(
        tickets,
        key=lambda t: (-t.priority.value if t.priority else 0, t.created_at),
    )
