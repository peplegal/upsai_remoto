class UpsaiRemotoCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      this.innerHTML = `
        <ha-card header="UPSAI Remoto">
          <style>
            .grid-container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; padding: 15px; text-align: center; }
            .telemetry-val { font-size: 24px; font-weight: bold; color: var(--primary-color); }
            
            .status-container { text-align: center; padding: 0 15px 15px 15px; border-bottom: 1px solid var(--divider-color); }
            .status-title { font-weight: bold; margin-bottom: 4px; font-size: 14px; }
            .status-val { font-size: 18px; color: var(--secondary-text-color); font-weight: 500; }

            .master-container { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; padding: 15px; border-bottom: 1px solid var(--divider-color); align-items: center; }
            .master-box { display: flex; flex-direction: column; align-items: center; justify-content: center; background: var(--card-background-color, var(--paper-card-background-color)); padding: 10px; border-radius: 8px; border: 1px solid var(--divider-color); min-height: 80px; }
            .master-label { font-weight: bold; margin-bottom: 8px; font-size: 14px; text-align: center; }
            
            /* 🚀 FIXED: MASTER UNLOCK TRANSFORMED INTO A PERFECT HIGH-VISIBILITY YELLOW ICON BUTTON */
            .master-icon-btn { 
              color: #e6b800 !important;
              --mdc-icon-button-size: 44px;
              display: inline-flex;
              justify-content: center;
            }
            .master-icon-btn ha-icon {
              --mdc-icon-size: 32px;
            }
            
            .tabular-control { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 5px; padding: 8px 15px; align-items: center; }
            .header-row { font-weight: bold; border-bottom: 1px solid var(--divider-color); padding-bottom: 5px; }
            ha-switch { display: inline-flex; justify-content: center; }
            ha-icon-button { --mdc-icon-button-size: 36px; display: inline-flex; justify-content: center; }
            
            .reboot-icon-btn { 
              color: var(--primary-color);
              display: inline-flex;
              justify-content: center;
              margin: 0 auto;
            }
          </style>
          
          <div class="grid-container">
            <div><div><b>Rede Elétrica</b></div><div class="telemetry-val" id="vin">- V</div></div>
            <div><div><b>Tensão Saída</b></div><div class="telemetry-val" id="vout">- V</div></div>
            <div><div><b>Consumo</b></div><div class="telemetry-val" id="power">- %</div></div>
          </div>
          
          <div class="status-container">
            <div class="status-title">ESTADO DO SISTEMA</div>
            <div class="status-val" id="msg">Iniciando...</div>
          </div>
          
          <div class="master-container">
            <div class="master-box">
              <div class="master-label">COMANDO GLOBAL</div>
              <!-- 🚀 FIXED: REPLACED TEXT BUTTON WITH A STUNNING PURE ICON ACTION TOGGLE -->
              <ha-icon-button class="master-icon-btn" id="masterlock_btn">
                <ha-icon icon="mdi:lock-open-check"></ha-icon>
              </ha-icon-button>
            </div>
            <div class="master-box">
              <div class="master-label">DISPOSITIVO</div>
              <ha-switch id="masterdevice_sw"></ha-switch>
            </div>
          </div>

          <div style="padding: 10px 0;">
            <div class="tabular-control header-row">
              <div>CANAL</div><div style="text-align:center;">ATIVAR</div><div style="text-align:center;">TRAVAR</div><div style="text-align:center;">REINICIAR</div>
            </div>
            ${Array.from({length: 8}, (_, i) => `
              <div class="tabular-control">
                <div><b>SAÍDA ${i}</b></div>
                <div style="text-align:center;"><ha-switch id="out_${i}" data-index="${i}"></ha-switch></div>
                <div style="text-align:center;">
                  <ha-icon-button id="lockbtn_${i}" data-index="${i}">
                    <ha-icon id="lockico_${i}" icon="mdi:lock-open"></ha-icon>
                  </ha-icon-button>
                </div>
                <div style="text-align:center;">
                  <ha-icon-button class="reboot-icon-btn" id="reboot_${i}" data-index="${i}">
                    <ha-icon icon="mdi:restart"></ha-icon>
                  </ha-icon-button>
                </div>
              </div>
            `).join('')}
          </div>
        </ha-card>
      `;
      this.content = true;
      this._setupListeners();
    }
    this._updateStates(hass);
  }

  _findSensorState(hass, suffix) {
    const devId = this.config.device_id.toLowerCase();
    const exactMatch = hass.states[`sensor.${devId}_${suffix}`];
    if (exactMatch) return exactMatch.state;

    const stateKey = Object.keys(hass.states).find(key => 
      key.startsWith('sensor.') && key.includes(devId) && key.endsWith(suffix)
    );
    return stateKey ? hass.states[stateKey].state : undefined;
  }

  _setupListeners() {
    this.addEventListener('click', (ev) => {
      ev.stopImmediatePropagation();
      
      const now = Date.now();
      if (this._lastClick && (now - this._lastClick < 250)) {
        return;
      }
      this._lastClick = now;

      const target = ev.composedPath().find(el => el.id && (
        el.id.startsWith('out_') || 
        el.id.startsWith('lockbtn_') || 
        el.id.startsWith('reboot_') ||
        el.id === 'masterlock_btn' ||
        el.id === 'masterdevice_sw'
      ));
      if (!target) return;
      
      const devId = this.config.device_id.toLowerCase();
      
      if (target.id === 'masterlock_btn') {
        this._hass.callService('button', 'press', { entity_id: `button.${devId}_master_unlock` });
        return;
      }
      if (target.id === 'masterdevice_sw') {
        this._hass.callService('switch', 'toggle', { entity_id: `switch.${devId}_master_device` });
        return;
      }
      
      const [type, index] = target.id.split('_');
      if (type === 'out') {
        this._hass.callService('switch', 'toggle', { entity_id: `switch.${devId}_out0_${index}` });
      } else if (type === 'lockbtn') {
        this._hass.callService('switch', 'toggle', { entity_id: `switch.${devId}_lock0_${index}` });
      } else if (type === 'reboot') {
        this._hass.callService('button', 'press', { entity_id: `button.${devId}_reboot0_${index}` });
      }
    });
  }

  _updateStates(hass) {
    const devId = this.config.device_id.toLowerCase();
    
    const vinState = this._findSensorState(hass, 'vin') || '-';
    const voutState = this._findSensorState(hass, 'vout') || '-';
    const powerState = this._findSensorState(hass, 'power') || '-';
    const msgState = this._findSensorState(hass, 'msg') || '-';

    this.querySelector('#vin').innerText = `${vinState} V`;
    this.querySelector('#vout').innerText = `${voutState} V`;
    this.querySelector('#power').innerText = `${powerState} %`;
    this.querySelector('#msg').innerText = msgState;

    let masterDeviceState = hass.states[`switch.${devId}_master_device`]?.state === 'on';
    if (hass.states[`switch.${devId}_master_device`] === undefined) {
      const masterKey = Object.keys(hass.states).find(key => 
        key.startsWith('switch.') && key.includes(devId) && key.endsWith('master_device')
      );
      if (masterKey) masterDeviceState = hass.states[masterKey].state === 'on';
    }

    const masterSwEl = this.querySelector('#masterdevice_sw');
    if (masterSwEl) masterSwEl.checked = masterDeviceState;

    for (let i = 0; i < 8; i++) {
      const swState = hass.states[`switch.${devId}_out0_${i}`]?.state === 'on';
      const lockState = hass.states[`switch.${devId}_lock0_${i}`]?.state === 'on';
      
      const swEl = this.querySelector(`#out_${i}`);
      const lockIco = this.querySelector(`#lockico_${i}`);
      
      if (swEl) swEl.checked = swState;
      if (lockIco) {
        lockIco.setAttribute('icon', lockState ? "mdi:lock" : "mdi:lock-open");
        lockIco.style.color = lockState ? "var(--error-color)" : "var(--success-color)";
      }
    }
  }

  setConfig(config) {
    if (!config.device_id) throw new Error('Please define device_id');
    this.config = config;
  }

  getCardSize() { return 10; }
}
customElements.define('upsai-remoto-card', UpsaiRemotoCard);
