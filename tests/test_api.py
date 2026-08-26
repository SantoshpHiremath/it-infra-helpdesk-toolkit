import pytest

from src.api import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    # Reset in-memory ticket store between tests so tests don't leak state.
    import src.api as api_module
    api_module._TICKETS.clear()
    api_module._NEXT_ID[0] = 1
    with app.test_client() as c:
        yield c


class TestHealthEndpoints:
    def test_healthz_returns_ok(self, client):
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.get_json()["status"] == "ok"

    def test_readyz_returns_ready_with_ticket_count(self, client):
        response = client.get("/readyz")
        assert response.status_code == 200
        body = response.get_json()
        assert body["status"] == "ready"
        assert body["ticket_count"] == 0

    def test_infra_disk_returns_a_real_check_result(self, client):
        response = client.get("/infra/disk")
        assert response.status_code == 200
        body = response.get_json()
        assert body["status"] in ("ok", "warning", "critical")
        assert body["value"] is not None


class TestTicketEndpoints:
    def test_create_ticket_returns_201_with_triaged_priority(self, client):
        response = client.post("/tickets", json={
            "requester": "bob",
            "category": "network",
            "description": "Office wifi down",
            "affected_user_count": 8,
            "is_blocking_work": True,
        })
        assert response.status_code == 201
        body = response.get_json()
        assert body["ticket_id"] == "IT-1"
        assert body["priority"] == "CRITICAL"

    def test_create_ticket_with_invalid_category_returns_400(self, client):
        response = client.post("/tickets", json={"category": "not_a_real_category"})
        assert response.status_code == 400

    def test_create_ticket_with_missing_category_returns_400(self, client):
        response = client.post("/tickets", json={"requester": "bob"})
        assert response.status_code == 400

    def test_get_ticket_returns_the_created_ticket(self, client):
        create_response = client.post("/tickets", json={"category": "laptop", "requester": "carol"})
        ticket_id = create_response.get_json()["ticket_id"]

        get_response = client.get(f"/tickets/{ticket_id}")
        assert get_response.status_code == 200
        assert get_response.get_json()["requester"] == "carol"

    def test_get_nonexistent_ticket_returns_404(self, client):
        response = client.get("/tickets/IT-999")
        assert response.status_code == 404

    def test_list_tickets_returns_all_created_tickets(self, client):
        client.post("/tickets", json={"category": "laptop"})
        client.post("/tickets", json={"category": "network", "affected_user_count": 3})

        response = client.get("/tickets")
        assert response.status_code == 200
        assert len(response.get_json()) == 2

    def test_default_affected_user_count_is_one_when_not_provided(self, client):
        response = client.post("/tickets", json={"category": "laptop"})
        body = response.get_json()
        assert body["affected_user_count"] == 1
