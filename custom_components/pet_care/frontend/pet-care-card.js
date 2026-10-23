// Pet Care card: tiles that look like Home Assistant's own, and dialogs made for each kind of record.
// Every card points at the pet's log sensor, whose `card` attribute says where everything else is.

const VERSION = "0.3.1";

const TEXT = {
  pt: {
    today: "Hoje", pending: "Por dar", given: "Dada", skipped: "Saltada", missed: "Falhou",
    amounts: { all: "Tudo", half: "Metade", little: "Pouco", none: "Nada" },
    ate: { all: "Comeu tudo", half: "Comeu metade", little: "Comeu pouco", none: "Não comeu" },
    symptoms: {
      vomit: "Vómito", soft_stool: "Fezes moles", diarrhea: "Diarreia", itching: "Coceira forte",
      paw_licking: "Patas", red_eyes_ears: "Olhos/orelhas", no_appetite: "Sem apetite",
      lethargy: "Letargia", other: "Outro",
    },
    kinds: { ointment: "Pomada", spray: "Spray", pill: "Comprimido", drops: "Gotas", shampoo: "Shampoo", injection: "Injeção", other: "Outro" },
    meal: "Refeição", symptom: "Sintoma", snack: "Snack", weight: "Peso", treatment: "Tratamento",
    newTreatment: "Novo tratamento", editTreatment: "Tratamento", medicines: "Remédios de hoje",
    noMedicines: "Sem remédios hoje", details: "Mais detalhes", grams: "Gramas", note: "Nota",
    when: "Quando", now: "Agora", save: "Guardar", cancel: "Cancelar", undo: "Desfazer",
    done: "Feito hoje", otherDay: "Noutra data", lastDone: "Último", never: "Sem registo",
    daysAgo: (n) => (n === 0 ? "hoje" : n === 1 ? "ontem" : `há ${n} dias`),
    inDays: (n) => (n === 0 ? "hoje" : n === 1 ? "amanhã" : n < 0 ? `atrasado ${-n} d` : `daqui a ${n} d`),
    sunnyDay: "dia de sol", planSun: "Escolher dia de sol", shedding: "Época de troca de pelo",
    what: "O quê", name: "Nome", kind: "Tipo", times: "Horas", addTime: "Outra hora", dose: "Dose",
    start: "Início", end: "Último dia", noEnd: "Sem fim", forDays: "Durar", endTreatment: "Terminar tratamento",
    saved: "Registado", undone: "Desfeito", gaveAt: (t, by) => `Dada às ${t}${by ? " · " + by : ""}`,
    markGiven: "Dei", markSkipped: "Saltei", undoDose: "Desfazer esta dose", edit: "Editar tratamento",
    upcoming: "Próximas datas", noWeights: "Sem pesagens · toca para pesar", nothing: "Nada marcado", medicinesLeft: (n) => `${n} remédio(s) por dar`,
    lateCare: (n) => `${n} cuidado(s) atrasado(s)`, next: "Próximo", kg: "kg", choose: "Escolhe um",
    mealPending: (name, time) => `${name} por dar · ${time}`,
    ateMeals: (n, total) => (n === total ? (total === 1 ? "Já comeu" : `Comeu as ${total} refeições`) : `Comeu ${n} de ${total} refeições`),
    mealLate: (name) => `${name} por dar`, medicinesDone: "remédios dados", careLate: (name) => `${name} atrasado`,
    treatments: "Tratamentos", until: (d) => `até ${d}`, from: (d) => `começa ${d}`, history: "Histórico", noHistory: "Sem registos", more: "Mostrar mais", care: "Cuidado", yesterday: "Ontem",
    remove: "Apagar", confirmRemove: "Apagar mesmo?", removed: "Apagado", corrected: "Corrigido", failed: "Não deu",
  },
  en: {
    today: "Today", pending: "Pending", given: "Given", skipped: "Skipped", missed: "Missed",
    amounts: { all: "All", half: "Half", little: "Little", none: "None" },
    ate: { all: "Ate it all", half: "Ate half", little: "Ate a little", none: "Didn't eat" },
    symptoms: {
      vomit: "Vomit", soft_stool: "Soft stool", diarrhea: "Diarrhea", itching: "Itching",
      paw_licking: "Paws", red_eyes_ears: "Eyes/ears", no_appetite: "No appetite",
      lethargy: "Lethargy", other: "Other",
    },
    kinds: { ointment: "Ointment", spray: "Spray", pill: "Pill", drops: "Drops", shampoo: "Shampoo", injection: "Injection", other: "Other" },
    meal: "Meal", symptom: "Symptom", snack: "Snack", weight: "Weight", treatment: "Treatment",
    newTreatment: "New treatment", editTreatment: "Treatment", medicines: "Today's medicines",
    noMedicines: "No medicines today", details: "More details", grams: "Grams", note: "Note",
    when: "When", now: "Now", save: "Save", cancel: "Cancel", undo: "Undo",
    done: "Done today", otherDay: "Another day", lastDone: "Last", never: "Never",
    daysAgo: (n) => (n === 0 ? "today" : n === 1 ? "yesterday" : `${n} days ago`),
    inDays: (n) => (n === 0 ? "today" : n === 1 ? "tomorrow" : n < 0 ? `${-n} d late` : `in ${n} d`),
    sunnyDay: "sunny day", planSun: "Pick a sunny day", shedding: "Shedding season",
    what: "What", name: "Name", kind: "Kind", times: "Times", addTime: "Other time", dose: "Dose",
    start: "Start", end: "Last day", noEnd: "No end", forDays: "Lasts", endTreatment: "End treatment",
    saved: "Saved", undone: "Undone", gaveAt: (t, by) => `Given at ${t}${by ? " · " + by : ""}`,
    markGiven: "Given", markSkipped: "Skipped", undoDose: "Undo this dose", edit: "Edit treatment",
    upcoming: "Upcoming", noWeights: "No weigh-ins · tap to weigh", nothing: "Nothing planned", medicinesLeft: (n) => `${n} medicine(s) pending`,
    lateCare: (n) => `${n} care item(s) late`, next: "Next", kg: "kg", choose: "Pick one",
    mealPending: (name, time) => `${name} pending · ${time}`,
    ateMeals: (n, total) => (n === total ? (total === 1 ? "Has eaten" : `Ate all ${total} meals`) : `Ate ${n} of ${total} meals`),
    mealLate: (name) => `${name} pending`, medicinesDone: "medicines given", careLate: (name) => `${name} late`,
    treatments: "Treatments", until: (d) => `until ${d}`, from: (d) => `starts ${d}`, history: "History", noHistory: "No records", more: "Show more", care: "Care", yesterday: "Yesterday",
    remove: "Delete", confirmRemove: "Really delete?", removed: "Deleted", corrected: "Corrected", failed: "Failed",
  },
};

