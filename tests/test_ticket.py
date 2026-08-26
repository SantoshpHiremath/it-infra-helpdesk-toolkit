from datetime import datetime

import pytest

from src.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus


def make_ticket(**overrides):
    defaults = dict(
        ticket_id="IT-1",
        requester="alice",
        category=TicketCategory.LAPTOP,
        description="Laptop won't turn on",
    )
    defaults.update(overrides)
    return Ticket(**defaults)


class TestTicket:
    def test_default_status_is_open(self):
        ticket = make_ticket()
        assert ticket.status == TicketStatus.OPEN

    def test_default_priority_is_none_until_triaged(self):
        ticket = make_ticket()
        assert ticket.priority is None

    def test_default_affected_user_count_is_one(self):
        ticket = make_ticket()
        assert ticket.affected_user_count == 1

    def test_zero_affected_user_count_is_rejected(self):
        with pytest.raises(ValueError):
            make_ticket(affected_user_count=0)

    def test_negative_affected_user_count_is_rejected(self):
        with pytest.raises(ValueError):
            make_ticket(affected_user_count=-1)

    def test_can_construct_with_multiple_affected_users(self):
        ticket = make_ticket(affected_user_count=15)
        assert ticket.affected_user_count == 15
