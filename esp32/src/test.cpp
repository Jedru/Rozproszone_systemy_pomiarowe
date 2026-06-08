#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <WiFiUdp.h>
#include <NTPClient.h>
#include <ArduinoJson.h>
#include <DHT11.h>

// ===== WIFI =====
const char* WIFI_SSID = "";
const char* WIFI_PASS = "";

// ===== MQTT =====
const char* MQTT_HOST = "";
const uint16_t MQTT_PORT = 1883;
const char* MQTT_TOPIC = "/measurements";

// ===== DEVICE =====
const char* DEVICE_ID = "esp8266-test-01";
const char* GROUP_ID  = "lab-a";

// ===== TIME =====
WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org", 0, 60 * 1000);

// ===== MQTT/WIFI =====
WiFiClient espClient;
PubSubClient mqtt(espClient);

// ===== TIMERS =====
unsigned long lastPublishMs = 0;
unsigned long lastStatusMs = 0;
const unsigned long PUBLISH_INTERVAL_MS = 5000;
const unsigned long STATUS_INTERVAL_MS  = 10000;

// ===== DATA =====
uint32_t seqNo = 0;

// ===== SENSOR READ =====
DHT11 dht11(5);
const int analogPin = 0; 



const char* wifiStatusToString(wl_status_t status) {
  switch (status) {
    case WL_IDLE_STATUS: return "WL_IDLE_STATUS";
    case WL_NO_SSID_AVAIL: return "WL_NO_SSID_AVAIL";
    case WL_SCAN_COMPLETED: return "WL_SCAN_COMPLETED";
    case WL_CONNECTED: return "WL_CONNECTED";
    case WL_CONNECT_FAILED: return "WL_CONNECT_FAILED";
    case WL_CONNECTION_LOST: return "WL_CONNECTION_LOST";
    case WL_DISCONNECTED: return "WL_DISCONNECTED";
    default: return "UNKNOWN";
  }
}

void connectWiFi() {
  Serial.println();
  Serial.printf("[WIFI] Laczenie z siecia: %s\n", WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    attempts++;
    if (attempts >= 40) {
      Serial.println("\n[WIFI] Timeout laczenia, ponawiam...");
      WiFi.disconnect();
      delay(1000);
      WiFi.begin(WIFI_SSID, WIFI_PASS);
      attempts = 0;
    }
  }

  Serial.println();
  Serial.println("[WIFI] Polaczono");
  Serial.print("[WIFI] IP: ");
  Serial.println(WiFi.localIP());
  Serial.print("[WIFI] RSSI: ");
  Serial.println(WiFi.RSSI());
}

void connectMQTT() {
  mqtt.setServer(MQTT_HOST, MQTT_PORT);

  while (!mqtt.connected()) {
    String clientId = "esp8266-" + String(ESP.getChipId(), HEX);

    Serial.printf("[MQTT] Laczenie z %s:%d ...\n", MQTT_HOST, MQTT_PORT);
    if (mqtt.connect(clientId.c_str())) {
      Serial.println("[MQTT] Polaczono");
    } else {
      Serial.printf("[MQTT] Blad, rc=%d. Ponawiam za 2s\n", mqtt.state());
      delay(2000);
    }
  }
}

uint64_t epochMs() {
  timeClient.update();

  unsigned long epochSec = timeClient.getEpochTime();
  unsigned long fracMs = millis() % 1000UL;

  uint64_t ts = ((uint64_t)epochSec * 1000ULL) + fracMs;
  return ts;
}

float fakeTemperature() {
  return 22.0 + (float)(seqNo % 15) * 0.1;
}

float fakeHumidity() {
  return 45.0 + (float)(seqNo % 20) * 0.3;
}

float fakeVoltage() {
  return 3.25 + (float)(seqNo % 10) * 0.01;
}

bool publishMeasurement(const char* sensor, float value, const char* unit) {
  StaticJsonDocument<256> doc;
  doc["group_id"] = GROUP_ID;
  doc["device_id"] = DEVICE_ID;
  doc["sensor"] = sensor;
  doc["value"] = value;
  doc["unit"] = unit;
  doc["ts_ms"] = epochMs();
  doc["seq"] = seqNo++;

  char payload[256];
  size_t n = serializeJson(doc, payload);

  bool ok = mqtt.publish(MQTT_TOPIC, payload, n);

  Serial.print("[PUB] topic=");
  Serial.println(MQTT_TOPIC);
  Serial.print("[PUB] payload=");
  Serial.println(payload);
  Serial.print("[PUB] status=");
  Serial.println(ok ? "OK" : "FAIL");
  Serial.println();

  return ok;
}

void printStatus() {
  Serial.println("===== STATUS ESP8266 =====");
  Serial.print("[WIFI] status: ");
  Serial.println(wifiStatusToString((wl_status_t)WiFi.status()));
  Serial.print("[WIFI] connected: ");
  Serial.println(WiFi.status() == WL_CONNECTED ? "TAK" : "NIE");
  Serial.print("[WIFI] ip: ");
  Serial.println(WiFi.localIP());
  Serial.print("[WIFI] rssi: ");
  Serial.println(WiFi.RSSI());
  Serial.print("[MQTT] connected: ");
  Serial.println(mqtt.connected() ? "TAK" : "NIE");
  Serial.print("[NTP] epoch_s: ");
  Serial.println(timeClient.getEpochTime());
  Serial.println("==========================");
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  connectWiFi();
  timeClient.begin();
  timeClient.update();
  connectMQTT();

  Serial.println("[SYS] Start programu testowego");
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI] Utrata polaczenia, reconnect...");
    connectWiFi();
  }

  if (!mqtt.connected()) {
    Serial.println("[MQTT] Utrata polaczenia, reconnect...");
    connectMQTT();
  }

  mqtt.loop();
  timeClient.update();

  unsigned long now = millis();

  if (now - lastStatusMs >= STATUS_INTERVAL_MS) {
    lastStatusMs = now;
    printStatus();
  }
  int temperature = 0;
  int humidity = 0;

    // Attempt to read the temperature and humidity values from the DHT11 sensor.
  int result = dht11.readTemperatureHumidity(temperature, humidity);
  
  // 2. Read Analog Value (0 - 4095)
  int analogValue = analogRead(analogPin);
  float percentage = (analogValue/1024.0)*100.0;
  // Print results to Serial Monitor


  delay(300); // Wait half a second between readings
    if (result == 0) {
        Serial.print("Temperature: ");
        Serial.print(temperature);
        Serial.print(" °C\tHumidity: ");
        Serial.print(humidity);
        Serial.println(" %");
        Serial.print("\t Analog Value: ");
        Serial.println(percentage);
    } else {
        // Print error message based on the error code.
        Serial.println(DHT11::getErrorString(result));
    }

  if (now - lastPublishMs >= PUBLISH_INTERVAL_MS) {
    lastPublishMs = now;

    publishMeasurement("temperature", temperature, "C");
    delay(100);

    publishMeasurement("humidity", humidity, "%");
    delay(100);

    publishMeasurement("illumination", percentage, "%");
  }
}