const SYMPTOM_ICONS = {
  vomit: "mdi:emoticon-sick-outline", soft_stool: "mdi:emoticon-poop-outline", diarrhea: "mdi:water-alert-outline",
  itching: "mdi:allergy", paw_licking: "mdi:paw", red_eyes_ears: "mdi:eye-outline", no_appetite: "mdi:food-off-outline",
  lethargy: "mdi:sleep", other: "mdi:dots-horizontal",
};
const KIND_ICONS = {
  ointment: "mdi:lotion-plus-outline", spray: "mdi:spray", pill: "mdi:pill", drops: "mdi:eyedropper",
  shampoo: "mdi:bottle-tonic-outline", injection: "mdi:needle", other: "mdi:medication-outline",
};
const AMOUNT_ICONS = { all: "mdi:bowl", half: "mdi:circle-half-full", little: "mdi:circle-slice-2", none: "mdi:close-circle-outline" };
const AMOUNT_COLORS = { all: "green", half: "amber", little: "orange", none: "red" };
const ACTIONS = {
  symptom: { icon: "mdi:emoticon-sick-outline", color: "red" },
  snack: { icon: "mdi:food-drumstick-outline", color: "orange" },
  weight: { icon: "mdi:scale-bathroom", color: "blue" },
  treatment: { icon: "mdi:medication-outline", color: "purple" },
  meal: { icon: "mdi:bowl-mix-outline", color: "green" },
};

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const color = (name) => (name ? `var(--${name}-color, var(--state-icon-color))` : "var(--state-icon-color)");
const pad = (n) => String(n).padStart(2, "0");
const localInput = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
const dateInput = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const hhmm = (iso) => { const d = new Date(iso); return `${pad(d.getHours())}:${pad(d.getMinutes())}`; };
const daysBetween = (a, b) => Math.round((new Date(b.toDateString()) - new Date(a.toDateString())) / 86400000);
const parseDay = (s) => { const [y, m, d] = String(s).slice(0, 10).split("-").map(Number); return new Date(y, m - 1, d); };

const TILE_CSS = `
  :host { display: block; height: 100%; }
  ha-card { height: 100%; box-sizing: border-box; overflow: hidden; }
  .tile { display: flex; align-items: center; gap: 10px; padding: 0 10px; height: 100%; min-height: 56px; box-sizing: border-box; cursor: pointer; user-select: none; -webkit-tap-highlight-color: transparent; }
  .tile.vertical { flex-direction: column; justify-content: center; gap: 6px; padding: 10px 6px; text-align: center; }
  .icon { flex: none; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; position: relative; color: var(--c); }
  .icon::before { content: ""; position: absolute; inset: 0; border-radius: 50%; background: var(--c); opacity: .2; }
  .vertical .icon { width: 40px; height: 40px; }
  .vertical .icon::before { display: none; }
  .vertical ha-icon { --mdc-icon-size: 32px; }
  ha-icon { --mdc-icon-size: 24px; position: relative; }
  .text { min-width: 0; display: flex; flex-direction: column; }
  .primary { font-size: 14px; font-weight: 500; line-height: 20px; color: var(--primary-text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .secondary { font-size: 12px; line-height: 16px; color: var(--secondary-text-color); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .vertical .primary { font-size: 13px; white-space: normal; }
  .chart { padding: 0 12px 10px; height: calc(100% - 60px); box-sizing: border-box; }
  .chart svg { width: 100%; height: 100%; overflow: visible; }
  .chart text { font-size: 10px; fill: var(--secondary-text-color); }
  .grid { display: grid; grid-template-columns: repeat(var(--cols, 2), minmax(0, 1fr)); gap: 8px; }
  .grid > ha-card { height: 56px; }
  .list { padding: 6px 12px; }
  .row { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; font-size: 14px; border-bottom: 1px solid var(--divider-color); }
  .row:last-child { border-bottom: none; }
  .row .day { color: var(--secondary-text-color); white-space: nowrap; }
  .empty { padding: 16px; color: var(--secondary-text-color); font-size: 14px; }
  .dayhead { font-size: 12px; font-weight: 500; color: var(--secondary-text-color); padding: 12px 0 4px; text-transform: capitalize; }
  .dayhead:first-child { padding-top: 4px; }
  .entry { display: flex; align-items: center; gap: 10px; padding: 6px 0; cursor: pointer; border-bottom: 1px solid var(--divider-color); color: var(--c); -webkit-tap-highlight-color: transparent; }
  .entry .icon { width: 32px; height: 32px; }
  .entry ha-icon { --mdc-icon-size: 20px; }
  .entry .text { flex: 1; }
  .entry .day { font-size: 12px; color: var(--secondary-text-color); white-space: nowrap; }
  .more { width: 100%; background: none; border: none; color: var(--primary-color); font: inherit; font-size: 14px; padding: 10px 0 4px; cursor: pointer; }
`;

function lang(hass) {
  return hass?.locale?.language || hass?.language || undefined;
}

function t(hass) {
  return (hass?.locale?.language || hass?.language || "en").startsWith("pt") ? TEXT.pt : TEXT.en;
}

// Only these services answer; asking the others for a response makes Home Assistant refuse the call.
const ANSWERS = new Set(["log_care", "log_meal", "log_snack", "log_symptom", "log_weight", "log_dose", "add_treatment", "export"]);

async function callService(hass, service, data) {
  const answers = ANSWERS.has(service);
  const result = await hass.callWS({ type: "call_service", domain: "pet_care", service, service_data: data, ...(answers ? { return_response: true } : {}) });
  return (answers && result?.response) || {};
}

// ---------- toast -------------------------------------------------------------------------

function toast(hass, message, undoIds) {
  document.querySelectorAll("pet-care-toast").forEach((el) => el.remove());
  const el = document.createElement("pet-care-toast");
  const T = t(hass);
  el.innerHTML = `<div class="bar"><span>${esc(message)}</span>${undoIds?.length ? `<button>${esc(T.undo)}</button>` : ""}</div>`;
  el.attachShadow({ mode: "open" }).innerHTML = `<style>
    .bar { position: fixed; left: 50%; bottom: 24px; transform: translateX(-50%); z-index: 10000; display: flex; align-items: center; gap: 16px;
      background: var(--primary-text-color); color: var(--card-background-color, #fff); padding: 12px 16px; border-radius: 8px;
      font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); font-size: 14px; box-shadow: 0 4px 12px rgba(0,0,0,.3); max-width: calc(100vw - 48px); }
    button { background: none; border: none; color: var(--primary-color); font-weight: 600; font-size: 14px; cursor: pointer; text-transform: uppercase; padding: 0; }
  </style>${el.innerHTML}`;
  document.body.appendChild(el);
  el.shadowRoot.querySelector("button")?.addEventListener("click", async () => {
    el.remove();
    const entryId = el.dataset.entry;
    try {
      for (const id of undoIds) await callService(hass, "delete_entry", { entry: id, config_entry_id: entryId });
      toast(hass, T.undone);
    } catch (err) {
      toast(hass, `${T.failed}: ${err?.message || err}`);
    }
  });
  setTimeout(() => el.remove(), 6000);
  return el;
}

// ---------- dialog ------------------------------------------------------------------------

