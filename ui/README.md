# Flask GUI do podglądu pomiarów

Aplikacja pobiera dane z:
- `http://localhost:5001/measurements`
- `http://localhost:5001/measurements/latest`

## Uruchomienie

```bash
cd output/sensor_flask_gui
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
pip install -r requirements.txt
python app.py
```

GUI będzie dostępne pod adresem:
- `http://127.0.0.1:5055`

## Co zawiera

- panel z temperaturą, wilgotnością i ciśnieniem,
- wykres typu „oscyloskop” z odświeżaniem co 3 sekundy,
- tabela z rekordami z `/latest`,
- status połączenia z API,
- uproszczony status MQTT / ingestora (na podstawie tego, czy napływają dane),
- przyciski `Obserwuj`, `Zatrzymaj`, `Wznów`, bez podpiętej logiki sterowania.

## Założenia

- API zwraca JSON jako listę rekordów albo obiekt z polem `items` / `data`.
- Nazwy sensorów są mapowane m.in. dla: `temperature`, `humidity`, `pressure`, `bme280_*`, `bmp280_*`.
- Status MQTT nie jest pobierany z prawdziwego brokera, tylko szacowany na podstawie obecności danych. Jeśli chcesz, można go później podpiąć pod realny endpoint healthcheck.
