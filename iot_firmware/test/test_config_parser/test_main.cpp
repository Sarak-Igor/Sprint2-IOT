#include <unity.h>
#include <cstring>

#include "config_parser.h"

void setUp() {}
void tearDown() {}

// Deve (Firmware C++) atualizar a variável global de atraso apenas se o JSON for válido e
// contiver a chave correta — specs/specs/03-migracao-simulador-esp32.md §4.
void test_valid_payload_with_key_updates_interval() {
  int interval = 2000;
  const char *payload = "{\"measurement_interval_ms\":500}";

  bool updated = try_parse_measurement_interval(
      reinterpret_cast<const uint8_t *>(payload), strlen(payload), interval);

  TEST_ASSERT_TRUE(updated);
  TEST_ASSERT_EQUAL_INT(500, interval);
}

// Deve (Firmware C++) manter o valor de tempo original caso o payload MQTT seja malformado.
void test_malformed_json_keeps_original_interval() {
  int interval = 2000;
  const char *payload = "{not-json";

  bool updated = try_parse_measurement_interval(
      reinterpret_cast<const uint8_t *>(payload), strlen(payload), interval);

  TEST_ASSERT_FALSE(updated);
  TEST_ASSERT_EQUAL_INT(2000, interval);
}

// Deve (Firmware C++) manter o valor original quando o JSON é válido mas não traz a chave
// esperada — mesmo requisito do malformado, ramo diferente do guard clause.
void test_valid_json_without_expected_key_keeps_original_interval() {
  int interval = 2000;
  const char *payload = "{\"other_key\":123}";

  bool updated = try_parse_measurement_interval(
      reinterpret_cast<const uint8_t *>(payload), strlen(payload), interval);

  TEST_ASSERT_FALSE(updated);
  TEST_ASSERT_EQUAL_INT(2000, interval);
}

int main(int argc, char **argv) {
  UNITY_BEGIN();
  RUN_TEST(test_valid_payload_with_key_updates_interval);
  RUN_TEST(test_malformed_json_keeps_original_interval);
  RUN_TEST(test_valid_json_without_expected_key_keeps_original_interval);
  return UNITY_END();
}
