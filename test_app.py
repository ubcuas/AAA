import pytest
from app import create_app # add this init function to app.py

@pytest.fixture
def client():

    client = create_app()

    yield client