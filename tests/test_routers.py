import pytest
from fastapi import status


class TestFundEndpoints:
    
    def test_get_fund_list_empty(self, client):
        response = client.get("/api/v1/funds")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["funds"] == []
    
    def test_get_fund_list_with_data(self, client, sample_fund):
        response = client.get("/api/v1/funds")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["funds"]) == 1
        assert data["funds"][0]["fund_code"] == "000001"
        assert data["funds"][0]["fund_name"] == "测试基金"
    
    def test_get_fund_list_with_pagination(self, client, sample_fund):
        response = client.get("/api/v1/funds?skip=0&limit=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["funds"]) == 1
    
    def test_get_fund_list_with_type_filter(self, client, sample_fund):
        response = client.get("/api/v1/funds?fund_type=QDII")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        
        response = client.get("/api/v1/funds?fund_type=UNKNOWN")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
    
    def test_get_fund_detail_success(self, client, sample_fund):
        response = client.get(f"/api/v1/funds/{sample_fund.fund_code}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["fund"]["fund_code"] == "000001"
        assert data["fund"]["fund_name"] == "测试基金"
        assert "holdings" in data
    
    def test_get_fund_detail_not_found(self, client):
        response = client.get("/api/v1/funds/999999")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error_code"] == "FUND_NOT_FOUND"
    
    def test_get_fund_holdings_success(self, client, sample_fund, sample_holding):
        response = client.get(f"/api/v1/funds/{sample_fund.fund_code}/holdings")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["stock_code"] == "600001"
        assert data[0]["stock_name"] == "测试股票"
    
    def test_get_fund_holdings_not_found(self, client):
        response = client.get("/api/v1/funds/999999/holdings")
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "docs" in data
    
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
