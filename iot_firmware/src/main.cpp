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
  setup_wifi(); // Inicializa conexão com a rede local
  client.setServer(MQTT_BROKER, MQTT_PORT); // Configura o Broker MQTT de destino
}

void loop() {
  if (!client.connected()) {
    reconnect(); // Garante que o dispositivo esteja sempre conectado ao Broker
  }
  client.loop();

  long now = millis();
  if (now - lastMsg > 2000) { // Frequência de amostragem: 2 segundos
    lastMsg = now;

    // --- Coleta de Dados (Simulação de Sensores Industriais) ---
    float tempW = 70.0 + random(0, 100) / 10.0;  // Temperatura Enrolamento
    float tempB = 60.0 + random(0, 50) / 10.0;   // Temperatura Mancal
    float vib   = 1.0 + random(0, 50) / 100.0;   // Vibração RMS
    float curr  = 25.0 + random(-10, 10) / 10.0; // Corrente Nominal
    float volt  = 220.0 + random(-5, 5);         // Tensão de Linha
    int   rpm   = 1765 + random(-10, 10);        // Rotação por Minuto

    // Injeção de Caos: Simula comportamento anômalo para teste de alertas (5% de chance)
    if (random(0, 100) < 5) { 
       tempW = 156.0; // Gatilho de Alerta Crítico
       vib = 5.2;     
    }

    // --- Empacotamento de Dados (JSON Industrial) ---
    StaticJsonDocument<256> doc;
    doc["device_id"] = DEVICE_ID; // Vínculo obrigatório com a TAG do Ativo
    doc["temp_windings"] = tempW;
    doc["temp_bearings"] = tempB;
    doc["vibration_rms"] = vib;
    doc["current"] = curr;
    doc["voltage"] = volt;
    doc["rpm"] = rpm;

    char buffer[256];
    serializeJson(doc, buffer);

    // Exibição local no Monitor Serial (Requisito da Sprint)
    Serial.print("Publicando: ");
    Serial.println(buffer);
    
    // Transmissão via MQTT para o Ecossistema Forzy
    client.publish(MQTT_TOPIC, buffer);
  }
}
