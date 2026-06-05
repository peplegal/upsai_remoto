class UpsaiRemotoCard extends HTMLElement {
  set hass(hass) {
    if (!this.content) {
      this.innerHTML = `
        <ha-card header="UPSAI Remoto">
          <style>
            .grid-container { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; padding: 15px; text-align: center; }
            .telemetry-val { font-size: 24px; font-weight: bold; color: var(--primary-color); }
            .tabular-control { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 5px; padding: 10px; align-items: center; }
            .header-row { font-weight: bold; border-bottom: 1px solid var(--divider-color); padding-bottom: 5px; }
          </style>
          <div class="grid-container">
            <div><div><b>Rede Elétrica</b></div><div class="telemetry-val" id="vin">- V</div></div>
            <div><div><b>Tensão Saída</b></div><div class="telemetry-val" id="vout">- V</div></div>
            <div><div><b>Consumo</b></div><div class="telemetry-val" id="power">- %</div></div>
          </div>
          <div style="padding: 0 15px 15px 15px;">
            <b>Estado do Sistema:</b> <span id="msg">Iniciando...</span>
          </div>
          <div style="padding: 10px 15px;">
            <div class="tabular-control header-row">
              <div>CANAL</div><div>ATIVAR</div><div>TRAVAR</div><div>REINICIAR</div>
            </div>
            ${[0,1,2,3,4,5,6,7].map(i => `
              <div class="tabular-control">
                <div><b>SAÍDA ${i}</b></div>
                <div><ha-switch id="out_${i}"></ha-switch></div>
                <div><ha-icon-button id="lock_${i}" icon="mdi:lock"></ha-icon-button></div>
                <div><ha-button id="reboot_${i}">Reset</ha-button></div>
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

  _setupListeners() {
    // Hooks user interaction clicks directly back into HA entities
    this.addEventListener('click', (ev) => {
      const id = ev.target.id;
      if (!id) return;
      
      const [type, index] = id.split('_');
      if (type === 'out') {
        this._hass.callService('switch', 'toggle', { entity_id: `switch.${this.config.device_id}_out0_${index}` });
      } else if (type === 'lock') {
        this._hass.callService('switch', 'toggle', { entity_id: `switch.${this.config.device_id}_lock0_${index}` });
      } else if (type === 'reboot') {
        this._hass.callService('button', 'press', { entity_id: `button.${this.config.device_id}_reboot0_${index}` });
      }
    });
  }

  _updateStates(hass) {
    this._hass = hass;
    const devId = this.config.device_id;
    
    // Dynamically query entities populated by your Python WebSocket Engine
    const vin = hass.states[`sensor.${devId}_vin`]?.state || '-';
    const vout = hass.states[`sensor.${devId}_vout`]?.state || '-';
    const power = hass.states[`sensor.${devId}_power`]?.state || '-';
    const msg = hass.states[`sensor.${devId}_msg`]?.state || '-';

    this.querySelector('#vin').innerText = `${vin} V`;
    this.querySelector('#vout').innerText = `${vout} V`;
    this.querySelector('#power').innerText = `${power} %`;
    this.querySelector('#msg').innerText = msg;

    for (let i = 0; i < 8; i++) {
      const swState = hass.states[`switch.${devId}_out0_${i}`]?.state === 'on';
      const lockState = hass.states[`switch.${devId}_lock0_${i}`]?.state === 'on';
      
      const swEl = this.querySelector(`#out_${i}`);
      const lockEl = this.querySelector(`#lock_${i}`);
      if (swEl) swEl.checked = swState;
      if (lockEl) lockEl.icon = lockState ? "mdi:lock" : "mdi:lock-open";
    }
  }

  setConfig(config) {
    if (!config.device_id) throw new Error('Please define device_id');
    this.config = config;
  }

  getCardSize() { return 5; }
}
customElements.define('upsai-remoto-card', UpsaiRemotoCard);