const DIALOG_CSS = `
  .scrim { position: fixed; inset: 0; z-index: 9999; background: rgba(0,0,0,.45); display: flex; align-items: center; justify-content: center; }
  .sheet { background: var(--ha-card-background, var(--card-background-color, #1c1c1c)); color: var(--primary-text-color);
    border-radius: var(--ha-dialog-border-radius, 24px); width: min(440px, calc(100vw - 32px)); max-height: calc(100vh - 48px); overflow: auto;
    box-shadow: 0 8px 32px rgba(0,0,0,.4); font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); box-sizing: border-box; padding: 20px; }
  @media (max-width: 600px) { .scrim { align-items: flex-end; } .sheet { width: 100vw; border-radius: 24px 24px 0 0; max-height: 88vh; padding-bottom: calc(20px + env(safe-area-inset-bottom)); } }
  h2 { margin: 0 0 4px; font-size: 20px; font-weight: 500; display: flex; align-items: center; gap: 10px; }
  .sub { color: var(--secondary-text-color); font-size: 13px; margin-bottom: 16px; }
  .big { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin: 12px 0; }
  .big button, .chips button { border: 1px solid var(--divider-color); background: none; color: var(--primary-text-color); border-radius: 16px;
    display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; padding: 14px 4px; font-size: 13px; cursor: pointer; font-family: inherit; }
  .big button ha-icon { --mdc-icon-size: 28px; color: var(--c); }
  .big button:hover, .chips button:hover { background: rgba(127,127,127,.08); }
  .chips { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 12px 0; }
  .chips.row4 { grid-template-columns: repeat(4, 1fr); }
  .chips button { padding: 10px 4px; border-radius: 12px; }
  .chips button ha-icon { --mdc-icon-size: 22px; color: var(--c, var(--secondary-text-color)); }
  .chips button.on { border-color: var(--primary-color); background: color-mix(in srgb, var(--primary-color) 14%, transparent); }
  label { display: block; font-size: 12px; color: var(--secondary-text-color); margin: 12px 0 4px; }
  input, textarea, select { width: 100%; box-sizing: border-box; background: var(--input-fill-color, rgba(127,127,127,.08)); color: var(--primary-text-color);
    border: none; border-bottom: 1px solid var(--input-idle-line-color, var(--divider-color)); border-radius: 8px 8px 0 0; padding: 10px 12px; font-size: 15px; font-family: inherit; }
  input:focus, textarea:focus { outline: none; border-bottom: 2px solid var(--primary-color); }
  textarea { min-height: 64px; resize: vertical; }
  .two { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .stepper { display: flex; align-items: center; gap: 8px; margin: 12px 0; }
  .stepper input { text-align: center; font-size: 28px; font-weight: 500; }
  .stepper button { width: 52px; height: 52px; flex: none; border-radius: 50%; border: 1px solid var(--divider-color); background: none; color: var(--primary-text-color); font-size: 24px; cursor: pointer; }
  .actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 20px; flex-wrap: wrap; }
  .actions button { border: none; border-radius: 20px; padding: 10px 20px; font-size: 14px; font-weight: 500; cursor: pointer; font-family: inherit; }
  .primary-btn { background: var(--primary-color); color: var(--text-primary-color, #fff); }
  .primary-btn:disabled { opacity: .4; cursor: default; }
  .text-btn { background: none; color: var(--primary-color); }
  .danger-btn { background: none; color: var(--error-color, #db4437); margin-right: auto; }
  details summary { cursor: pointer; color: var(--primary-color); font-size: 14px; margin-top: 8px; }
  .wide { width: 100%; justify-content: center; display: flex; }
  .items { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
  .item { display: flex; align-items: center; gap: 12px; padding: 12px; border: 1px solid var(--divider-color); border-radius: 12px; background: none;
    color: var(--primary-text-color); font-family: inherit; text-align: left; cursor: pointer; }
  .item:hover { background: rgba(127,127,127,.08); }
  .item > ha-icon:first-child { color: var(--c); }
  .item > ha-icon:last-child { color: var(--secondary-text-color); margin-left: auto; }
  .item span { display: flex; flex-direction: column; gap: 2px; min-width: 0; font-size: 15px; }
  .item b { font-weight: 500; }
  .item small { color: var(--secondary-text-color); font-size: 12px; }
`;

function openDialog(hass, title, icon, iconColor, body, onReady) {
  document.querySelectorAll("pet-care-dialog").forEach((el) => el.remove());
  const host = document.createElement("pet-care-dialog");
  const root = host.attachShadow({ mode: "open" });
  root.innerHTML = `<style>${DIALOG_CSS}</style><div class="scrim"><div class="sheet" role="dialog" aria-modal="true">
    <h2>${icon ? `<ha-icon icon="${icon}" style="color:${color(iconColor)}"></ha-icon>` : ""}${esc(title)}</h2>${body}</div></div>`;
  const onKey = (ev) => { if (ev.key === "Escape") close(); };
  const close = () => { host.remove(); document.removeEventListener("keydown", onKey); };
  root.querySelector(".scrim").addEventListener("click", (ev) => { if (ev.target.classList.contains("scrim")) close(); });
  document.addEventListener("keydown", onKey);
  root.querySelectorAll("[data-close]").forEach((b) => b.addEventListener("click", close));
  document.body.appendChild(host);
  onReady?.(root, close);
  return { root, close };
}

const whenField = (T) => `<label>${esc(T.when)}</label><input type="datetime-local" name="at" value="${localInput(new Date())}">`;
const atValue = (root) => {
  const v = root.querySelector("[name=at]")?.value;
  if (!v) return undefined;
  const d = new Date(v);
  return Math.abs(d - new Date()) < 90000 ? undefined : d.toISOString();
};
const val = (root, name) => { const v = root.querySelector(`[name=${name}]`)?.value?.trim(); return v ? v : undefined; };

function mealDialog(hass, card, meal) {
  const T = t(hass);
  const meals = card.meals;
  let slot = meal || meals[0].key;
  const body = `
    ${meals.length > 1 ? `<div class="chips row4">${meals.map((m) => `<button data-slot="${esc(m.key)}" class="${m.key === slot ? "on" : ""}">${esc(m.name)}<small>${esc(m.time)}</small></button>`).join("")}</div>` : ""}
    <div class="big">${Object.entries(T.amounts).map(([k, label]) => `<button data-amount="${k}" style="--c:${color(AMOUNT_COLORS[k])}"><ha-icon icon="${AMOUNT_ICONS[k]}"></ha-icon>${esc(label)}</button>`).join("")}</div>
    <details><summary>${esc(T.details)}</summary>
      <div class="two"><div><label>${esc(T.grams)}</label><input name="grams" type="number" inputmode="decimal" min="0" placeholder="${esc(card.food?.food_grams ?? "")}"></div>
      <div>${whenField(T)}</div></div>
      <label>${esc(T.note)}</label><textarea name="note"></textarea>
    </details>
    <div class="actions"><button class="text-btn" data-close>${esc(T.cancel)}</button></div>`;
  openDialog(hass, `${T.meal} · ${card.pet}`, "mdi:bowl-mix", "green", body, (root, close) => {
    root.querySelectorAll("[data-slot]").forEach((b) => b.addEventListener("click", () => {
      slot = b.dataset.slot;
      root.querySelectorAll("[data-slot]").forEach((x) => x.classList.toggle("on", x === b));
    }));
    root.querySelectorAll("[data-amount]").forEach((b) => b.addEventListener("click", async () => {
      const res = await callService(hass, "log_meal", {
        config_entry_id: card.entry_id, meal: slot, amount: b.dataset.amount,
        grams: val(root, "grams") ? Number(val(root, "grams")) : undefined, note: val(root, "note"), at: atValue(root),
      });
      close();
      toast(hass, `${T.saved}: ${T.ate[b.dataset.amount]}`, res.ids).dataset.entry = card.entry_id;
    }));
  });
}

