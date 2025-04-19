import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow

SCOPES = [
    "https://www.googleapis.com/auth/fitness.activity.read",
    "https://www.googleapis.com/auth/fitness.sleep.read",
    "https://www.googleapis.com/auth/fitness.heart_rate.read",
    "https://www.googleapis.com/auth/fitness.body.read",
    "https://www.googleapis.com/auth/fitness.location.read"
]


def google_fit_credentials():
    try:
        creds = None
        token_path = os.getenv('TOKEN_PATH', 'config/token.json')

        # POPRAWKA: Użyj typu "web" zamiast "installed"
        client_config = {
            "web": {  # Zmiana z "installed" na "web"
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # POPRAWKA: Jawnie podaj redirect_uri
                flow = Flow.from_client_config(
                    client_config,
                    SCOPES,
                    redirect_uri=os.getenv("GOOGLE_REDIRECT_URI")  # Wymagane dla typu "web"
                )

                # Uruchom serwer z potwierdzeniem portu
                authorization_url, _ = flow.authorization_url(
                    prompt='consent',
                    access_type='offline'
                )
                print(f"Przejdź do tego adresu: {authorization_url}")  # For debugging

                creds = flow.run_local_server(
                    port=8000,  # Jawnie ustaw port 8000
                    host="localhost",
                    open_browser=False
                )

            with open(token_path, "w") as token:
                token.write(creds.to_json())

        return creds

    except Exception as e:
        print(f"Błąd autoryzacji: {str(e)}")
        raise