import pytest


class TestFundAPI:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_fund_list_endpoint(self, client):
        response = client.get("/api/v1/funds")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "funds" in data
        assert isinstance(data["funds"], list)

    def test_fund_list_with_pagination(self, client):
        response = client.get("/api/v1/funds?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["funds"], list)

    def test_fund_list_invalid_skip(self, client):
        response = client.get("/api/v1/funds?skip=-1")
        assert response.status_code == 422

    def test_fund_list_invalid_limit(self, client):
        response = client.get("/api/v1/funds?limit=0")
        assert response.status_code == 422

    def test_fund_detail_not_found(self, client):
        response = client.get("/api/v1/funds/INVALID_CODE")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "FUND_NOT_FOUND"

    def test_fund_holdings_not_found(self, client):
        response = client.get("/api/v1/funds/INVALID_CODE/holdings")
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "FUND_NOT_FOUND"

    def test_trigger_update_invalid_type(self, client):
        response = client.post("/api/v1/funds/update?update_type=invalid")
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_PARAMETER"

    def test_trigger_update_valid_type(self, client):
        types = ["all", "funds", "nav", "holdings"]
        for update_type in types:
            response = client.post(f"/api/v1/funds/update?update_type={update_type}")
            assert response.status_code == 200
            data = response.json()
            assert "success" in data

    def test_error_response_format(self, client):
        response = client.get("/api/v1/funds/NOT_EXISTS")
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "details" in data["error"]

    def test_openapi_docs(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
