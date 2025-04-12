import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json
from unittest.mock import patch, MagicMock

from main import app
from app.services.health import GoogleFitServices

client = TestClient(app)


@pytest.fixture
def mock_google_fit_services():
    with patch('app.api.health.GoogleFitServices') as mock:
        service_mock = MagicMock()
        mock.return_value = service_mock
        yield service_mock


def test_get_steps_endpoint(mock_google_fit_services):
    # Mock data
    mock_steps_data = [
        {"date": "2025-04-05", "steps": 8500},
        {"date": "2025-04-06", "steps": 10200}
    ]
    mock_google_fit_services.get_steps_data.return_value = mock_steps_data

    # Test endpoint
    response = client.get("/api/health/steps")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"data": mock_steps_data}

    # Verify mock
    mock_google_fit_services.get_steps_data.assert_called_once()


def test_get_sleep_endpoint(mock_google_fit_services):
    # Mock data
    mock_sleep_data = [
        {
            "date": "2025-04-05",
            "start_time": "2025-04-05 22:30:00",
            "end_time": "2025-04-06 06:45:00",
            "total_minutes": 495,
            "light_minutes": 240,
            "deep_minutes": 120,
            "rem_minutes": 100,
            "awake_minutes": 35,
            "efficiency": 0.93
        }
    ]
    mock_google_fit_services.get_sleep_data.return_value = mock_sleep_data

    # Test endpoint
    response = client.get("/api/health/sleep")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"data": mock_sleep_data}

    # Verify mock
    mock_google_fit_services.get_sleep_data.assert_called_once()


def test_get_heart_rate_endpoint(mock_google_fit_services):
    # Mock data
    mock_heart_rate_data = [
        {
            "date": "2025-04-05",
            "avg_bpm": 72.5,
            "min_bpm": 58,
            "max_bpm": 120,
            "readings_count": 24
        }
    ]
    mock_google_fit_services.get_heart_rate_data.return_value = mock_heart_rate_data

    # Test endpoint
    response = client.get("/api/health/heart-rate")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"data": mock_heart_rate_data}

    # Verify mock
    mock_google_fit_services.get_heart_rate_data.assert_called_once()


def test_get_all_health_data_endpoint(mock_google_fit_services):
    # Mock service method to return pandas DataFrames
    import pandas as pd

    steps_df = pd.DataFrame([{"date": pd.Timestamp("2025-04-05"), "steps": 8500}])
    heart_rate_df = pd.DataFrame([{"date": pd.Timestamp("2025-04-05"), "avg_bpm": 72.5}])
    sleep_df = pd.DataFrame([{"date": pd.Timestamp("2025-04-05"), "total_minutes": 495}])
    activity_df = pd.DataFrame([{"date": pd.Timestamp("2025-04-05"), "calories": 1800}])

    mock_google_fit_services.get_all_health_data.return_value = {
        "steps": steps_df,
        "heart_rate": heart_rate_df,
        "sleep": sleep_df,
        "activity": activity_df
    }

    # Test endpoint
    response = client.get("/api/health/all")

    # Assert
    assert response.status_code == 200
    data = response.json().get("data", {})
    assert "steps" in data
    assert "heart_rate" in data
    assert "sleep" in data
    assert "activity" in data

    # Verify mock
    mock_google_fit_services.get_all_health_data.assert_called_once()