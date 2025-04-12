import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pandas as pd

from app.services.health import GoogleFitServices


@pytest.fixture
def mock_google_fit_service():
    with patch('app.services.health.build') as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        with patch('app.services.health.google_fit_credentials') as mock_creds:
            mock_creds.return_value = MagicMock()

            service = GoogleFitServices()
            service.service = mock_service
            yield service


def test_get_steps_data(mock_google_fit_service):
    # Przygotowanie danych testowych
    mock_response = {
        "bucket": [
            {
                "startTimeMillis": "1617580800000",  # 2021-04-05
                "dataset": [
                    {
                        "point": [
                            {
                                "value": [{"intVal": 7500}]
                            }
                        ]
                    }
                ]
            },
            {
                "startTimeMillis": "1617667200000",  # 2021-04-06
                "dataset": [
                    {
                        "point": [
                            {
                                "value": [{"intVal": 9000}]
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Konfiguracja mocka
    mock_aggregate = MagicMock()
    mock_aggregate.execute.return_value = mock_response

    mock_dataset = MagicMock()
    mock_dataset.aggregate.return_value = mock_aggregate

    mock_users = MagicMock()
    mock_users.dataset.return_value = mock_dataset

    mock_google_fit_service.service.users.return_value = mock_users

    # Wywołanie testowanej metody
    start_date = datetime(2021, 4, 5)
    end_date = datetime(2021, 4, 6)
    result = mock_google_fit_service.get_steps_data(start_date, end_date)

    # Asercje
    assert len(result) == 2
    assert result[0]["date"] == "2021-04-05"
    assert result[0]["steps"] == 7500
    assert result[1]["date"] == "2021-04-06"
    assert result[1]["steps"] == 9000


def test_get_heart_rate_data(mock_google_fit_service):
    # Przygotowanie danych testowych
    mock_response = {
        "bucket": [
            {
                "startTimeMillis": "1617580800000",  # 2021-04-05
                "dataset": [
                    {
                        "point": [
                            {
                                "value": [{"fpVal": 70.0}, {"fpVal": 75.0}, {"fpVal": 80.0}]
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Konfiguracja mocka
    mock_aggregate = MagicMock()
    mock_aggregate.execute.return_value = mock_response

    mock_dataset = MagicMock()
    mock_dataset.aggregate.return_value = mock_aggregate

    mock_users = MagicMock()
    mock_users.dataset.return_value = mock_dataset

    mock_google_fit_service.service.users.return_value = mock_users

    # Wywołanie testowanej metody
    start_date = datetime(2021, 4, 5)
    end_date = datetime(2021, 4, 6)
    result = mock_google_fit_service.get_heart_rate_data(start_date, end_date)

    # Asercje
    assert len(result) == 1
    assert result[0]["date"] == "2021-04-05"
    assert result[0]["avg_bpm"] == 75.0
    assert result[0]["min_bpm"] == 70.0
    assert result[0]["max_bpm"] == 80.0
    assert result[0]["readings_count"] == 3


def test_get_sleep_data(mock_google_fit_service):
    # Przygotowanie danych testowych
    mock_response = {
        "bucket": [
            {
                "startTimeMillis": "1617580800000",  # 2021-04-05
                "dataset": [
                    {
                        "point": [
                            {
                                "startTimeNanos": "1617580800000000000",  # Przykładowy czas
                                "endTimeNanos": "1617595200000000000",  # Przykładowy czas + 4 godziny
                                "value": [{"intVal": 2}]  # Light sleep
                            },
                            {
                                "startTimeNanos": "1617595200000000000",  # Przykładowy czas + 4 godziny
                                "endTimeNanos": "1617602400000000000",  # Przykładowy czas + 6 godzin
                                "value": [{"intVal": 3}]  # Deep sleep
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Konfiguracja mocka
    mock_aggregate = MagicMock()
    mock_aggregate.execute.return_value = mock_response

    mock_dataset = MagicMock()
    mock_dataset.aggregate.return_value = mock_aggregate

    mock_users = MagicMock()
    mock_users.dataset.return_value = mock_dataset

    mock_google_fit_service.service.users.return_value = mock_users

    # Wywołanie testowanej metody
    start_date = datetime(2021, 4, 5)
    end_date = datetime(2021, 4, 6)
    result = mock_google_fit_service.get_sleep_data(start_date, end_date)

    # Asercje
    assert len(result) == 1
    assert result[0]["date"] == "2021-04-05"
    assert "total_minutes" in result[0]
    assert "light_minutes" in result[0]
    assert "deep_minutes" in result[0]
    # Głębszy test wartości będzie zależał od konkretnej implementacji parsowania