function symptomDialog(hass, card) {
  const T = t(hass);
  let chosen = null;
  const body = `
    <div class="chips">${Object.entries(T.symptoms).map(([k, label]) => `<button data-s="${k}" style="--c:${color("red")}"><ha-icon icon="${SYMPTOM_ICONS[k]}"></ha-icon>${esc(label)}</button>`).join("")}</div>
    <label>${esc(T.note)}</label><textarea name="note"></textarea>
    ${whenField(T)}
    <div class="actions"><button class="text-btn" data-close>${esc(T.cancel)}</button><button class="primary-btn" data-save disabled>${esc(T.save)}</button></div>`;
  openDialog(hass, `${T.symptom} · ${card.pet}`, ACTIONS.symptom.icon, "red", body, (root, close) => {
    const save = root.querySelector("[data-save]");
    root.querySelectorAll("[data-s]").forEach((b) => b.addEventListener("click", () => {
      chosen = b.dataset.s;
      root.querySelectorAll("[data-s]").forEach((x) => x.classList.toggle("on", x === b));
      save.disabled = false;
    }));
    save.addEventListener("click", async () => {
      const res = await callService(hass, "log_symptom", { config_entry_id: card.entry_id, symptom: chosen, note: val(root, "note"), at: atValue(root) });
      close();
      toast(hass, `${T.saved}: ${T.symptoms[chosen]}`, res.ids).dataset.entry = card.entry_id;
    });
  });
}

function weightDialog(hass, card) {
  const T = t(hass);
  const last = Number(hass.states[card.weight]?.state);
  const start = Number.isFinite(last) ? last : 30;
  const body = `
    <div class="stepper"><button data-step="-0.1">−</button><input name="kg" type="number" inputmode="decimal" step="0.1" value="${start.toFixed(1)}"><button data-step="0.1">+</button></div>
    <div class="sub" style="text-align:center">${esc(T.kg)}</div>
    <label>${esc(T.note)}</label><textarea name="note"></textarea>
    ${whenField(T)}
    <div class="actions"><button class="text-btn" data-close>${esc(T.cancel)}</button><button class="primary-btn" data-save>${esc(T.save)}</button></div>`;
  openDialog(hass, `${T.weight} · ${card.pet}`, ACTIONS.weight.icon, "blue", body, (root, close) => {
    const input = root.querySelector("[name=kg]");
    root.querySelectorAll("[data-step]").forEach((b) => b.addEventListener("click", () => {
      input.value = (Number(input.value || 0) + Number(b.dataset.step)).toFixed(1);
    }));
    root.querySelector("[data-save]").addEventListener("click", async () => {
      const res = await callService(hass, "log_weight", { config_entry_id: card.entry_id, kg: Number(input.value), note: val(root, "note"), at: atValue(root) });
      close();
      toast(hass, `${T.saved}: ${input.value} kg`, res.ids).dataset.entry = card.entry_id;
    });
  });
}

function snackDialog(hass, card, recent) {
  const T = t(hass);
  const known = [...new Set((recent || []).filter((e) => e.type === "snack").map((e) => e.value))].slice(0, 6);
  const body = `
    ${known.length ? `<div class="chips">${known.map((k) => `<button data-k="${esc(k)}">${esc(k)}</button>`).join("")}</div>` : ""}
    <label>${esc(T.what)}</label><input name="what" type="text">
    <div class="two"><div><label>${esc(T.grams)}</label><input name="grams" type="number" inputmode="decimal" min="0"></div><div>${whenField(T)}</div></div>
    <label>${esc(T.note)}</label><textarea name="note"></textarea>
    <div class="actions"><button class="text-btn" data-close>${esc(T.cancel)}</button><button class="primary-btn" data-save>${esc(T.save)}</button></div>`;
  openDialog(hass, `${T.snack} · ${card.pet}`, ACTIONS.snack.icon, "orange", body, (root, close) => {
    root.querySelectorAll("[data-k]").forEach((b) => b.addEventListener("click", () => { root.querySelector("[name=what]").value = b.dataset.k; }));
    root.querySelector("[data-save]").addEventListener("click", async () => {
      const what = val(root, "what");
      if (!what) return root.querySelector("[name=what]").focus();
      const res = await callService(hass, "log_snack", {
        config_entry_id: card.entry_id, what, grams: val(root, "grams") ? Number(val(root, "grams")) : undefined, note: val(root, "note"), at: atValue(root),
      });
      close();
      toast(hass, `${T.saved}: ${what}`, res.ids).dataset.entry = card.entry_id;
    });
  });
}

function careDialog(hass, card, care) {
  const T = t(hass);
  const st = hass.states[care.entity];
  const a = st?.attributes || {};
  const body = `
    <div class="sub">${esc(a.last_done ? `${T.lastDone}: ${parseDay(a.last_done).toLocaleDateString(lang(hass))}` : T.never)}${a.due ? ` · ${T.next}: ${parseDay(a.planned_day || a.due).toLocaleDateString(lang(hass))}` : ""}</div>
    <button class="primary-btn wide" data-today style="border:none;border-radius:20px;padding:14px;font-size:15px;cursor:pointer;width:100%">${esc(T.done)}</button>
    <details><summary>${esc(T.otherDay)}</summary><label>${esc(T.when)}</label><input type="date" name="day" value="${dateInput(new Date())}">
      <label>${esc(T.note)}</label><textarea name="note"></textarea>
      <div class="actions"><button class="primary-btn" data-other>${esc(T.save)}</button></div></details>
    ${care.kind === "sunny" && card.plan ? `<div class="actions"><button class="text-btn" data-plan>☀️ ${esc(T.planSun)}</button></div>` : ""}
    ${care.kind === "shedding" && card.shedding ? `<label style="display:flex;align-items:center;gap:8px;font-size:14px;color:var(--primary-text-color)"><input type="checkbox" data-shed style="width:auto" ${hass.states[card.shedding]?.state === "on" ? "checked" : ""}>${esc(T.shedding)}</label>` : ""}
    <div class="actions"><button class="text-btn" data-close>${esc(T.cancel)}</button></div>`;
  openDialog(hass, `${care.name} · ${card.pet}`, care.icon || "mdi:paw", "teal", body, (root, close) => {
    const log = async (at, note) => {
      const res = await callService(hass, "log_care", { config_entry_id: card.entry_id, care: care.key, at, note });
      close();
      toast(hass, `${T.saved}: ${care.name}`, res.ids).dataset.entry = card.entry_id;
    };
    root.querySelector("[data-today]").addEventListener("click", () => log(undefined, undefined));
    root.querySelector("[data-other]").addEventListener("click", () => {
      const d = root.querySelector("[name=day]").value;
      log(d ? new Date(`${d}T12:00`).toISOString() : undefined, val(root, "note"));
    });
    root.querySelector("[data-plan]")?.addEventListener("click", async () => {
      await hass.callService("button", "press", { entity_id: card.plan });
      close();
    });
    root.querySelector("[data-shed]")?.addEventListener("change", (ev) => {
      hass.callService("switch", ev.target.checked ? "turn_on" : "turn_off", { entity_id: card.shedding });
    });
  });
}

