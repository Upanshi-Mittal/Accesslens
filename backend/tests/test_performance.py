


import pytest
import time
import asyncio
import psutil
import os
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_api_response_time():


    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        endpoints = [
            ("/health", "GET"),
            ("/", "GET"),
            ("/api/v1/engines", "GET"),
        ]

        for endpoint, method in endpoints:
            start_time = time.time()

            if method == "GET":
                response = await ac.get(endpoint)
            else:
                response = await ac.post(endpoint)

            elapsed = time.time() - start_time

            assert response.status_code == 200
            assert elapsed < 0.5

@pytest.mark.asyncio
async def test_audit_startup_time():


    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        start_time = time.time()

        response = await ac.post(
            "/api/v1/audit",
            json={"url": "https://example.com"}
        )

        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 3.0

@pytest.mark.asyncio
async def test_memory_usage():


    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        for i in range(5):
            response = await ac.post(
                "/api/v1/audit",
                json={"url": f"https://example.com/page{i}"}
            )
            assert response.status_code == 200


        current_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - initial_memory


        assert memory_increase < 100

@pytest.mark.asyncio
async def test_concurrent_audit_performance():


    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        start_time = time.time()

        tasks = []
        for i in range(10):
            task = ac.post(
                "/api/v1/audit",
                json={"url": f"https://example.com/page{i}"}
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        elapsed = time.time() - start_time


        for response in responses:
            assert response.status_code == 200


        assert elapsed < 10.0

@pytest.mark.asyncio
async def test_cpu_usage_during_analysis():


    import psutil
    import threading

    cpu_samples = []

    def sample_cpu():
        for _ in range(10):
            cpu_samples.append(psutil.cpu_percent(interval=0.5))


    sampler = threading.Thread(target=sample_cpu)
    sampler.start()


    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for _ in range(5):
            await ac.get("/api/v1/engines")
            await asyncio.sleep(0.1)

    sampler.join()


    avg_cpu = sum(cpu_samples) / len(cpu_samples)
    assert avg_cpu < 50