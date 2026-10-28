"""Retired movie routes are absent; speech routes remain protected."""
import httpx
import pytest
from fastapi import FastAPI
from app.api import tutor


@pytest.mark.asyncio
@pytest.mark.parametrize('suffix',['','/status','/content'])
async def test_retired_movie_routes_have_no_handler(suffix):
    app=FastAPI();app.include_router(tutor.router)
    assert not any(path.startswith('/lesson/video') for path in app.openapi()['paths'])
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
        response=await client.post('/lesson/video'+suffix,json={})
        assert response.status_code==404
        assert (await client.post('/lesson/narration',json={})).status_code==401
