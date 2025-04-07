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

