# UPSAI Remoto - Home Assistant Integration

[![hacs_badge](https://shields.io)](https://github.com)
![Version](https://shields.io)

Esta é a integração oficial para o **Dispositivo UPSAI Remoto**, permitindo o controle em tempo real e o monitoramento completo de gerenciadores de energia industriais e residenciais diretamente pelo Home Assistant.

This is the official integration for the **UPSAI Remote Device**, allowing real-time control and complete monitoring of industrial and residential power managers directly through Home Assistant.

---

## 📂 Estrutura do Repositório / Repository Structure

O repositório está estruturado seguindo rigorosamente os padrões do Home Assistant Core e HACS:
The repository is structured strictly according to Home Assistant Core and HACS standards:

```text
upsai_remoto/ (GitHub Root)
├── custom_components/
│   └── upsai_remoto/
│       ├── __init__.py      # WebSocket Connection Engine
│       ├── button.py        # Safety Global Unlock Trigger
│       ├── config_flow.py   # Plug-and-Play SSDP Auto-Discovery
│       ├── manifest.json    # Integration Metadata
│       ├── sensor.py        # Real-time Telemetry (Vin, Vout, Load, Msg)
│       ├── strings.json     # UI Translations (Português/English)
│       └── switch.py        # 16 Control Toggles (8 Outlets + 8 Safety Locks)
├── hacs.json                # HACS Catalog Metadata
└── README.md                # Documentation
```

---

## ⚡ Características / Features

- **Zero-Configuration Auto-Discovery:** O dispositivo é descoberto automaticamente na rede local via broadcast SSDP/UPnP (Exibe um banner amarelo instantâneo na tela de Dispositivos).
- **Pure Event-Driven WebSocket Stream:** Comunicação bidirecional em tempo real utilizando um único canal de comunicação persistente (baseado no servidor web Cesanta Mongoose). Atualizações instantâneas de telemetria sem necessidade de polling HTTP.
- **Bitmask Extraction (LSB):** Processamento eficiente de strings binárias compactadas de 8 bits lidas da direita para a esquerda.
- **Visual Availability Protection:** Os sensores zeram e os switches são desativados/cinza instantaneamente caso a conexão de rede caia.

---

## 🎛️ Entidades Suportadas / Supported Entities

A integração gera automaticamente **22 entidades** agrupadas em um único dispositivo unificado:

1. **Sensores (4):**
   - **Input Voltage (`Vin`):** Tensão de entrada da rede elétrica (V).
   - **Output Voltage (`Vout`):** Tensão de saída regulada (V).
   - **Power Load:** Percentual de carga consumida (%).
   - **Status Message:** Mensagens de diagnóstico em tempo real vindas da placa de potência.
2. **Interruptores / Switches (17):**
   - **Saídas (0 a 7):** Controle individual de ligar/desligar de cada tomada física.
   - **Safety Locks (0 a 7):** Travas de segurança independentes que bloqueiam comandos acidentais nas saídas protegidas.
   - **Dispositivo (Master):** Chave mestre que liga/desliga todas as tomadas não bloqueadas simultaneamente.
3. **Botões / Buttons (1):**
   - **Global Unlock:** Botão tátil momentâneo para limpar todas as travas de segurança da unidade de uma só vez.

---

## 🛠️ Comunicação a Nível de Protocolo / Protocol Blueprint

### Downstream (Device -> Home Assistant)
O firmware do dispositivo (Mongoose) envia frames JSON uncompressed contendo a telemetria compactada a cada ciclo:
```json
{
  "Vin": 115.4, 
  "Vout": 115.4, 
  "Power": 2, 
  "Msg": "Rede Elétrica OK", 
  "bank0_stat": "11100111", 
  "bank0_lock": "00000101"
}
```

### Upstream (Home Assistant -> Device)
Os comandos enviados pelo Home Assistant são strings ASCII puras injetadas diretamente no WebSocket utilizando o prefixo multiplexador de canal `HA_`:
- `HA_OUT0-X:ON` / `HA_OUT0-X:OFF` -> Controle de Saídas.
- `HA_OUT0-X:LOCKON` / `HA_OUT0-X:UNLOCK` -> Controle de Travas.
- `HA_DEV:ON` / `HA_DEV:OFF` / `HA_DEV:UNLOCK` -> Comandos Globais.
- `HA_SYSTEM:CONNECT` / `HA_SYSTEM:DISCONNECT` -> Ciclo de Vida do Sistema.

---

## 📦 Instalação / Installation

### Método 1: HACS (Recomendado / Recommended)
Quando este repositório for mesclado ao índice oficial:
1. No Home Assistant, vá em **HACS > Integrações**.
2. Clique nos Três Pontos ⋮ no canto superior direito e busque por **UPSAI Remoto**.
3. Clique em **Download**.
4. Reinicie o Home Assistant.

### Método 2: Repositório Personalizado / Custom Repository
Enquanto o Pull Request está em análise:
1. Vá em **HACS > Integrações**.
2. Três Pontos ⋮ > **Repositórios Personalizados**.
3. Adicione a URL: `https://github.com`
4. Selecione a categoria **Integração** e clique em **Adicionar**.

---

## 📝 Licença / License

Desenvolvido por **UPSAI Sistemas de Energia** e mantido por [@peplegal](https://github.com).  
Distributed under the MIT License. See `LICENSE` for more information.
