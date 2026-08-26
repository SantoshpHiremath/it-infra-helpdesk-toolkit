from datetime import datetime, timedelta

from src.ticket import Ticket, TicketCategory, TicketPriority
from src.triage import compute_priority, triage_ticket, sort_queue_by_priority


def make_ticket(**overrides):
    defaults = dict(
        ticket_id="IT-1",
        requester="alice",
        category=TicketCategory.LAPTOP,
        description="issue",
        created_at=datetime(2026, 1, 1),
    )
    defaults.update(overrides)
    return Ticket(**defaults)


class TestComputePriority:
    def test_network_outage_affecting_multiple_people_is_critical(self):
        ticket = make_ticket(category=TicketCategory.NETWORK, affected_user_count=5)
        assert compute_priority(ticket) == TicketPriority.CRITICAL

    def test_server_outage_affecting_multiple_people_is_critical(self):
        ticket = make_ticket(category=TicketCategory.SERVER, affected_user_count=3)
        assert compute_priority(ticket) == TicketPriority.CRITICAL

    def test_multi_user_blocking_issue_of_any_category_is_critical(self):
        ticket = make_ticket(category=TicketCategory.AI_TOOLING, affected_user_count=4, is_blocking_work=True)
        assert compute_priority(ticket) == TicketPriority.CRITICAL

    def test_multi_user_non_blocking_non_infra_issue_is_high_not_critical(self):
        ticket = make_ticket(category=TicketCategory.LAPTOP, affected_user_count=2, is_blocking_work=False)
        assert compute_priority(ticket) == TicketPriority.HIGH

    def test_single_user_blocked_on_server_is_high(self):
        ticket = make_ticket(category=TicketCategory.SERVER, affected_user_count=1, is_blocking_work=True)
        assert compute_priority(ticket) == TicketPriority.HIGH

    def test_single_user_blocked_on_laptop_is_medium_not_high(self):
        ticket = make_ticket(category=TicketCategory.LAPTOP, affected_user_count=1, is_blocking_work=True)
        assert compute_priority(ticket) == TicketPriority.MEDIUM

    def test_account_access_issue_has_a_medium_floor_even_if_not_marked_blocking(self):
        ticket = make_ticket(category=TicketCategory.ACCOUNT_ACCESS, is_blocking_work=False)
        assert compute_priority(ticket) == TicketPriority.MEDIUM

    def test_single_user_non_blocking_cosmetic_issue_is_low(self):
        ticket = make_ticket(category=TicketCategory.LAPTOP, is_blocking_work=False)
        assert compute_priority(ticket) == TicketPriority.LOW

    def test_gpu_workstation_single_user_blocking_is_high(self):
        ticket = make_ticket(category=TicketCategory.GPU_WORKSTATION, is_blocking_work=True)
        assert compute_priority(ticket) == TicketPriority.HIGH


class TestTriageTicket:
    def test_assigns_priority_on_the_ticket_object(self):
        ticket = make_ticket(category=TicketCategory.NETWORK, affected_user_count=10)
        result = triage_ticket(ticket)
        assert result.priority == TicketPriority.CRITICAL
        assert ticket.priority == TicketPriority.CRITICAL  # mutated in place

    def test_returns_the_same_ticket_object_for_chaining(self):
        ticket = make_ticket()
        result = triage_ticket(ticket)
        assert result is ticket


class TestSortQueueByPriority:
    def test_higher_priority_tickets_come_first(self):
        low = triage_ticket(make_ticket(ticket_id="IT-1", category=TicketCategory.LAPTOP))
        critical = triage_ticket(make_ticket(ticket_id="IT-2", category=TicketCategory.NETWORK, affected_user_count=5))
        sorted_queue = sort_queue_by_priority([low, critical])
        assert sorted_queue[0].ticket_id == "IT-2"
        assert sorted_queue[1].ticket_id == "IT-1"

    def test_equal_priority_tickets_are_ordered_oldest_first(self):
        older = triage_ticket(make_ticket(ticket_id="IT-1", category=TicketCategory.LAPTOP,
                                           created_at=datetime(2026, 1, 1)))
        newer = triage_ticket(make_ticket(ticket_id="IT-2", category=TicketCategory.LAPTOP,
                                           created_at=datetime(2026, 1, 2)))
        sorted_queue = sort_queue_by_priority([newer, older])
        assert sorted_queue[0].ticket_id == "IT-1"
        assert sorted_queue[1].ticket_id == "IT-2"

    def test_empty_queue_returns_empty_list(self):
        assert sort_queue_by_priority([]) == []

    def test_does_not_mutate_the_input_list_order(self):
        low = triage_ticket(make_ticket(ticket_id="IT-1", category=TicketCategory.LAPTOP))
        critical = triage_ticket(make_ticket(ticket_id="IT-2", category=TicketCategory.NETWORK, affected_user_count=5))
        original_order = [low, critical]
        sort_queue_by_priority(original_order)
        assert original_order == [low, critical]  # sorted() doesn't mutate in place
