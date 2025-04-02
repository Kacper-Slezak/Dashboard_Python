import os
import sys
import pytest

# Konfiguracja ścieżek
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.google_auth import google_fit_credentials


def test_google_fit_credentials():
    """Testuje podstawową autoryzację"""
    print("\n=== Test 1: Sprawdzanie zwracanych creds ===")

    creds = google_fit_credentials()
    print(f"Token file exists: {os.path.exists('config/token.json')}")
    print(f"Creds object: {creds}")

    assert creds is not None, "Funkcja zwróciła None - sprawdź czy: 1) plik client_secret.json istnieje, 2) logowanie przez Google działa"
    assert creds.valid, "Token jest nieważny. Data wygaśnięcia: " + str(creds.expiry)


def test_token_auto_refresh():
    """Testuje automatyczne odświeżanie tokenu"""
    print("\n=== Test 2: Odświeżanie tokenu ===")

    old_token_path = "config/token.json"
    if os.path.exists(old_token_path):
        os.remove(old_token_path)
        print("Usunięto stary token")

    creds = google_fit_credentials()
    assert creds is not None, "Nie udało się wygenerować nowego tokenu"
    print("Nowy token wygenerowany poprawnie")