# 👁️ Estratégia de Visão Computacional - Projeto Forzy (Sprint 2)

## 1. Objetivo
Automatizar o cadastro de ativos industriais (motores elétricos) através da leitura da placa de identificação técnica utilizando técnicas de OCR (Optical Character Recognition).

## 2. Pipeline de Processamento
1.  **Captura:** Fotografia da placa técnica via dispositivo móvel ou câmera industrial.
2.  **Pré-processamento (OpenCV):**
    *   Grayscale conversion.
    *   Gaussian Blur para redução de ruído.
    *   Thresholding adaptativo para destacar o texto.
    *   Correção de perspectiva (Warp Perspective) caso a foto esteja angulada.
3.  **Extração (EasyOCR / Tesseract):**
    *   Utilização do EasyOCR pela melhor performance em ambientes industriais com variações de luz.
4.  **Parsing de Entidades:**
    *   Regex para identificar padrões como `V`, `A`, `kW`, `RPM` e `IP`.

## 3. Campos a serem Extraídos
| Campo | Exemplo na Placa | Atributo no Sistema |
| :--- | :--- | :--- |
| Modelo | W22 IR3 Premium | `model` |
| Potência | 7.5 kW / 10 CV | `power_kw` |
| Tensão | 220/380/440 V | `voltage_v` |
| Rotação | 1765 RPM | `rpm_nominal` |
| Grau de Proteção | IP55 | `protection_degree` |

## 4. Integração
Os dados extraídos serão validados via modelos Pydantic e enviados para o endpoint de cadastro (`/assets`) para persistência no Neon.
