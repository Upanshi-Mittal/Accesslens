import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.middleware.rate_limit import rate_limiter

@pytest.mark.asyncio
async def test_rate_limit_headers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health", headers={"X-Test-Enforce-Rate-Limit": "true"})
        
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

@pytest.mark.asyncio
async def test_rate_limit_exceeded():
    rate_limiter.requests.clear()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        responses = []
        for i in range(310):  
            response = await ac.get("/health", headers={"X-Test-Enforce-Rate-Limit": "true"})
            responses.append(response)
            
            if response.status_code == 429:
                break
            
            await asyncio.sleep(0.01)
        
        assert any(r.status_code == 429 for r in responses)
        
        rate_limit_resp = next(r for r in responses if r.status_code == 429)
        assert "Retry-After" in rate_limit_resp.headers

@pytest.mark.asyncio
async def test_different_endpoint_limits():
    
    rate_limiter.requests.clear()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for i in range(250):
            response = await ac.get("/health", headers={"X-Test-Enforce-Rate-Limit": "true"})
            assert response.status_code == 200
            remaining = int(response.headers["X-RateLimit-Remaining"])
            assert remaining >= 0