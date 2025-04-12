import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.sleep.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read"
]


def google_fit_credentials():
    try:
        creds = None
        token_path = "config/token.json"

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Poprawiona nazwa pliku - bez podkreślnika na końcu
                flow = InstalledAppFlow.from_client_secrets_file(
                    "config/client_secret.json",
                    SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(token_path, "w") as token:
                token.write(creds.to_json())

        return creds

    except RefreshError as e:
        print(f"Błąd odświeżania tokenu: {str(e)}")
        raise
    except Exception as e:
        print(f"Błąd: {str(e)}")
        raise