function treatmentDialog(hass, card, treatment) {
  const T = t(hass);
  const editing = !!treatment;
  const tr = treatment || { name: "", kind: "ointment", times: [], start: dateInput(new Date()), end: null, dose: "" };
  const presets = ["07:45", "13:00", "19:45"];
  let times = new Set(tr.times);
  let kind = tr.kind || "other";
  const timeChips = () => [...new Set([...presets, ...times])].sort().map((x) => `<button data-t="${x}" class="${times.has(x) ? "on" : ""}">${x}</button>`).join("");
  const body = `
    <label>${esc(T.name)}</label><input name="name" type="text" value="${esc(tr.name)}">
    <label>${esc(T.kind)}</label><div class="chips row4">${Object.entries(T.kinds).map(([k, label]) => `<button data-kind="${k}" class="${k === kind ? "on" : ""}" style="--c:${color("purple")}"><ha-icon icon="${KIND_ICONS[k]}"></ha-icon>${esc(label)}</button>`).join("")}</div>
    <label>${esc(T.times)}</label><div class="chips row4" data-times>${timeChips()}</div>
    <div class="two"><input type="time" name="extra"><button class="text-btn" data-addtime style="border:1px solid var(--divider-color);border-radius:12px;cursor:pointer">+ ${esc(T.addTime)}</button></div>
    <div class="two"><div><label>${esc(T.start)}</label><input type="date" name="start" value="${esc(tr.start || "")}"></div>
      <div><label>${esc(T.end)}</label><input type="date" name="end" value="${esc(tr.end || "")}" placeholder="${esc(T.noEnd)}"></div></div>
    <label>${esc(T.forDays)}</label><div class="chips row4">${[5, 7, 10, 15].map((n) => `<button data-days="${n}">${n} d</button>`).join("")}</div>
    <label>${esc(T.dose)}</label><input name="dose" type="text" value="${esc(tr.dose || "")}">
    <div class="actions">${editing ? `<button class="danger-btn" data-end>${esc(T.endTreatment)}</button>` : ""}<button class="text-btn" data-close>${esc(T.cancel)}</button><button class="primary-btn" data-save>${esc(T.save)}</button></div>`;
  openDialog(hass, editing ? `${T.editTreatment} · ${tr.name}` : `${T.newTreatment} · ${card.pet}`, KIND_ICONS[kind], "purple", body, (root, close) => {
    const bindTimes = () => root.querySelectorAll("[data-t]").forEach((b) => b.addEventListener("click", () => {
      times.has(b.dataset.t) ? times.delete(b.dataset.t) : times.add(b.dataset.t);
      b.classList.toggle("on", times.has(b.dataset.t));
    }));
    bindTimes();
    root.querySelectorAll("[data-kind]").forEach((b) => b.addEventListener("click", () => {
      kind = b.dataset.kind;
      root.querySelectorAll("[data-kind]").forEach((x) => x.classList.toggle("on", x === b));
    }));
    root.querySelector("[data-addtime]").addEventListener("click", () => {
      const v = root.querySelector("[name=extra]").value;
      if (!v) return;
      times.add(v.slice(0, 5));
      root.querySelector("[data-times]").innerHTML = timeChips();
      bindTimes();
    });
    root.querySelectorAll("[data-days]").forEach((b) => b.addEventListener("click", () => {
      const s = root.querySelector("[name=start]").value ? parseDay(root.querySelector("[name=start]").value) : new Date();
      const e = new Date(s); e.setDate(e.getDate() + Number(b.dataset.days) - 1);
      root.querySelector("[name=end]").value = dateInput(e);
    }));
    root.querySelector("[data-end]")?.addEventListener("click", async () => {
      await callService(hass, "end_treatment", { config_entry_id: card.entry_id, treatment: tr.id });
      close();
      toast(hass, `${T.endTreatment}: ${tr.name}`);
    });
    root.querySelector("[data-save]").addEventListener("click", async () => {
      const name = val(root, "name");
      if (!name || !times.size) return;
      const data = { config_entry_id: card.entry_id, name, kind, times: [...times].sort().join(", "), dose: val(root, "dose"), start: val(root, "start"), end: val(root, "end") || null };
      if (editing) await callService(hass, "update_treatment", { ...data, treatment: tr.id });
      else await callService(hass, "add_treatment", data);
      close();
      toast(hass, `${T.saved}: ${name}`);
    });
  });
}

function treatmentsDialog(hass, card) {
  const T = t(hass);
  if (!card.treatments.length) return treatmentDialog(hass, card);
  const day = (d) => parseDay(d).toLocaleDateString(lang(hass), { day: "2-digit", month: "2-digit" });
  const today = dateInput(new Date());
  const rows = card.treatments.map((tr, i) => {
    const when = tr.start && tr.start > today ? T.from(day(tr.start)) : tr.end ? T.until(day(tr.end)) : T.noEnd;
    return `<button class="item" data-i="${i}" style="--c:${color("purple")}"><ha-icon icon="${KIND_ICONS[tr.kind] || KIND_ICONS.other}"></ha-icon>
      <span><b>${esc(tr.name)}</b><small>${esc([tr.times.join(" · "), when, tr.dose].filter(Boolean).join(" · "))}</small></span><ha-icon icon="mdi:chevron-right"></ha-icon></button>`;
  }).join("");
  const body = `<div class="items">${rows}</div>
    <div class="actions"><button class="text-btn" data-close>${esc(T.cancel)}</button><button class="primary-btn" data-new>+ ${esc(T.newTreatment)}</button></div>`;
  openDialog(hass, `${T.treatments} · ${card.pet}`, ACTIONS.treatment.icon, "purple", body, (root, close) => {
    root.querySelectorAll("[data-i]").forEach((b) => b.addEventListener("click", () => { close(); treatmentDialog(hass, card, card.treatments[Number(b.dataset.i)]); }));
    root.querySelector("[data-new]").addEventListener("click", () => { close(); treatmentDialog(hass, card); });
  });
}

