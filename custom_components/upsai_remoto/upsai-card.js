class UpsaiRemotoCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      this.innerHTML = `
        <ha-card header="UPSAI Remoto">
          <style>
            .grid-container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; padding: 15px; text-align: center; }
            .telemetry-val { font-size: 24px; font-weight: bold; color: var(--primary-color); }
            .tabular-control { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 5px; padding: 8px 15px; align-items: center; }
            .header-row { font-weight: bold; border-bottom: 1px solid var(--divider-color); padding-bottom: 5px; }
            ha-switch { display: inline-flex; justify-content: center; }
            ha-icon-button { --mdc-icon-button-size: 36px; display: inline-flex; justify-content: center; }
            mwc-button { --mdc-theme-primary: var(--primary-color); }
          </style>
          <div class="grid-container">
            <div><div><b>Rede Elétrica</b></div><div class="telemetry-val" id="vin">- V</div></div>
            <div><div><b>Tensão Saída</b></div><div class="telemetry-val" id="vout">- V</div></div>
            <div><div><b>Consumo</b></div><div class="telemetry-val" id="power">- %</div></div>
          </div>
          <div style="padding: 0 15px 15px 15px; border-bottom: 1px solid var(--divider-color);">
            <b>Estado do Sistema:</b> <span id="msg">Iniciando...</span>
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
                  <mwc-button raised dense id="reboot_${i}" data-index="${i}">Reset</mwc-button>
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
      const target = ev.composedPath().find(el => el.id && (el.id.startsWith('out_') || el.id.startsWith('lockbtn_') || el.id.startsWith('reboot_')));
      if (!target) return;
      
      const [type, index] = target.id.split('_');
      const devId = this.config.device_id.toLowerCase(); // Lowercase string alignment
      
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
    const devId = this.config.device_id.toLowerCase(); // Forces lowercase match to match backend configuration
    
    const vinState = this._findSensorState(hass, 'vin') || '-';
    const voutState = this._findSensorState(hass, 'vout') || '-';
    const powerState = this._findSensorState(hass, 'power') || '-';
    const msgState = this._findSensorState(hass, 'msg') || '-';

    this.querySelector('#vin').innerText = `${vinState} V`;
    this.querySelector('#vout').innerText = `${voutState} V`;
    this.querySelector('#power').innerText = `${powerState} %`;
    this.querySelector('#msg').innerText = msgState;

    for (let i = 0; i < 8; i++) {
      // Corrected strings layout targeting the exact generated state maps
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

  getCardSize() { return 8; }
}
customElements.define('upsai-remoto-card', UpsaiRemotoCard);
