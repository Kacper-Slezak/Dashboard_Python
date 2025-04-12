"""
Moduł zawierający serwisy do pobierania danych zdrowotnych z Google Fit API.
Ten moduł dostarcza kompleksową obsługę pobierania różnego rodzaju danych zdrowotnych
z Google Fit, w tym dane o krokach, śnie, tętnie i aktywności fizycznej.
"""

from datetime import datetime
from typing import List, Dict, Any
from googleapiclient.discovery import build
import pandas as pd

from app.models.health import Sleep, HeartRate, Activity
from database.db_setup import SessionLocal
from config.google_auth import google_fit_credentials


class GoogleFitServices:
    """
    Klasa odpowiedzialna za pobieranie danych zdrowotnych z Google Fit API.

    Zapewnia metody do interakcji z Google Fit API i pobierania różnych
    kategorii danych zdrowotnych, takich jak kroki, sen, tętno i aktywność.
    """

    def __init__(self):
        """
        Inicjalizuje serwis Google Fit z odpowiednimi uprawnieniami.
        """
        self.google_fit_credentials = google_fit_credentials()
        self.service = build('fitness', 'v1', credentials=self.google_fit_credentials)

    def get_steps_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Pobiera liczbę kroków z określonego przedziału czasowego.

        Args:
            start_date: Data początkowa zakresu.
            end_date: Data końcowa zakresu.

        Returns:
            Lista słowników zawierających datę i liczbę kroków dla każdego dnia.
        """
        start_time = int(start_date.timestamp() * 1000)
        end_time = int(end_date.timestamp() * 1000)

        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.step_count.delta",
                "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
            }],
            "bucketByTime": {"durationMillis": 86400000},  # 24 godziny w milisekundach
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }

        response = self.service.users().dataset().aggregate(userId='me', body=body).execute()
        return self._parse_steps_response(response)

    def _parse_steps_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parsuje odpowiedź z API Google Fit dotyczącą kroków.

        Args:
            response: Surowa odpowiedź z API Google Fit.

        Returns:
            Lista słowników z datą i liczbą kroków.
        """
        steps_data = []
        for bucket in response.get("bucket", []):
            start_time_millis = int(bucket.get("startTimeMillis", 0))
            date = datetime.fromtimestamp(start_time_millis / 1000)

            # Pobieramy dane o krokach
            steps = 0
            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    steps += point.get("value", [{}])[0].get("intVal", 0)

            steps_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "steps": steps
            })

        return steps_data

    def get_heart_rate_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Pobiera dane o tętnie z określonego przedziału czasowego.

        Args:
            start_date: Data początkowa zakresu.
            end_date: Data końcowa zakresu.

        Returns:
            Lista słowników zawierających datę i pomiary tętna.
        """
        start_time = int(start_date.timestamp() * 1000)
        end_time = int(end_date.timestamp() * 1000)

        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.heart_rate.bpm",
                "dataSourceId": "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm"
            }],
            "bucketByTime": {"durationMillis": 86400000},  # 24 godziny w milisekundach
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }

        response = self.service.users().dataset().aggregate(userId='me', body=body).execute()
        return self._parse_heart_rate_response(response)

    def _parse_heart_rate_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parsuje odpowiedź z API Google Fit dotyczącą tętna.

        Args:
            response: Surowa odpowiedź z API Google Fit.

        Returns:
            Lista słowników z datą, średnim, minimalnym i maksymalnym tętnem.
        """
        heart_rate_data = []

        for bucket in response.get("bucket", []):
            start_time_millis = int(bucket.get("startTimeMillis", 0))
            date = datetime.fromtimestamp(start_time_millis / 1000)

            hr_values = []

            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    for value in point.get("value", []):
                        if "fpVal" in value:
                            hr_values.append(value.get("fpVal"))

            if hr_values:
                heart_rate_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "avg_bpm": round(sum(hr_values) / len(hr_values), 1),
                    "min_bpm": min(hr_values),
                    "max_bpm": max(hr_values),
                    "readings_count": len(hr_values)
                })

        return heart_rate_data

    def get_sleep_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Pobiera dane o śnie z określonego przedziału czasowego.

        Args:
            start_date: Data początkowa zakresu.
            end_date: Data końcowa zakresu.

        Returns:
            Lista słowników zawierających szczegółowe dane o śnie dla każdego dnia.
        """
        start_time = int(start_date.timestamp() * 1000)
        end_time = int(end_date.timestamp() * 1000)

        body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.sleep.segment",
            }],
            "bucketByTime": {"durationMillis": 86400000},  # 24 godziny w milisekundach
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }
        response = self.service.users().dataset().aggregate(userId='me', body=body).execute()
        return self._parse_sleep(response)

    def _parse_sleep(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parsuje odpowiedzi z Google Fit API dotyczące snu.

        Args:
            response: Surowa odpowiedź z API Google Fit.

        Returns:
            Lista słowników z danymi o śnie, zawierającymi informacje o 
            długości i jakości snu dla każdej nocy.
        """
        sleep_data = []

        sleep_stages = {
            1: "awake",
            2: "light",
            3: "deep",
            4: "rem"
        }

        for bucket in response.get("bucket", []):
            date_millis = int(bucket.get("startTimeMillis", 0))
            date = datetime.fromtimestamp(date_millis / 1000)

            sleep_segments = []

            for dataset in bucket.get("dataset", []):
                for point in dataset.get("point", []):
                    start_time_nanos = point.get("startTimeNanos", 0)
                    end_time_nanos = point.get("endTimeNanos", 0)

                    start_time = datetime.fromtimestamp(start_time_nanos / 1e9)
                    end_time = datetime.fromtimestamp(end_time_nanos / 1e9)

                    duration = (end_time - start_time).total_seconds() / 60
                    for value in point.get("value", []):
                        if "intVal" in value:
                            stage = sleep_stages.get(value.get("intVal"), "unknown")
                            sleep_segments.append({
                                "start_time": start_time,
                                "end_time": end_time,
                                "duration": duration,
                                "stage": stage
                            })
            if sleep_segments:
                # Obliczamy statystyki
                total_minutes = sum(segment["duration"] for segment in sleep_segments)
                light_minutes = sum(segment["duration"] for segment in sleep_segments if segment["stage"] == "light")
                deep_minutes = sum(segment["duration"] for segment in sleep_segments if segment["stage"] == "deep")
                rem_minutes = sum(segment["duration"] for segment in sleep_segments if segment["stage"] == "rem")
                awake_minutes = sum(segment["duration"] for segment in sleep_segments if segment["stage"] == "awake")

                # Znajdujemy najwcześniejszy i najpóźniejszy czas
                min_time = min(segment["start_time"] for segment in sleep_segments)
                max_time = max(segment["end_time"] for segment in sleep_segments)

                sleep_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "start_time": min_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": max_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_minutes": total_minutes,
                    "light_minutes": light_minutes,
                    "deep_minutes": deep_minutes,
                    "rem_minutes": rem_minutes,
                    "awake_minutes": awake_minutes,
                    "efficiency": (total_minutes - awake_minutes) / total_minutes if total_minutes > 0 else 0
                })

        return sleep_data

    def get_activity_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Pobiera dane o aktywnościach fizycznych z określonego przedziału czasowego.

        Args:
            start_date: Data początkowa zakresu.
            end_date: Data końcowa zakresu.

        Returns:
            Lista słowników zawierających dane o aktywnościach dla każdego dnia,
            w tym kalorie, czas aktywności i przebyty dystans.
        """
        start_time = int(start_date.timestamp() * 1000)
        end_time = int(end_date.timestamp() * 1000)

        body = {
            "aggregateBy": [
                {
                    "dataTypeName": "com.google.calories.expended",
                    "dataSourceId": "derived:com.google.calories.expended:com.google.android.gms:merge_calories_expended"
                },
                {
                    "dataTypeName": "com.google.active_minutes",
                    "dataSourceId": "derived:com.google.active_minutes:com.google.android.gms:merge_active_minutes"
                },
                {
                    "dataTypeName": "com.google.distance.delta",
                    "dataSourceId": "derived:com.google.distance.delta:com.google.android.gms:merge_distance_delta"
                }
            ],
            "bucketByTime": {"durationMillis": 86400000},  # 24 godziny w milisekundach
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }

        response = self.service.users().dataset().aggregate(userId="me", body=body).execute()
        return self._parse_activity_response(response)

    def _parse_activity_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parsuje odpowiedź z API Google Fit dotyczącą aktywności.

        Args:
            response: Surowa odpowiedź z API Google Fit.

        Returns:
            Lista słowników z danymi o aktywnościach.
        """
        activity_data = []

        for bucket in response.get("bucket", []):
            start_time_millis = int(bucket.get("startTimeMillis"))
            date = datetime.fromtimestamp(start_time_millis / 1000)

            # Inicjalizacja wartości dla danego dnia
            calories = 0
            active_minutes = 0
            distance = 0

            for dataset in bucket.get("dataset", []):
                data_type = dataset.get("dataSourceId", "")

                for point in dataset.get("point", []):
                    for value in point.get("value", []):
                        if "calories" in data_type and "fpVal" in value:
                            calories += value.get("fpVal")
                        elif "active_minutes" in data_type and "intVal" in value:
                            active_minutes += value.get("intVal")
                        elif "distance" in data_type and "fpVal" in value:
                            distance += value.get("fpVal") / 1000  # konwersja m -> km

            activity_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "calories": round(calories, 2),
                "active_minutes": active_minutes,
                "distance": round(distance, 2)
            })

        return activity_data

    def get_all_health_data(self, start_date: datetime, end_date: datetime) -> Dict[str, pd.DataFrame]:
        """
        Pobiera wszystkie dane zdrowotne i zwraca je jako słownik DataFrames.

        Ta metoda agreguje dane z wszystkich dostępnych źródeł zdrowotnych
        i konwertuje je do formatu DataFrame dla łatwiejszej analizy.

        Args:
            start_date: Data początkowa zakresu.
            end_date: Data końcowa zakresu.

        Returns:
            Słownik z DataFrames dla każdego typu danych:
            - steps: DataFrame z danymi o krokach
            - heart_rate: DataFrame z danymi o tętnie
            - sleep: DataFrame z danymi o śnie
            - activity: DataFrame z danymi o aktywności
        """
        steps_data = self.get_steps_data(start_date, end_date)
        heart_rate_data = self.get_heart_rate_data(start_date, end_date)
        sleep_data = self.get_sleep_data(start_date, end_date)
        activity_data = self.get_activity_data(start_date, end_date)

        # Konwersja na DataFrames
        steps_df = pd.DataFrame(steps_data)
        heart_rate_df = pd.DataFrame(heart_rate_data)
        sleep_df = pd.DataFrame(sleep_data)
        activity_df = pd.DataFrame(activity_data)

        # Konwersja kolumny date na datetime
        if not steps_df.empty:
            steps_df['date'] = pd.to_datetime(steps_df['date'])
        if not heart_rate_df.empty:
            heart_rate_df['date'] = pd.to_datetime(heart_rate_df['date'])
        if not sleep_df.empty:
            sleep_df['date'] = pd.to_datetime(sleep_df['date'])
        if not activity_df.empty:
            activity_df['date'] = pd.to_datetime(activity_df['date'])

        return {
            'steps': steps_df,
            'heart_rate': heart_rate_df,
            'sleep': sleep_df,
            'activity': activity_df
        }