#ifndef CONFIG_PARSER_H
#define CONFIG_PARSER_H

#include <cstdint>

// Decodifica o payload do tópico de controle (forzy/config/device). Se `payload` for um JSON
// válido contendo a chave "measurement_interval_ms", grava o valor em `out_interval_ms` e
// retorna true. Caso contrário (JSON malformado ou chave ausente), não toca em
// `out_interval_ms` e retorna false — quem chama mantém o intervalo atual.
bool try_parse_measurement_interval(const uint8_t *payload, unsigned int length, int &out_interval_ms);

#endif
