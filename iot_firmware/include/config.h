#ifndef CONFIG_H
#define CONFIG_H

// --- Configurações de Rede ---
const char* WIFI_SSID = "Wokwi-GUEST"; // Padrão do simulador Wokwi
const char* WIFI_PASSWORD = "";

// --- Configurações MQTT ---
// Se rodar no Wokwi, use o IP da sua máquina ou 'broker.emqx.io' para testes externos.
// Para Docker Local (localhost), no simulador Wokwi usa-se geralmente um proxy.
const char* MQTT_BROKER = "10.0.0.2"; // Placeholder: Ajustar para o IP da máquina host
const int   MQTT_PORT   = 1883;
const char* MQTT_TOPIC  = "Forzy/telemetry/W22_IR3_Premium";
const char* MQTT_CONFIG_TOPIC = "Forzy/config/device";

// --- Identificação do Ativo ---
const char* DEVICE_ID = "WEG_W22_Wokwi_Sim";

#endif
