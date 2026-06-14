"""Tests for leaderboard and metrics endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_leaderboard_overall(client: AsyncClient, auth_headers: dict):
    response = await client.get("/leaderboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Even with no data, should return an empty list, not error
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_leaderboard_by_task(client: AsyncClient, auth_headers: dict):
    for task in ["credit", "disease", "handwriting"]:
        response = await client.get(
            f"/leaderboard?task_type={task}", headers=auth_headers
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_leaderboard_views(client: AsyncClient, auth_headers: dict):
    for view in ["overall", "fastest", "most_accurate", "lowest_resource"]:
        response = await client.get(
            f"/leaderboard?view={view}", headers=auth_headers
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_analytics_overview(client: AsyncClient, auth_headers: dict):
    response = await client.get("/analytics/overview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_experiments" in data


@pytest.mark.asyncio
async def test_analytics_task_credit(client: AsyncClient, auth_headers: dict):
    response = await client.get("/analytics/task/credit", headers=auth_headers)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