function doseDialog(hass, card, dose) {
  const T = t(hass);
  const treatment = card.treatments.find((x) => x.id === dose.id);
  const body = `
    <div class="sub">${esc(dose.status ? `${T[dose.status] || dose.status}${dose.at ? " · " + hhmm(dose.at) : ""}${dose.by ? " · " + dose.by : ""}` : T.pending)}${dose.dose ? ` · ${esc(dose.dose)}` : ""}</div>
    <div class="actions">
      ${treatment ? `<button class="text-btn" data-edit>${esc(T.edit)}</button>` : ""}
      ${dose.status ? `<button class="danger-btn" data-undo>${esc(T.undoDose)}</button>` : `<button class="text-btn" data-skip>${esc(T.markSkipped)}</button><button class="primary-btn" data-give>${esc(T.markGiven)}</button>`}
    </div>`;
  openDialog(hass, `${dose.treatment} · ${dose.time}`, KIND_ICONS[dose.kind] || KIND_ICONS.other, "purple", body, (root, close) => {
    const mark = async (status) => {
      const res = await callService(hass, "log_dose", { config_entry_id: card.entry_id, treatment: dose.id, time: dose.time, status });
      close();
      toast(hass, `${dose.treatment}: ${T[status]}`, res.ids).dataset.entry = card.entry_id;
    };
    root.querySelector("[data-give]")?.addEventListener("click", () => mark("given"));
    root.querySelector("[data-skip]")?.addEventListener("click", () => mark("skipped"));
    root.querySelector("[data-undo]")?.addEventListener("click", async () => {
      await callService(hass, "delete_entry", { config_entry_id: card.entry_id, entry: dose.entry });
      close();
      toast(hass, T.undone);
    });
    root.querySelector("[data-edit]")?.addEventListener("click", () => { close(); treatmentDialog(hass, card, treatment); });
  });
}

const TYPE_TITLES = { meal: "meal", snack: "snack", symptom: "symptom", weight: "weight", dose: "dose", treatment: "treatment", care: "care" };

function entryLook(card, e) {
  if (e.type === "meal") return { icon: AMOUNT_ICONS[e.value] || "mdi:bowl-mix", color: AMOUNT_COLORS[e.value] || "green" };
  if (e.type === "symptom") return { icon: SYMPTOM_ICONS[e.key] || ACTIONS.symptom.icon, color: "red" };
  if (e.type === "dose") return { icon: e.value === "given" ? "mdi:check-circle" : "mdi:debug-step-over", color: e.value === "given" ? "purple" : "grey" };
  if (e.type === "care") return { icon: card.care.find((c) => c.key === e.key)?.icon || "mdi:paw", color: "teal" };
  return ACTIONS[e.type] || { icon: "mdi:note-outline", color: "grey" };
}

function entryDialog(hass, card, e) {
  const T = t(hass);
  const original = localInput(new Date(e.at));
  let meal = e.key, amount = e.value, symptom = e.key, status = e.value;
  const chips = (name, options, current) => `<div class="chips row4">${options.map(([k, label, icon, c]) => `<button data-${name}="${esc(k)}" class="${k === current ? "on" : ""}"${c ? ` style="--c:${color(c)}"` : ""}>${icon ? `<ha-icon icon="${icon}"></ha-icon>` : ""}${esc(label)}</button>`).join("")}</div>`;
  const note = `<label>${esc(T.note)}</label><textarea name="note">${esc(e.note || "")}</textarea>`;
  const grams = `<label>${esc(T.grams)}</label><input name="grams" type="number" inputmode="decimal" min="0" value="${esc(e.grams ?? "")}">`;
  const fields = {
    meal: () => `${card.meals.length > 1 ? chips("meal", card.meals.map((m) => [m.key, m.name]), meal) : ""}
      ${chips("amount", Object.entries(T.amounts).map(([k, label]) => [k, label, AMOUNT_ICONS[k], AMOUNT_COLORS[k]]), amount)}${grams}${note}`,
    snack: () => `<label>${esc(T.what)}</label><input name="what" type="text" value="${esc(e.value)}">${grams}${note}`,
    symptom: () => `<div class="chips">${Object.entries(T.symptoms).map(([k, label]) => `<button data-symptom="${k}" class="${k === symptom ? "on" : ""}" style="--c:${color("red")}"><ha-icon icon="${SYMPTOM_ICONS[k]}"></ha-icon>${esc(label)}</button>`).join("")}</div>${note}`,
    weight: () => `<div class="stepper"><button data-step="-0.1">−</button><input name="kg" type="number" inputmode="decimal" step="0.1" value="${esc(Number(e.value).toFixed(1))}"><button data-step="0.1">+</button></div>${note}`,
    dose: () => chips("status", [["given", T.given, "mdi:check-circle", "purple"], ["skipped", T.skipped, "mdi:debug-step-over", "grey"]], status),
  };
  const body = `<div class="sub">${esc(e.label)}${e.by ? ` · ${esc(e.by)}` : ""}</div>
    ${(fields[e.type] || (() => note))()}
    <label>${esc(T.when)}</label><input type="datetime-local" name="at" value="${original}">
    <div class="actions"><button class="danger-btn" data-remove>${esc(T.remove)}</button><button class="text-btn" data-close>${esc(T.cancel)}</button><button class="primary-btn" data-save>${esc(T.save)}</button></div>`;
  const look = entryLook(card, e);
  openDialog(hass, `${T[TYPE_TITLES[e.type]] || e.type} · ${new Date(e.at).toLocaleDateString(lang(hass), { weekday: "short", day: "2-digit", month: "2-digit" })}`, look.icon, look.color, body, (root, close) => {
    const pick = (name, set) => root.querySelectorAll(`[data-${name}]`).forEach((b) => b.addEventListener("click", () => {
      set(b.dataset[name]);
      root.querySelectorAll(`[data-${name}]`).forEach((x) => x.classList.toggle("on", x === b));
    }));
    pick("meal", (v) => { meal = v; });
    pick("amount", (v) => { amount = v; });
    pick("symptom", (v) => { symptom = v; });
    pick("status", (v) => { status = v; });
    const kg = root.querySelector("[name=kg]");
    root.querySelectorAll("[data-step]").forEach((b) => b.addEventListener("click", () => { kg.value = (Number(kg.value || 0) + Number(b.dataset.step)).toFixed(1); }));
    const run = async (service, data, done) => {
      try {
        await callService(hass, service, { config_entry_id: card.entry_id, entry: e.id, ...data });
        close();
        toast(hass, done);
      } catch (err) {
        toast(hass, `${T.failed}: ${err?.message || err}`);
      }
    };
    const remove = root.querySelector("[data-remove]");
    remove.addEventListener("click", () => {
      if (remove.dataset.armed) return run("delete_entry", {}, T.removed);
      remove.dataset.armed = "1";
      remove.textContent = T.confirmRemove;
    });
    root.querySelector("[data-save]").addEventListener("click", () => {
      const at = root.querySelector("[name=at]").value;
      const data = at && at !== original ? { at: new Date(at).toISOString() } : {};
      const text = (name) => root.querySelector(`[name=${name}]`)?.value.trim() ?? "";
      if (e.type !== "dose") data.note = text("note");
      if (e.type === "meal") Object.assign(data, { meal, amount, grams: text("grams") });
      if (e.type === "snack") Object.assign(data, { what: text("what") || e.value, grams: text("grams") });
      if (e.type === "symptom") data.symptom = symptom;
      if (e.type === "weight") data.kg = Number(kg.value);
      if (e.type === "dose") data.status = status;
      run("update_entry", data, T.corrected);
    });
  });
}

