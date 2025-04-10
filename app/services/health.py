from datetime import datetime
from app.models.health import Sleep, HeartRate, Activity
from database.db_setup import SessionLocal
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pandas as pd
from config.google_auth import google_fit_credentials
db = SessionLocal()

class GoogleFitServices:
    def __init__(self):
        self.google_fit_credentials = google_fit_credentials
        self.service = build('health', 'v1', credentials=self.google_fit_credentials)

    def get_steps_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
               Pobiera liczbę kroków z określonego przedziału czasowego

               Args:
                   start_date: Data początkowa
                   end_date: Data końcowa

               Returns:
                   Lista słowników z datą i liczbą kroków
               """
        start_time = int(start_date.timestamp() * 1000)
        end_time = int(end_date.timestamp() * 1000)

        body = {
            "aggregateBy": [{
                "dataName": "com.google.step_count.delta",
                "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }

        response = self.service.users().dataset().aggregate(userID ='me', body=body).execute()
        return self._parse_steps_response(response)

    def _parse_steps_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
               Parsuje odpowiedź z API Google Fit dotyczącą kroków

               Args:
                   response: Odpowiedź z API Google Fit

               Returns:
                   Lista słowników z datą i liczbą kroków
        """
        steps_data = []
        for bucket in response.get("bucket", []):
            start_time_millis = int(bucket["startTimeMillis"])
            date = datetime.fromtimestamp(start_time_millis / 1000)

            #pobieramy dane o krokach

            steps = 0
            for dataset in bucket.get["dataset", []]:
                for point in dataset.get["points", []]:
                    steps += point.get("steps", [{}])[0].get("intVal", 0)

            steps_data.append({
                "date": date.strftime("%m/%d/%Y"),
                "steps": steps
            })

            return steps_data

    def get_sleep_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Pobiera dane o śnie z okreśłonego przedziału czasowego

        Args:
            start_date:Początkowa data
            end_date: Końcowa data
        Returns:
            Lista słowników z danymi o śnie
        """
        start_time = int(start_date.timestamp() * 1000)
        end_time = int(end_date.timestamp() * 1000)

        body = {
            "aggregateBy": [{
                "dataName": "com.google.sleep.segment",
            }],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time,
            "endTimeMillis": end_time
        }
        response = self.service.users().dataset().aggregate(userID ='me', body=body).execute()
        return self._parse_sleep(response)

    def _parse_sleep(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parsuje odpowiedzi z google fit API dotyczace snu
        :param response: Odpowiedzi z google fit API dotyczace snu
        :return: Lista słowników z danymi o śnie
        """
        sleep_data = []

        sleep_stages = {
            1: "awake",
            2: "light",
            3: "deep",
            4: "rem"
        }

        for bucket in response.get("bucket", []):
            date_millis = int(bucket["startTimeMillis"])
            date = datetime.fromtimestamp(date_millis / 1000)

            sleep_segments = []

            for dataset in bucket.get["dataset", []]:
                for point in dataset.get["points", []]:
                    start_time_nanos = point.get("startTimeNanos", 0)
                    end_time_nanos = point.get("endTimeNanos", 0)

                    start_time = datetime.fromtimestamp(start_time_nanos / 1e9)
                    end_time = datetime.fromtimestamp(end_time_nanos / 1e9)

                    duration = (end_time - start_time).total_seconds() / 60
                    for value in sleep_stages.values():
                        if "intVal" in value:
                            sleep_stages = sleep_stages.get(value.get("intVal"), "unknown")
                            sleep_segments.append({
                                "start_time": start_time,
                                "end_time": end_time,
                                "duration": duration,
                                "stage": sleep_stages
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