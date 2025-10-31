import requests
import os
import json # Dodano import json do formatowania printów
from datetime import datetime, timedelta, time
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.api_connections import ApiConnection
from database.db_setup import get_db, SessionLocal
from app.config import get_settings
from typing import Optional # <<< POPRAWKA: Dodano import Optional

settings = get_settings()

class GoogleFitServices:
    def __init__(self, user_id: int):
        self.user_id = user_id
        # Używamy nowej, niezależnej sesji, aby uniknąć problemów z zależnościami FastAPI
        self.db: Session = SessionLocal()
        self.connection = self._get_connection()
        if not self.connection or not self.connection.access_token:
             # Zamknij sesję, jeśli nie znaleziono połączenia
            self.db.close()
            raise HTTPException(status_code=404, detail="Aktywne połączenie Google Fit nie zostało znalezione dla tego użytkownika.")

    def __del__(self):
        # Upewnij się, że sesja jest zamykana, gdy obiekt jest niszczony
        if self.db:
            self.db.close()

    def _get_connection(self) -> Optional[ApiConnection]:
        """Pobiera aktywne połączenie Google Fit dla użytkownika."""
        try:
            connection = self.db.query(ApiConnection).filter(
                ApiConnection.user_id == self.user_id,
                ApiConnection.provider == "google_fit",
                ApiConnection.is_active == True
            ).first()
            return connection
        except Exception as e:
            print(f"Błąd podczas pobierania połączenia z bazy danych: {e}")
            return None


    def _refresh_token(self) -> bool:
        """Odświeża access token, jeśli jest refresh token i token wygasł."""
        if not self.connection or not self.connection.refresh_token:
            return False

        if self.connection.token_expires_at and self.connection.token_expires_at > datetime.now() + timedelta(minutes=1):
            return True

        print("Próba odświeżenia tokenu Google Fit...")
        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "refresh_token": self.connection.refresh_token,
            "grant_type": "refresh_token",
        }
        try:
            response = requests.post(token_url, data=payload)
            response.raise_for_status()
            token_data = response.json()

            self.connection.access_token = token_data["access_token"]
            if "refresh_token" in token_data:
                 self.connection.refresh_token = token_data["refresh_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.connection.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            self.connection.updated_at = datetime.now()

            self.db.commit()
            self.db.refresh(self.connection)
            print("Token Google Fit odświeżony pomyślnie.")
            return True
        except requests.RequestException as e:
            print(f"Błąd podczas odświeżania tokenu Google Fit: {e}")
            if e.response is not None and e.response.status_code in [400, 401]:
                print("Dezaktywacja połączenia Google Fit z powodu błędu odświeżania.")
                self.connection.is_active = False
                self.connection.access_token = None
                self.connection.refresh_token = None
                self.connection.token_expires_at = None
                self.db.commit()
            return False
        except Exception as e:
            print(f"Nieoczekiwany błąd podczas odświeżania tokenu: {e}")
            return False

    def _make_request(self, url: str, method: str = "POST", headers: dict = None, json_data: dict = None, params: dict = None):
        """Wykonuje żądanie do API Google Fit, obsługując odświeżanie tokenu."""
        if not self.connection or not self.connection.access_token:
            raise HTTPException(status_code=401, detail="Brak ważnego tokenu dostępu Google Fit.")

        auth_headers = {"Authorization": f"Bearer {self.connection.access_token}"}
        if headers:
            auth_headers.update(headers)

        try:
            if method.upper() == "POST":
                response = requests.post(url, headers=auth_headers, json=json_data, params=params)
            elif method.upper() == "GET":
                 response = requests.get(url, headers=auth_headers, params=params)
            else:
                 raise ValueError("Nieobsługiwana metoda HTTP")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            if e.response is not None and e.response.status_code == 401:
                print("Otrzymano błąd 401, próba odświeżenia tokenu...")
                if self._refresh_token():
                    print("Token odświeżony, ponawianie żądania...")
                    auth_headers["Authorization"] = f"Bearer {self.connection.access_token}"
                    try:
                        if method.upper() == "POST":
                            response = requests.post(url, headers=auth_headers, json=json_data, params=params)
                        elif method.upper() == "GET":
                            response = requests.get(url, headers=auth_headers, params=params)

                        response.raise_for_status()
                        return response.json()
                    except requests.exceptions.RequestException as retry_e:
                        print(f"Błąd podczas ponawiania żądania po odświeżeniu tokenu: {retry_e}")
                        raise HTTPException(status_code=retry_e.response.status_code if retry_e.response else 500,
                                            detail=f"Błąd API Google Fit po odświeżeniu tokenu: {retry_e}")
                else:
                    raise HTTPException(status_code=401, detail="Nie można odświeżyć tokenu Google Fit. Wymagana ponowna autoryzacja.")
            else:
                print(f"Błąd żądania do Google Fit API: {e}")
                raise HTTPException(status_code=e.response.status_code if e.response else 503,
                                    detail=f"Błąd komunikacji z Google Fit API: {e}")
        except Exception as e:
            print(f"Nieoczekiwany błąd podczas żądania do Google Fit API: {e}")
            raise HTTPException(status_code=500, detail="Wewnętrzny błąd serwera podczas komunikacji z Google Fit API.")


    def get_dashboard_data(self, days: int):
        """Pobiera i agreguje dane z Google Fit dla dashboardu."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)

        end_time_millis = int(end_time.timestamp() * 1000)
        start_time_millis = int(start_time.timestamp() * 1000)

        aggregate_request_body = {
            "aggregateBy": [{
                "dataTypeName": "com.google.step_count.delta",
                "dataSourceId": "derived:com.google.step_count.delta:com.google.android.gms:estimated_steps"
            }, {
                "dataTypeName": "com.google.distance.delta",
                "dataSourceId": "derived:com.google.distance.delta:com.google.android.gms:merge_distance_delta"
            },{
                 "dataTypeName": "com.google.heart_rate.bpm",
                 "dataSourceId": "derived:com.google.heart_rate.bpm:com.google.android.gms:merge_heart_rate_bpm"
            },{
                 "dataTypeName": "com.google.sleep.segment", # Usuniemy to z głównego zapytania agregacji
                 "dataSourceId": "derived:com.google.sleep.segment:com.google.android.gms:merged"
            },{
                "dataTypeName": "com.google.weight",
                "dataSourceId": "derived:com.google.weight:com.google.android.gms:merge_weight"
            }, {
                "dataTypeName": "com.google.height",
                "dataSourceId": "derived:com.google.height:com.google.android.gms:merge_height"
            }
            ],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_time_millis,
            "endTimeMillis": end_time_millis
        }
        # Usuń sleep.segment z aggregateBy, bo i tak pobieramy go osobno
        aggregate_request_body["aggregateBy"] = [
            item for item in aggregate_request_body["aggregateBy"]
            if item["dataTypeName"] != "com.google.sleep.segment"
        ]

        url = "https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate"

        try:
            response_data = self._make_request(url, method="POST", json_data=aggregate_request_body)
            # <<< DODANO PRINT DIAGNOSTYCZNY >>>
            print("\n--- DEBUG: SUROWA ODPOWIEDŹ Z AGREGACJI ---")
            print(json.dumps(response_data, indent=2))
            print("--- KONIEC SUROWEJ ODPOWIEDZI Z AGREGACJI ---\n")


            daily_stats = self._parse_daily_stats(response_data, days)
            # <<< DODANO PRINT DIAGNOSTYCZNY >>>
            print(f"--- DEBUG: Parsed Daily Stats (przed snem/wagą): {daily_stats} ---\n")
            charts_data = self._parse_charts_data(response_data, days)
            # <<< DODANO PRINT DIAGNOSTYCZNY >>>
            print(f"--- DEBUG: Parsed Charts Data (przed snem/wagą): {charts_data} ---\n")


            sleep_data = self._get_sleep_data_for_period(start_time_millis, end_time_millis)
            daily_stats.update(self._calculate_sleep_stats(sleep_data))
            charts_data["sleep"] = self._parse_sleep_chart_data(sleep_data, days, start_time)

            weight_stats = self._get_latest_weight_and_height()
            daily_stats.update(weight_stats)

            return {
                "daily_stats": daily_stats,
                "charts": charts_data
            }

        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Nieoczekiwany błąd podczas pobierania danych dashboardu: {e}")
            raise HTTPException(status_code=500, detail="Nie udało się przetworzyć danych z Google Fit.")


    def _parse_daily_stats(self, response_data, days):
        """Przetwarza zagregowane dane na statystyki ostatniego dnia."""
        stats = {
            "steps": 0, "goal_steps": 10000,
            "avg_heart_rate": 0, "resting_heart_rate": 0, "max_heart_rate": 0,
            "sleep_hours": 0, "goal_sleep_hours": 8,
            "distance": 0, "weight": 0, "bmi": 0, "weight_change": 0
        }
        last_bucket = None
        if response_data and response_data.get("bucket"):
            sorted_buckets = sorted(response_data["bucket"], key=lambda b: int(b.get("startTimeMillis", 0)), reverse=True)
            if sorted_buckets:
                last_bucket = sorted_buckets[0]

        if last_bucket:
            for dataset in last_bucket.get("dataset", []):
                data_type = dataset.get("dataSourceId", "")
                point = dataset.get("point", [])
                if point:
                    value = point[0].get("value", [])
                    if value:
                        if "step_count.delta" in data_type:
                            stats["steps"] = value[0].get("intVal", 0)
                        elif "distance.delta" in data_type:
                            stats["distance"] = round(value[0].get("fpVal", 0) / 1000, 2)
                        elif "heart_rate.bpm" in data_type:
                            if len(value) >= 3:
                                stats["avg_heart_rate"] = round(value[0].get("fpVal", 0))
                                stats["max_heart_rate"] = round(value[1].get("fpVal", 0))
                                stats["min_heart_rate"] = round(value[2].get("fpVal", 0))
                                stats["resting_heart_rate"] = stats["min_heart_rate"]

        return stats


    def _parse_charts_data(self, response_data, days):
        """Przetwarza zagregowane dane na dane do wykresów."""
        labels = []
        steps_data = []
        distance_data = []
        avg_hr_data = []
        max_hr_data = []
        data_by_date = {}

        if response_data and response_data.get("bucket"):
            for bucket in response_data["bucket"]:
                start_millis = int(bucket.get("startTimeMillis", 0))
                dt_object = datetime.fromtimestamp(start_millis / 1000)
                date_str = dt_object.strftime("%Y-%m-%d")
                daily_data = {"steps": 0, "distance": 0, "avg_hr": None, "max_hr": None}

                for dataset in bucket.get("dataset", []):
                    data_type = dataset.get("dataSourceId", "")
                    point = dataset.get("point", [])
                    if point:
                        value = point[0].get("value", [])
                        if value:
                            if "step_count.delta" in data_type:
                                daily_data["steps"] = value[0].get("intVal", 0)
                            elif "distance.delta" in data_type:
                                daily_data["distance"] = round(value[0].get("fpVal", 0) / 1000, 2)
                            elif "heart_rate.bpm" in data_type:
                                if len(value) >= 3:
                                    daily_data["avg_hr"] = round(value[0].get("fpVal", 0))
                                    daily_data["max_hr"] = round(value[1].get("fpVal", 0))
                data_by_date[date_str] = daily_data

        end_date = datetime.now().date()
        for i in range(days -1, -1, -1):
            current_date = end_date - timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            labels.append(current_date.strftime("%d-%m"))
            day_data = data_by_date.get(date_str)
            if day_data:
                steps_data.append(day_data["steps"])
                distance_data.append(day_data["distance"])
                avg_hr_data.append(day_data["avg_hr"])
                max_hr_data.append(day_data["max_hr"])
            else:
                steps_data.append(0)
                distance_data.append(0)
                avg_hr_data.append(None)
                max_hr_data.append(None)

        avg_hr_data = [hr if hr is not None else 0 for hr in avg_hr_data]
        max_hr_data = [hr if hr is not None else 0 for hr in max_hr_data]

        return {
            "activity": {"labels": labels, "steps": steps_data, "distance": distance_data},
            "heart_rate": {"labels": labels, "avg": avg_hr_data, "max": max_hr_data},
            "sleep": {"labels": [], "hours": [], "quality": []},
            "weight": {"labels": [], "values": []}
        }

    # --- Metody specyficzne dla typów danych ---

    def _get_sleep_data_for_period(self, start_time_millis: int, end_time_millis: int) -> list:
        """Pobiera surowe segmenty snu dla danego okresu."""
        # <<< POPRAWKA FORMATOWANIA DATY >>>
        start_iso = datetime.utcfromtimestamp(start_time_millis/1000).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        end_iso = datetime.utcfromtimestamp(end_time_millis/1000).strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        url = f"https://www.googleapis.com/fitness/v1/users/me/sessions?startTime={start_iso}&endTime={end_iso}&activityType=72"

        try:
            response = self._make_request(url, method="GET")
            # <<< DODANO PRINT DIAGNOSTYCZNY >>>
            print("\n--- DEBUG: SUROWA ODPOWIEDŹ Z API SNU ---")
            print(json.dumps(response, indent=2))
            print("--- KONIEC SUROWEJ ODPOWIEDZI Z API SNU ---\n")
            return response.get("session", [])
        except HTTPException as e:
            print(f"Błąd podczas pobierania sesji snu: {e.detail}")
            return []
        except Exception as e:
            print(f"Nieoczekiwany błąd podczas pobierania sesji snu: {e}")
            return []

    def _calculate_sleep_stats(self, sleep_sessions: list) -> dict:
        """Oblicza statystyki snu z ostatniej nocy."""
        stats = {"sleep_hours": 0}
        if not sleep_sessions:
            return stats
        try: # Dodano try-except na wypadek pustej listy po filtrowaniu
            latest_session = max(sleep_sessions, key=lambda s: int(s.get("endTimeMillis", 0)))
            start_millis = int(latest_session.get("startTimeMillis", 0))
            end_millis = int(latest_session.get("endTimeMillis", 0))
            if start_millis and end_millis:
                duration_millis = end_millis - start_millis
                stats["sleep_hours"] = round(duration_millis / (1000 * 60 * 60), 1)
        except ValueError: # Jeśli sleep_sessions jest puste, max() rzuci błąd
             print("Brak sesji snu do przetworzenia dla _calculate_sleep_stats.")
        return stats


    def _parse_sleep_chart_data(self, sleep_sessions: list, days: int, start_time_dt: datetime) -> dict:
        """Przetwarza sesje snu na dane do wykresu."""
        labels = []
        sleep_hours_data = []
        sleep_by_end_date = {}

        for session in sleep_sessions:
            start_millis = int(session.get("startTimeMillis", 0))
            end_millis = int(session.get("endTimeMillis", 0))
            if start_millis and end_millis:
                duration_millis = end_millis - start_millis
                duration_hours = duration_millis / (1000 * 60 * 60)
                end_dt = datetime.fromtimestamp(end_millis / 1000)
                end_date_str = end_dt.strftime("%Y-%m-%d")
                sleep_by_end_date[end_date_str] = sleep_by_end_date.get(end_date_str, 0) + duration_hours

        end_date_chart = datetime.now().date()
        for i in range(days -1, -1, -1):
            current_date = end_date_chart - timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            labels.append(current_date.strftime("%d-%m"))
            sleep_hours = round(sleep_by_end_date.get(date_str, 0), 1)
            sleep_hours_data.append(sleep_hours)

        return {
            "labels": labels,
            "hours": sleep_hours_data,
            "quality": [85] * days # Mock
        }

    def _get_latest_weight_and_height(self) -> dict:
        """Pobiera ostatni zapis wagi i wzrostu."""
        stats = {"weight": 0, "bmi": 0, "weight_change": 0}
        weight = None
        height = None
        weight_response = None # Inicjalizacja zmiennych
        height_response = None # Inicjalizacja zmiennych

        end_time = datetime.now()
        start_time = end_time - timedelta(days=90)
        # Użyj nanosekund dla dataset ID
        start_nanos = int(start_time.timestamp() * 1e9)
        end_nanos = int(end_time.timestamp() * 1e9)
        dataset_id = f"{start_nanos}-{end_nanos}"

        weight_url = f"https://www.googleapis.com/fitness/v1/users/me/dataSources/derived:com.google.weight:com.google.android.gms:merge_weight/datasets/{dataset_id}"
        height_url = f"https://www.googleapis.com/fitness/v1/users/me/dataSources/derived:com.google.height:com.google.android.gms:merge_height/datasets/{dataset_id}"

        try:
            weight_response = self._make_request(weight_url, method="GET")
            if weight_response and weight_response.get("point"):
                latest_weight_point = max(weight_response["point"], key=lambda p: int(p.get("endTimeNanos", 0)))
                weight_val = latest_weight_point.get("value", [])
                if weight_val:
                    weight = weight_val[0].get("fpVal")
                    if weight:
                        stats["weight"] = round(weight, 1)

            height_response = self._make_request(height_url, method="GET")
            if height_response and height_response.get("point"):
                latest_height_point = max(height_response["point"], key=lambda p: int(p.get("endTimeNanos", 0)))
                height_val = latest_height_point.get("value", [])
                if height_val:
                    height = height_val[0].get("fpVal")

            if weight and height and height > 0:
                stats["bmi"] = round(weight / (height ** 2), 1)

            # <<< DODANO PRINT DIAGNOSTYCZNY >>>
            print("\n--- DEBUG: SUROWA ODPOWIEDŹ Z API WAGI ---")
            print(json.dumps(weight_response, indent=2) if weight_response else "Brak odpowiedzi wagowej")
            print("--- KONIEC SUROWEJ ODPOWIEDZI Z API WAGI ---\n")
            print("\n--- DEBUG: SUROWA ODPOWIEDŹ Z API WZROSTU ---")
            print(json.dumps(height_response, indent=2) if height_response else "Brak odpowiedzi wzrostowej")
            print("--- KONIEC SUROWEJ ODPOWIEDZI Z API WZROSTU ---\n")
            print(f"--- DEBUG: Obliczone Weight Stats: {stats} ---\n")

        except HTTPException as e:
            print(f"Błąd podczas pobierania danych wagi/wzrostu: {e.detail}")
        except Exception as e:
            print(f"Nieoczekiwany błąd podczas pobierania danych wagi/wzrostu: {e}")

        return stats