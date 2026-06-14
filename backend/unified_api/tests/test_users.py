"""Tests for user management endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_users_as_admin(client: AsyncClient, auth_headers: dict, admin_user):
    response = await client.get("/users", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_create_user_as_admin(client: AsyncClient, auth_headers: dict):
    response = await client.post(
        "/users",
        headers=auth_headers,
        json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "newpass123",
            "role": "viewer",
        },
    )
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["username"] == "newuser"


@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, auth_headers: dict, admin_user):
    response = await client.get(f"/users/{admin_user.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == admin_user.id


@pytest.mark.asyncio
async def test_update_user_role(client: AsyncClient, auth_headers: dict):
    # Create user first
    create_resp = await client.post(
        "/users",
        headers=auth_headers,
        json={
            "username": "roletest",
            "email": "roletest@test.com",
            "password": "test1234",
            "role": "viewer",
        },
    )
    assert create_resp.status_code == 201, f"Failed to create user: {create_resp.text}"
    user_id = create_resp.json()["id"]

    # Update role
    response = await client.put(
        f"/users/{user_id}/role?role=ml_engineer",
        headers=auth_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, auth_headers: dict):
    # Create user
    create_resp = await client.post(
        "/users",
        headers=auth_headers,
        json={
            "username": "deleteuser",
            "email": "delete@test.com",
            "password": "test1234",
            "role": "viewer",
        },
    )
    assert create_resp.status_code == 201, f"Failed to create user: {create_resp.text}"
    user_id = create_resp.json()["id"]

    # Delete
    response = await client.delete(f"/users/{user_id}", headers=auth_headers)
    assert response.status_code in (200, 204)
