
---

## Dashboard Finanse Zdrowie

Aplikacja FastAPI do zarządzania finansami i zdrowiem, z wykorzystaniem SQLite jako bazy danych.

---

###  **Funkcje**
 - API do zarządzania finansami (wydatki, dochody)  
 - API do śledzenia zdrowia (np. waga, kalorie)  
 - Wykorzystanie **SQLite + SQLAlchemy**  
 - Struktura modularna, gotowa do rozbudowy  
 - Testy jednostkowe  

---

###  **Struktura katalogów**
```
dashboard_finanse_zdrowie/
├── app/
│   ├── api/
│   │   ├── finance.py
│   │   └── health.py
│   ├── models/
│   │   ├── finance.py
│   │   └── health.py
│   ├── services/
│   │   ├── finance.py
│   │   └── health.py
│   ├── utils/
│   └── __init__.py
├── database/
│   ├── migrations/
│   └── db_setup.py
├── config/
│   └── settings.py
├── scripts/
├── tests/
├── main.py
├── requirements.txt
└── README.md            
```

---

### 🛠 **Instalacja**
1. **Klonowanie repozytorium**
```sh
git clone https://github.com/użytkownik/dashboard_finanse_zdrowie.git
cd dashboard_finanse_zdrowie
```

2. **Tworzenie i aktywowanie wirtualnego środowiska**
```sh
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

3. **Instalacja zależności**
```sh
pip install -r requirements.txt
```

4. **Uruchomienie aplikacji**
```sh
python main.py
```
Aplikacja będzie dostępna pod:  
🔗 **http://127.0.0.1:8000**

---

###  **API – dostępne endpointy**
| Metoda | Endpoint              | Opis                    |
|--------|----------------------|-------------------------|
| GET    | `/finanse`           | Pobiera listę transakcji |
| POST   | `/finanse`           | Dodaje nową transakcję |
| GET    | `/zdrowie`           | Pobiera dane zdrowotne |
| POST   | `/zdrowie`           | Dodaje wpis zdrowotny |

Dokumentacja Swagger dostępna pod:  
🔹 **http://127.0.0.1:8000/docs**  

---

###  **TODO**
- [ ] Dodanie autoryzacji JWT  
- [ ] Frontend w React  
- [ ] Analiza danych  

**Autor:**  *Kacper Ślęzak*  
