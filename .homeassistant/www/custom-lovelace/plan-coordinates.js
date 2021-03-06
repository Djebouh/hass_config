class PlanCoordinates extends HTMLElement {

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  setConfig(config) {
    const root = this.shadowRoot;
    if (root.lastChild) root.removeChild(root.lastChild);
    this.style.display = 'none';
    const card = document.createElement('div');
    card.id = "plan-coordinates"
    const content = document.createElement('div');
    const style = document.createElement('style');
    style.textContent = `
        #plan-coordinates {
          position: absolute;
          right: 0px;
          top: 16px;
          z-index: 1000;
        }
        #content {
          background-color: var(--paper-card-background-color);
          border: 1px solid var(--label-badge-blue);
          padding: 16px;
        }
      `;
    content.id = "content";
    card.appendChild(content);
    root.appendChild(style);
    root.appendChild(card);
    document.addEventListener("mousemove", el => {
      if (el.path[0] && el.path[0].tagName == 'IMG') {
        this.style.display = 'block';
        const percentX = Math.ceil((el.pageX - el.path[0].x) * 100 / el.path[0].width);
        const percentY = Math.ceil((el.pageY - el.path[0].y) * 100 / el.path[0].height);
        content.innerHTML = `left: ${percentX}%<br/>top: ${percentY}%`;
      }
    });
  }
  set hass(hass) {
  }

  getCardSize() {
    return 1;
  }
}
customElements.define('plan-coordinates', PlanCoordinates);
