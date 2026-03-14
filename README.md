# Python-CAN 🚗 Automotive OTA Simulator over CAN

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![CAN](https://img.shields.io/badge/protocol-CAN%20%7C%20UDS%20(ISO%2014229)-success.svg)
![Status](https://img.shields.io/badge/status-Concluído-brightgreen.svg)

Este repositório contém um simulador de atualizações automotivas **Over-The-Air (OTA)** utilizando o protocolo **UDS (Unified Diagnostic Services - ISO 14229)** sobre o barramento CAN. O projeto foi desenvolvido inteiramente em Python utilizando a biblioteca `python-can` para injeção e leitura de *raw frames* (pacotes brutos) de rede.

Este projeto foi desenvolvido como parte da avaliação do módulo de Redes Automotivas da **Residência em Software Automotivo (CIn-UFPE & Stellantis)**.

## 📌 Funcionalidades

O simulador é composto por dois nós independentes que se comunicam através de uma interface CAN virtual (`vcan0`):

1. **ECU Simulada (`ecu_uds_robusta.py`)**: 
   - Escuta requisições no ID `0x7E0` e responde no ID `0x7E8`.
   - Implementa respostas positivas e códigos de resposta negativa (NRCs).
   - Suporta fluxo de segurança via algoritmo *Seed & Key*.
   
2. **Cliente OTA / Testador (`cliente_ota_real.py`)**:
   - Atua como o módulo telemático que baixa e injeta o novo *firmware*.
   - Constrói manualmente os *payloads* hexadecimais (PCI, SID e Subfunções).
   - Orquestra os serviços UDS respeitando os *timeouts* da rede.

### 🛠️ Serviços UDS Implementados:
- `0x10` - Diagnostic Session Control (Programming Session)
- `0x27` - Security Access (Request Seed & Send Key)
- `0x34` - Request Download
- `0x36` - Transfer Data
- `0x37` - Request Transfer Exit
- `0x3E` - Tester Present

---

## 🚀 Como Executar

### 1. Pré-requisitos
O projeto foi feito para rodar em ambiente **Linux**, pois utiliza o módulo de *kernel* `vcan` (Virtual CAN) via SocketCAN.

Instale a biblioteca `python-can`:
```bash
pip install python-can
