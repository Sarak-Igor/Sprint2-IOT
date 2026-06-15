#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "config.h"

WiFiClient espClient;
PubSubClient client(espClient);
long lastMsg = 0;

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Conectando em ");
  Serial.println(WIFI_SSID);

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi conectado");
  Serial.println("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Tentando conexão MQTT...");
    if (client.connect(DEVICE_ID)) {
      Serial.println("conectado!");
    } else {
      Serial.print("falhou, rc=");
      Serial.print(client.state());
      Serial.println(" tentando novamente em 5 segundos");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(MQTT_BROKER, MQTT_PORT);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  long now = millis();
  if (now - lastMsg > 2000) { // Envia a cada 2 segundos
    lastMsg = now;

    // --- Simulação de Sensores (Lógica de Bancada) ---
    float tempW = 70.0 + random(0, 100) / 10.0;
    float tempB = 60.0 + random(0, 50) / 10.0;
    float vib   = 1.0 + random(0, 50) / 100.0;
    float curr  = 25.0 + random(-10, 10) / 10.0;
    float volt  = 220.0 + random(-5, 5);
    int   rpm   = 1765 + random(-10, 10);

    // Injeção de Caos (Simulação de anomalia)
    if (random(0, 100) < 5) { // 5% de chance de falha
       tempW = 156.0; // Acima do crítico (Classe F)
       vib = 5.2;     // Acima do crítico
    }

    // --- Criação do JSON ---
    StaticJsonDocument<256> doc;
    doc["device_id"] = DEVICE_ID;
    doc["temp_windings"] = tempW;
    doc["temp_bearings"] = tempB;
    doc["vibration_rms"] = vib;
    doc["current"] = curr;
    doc["voltage"] = volt;
    doc["rpm"] = rpm;

    char buffer[256];
    serializeJson(doc, buffer);

    Serial.print("Publicando: ");
    Serial.println(buffer);
    client.publish(MQTT_TOPIC, buffer);
  }
}
