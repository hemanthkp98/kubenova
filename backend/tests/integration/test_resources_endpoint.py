"""
Integration tests for GET /api/resources/* endpoints.

The kubernetes client is mocked so no real cluster connection is needed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.models.resource import PodInfo, DeploymentInfo, NodeInfo


def _pod_info(name: str = "nginx") -> PodInfo:
    return PodInfo(
        name=name, namespace="default", status="Running",
        ready="1/1", restarts=0, age="5m",
    )


def _deployment_info(name: str = "web") -> DeploymentInfo:
    return DeploymentInfo(
        name=name, namespace="default", desired=3, ready=3,
        available=3, updated=3, age="1d",
    )


def _node_info(name: str = "node-1") -> NodeInfo:
    return NodeInfo(
        name=name, status="Ready", age="10d", version="v1.30.0",
    )


@pytest.mark.asyncio
class TestResourcesEndpoints:
    """Integration tests for /api/resources/* routes."""

    async def test_list_pods_success(self, async_client) -> None:
        """GET /api/resources/pods returns a list of pod objects."""
        with patch("app.api.routes.resources.resource_fetcher") as mock:
            mock.list_pods.return_value = [_pod_info("nginx"), _pod_info("redis")]
            response = await async_client.get(
                "/api/resources/pods?cluster_context=minikube&namespace=default"
            )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "nginx"

    async def test_list_pods_missing_context_returns_422(self, async_client) -> None:
        """GET /api/resources/pods without cluster_context returns 422."""
        response = await async_client.get("/api/resources/pods")
        assert response.status_code == 422

    async def test_list_deployments_success(self, async_client) -> None:
        """GET /api/resources/deployments returns deployment list."""
        with patch("app.api.routes.resources.resource_fetcher") as mock:
            mock.list_deployments.return_value = [_deployment_info("web")]
            response = await async_client.get(
                "/api/resources/deployments?cluster_context=minikube"
            )
        assert response.status_code == 200
        assert response.json()[0]["name"] == "web"

    async def test_list_nodes_success(self, async_client) -> None:
        """GET /api/resources/nodes returns node list."""
        with patch("app.api.routes.resources.resource_fetcher") as mock:
            mock.list_nodes.return_value = [_node_info()]
            response = await async_client.get(
                "/api/resources/nodes?cluster_context=minikube"
            )
        assert response.status_code == 200
        assert response.json()[0]["status"] == "Ready"

    async def test_list_namespaces_success(self, async_client) -> None:
        """GET /api/resources/namespaces returns list of strings."""
        with patch("app.api.routes.resources.resource_fetcher") as mock:
            mock.list_namespaces.return_value = ["default", "kube-system"]
            response = await async_client.get(
                "/api/resources/namespaces?cluster_context=minikube"
            )
        assert response.status_code == 200
        assert "default" in response.json()

    async def test_list_events_success(self, async_client) -> None:
        """GET /api/resources/events returns event list."""
        with patch("app.api.routes.resources.resource_fetcher") as mock:
            from app.models.resource import EventInfo
            mock.list_events.return_value = [
                EventInfo(
                    name="ev1", namespace="default", type="Warning",
                    reason="BackOff", message="Back-off restarting failed container",
                    involved_object_kind="Pod", involved_object_name="nginx",
                )
            ]
            response = await async_client.get(
                "/api/resources/events?cluster_context=minikube"
            )
        assert response.status_code == 200
        assert response.json()[0]["type"] == "Warning"