// ---------- the card -------------------------------------------------------------------------

class PetCareCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) throw new Error("entity: the pet's log sensor (sensor.<pet>_log)");
    this._config = { show: "action", ...config };
    this._sig = null;
  }

  static getStubConfig(hass) {
    const log = Object.keys(hass.states).find((e) => e.startsWith("sensor.") && hass.states[e].attributes?.card?.entry_id);
    return { entity: log || "sensor.pet_log", show: "summary" };
  }

  set hass(hass) {
    this._hass = hass;
    const st = hass.states[this._config.entity];
    const sig = JSON.stringify([st?.last_updated, st?.attributes?.card, (this._card?.care || []).map((c) => hass.states[c.entity]?.last_updated), hass.states[this._card?.shedding]?.state, hass.locale?.language]);
    if (sig === this._sig) return;
    this._sig = sig;
    this._card = st?.attributes?.card;
    this._recent = st?.attributes?.recent;
    this._render();
  }

  getCardSize() { if (this._config.show === "weight") return 3; return this._config.show === "doses" ? Math.max(1, Math.ceil((this._card?.doses?.length || 1) / 2)) : this._config.show === "action" ? 2 : 1; }

  getGridOptions() {
    const s = this._config.show;
    if (s === "summary") return { columns: "full", rows: 1, min_rows: 1 };
    if (s === "action") return { columns: 6, rows: 2, min_columns: 3, min_rows: 2 };
    if (s === "weight") return (this._hass?.states[this._card?.weight]?.attributes?.history || []).length ? { columns: 12, rows: 3, min_rows: 2 } : { columns: 12, rows: 1, min_rows: 1 };
    if (s === "doses") { const n = Math.max(1, Math.ceil((this._card?.doses?.length || 1) / 2)); return { columns: 12, rows: n, min_rows: n }; }
    if (s === "upcoming" || s === "history") return { columns: 12, rows: "auto" };
    return { columns: 6, rows: 1, min_rows: 1 };
  }

  _tile({ icon, colorName, primary, secondary, vertical, data }) {
    return `<ha-card><div class="tile${vertical ? " vertical" : ""}" ${data || ""} style="--c:${color(colorName)}">
      <div class="icon"><ha-icon icon="${esc(icon)}"></ha-icon></div>
      <div class="text"><span class="primary">${esc(primary)}</span>${secondary ? `<span class="secondary">${esc(secondary)}</span>` : ""}</div></div></ha-card>`;
  }

  _render() {
    if (!this.shadowRoot) this.attachShadow({ mode: "open" });
    const hass = this._hass;
    const card = this._card;
    const T = t(hass);
    if (!card) {
      this.shadowRoot.innerHTML = `<style>${TILE_CSS}</style><ha-card><div class="empty">Pet Care: ${esc(this._config.entity)} ?</div></ha-card>`;
      return;
    }
    const cfg = this._config;
    let html = "";
    const now = new Date();

    if (cfg.show === "summary") {
      const bits = [];
      const minutes = now.getHours() * 60 + now.getMinutes();
      const due = card.meals.filter((m) => minutes >= Number(m.time.slice(0, 2)) * 60 + Number(m.time.slice(3, 5)));
      const states = card.meals.map((m) => ({ m, s: hass.states[m.entity]?.state || "pending" }));
      const eaten = states.filter((x) => x.s !== "pending");
      const odd = eaten.filter((x) => x.s !== "all");
      const late = states.filter((x) => x.s === "pending" && due.includes(x.m));
      if (eaten.length && !odd.length && !late.length) bits.push(T.ateMeals(eaten.length, card.meals.length));
      for (const x of odd) bits.push(`${x.m.name}: ${T.ate[x.s].toLowerCase()}`);
      for (const x of late) bits.push(T.mealLate(x.m.name));
      const open = card.doses.filter((d) => !d.status);
      if (card.doses.length) bits.push(open.length ? T.medicinesLeft(open.length) : T.medicinesDone);
      const lateCare = card.care.filter((c) => hass.states[c.entity]?.attributes?.overdue);
      for (const c of lateCare) bits.push(T.careLate(c.name));
      const next = card.upcoming.find((u) => !lateCare.some((c) => u.summary.startsWith(c.name)));
      if (next) {
        const n = daysBetween(now, parseDay(next.day));
        const when = n <= 1 ? T.inDays(n) : parseDay(next.day).toLocaleDateString(lang(hass), { weekday: "short", day: "2-digit", month: "2-digit" });
        bits.push(`${T.next.toLowerCase()}: ${next.summary} ${when}`);
      }
      const colorName = lateCare.length ? "red" : open.length || late.length ? "amber" : "green";
      html = this._tile({ icon: "mdi:dog", colorName, primary: `${card.pet} · ${T.today}`, secondary: bits.join(" · ") });
    } else if (cfg.show === "meal") {
      const m = card.meals.find((x) => x.key === cfg.meal) || card.meals[0];
      const st = hass.states[m.entity];
      const s = st?.state || "pending";
      const secondary = s === "pending" ? `${T.pending} · ${m.time}` : `${T.ate[s] || s}${st.attributes.at ? " · " + hhmm(st.attributes.at) : ""}${st.attributes.grams ? ` · ${Math.round(st.attributes.grams)} g` : ""}`;
      html = this._tile({ icon: s === "pending" ? "mdi:bowl-outline" : "mdi:bowl-mix", colorName: s === "pending" ? "grey" : AMOUNT_COLORS[s], primary: `${T.meal} · ${m.name}`, secondary, data: `data-act="meal" data-meal="${esc(m.key)}"` });
    } else if (cfg.show === "doses") {
      const rows = card.doses.map((d, i) => {
        const secondary = d.status === "given" ? T.gaveAt(hhmm(d.at), d.by) : d.status ? T[d.status] || d.status : `${T.pending}${d.dose ? " · " + d.dose : ""}`;
        const colorName = d.status === "given" ? "green" : d.status ? "grey" : "purple";
        return this._tile({ icon: d.status === "given" ? "mdi:check-circle" : KIND_ICONS[d.kind] || KIND_ICONS.other, colorName, primary: `${d.treatment} · ${d.time}`, secondary, data: `data-act="dose" data-i="${i}"` });
      });
      html = rows.length ? `<div class="grid">${rows.join("")}</div>` : this._tile({ icon: "mdi:medication-outline", colorName: "grey", primary: T.medicines, secondary: T.noMedicines, data: `data-act="treatment"` });
    } else if (cfg.show === "care") {
      const care = card.care.find((c) => c.key === cfg.care) || card.care[0];
      const a = hass.states[care.entity]?.attributes || {};
      const short = (day) => parseDay(day).toLocaleDateString(lang(hass), { weekday: "short", day: "2-digit", month: "2-digit" });
      const bits = [];
      if (a.last_done) bits.push(T.daysAgo(daysBetween(parseDay(a.last_done), now)));
      if (a.planned_day) bits.push(`☀️ ${short(a.planned_day)}`);
      else if (a.days_left !== null && a.days_left !== undefined) bits.push(a.last_done ? T.inDays(a.days_left) : `${T.inDays(a.days_left)} · ${short(a.due)}`);
      if (!bits.length) bits.push(T.never);
      const n = a.days_left;
      const colorName = n === null || n === undefined ? "grey" : n < 0 ? "red" : n <= 1 ? "amber" : "green";
      html = this._tile({ icon: care.icon || "mdi:paw", colorName, primary: care.name, secondary: bits.join(" · "), data: `data-act="care" data-care="${esc(care.key)}"` });
    } else if (cfg.show === "weight") {
      const st = hass.states[card.weight];
      const points = (st?.attributes?.history || []).map((p) => ({ at: new Date(p.at), kg: Number(p.kg) })).filter((p) => Number.isFinite(p.kg));
      const last = points[points.length - 1];
      const secondary = last ? `${last.kg.toLocaleString(lang(hass), { maximumFractionDigits: 1 })} kg · ${T.daysAgo(daysBetween(last.at, now))}` : T.noWeights;
      let chart = "";
      if (points.length) {
        const W = 300, H = 80;
        const lo = Math.min(...points.map((p) => p.kg)) - 0.5, hi = Math.max(...points.map((p) => p.kg)) + 0.5;
        const t0 = points[0].at.getTime(), t1 = Math.max(last.at.getTime(), t0 + 86400000);
        const x = (p) => ((p.at.getTime() - t0) / (t1 - t0)) * W;
        const y = (p) => H - ((p.kg - lo) / (hi - lo)) * H;
        const path = points.map((p, i) => `${i ? "L" : "M"}${x(p).toFixed(1)},${y(p).toFixed(1)}`).join(" ");
        chart = `<div class="chart"><svg viewBox="0 -10 ${W} ${H + 24}" preserveAspectRatio="none">
          <path d="${path}" fill="none" stroke="${color("blue")}" stroke-width="2" vector-effect="non-scaling-stroke"/>
          ${points.map((p) => `<circle cx="${x(p).toFixed(1)}" cy="${y(p).toFixed(1)}" r="3" fill="${color("blue")}"/>`).join("")}
          <text x="0" y="${H + 14}">${esc(points[0].at.toLocaleDateString(lang(hass), { day: "2-digit", month: "2-digit" }))}</text>
          <text x="${W}" y="${H + 14}" text-anchor="end">${esc(last.at.toLocaleDateString(lang(hass), { day: "2-digit", month: "2-digit" }))}</text>
        </svg></div>`;
      }
      html = `<ha-card><div class="tile" data-act="weight" style="--c:${color("blue")};height:56px;min-height:56px">
        <div class="icon"><ha-icon icon="mdi:scale-bathroom"></ha-icon></div>
        <div class="text"><span class="primary">${esc(T.weight)}</span><span class="secondary">${esc(secondary)}</span></div></div>${chart}</ha-card>`;
    } else if (cfg.show === "upcoming") {
      html = `<ha-card><div class="list">${card.upcoming.length ? card.upcoming.map((u) => `<div class="row"><span>${esc(u.summary)}</span><span class="day">${esc(parseDay(u.day).toLocaleDateString(lang(hass), { weekday: "short", day: "2-digit", month: "2-digit" }))}</span></div>`).join("") : `<div class="empty">${esc(T.nothing)}</div>`}</div></ha-card>`;
    } else if (cfg.show === "history") {
      const all = this._recent || [];
      const rows = all.slice(0, this._more ? all.length : cfg.count || 12);
      const today = now.toDateString();
      const yesterday = new Date(now.getTime() - 86400000).toDateString();
      let lastDay = "";
      const items = rows.map((e) => {
        const d = new Date(e.at);
        const day = d.toDateString();
        const head = day === lastDay ? "" : `<div class="dayhead">${esc(day === today ? T.today : day === yesterday ? T.yesterday : d.toLocaleDateString(lang(hass), { weekday: "long", day: "2-digit", month: "2-digit" }))}</div>`;
        lastDay = day;
        const look = entryLook(card, e);
        const note = e.type !== "dose" && e.note ? `<span class="secondary">${esc(e.note)}</span>` : "";
        return `${head}<div class="entry" data-act="entry" data-id="${esc(e.id)}" style="--c:${color(look.color)}">
          <div class="icon"><ha-icon icon="${esc(look.icon)}"></ha-icon></div>
          <div class="text"><span class="primary">${esc(e.label)}</span>${note}</div>
          <span class="day">${esc(hhmm(e.at))}${e.by ? ` · ${esc(e.by.split(" ")[0])}` : ""}</span></div>`;
      });
      const more = !this._more && all.length > rows.length ? `<button class="more" data-act="more">${esc(T.more)}</button>` : "";
      html = `<ha-card><div class="list">${items.length ? items.join("") + more : `<div class="empty">${esc(T.noHistory)}</div>`}</div></ha-card>`;
    } else {
      const a = ACTIONS[cfg.action] || ACTIONS.symptom;
      html = this._tile({ icon: cfg.icon || a.icon, colorName: cfg.color || a.color, primary: cfg.name || T[cfg.action] || cfg.action, vertical: true, data: `data-act="${esc(cfg.action)}"` });
    }
    this.shadowRoot.innerHTML = `<style>${TILE_CSS}</style>${html}`;
    this.shadowRoot.querySelectorAll("[data-act]").forEach((el) => el.addEventListener("click", () => this._act(el)));
  }

  _act(el) {
    const hass = this._hass;
    const card = this._card;
    const act = el.dataset.act;
    if (act === "meal") return mealDialog(hass, card, el.dataset.meal);
    if (act === "symptom") return symptomDialog(hass, card);
    if (act === "weight") return weightDialog(hass, card);
    if (act === "snack") return snackDialog(hass, card, this._recent);
    if (act === "treatment") return treatmentsDialog(hass, card);
    if (act === "entry") return entryDialog(hass, card, this._recent.find((e) => e.id === el.dataset.id));
    if (act === "more") { this._more = true; return this._render(); }
    if (act === "care") return careDialog(hass, card, card.care.find((c) => c.key === el.dataset.care));
    if (act === "dose") {
      const dose = card.doses[Number(el.dataset.i)];
      if (dose.status) return doseDialog(hass, card, dose);
      // One tap gives the dose; the toast can take it back.
      return callService(hass, "log_dose", { config_entry_id: card.entry_id, treatment: dose.id, time: dose.time, status: "given" }).then((res) => {
        toast(hass, `${dose.treatment} · ${dose.time}: ${t(hass).given}`, res.ids).dataset.entry = card.entry_id;
      });
    }
  }
}

if (!customElements.get("pet-care-card")) {
  customElements.define("pet-care-card", PetCareCard);
  window.customCards = window.customCards || [];
  window.customCards.push({ type: "pet-care-card", name: "Pet Care", description: "Meals, medicines, care and records for a pet", preview: false });
  console.info(`%c PET-CARE-CARD %c ${VERSION} `, "background:#3d8bd8;color:#fff;font-weight:700", "background:#1c1f24;color:#fff");
}
