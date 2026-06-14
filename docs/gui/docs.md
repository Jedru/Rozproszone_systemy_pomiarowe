# GUI
## Uruchomienie
1. Utworzenie środowiska wirtualnego
```
python -m venv .venv
```
2. Aktywacja utworzonego wcześniej środowiska
```
source .venv/bin/activate
```
3. Instalacja zależności
```
pip install -r requirements.txt
```
4. Uruchomienie
```
python gui.py
```

## Obsługa
1. Pobranie listy urządzeń
2. Wybranie urządzenia z listy (poprzez kliknięcie)
3. Manualna / automatyczna aktualizacja

### Healtcheck
Sprawdza połączenie z API po naciśnięciu przycisku `Healtcheck`.
`Status` wyświetla status połączenia:
1. `???` - status nieznany
2. `OK` - działające połączenie
3. `DOWN` - niedziałające połączenie

### Pobieranie listy urządzeń
Pobieranie listy urządzeń odbywa się po kliknięciu przycisku `Refresh devices`.

### Aktualizacja pomiarów
Aktualizacja pomiarów następuje po kliknięciu przycisku `Update`.
Aktualizacja następuje automatycznie jeśli opcja `Auto-update` jest zaznaczona.
