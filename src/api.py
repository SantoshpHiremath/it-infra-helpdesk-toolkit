"""
A small, real Flask API exposing the ticket triage and infra-health
logic over HTTP -- a realistic, deployable target (matching the
posting's "help project teams deploy to cloud and on-premise
infrastructure" ask), containerized and health-checked exactly like
the pattern used in the devops-cicd-monitoring project earlier in this
portfolio.
"""
from datetime import datetime

from flask import Flask, jsonify, request

from src.infra_monitor import check_disk_usage
from src.ticket import Ticket, TicketCategory, TicketStatus
from src.triage import triage_ticket

app = Flask(__name__)

_TICKETS: dict[str, Ticket] = {}
_NEXT_ID = [1]


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


@app.get("/readyz")
def readyz():
    return jsonify({"status": "ready", "ticket_count": len(_TICKETS)}), 200


@app.get("/infra/disk")
def infra_disk():
    result = check_disk_usage("/")
    return jsonify({
        "check_name": result.check_name,
        "status": result.status.value,
        "detail": result.detail,
        "value": result.value,
    }), 200


@app.post("/tickets")
def create_ticket():
    payload = request.get_json(force=True)
    try:
        category = TicketCategory(payload["category"])
    except (KeyError, ValueError):
        return jsonify({"error": "invalid or missing 'category'"}), 400

    ticket_id = f"IT-{_NEXT_ID[0]}"
    _NEXT_ID[0] += 1

    ticket = Ticket(
        ticket_id=ticket_id,
        requester=payload.get("requester", "unknown"),
        category=category,
        description=payload.get("description", ""),
        affected_user_count=payload.get("affected_user_count", 1),
        is_blocking_work=payload.get("is_blocking_work", False),
        created_at=datetime.now(),
    )
    triage_ticket(ticket)
    _TICKETS[ticket_id] = ticket

    return jsonify(_ticket_to_dict(ticket)), 201


@app.get("/tickets/<ticket_id>")
def get_ticket(ticket_id: str):
    ticket = _TICKETS.get(ticket_id)
    if ticket is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(_ticket_to_dict(ticket)), 200


@app.get("/tickets")
def list_tickets():
    return jsonify([_ticket_to_dict(t) for t in _TICKETS.values()]), 200


def _ticket_to_dict(ticket: Ticket) -> dict:
    return {
        "ticket_id": ticket.ticket_id,
        "requester": ticket.requester,
        "category": ticket.category.value,
        "description": ticket.description,
        "affected_user_count": ticket.affected_user_count,
        "is_blocking_work": ticket.is_blocking_work,
        "status": ticket.status.value,
        "priority": ticket.priority.name if ticket.priority else None,
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
