#include "config_parser.h"

#include <ArduinoJson.h>

bool try_parse_measurement_interval(const uint8_t *payload, unsigned int length, int &out_interval_ms) {
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error || !doc.containsKey("measurement_interval_ms")) {
    return false;
  }

  out_interval_ms = doc["measurement_interval_ms"];
  return true;
}
