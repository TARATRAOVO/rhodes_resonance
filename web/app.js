(() => {
  const btnStart = document.getElementById('btnStart');
  const btnStop  = document.getElementById('btnStop');
  const btnRestart = document.getElementById('btnRestart');
  const statusEl = document.getElementById('status');
  const storyEl  = document.getElementById('storyLines');
  const hudEl    = document.getElementById('hud');
  const txtPlayer= document.getElementById('txtPlayer');
  const btnSend  = document.getElementById('btnSend');
  const playerHint = document.getElementById('playerHint');
  const btnSettings = document.getElementById('btnSettings');
  const cmdPrompt = document.getElementById('cmdPrompt');
  const btnToggleSide = document.getElementById('btnToggleSide');
  const storyPicker = document.getElementById('storyPicker');
  // Map elements
  const mapCanvas = document.getElementById('mapCanvas');
  const mapHint = document.getElementById('mapHint');
  const mapWrapEl = document.getElementById('mapWrap');
  // Settings drawer elements
  const drawer = document.getElementById('settingsDrawer');
  const tabBtns = drawer ? Array.from(drawer.querySelectorAll('.tab')) : [];
  const panes = drawer ? Array.from(drawer.querySelectorAll('.tabpane')) : [];
  const btnCfgClose = drawer ? drawer.querySelector('#btnCfgClose') : null;
  const btnCfgSave = drawer ? drawer.querySelector('#btnCfgSave') : null;
  const btnCfgSaveRestart = drawer ? drawer.querySelector('#btnCfgSaveRestart') : null;
  const btnCfgExport = drawer ? drawer.querySelector('#btnCfgExport') : null;
  const btnCfgReset = drawer ? drawer.querySelector('#btnCfgReset') : null;
  // Story controls
  const stSceneName = drawer ? drawer.querySelector('#stSceneName') : null;
  const stSceneTime = drawer ? drawer.querySelector('#stSceneTime') : null;
  const stSceneWeather = drawer ? drawer.querySelector('#stSceneWeather') : null;
  const stSceneDesc = drawer ? drawer.querySelector('#stSceneDesc') : null;
  const stDetails = drawer ? drawer.querySelector('#stDetails') : null;
  const stObjectives = drawer ? drawer.querySelector('#stObjectives') : null;
  const stTbl = drawer ? drawer.querySelector('#stPositions') : null;
  const stPosNameSel = drawer ? drawer.querySelector('#stPosNameSel') : null;
  const stPosX = drawer ? drawer.querySelector('#stPosX') : null;
  const stPosY = drawer ? drawer.querySelector('#stPosY') : null;
  const btnAddDetail = drawer ? drawer.querySelector('#btnAddDetail') : null;
  const btnAddObjective = drawer ? drawer.querySelector('#btnAddObjective') : null;
  const btnAddPos = drawer ? drawer.querySelector('#btnAddPos') : null;
  // Story endings editor controls
  const stEndingsBody = drawer ? drawer.querySelector('#stEndingsBody') : null;
  const btnAddEnding = drawer ? drawer.querySelector('#btnAddEnding') : null;
  // When builder modal
  const whenModal = drawer ? drawer.querySelector('#whenModal') : null;
  const whenTreeEl = drawer ? drawer.querySelector('#whenTree') : null;
  const btnWhenOk = drawer ? drawer.querySelector('#btnWhenOk') : null;
  const btnWhenCancel = drawer ? drawer.querySelector('#btnWhenCancel') : null;
  // Arts controls
  const artsTable = drawer ? drawer.querySelector('#artsTable') : null;
  const btnAddArt = drawer ? drawer.querySelector('#btnAddArt') : null;
  // Timeline controls
  const tlTable = drawer ? drawer.querySelector('#tlTable') : null;
  const btnAddEvent = drawer ? drawer.querySelector('#btnAddEvent') : null;
  // Scenes/Entrances/Initial scenes/Scene positions controls
  const stScenesTable = drawer ? drawer.querySelector('#stScenesTable') : null;
  const btnAddScene = drawer ? drawer.querySelector('#btnAddScene') : null;
  const stSceneEditor = drawer ? drawer.querySelector('#stSceneEditor') : null;
  const stSceneEditId = drawer ? drawer.querySelector('#stSceneEditId') : null;
  const stSceneEditName = drawer ? drawer.querySelector('#stSceneEditName') : null;
  const stSceneEditDetails = drawer ? drawer.querySelector('#stSceneEditDetails') : null;
  const btnAddSceneDetail = drawer ? drawer.querySelector('#btnAddSceneDetail') : null;
  const stEntrTable = drawer ? drawer.querySelector('#stEntrTable') : null;
  const btnAddEntrance = drawer ? drawer.querySelector('#btnAddEntrance') : null;
  const stInitScenesTable = drawer ? drawer.querySelector('#stInitScenesTable') : null;
  const stInitSceneNameSel = drawer ? drawer.querySelector('#stInitSceneNameSel') : null;
  const stInitSceneId = drawer ? drawer.querySelector('#stInitSceneId') : null;
  const btnSetInitScene = drawer ? drawer.querySelector('#btnSetInitScene') : null;
  const stScenePosSel = drawer ? drawer.querySelector('#stScenePosSel') : null;
  const stScenePosTable = drawer ? drawer.querySelector('#stScenePosTable') : null;
  const stScenePosNameSel = drawer ? drawer.querySelector('#stScenePosNameSel') : null;
  const stScenePosX = drawer ? drawer.querySelector('#stScenePosX') : null;
  const stScenePosY = drawer ? drawer.querySelector('#stScenePosY') : null;
  const btnAddScenePos = drawer ? drawer.querySelector('#btnAddScenePos') : null;

  
  
  // Story multi-selector controls
  const stStorySelect = drawer ? drawer.querySelector('#stStorySelect') : null;
  const btnStoryNew = drawer ? drawer.querySelector('#btnStoryNew') : null;
  const btnStoryCopy = drawer ? drawer.querySelector('#btnStoryCopy') : null;
  const btnStoryRename = drawer ? drawer.querySelector('#btnStoryRename') : null;
  const btnStoryDelete = drawer ? drawer.querySelector('#btnStoryDelete') : null;
  // Weapons controls
  const wpTable = drawer ? drawer.querySelector('#wpTable') : null;
  const btnAddWeapon = drawer ? drawer.querySelector('#btnAddWeapon') : null;
  // Characters form
  const chListEl = drawer ? drawer.querySelector('#chList') : null;
  const btnAddChar = drawer ? drawer.querySelector('#btnAddChar') : null;
  const btnDelChar = drawer ? drawer.querySelector('#btnDelChar') : null;
  const chName = drawer ? drawer.querySelector('#chName') : null;
  const chType = drawer ? drawer.querySelector('#chType') : null;
  const chPersona = drawer ? drawer.querySelector('#chPersona') : null;
  const chAppearance = drawer ? drawer.querySelector('#chAppearance') : null;
  const chQuotes = drawer ? drawer.querySelector('#chQuotes') : null;
  const btnAddQuote = drawer ? drawer.querySelector('#btnAddQuote') : null;
  // CoC selectors
  const cocSTR = drawer ? drawer.querySelector('#cocSTR') : null;
  const cocDEX = drawer ? drawer.querySelector('#cocDEX') : null;
  const cocCON = drawer ? drawer.querySelector('#cocCON') : null;
  const cocINT = drawer ? drawer.querySelector('#cocINT') : null;
  const cocPOW = drawer ? drawer.querySelector('#cocPOW') : null;
  const cocAPP = drawer ? drawer.querySelector('#cocAPP') : null;
  const cocEDU = drawer ? drawer.querySelector('#cocEDU') : null;
  const cocSIZ = drawer ? drawer.querySelector('#cocSIZ') : null;
  const cocLUCK = drawer ? drawer.querySelector('#cocLUCK') : null;
  const cocDerived = drawer ? drawer.querySelector('#cocDerived') : null;
  const chSkillsTable = drawer ? drawer.querySelector('#chSkillsTable') : null;
  const btnAddSkill = drawer ? drawer.querySelector('#btnAddSkill') : null;
  const terraInfectStage = drawer ? drawer.querySelector('#terraInfectStage') : null;
  const terraInfectStress = drawer ? drawer.querySelector('#terraInfectStress') : null;
  const terraCrystal = drawer ? drawer.querySelector('#terraCrystal') : null;
  const terraArmor = drawer ? drawer.querySelector('#terraArmor') : null;
  const terraBarrier = drawer ? drawer.querySelector('#terraBarrier') : null;
  const chInvTable = drawer ? drawer.querySelector('#chInvTable') : null;
  const chInvIdSel = drawer ? drawer.querySelector('#chInvIdSel') : null;
  const chInvCount = drawer ? drawer.querySelector('#chInvCount') : null;
  const btnAddInv = drawer ? drawer.querySelector('#btnAddInv') : null;

  let ws = null;
  let lastSeq = 0;
  let reconnectDelay = 500;
  const maxDelay = 8000;
  const maxStory = 500;
  let waitingActor = '';
  let mapPlayer = '';
  // simple command history for CLI experience
  const cmdHist = [];
  let cmdIdx = -1; // points to next insert position
  // Backend origin config + API helpers
  // Allows deploying the static UI separately from the Python backend.
  // If window.RR.backendOrigin is set (e.g., "https://your-backend.example.com"),
  // API calls and WebSocket connections will use that origin. Otherwise, same-origin.
  const RR_CFG = (typeof window !== 'undefined' && window.RR) ? window.RR : {};
  // Allow URL param override: ?backend=https://api.example.com
  let __backendOverride = '';
  try {
    const p = new URLSearchParams(location.search);
    const b = String(p.get('backend') || '').trim();
    if (b) __backendOverride = b.replace(/\/$/, '');
  } catch (e) { /* ignore */ }
  const BACKEND_ORIGIN = (__backendOverride
    || (RR_CFG && typeof RR_CFG.backendOrigin === 'string' && RR_CFG.backendOrigin))
    ? (__backendOverride || RR_CFG.backendOrigin).replace(/\/$/, '')
    : '';
  const BACKEND_URL = (BACKEND_ORIGIN ? new URL(BACKEND_ORIGIN) : null);
  function withApiBase(path) {
    try {
      if (BACKEND_ORIGIN && typeof path === 'string' && path.startsWith('/')) return BACKEND_ORIGIN + path;
    } catch (e) { /* ignore */ }
    return path;
  }
  // Per-page session: ensure each tab has its own SID and propagate to API/WS
  let SID = '';
  try {
    const u = new URL(location.href);
    SID = String(u.searchParams.get('sid') || '').trim();
    if (!SID) {
      // prefer crypto UUID; fallback to timestamp+rand
      SID = (typeof crypto !== 'undefined' && crypto.randomUUID) ? crypto.randomUUID() : (Date.now().toString(36) + Math.random().toString(36).slice(2));
      u.searchParams.set('sid', SID);
      history.replaceState(null, '', u.toString());
    }
  } catch (e) { /* ignore */ }
  // Monkey‑patch fetch so existing fetch('/api/...') calls keep working when deployed separately
  try {
    const __origFetch = (typeof window !== 'undefined' && window.fetch) ? window.fetch.bind(window) : null;
    if (__origFetch) {
      window.fetch = (input, init) => {
        try {
          // Attach session header for same-origin API calls
          const attach = (url, init0) => {
            const nextInit = Object.assign({}, init0 || {});
            const h = new Headers(nextInit.headers || {});
            if (SID) h.set('X-Session-ID', SID);
            nextInit.headers = h;
            return __origFetch(withApiBase(url), nextInit);
          };
          if (typeof input === 'string' && input.startsWith('/api/')) return attach(input, init);
          if (input && typeof input.url === 'string' && input.url.startsWith('/api/')) return attach(input.url, init);
        } catch (e) { /* ignore and fall through */ }
        return __origFetch(input, init);
      };
    }
  } catch (e) { /* ignore */ }
  let running = false;
  let paused = false; // soft-pause between actor turns
  const params = new URLSearchParams(location.search);
  const debugMode = params.get('debug') === '1' || params.get('debug') === 'true';
  let lastState = {};

  // ==== Simple Battle Map (static, no interaction/animation) ====
  // ==== UI: Custom Select (styled popup list, mirrors native select) ====
  const SelectUX = (() => {
    const OPEN_CLASS = 'open';
    // Close all open menus on outside click / ESC
    function closeAll(exceptWrap = null) {
      document.querySelectorAll('.ui-select.'+OPEN_CLASS).forEach(w => { if (w !== exceptWrap) w.classList.remove(OPEN_CLASS); });
    }
    function buildMenuFromSelect(sel, menu) {
      menu.innerHTML = '';
      const opts = Array.from(sel.options || []);
      opts.forEach((o, idx) => {
        const it = document.createElement('div');
        it.className = 'ui-select-option';
        it.setAttribute('role', 'option');
        it.dataset.value = o.value;
        it.textContent = o.textContent || o.value || '';
        if (o.disabled) it.setAttribute('aria-disabled', 'true');
        if (o.selected) it.setAttribute('aria-selected', 'true');
        it.addEventListener('click', (e) => {
          if (o.disabled) return;
          if (sel.value !== o.value) {
            sel.value = o.value;
            // Dispatch native change for existing handlers
            sel.dispatchEvent(new Event('change', { bubbles: true }));
          }
          const wrap = menu.closest('.ui-select');
          if (wrap) wrap.classList.remove(OPEN_CLASS);
        });
        menu.appendChild(it);
      });
    }
    function syncTriggerLabel(sel, trigger) {
      try {
        const t = sel.options && sel.selectedIndex >= 0 ? (sel.options[sel.selectedIndex].textContent || '') : '';
        trigger.textContent = t || '请选择';
      } catch { trigger.textContent = '请选择'; }
    }
    function ensureWrapWidth(sel, wrap) {
      // Fit-to-content selects: do not force full width
      if (sel.classList && sel.classList.contains('fit-select')) {
        wrap.classList.add('fit');
        wrap.style.width = 'auto';
        return;
      }
      try {
        const rect = sel.getBoundingClientRect();
        if (rect && rect.width) wrap.style.width = rect.width + 'px';
      } catch(e){ throw e }
      // table cells or toolbar rows want full width
      try {
        const p = sel.parentElement; const gp = p && p.parentElement;
        if (p && (p.classList.contains('tbl') || p.classList.contains('toolbar-row'))) wrap.classList.add('full');
        if (gp && (gp.classList.contains('tbl') || gp.classList.contains('toolbar-row'))) wrap.classList.add('full');
      } catch(e){ throw e }
    }
    function enhanceSelect(sel) {
      if (!sel || sel.tagName !== 'SELECT') return null;
      if (sel.dataset.enhanced === '1') return sel.closest('.ui-select');
      // Build wrapper structure
      const wrap = document.createElement('div'); wrap.className = 'ui-select';
      // Insert before select, then move select inside
      sel.parentElement.insertBefore(wrap, sel);
      wrap.appendChild(sel);
      // Trigger button
      const trigger = document.createElement('button');
      trigger.type = 'button'; trigger.className = 'ui-select-trigger'; trigger.setAttribute('aria-haspopup', 'listbox'); trigger.setAttribute('aria-expanded', 'false');
      wrap.insertBefore(trigger, sel);
      // Popup menu
      const menu = document.createElement('div'); menu.className = 'ui-select-menu'; menu.setAttribute('role', 'listbox');
      wrap.appendChild(menu);
      // Initial sync
      syncTriggerLabel(sel, trigger);
      buildMenuFromSelect(sel, menu);
      ensureWrapWidth(sel, wrap);
      // Track as enhanced
      sel.dataset.enhanced = '1';
      // Toggle open
      function openMenu() {
        closeAll(wrap);
        wrap.classList.add(OPEN_CLASS); trigger.setAttribute('aria-expanded', 'true');
        // Drop-up if not enough viewport space
        try {
          const r = wrap.getBoundingClientRect();
          const spaceBelow = window.innerHeight - r.bottom; const spaceAbove = r.top;
          if (spaceBelow < 160 && spaceAbove > spaceBelow) menu.classList.add('drop-up'); else menu.classList.remove('drop-up');
        } catch(e){ throw e }
        // Scroll to selected
        try {
          const cur = menu.querySelector('.ui-select-option[aria-selected="true"]');
          if (cur) { cur.scrollIntoView({ block: 'nearest' }); }
        } catch(e){ throw e }
      }
      function closeMenu() { wrap.classList.remove(OPEN_CLASS); trigger.setAttribute('aria-expanded', 'false'); }
      trigger.addEventListener('click', (e) => {
        if (wrap.classList.contains(OPEN_CLASS)) closeMenu(); else openMenu();
      });
      // Keyboard on trigger
      trigger.addEventListener('keydown', (e) => {
        const key = e.key;
        if (key === 'ArrowDown' || key === 'Enter' || key === ' ') { e.preventDefault(); openMenu(); }
        if (key === 'Escape') { closeMenu(); }
      });
      // Close on outside click
      document.addEventListener('click', (ev) => {
        if (!wrap.contains(ev.target)) closeMenu();
      });
      // Reflect native changes (programmatic or user) into trigger/menu
      sel.addEventListener('change', () => {
        syncTriggerLabel(sel, trigger);
        // update selected indicators
        const v = sel.value;
        menu.querySelectorAll('.ui-select-option').forEach(it => it.setAttribute('aria-selected', it.dataset.value === v ? 'true' : 'false'));
      });
      // Observe option list changes (e.g., storyPicker init)
      const mo = new MutationObserver(() => {
        buildMenuFromSelect(sel, menu);
        syncTriggerLabel(sel, trigger);
      });
      mo.observe(sel, { childList: true, subtree: true, attributes: false });
      // Keep width responsive on resize
      window.addEventListener('resize', () => ensureWrapWidth(sel, wrap));
      // Label click support: clicking <label for> opens menu
      try {
        const id = sel.id; if (id) {
          const lab = document.querySelector(`label[for="${CSS.escape(id)}"]`);
          if (lab) lab.addEventListener('click', (e) => { e.preventDefault(); trigger.focus(); openMenu(); });
        }
      } catch(e){ throw e }
      return wrap;
    }
    function enhanceAll(root = document) {
      (root.querySelectorAll ? root.querySelectorAll('select') : []).forEach(enhanceSelect);
    }
    // Auto-enhance dynamically added selects (e.g., in settings forms)
    const globalMO = new MutationObserver((ml) => {
      for (const m of ml) {
        if (m.type === 'childList') {
          m.addedNodes.forEach(n => {
            if (n && n.nodeType === 1) {
              if (n.tagName === 'SELECT') enhanceSelect(n);
              else if (n.querySelectorAll) n.querySelectorAll('select').forEach(enhanceSelect);
            }
          });
        }
      }
    });
    function startObserver() {
      try { globalMO.observe(document.body, { childList: true, subtree: true }); } catch(e){ throw e }
    }
    return { enhanceAll, enhanceSelect, closeAll, startObserver };
  })();
  const MapView = (() => {
    // Read CSS variables to keep canvas in sync with theme
    function cssVar(name, _fallback_unused) {
      // no fallback: require CSS variable to be present
      const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
      if (!v) throw new Error(`Missing CSS variable: ${name}`);
      return v;
    }
    function hashHue(s) {
      let h = 0 >>> 0;
      for (let i = 0; i < s.length; i++) h = (((h << 5) - h) + s.charCodeAt(i)) >>> 0; // 31x
      return h % 360;
    }
    function nameColor(nm) { return `hsl(${hashHue(String(nm||''))},60%,60%)`; }
    class MapView {
      constructor(canvas, hint) {
        this.canvas = canvas;
        this.hint = hint;
        this.ctx = canvas ? canvas.getContext('2d') : null;
        this.dpr = (typeof window !== 'undefined' && window.devicePixelRatio) ? window.devicePixelRatio : 1;
        this.bounds = null; // {minX,maxX,minY,maxY}
        this._lastState = null;
        this.theme = {
          bg: cssVar('--bg', '#f8f8f8'),
          surface: cssVar('--surface', '#ffffff'),
          border: cssVar('--border', '#e0e0e0'),
          text: cssVar('--text', '#383838'),
          muted: cssVar('--muted', '#7a7a7a')
        };
        this.resize();
      }
      resize() {
        if (!this.canvas || !this.ctx) return;
        const cw = this.canvas.clientWidth || 0;
        const ch = this.canvas.clientHeight || 0;
        const dpr = this.dpr || 1;
        if (cw <= 0 || ch <= 0) return;
        if (this.canvas.width !== Math.floor(cw * dpr) || this.canvas.height !== Math.floor(ch * dpr)) {
          this.canvas.width = Math.floor(cw * dpr);
          this.canvas.height = Math.floor(ch * dpr);
        }
        this.ctx.setTransform(1,0,0,1,0,0);
        this.ctx.scale(dpr, dpr);
        this.render(this._lastState || null);
      }
      _computeBounds(pos) {
        let minX=Infinity, maxX=-Infinity, minY=Infinity, maxY=-Infinity;
        let has=false;
        for (const [nm, p] of Object.entries(pos||{})) {
          if (!Array.isArray(p) || p.length < 2) continue;
          const x = parseInt(p[0], 10); const y = parseInt(p[1], 10);
          if (!isFinite(x) || !isFinite(y)) continue;
          if (x < minX) minX = x; if (x > maxX) maxX = x;
          if (y < minY) minY = y; if (y > maxY) maxY = y;
          has = true;
        }
        if (!has) return null;
        if (minX === Infinity || minY === Infinity) return null;
        // pad box to avoid touching edges; also ensure non-zero span
        if (minX === maxX) { minX -= 2; maxX += 2; }
        if (minY === maxY) { minY -= 2; maxY += 2; }
        return { minX, maxX, minY, maxY };
      }
      _clear() {
        if (!this.canvas || !this.ctx) return;
        const w = this.canvas.clientWidth || 0;
        const h = this.canvas.clientHeight || 0;
        // Use light surface like Awwwards cards
        this.ctx.fillStyle = this.theme.surface || '#ffffff';
        this.ctx.fillRect(0, 0, w, h);
      }
      _drawGrid(bounds, stepPx) {
        const ctx = this.ctx; if (!ctx) return;
        const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
        const pad = 24; // px
        const originX = pad - bounds.minX * stepPx;
        const originY = pad - bounds.minY * stepPx;
        // choose grid density
        const gap = stepPx >= 24 ? 1 : stepPx >= 12 ? 2 : stepPx >= 6 ? 5 : 10;
        ctx.save();
        ctx.strokeStyle = this.theme.border || '#e0e0e0';
        ctx.lineWidth = 1;
        // verticals
        const startX = Math.floor(bounds.minX / gap) * gap;
        const endX = Math.ceil(bounds.maxX / gap) * gap;
        for (let gx = startX; gx <= endX; gx += gap) {
          const x = originX + gx * stepPx;
          if (x < pad-1 || x > w - pad + 1) continue;
          ctx.beginPath(); ctx.moveTo(x, pad); ctx.lineTo(x, h - pad); ctx.stroke();
        }
        // horizontals
        const startY = Math.floor(bounds.minY / gap) * gap;
        const endY = Math.ceil(bounds.maxY / gap) * gap;
        for (let gy = startY; gy <= endY; gy += gap) {
          const y = originY + gy * stepPx;
          if (y < pad-1 || y > h - pad + 1) continue;
          ctx.beginPath(); ctx.moveTo(pad, y); ctx.lineTo(w - pad, y); ctx.stroke();
        }
        ctx.restore();
      }
      _drawEntrances(state, bounds, stepPx, focusScene) {
        // Draw scene entrances as diamond markers with labels.
        const ctx = this.ctx; if (!ctx) return;
        const pad = 24;
        const originX = pad - bounds.minX * stepPx;
        const originY = pad - bounds.minY * stepPx;
        const ents = state.entrances || {};
        const scenes = state.scenes || {};

        ctx.save();
        ctx.font = '11px ui-monospace, Menlo, monospace';
        ctx.textBaseline = 'middle';
        for (const [eid, e] of Object.entries(ents)) {
          try {
            const from = String((e || {}).from_scene || '');
            if (focusScene && from !== String(focusScene)) continue; // only draw in-focus scene
            const at = (e || {}).at;
            if (!Array.isArray(at) || at.length < 2) continue;
            const gx = parseInt(at[0], 10);
            const gy = parseInt(at[1], 10);
            if (!Number.isFinite(gx) || !Number.isFinite(gy)) continue;

            const x = originX + gx * stepPx;
            const y = originY + gy * stepPx;

            // Diamond marker (rotated square)
            const size = Math.max(6, Math.min(10, stepPx * 0.6));
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(Math.PI / 4);
            ctx.fillStyle = '#d97706';       // amber-ish color for entrances
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 1.5;
            const half = size / 1.4;
            ctx.beginPath();
            ctx.rect(-half, -half, size, size);
            ctx.fill();
            ctx.stroke();
            ctx.restore();

            // Label: "label → to_scene_name"
            const label = String((e || {}).label || '');
            const toId = String((e || {}).to_scene || '');
            const toName = String(((scenes[toId] || {}).name || toId));
            const text = label ? `${label} → ${toName}` : `→ ${toName}`;
            ctx.fillStyle = this.theme.text || '#383838';
            ctx.fillText(text, x + size * 0.9 + 4, y);
          } catch (_e) {
            // be defensive; skip malformed entries
            continue;
          }
        }
        ctx.restore();
      }
      _drawActors(state, bounds, stepPx) {
        const ctx = this.ctx; if (!ctx) return;
        const pad = 24;
        const originX = pad - bounds.minX * stepPx;
        const originY = pad - bounds.minY * stepPx;
        const pos = state.positions || {};
        const radius = Math.max(3, Math.min(6, stepPx * 0.35));
        ctx.save();
        ctx.font = '12px ui-monospace, Menlo, monospace';
        ctx.textBaseline = 'middle';
        for (const nm of Object.keys(pos)) {
          const p = pos[nm]; if (!Array.isArray(p) || p.length < 2) continue;
          const x = originX + parseInt(p[0],10) * stepPx;
          const y = originY + parseInt(p[1],10) * stepPx;
          const c = nameColor(nm);
          ctx.fillStyle = c; ctx.strokeStyle = '#ffffff';
          ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI*2); ctx.fill();
          ctx.stroke();
          // label (name only)
          ctx.fillStyle = this.theme.text || '#383838';
          ctx.fillText(String(nm), x + radius + 4, y);
        }
        ctx.restore();
      }
      render(state) {
        this._lastState = state || this._lastState || {};
        if (!this.canvas || !this.ctx) return;
        this._clear();
        const w = this.canvas.clientWidth || 0;
        const h = this.canvas.clientHeight || 0;
        if (w <= 0 || h <= 0) return;
        const st = this._lastState || {};
        const posAll = (st.positions || {});
        const sceneOf = st.scene_of || {};
        // Always prefer a player-anchored focus scene if resolvable
        let focusScene = null;
        const chars = st.characters || {};
        for (const nm of Object.keys(chars)) {
          try { if (String((chars[nm]||{}).type||'npc').toLowerCase() === 'player') { const sc = sceneOf[nm]; if (typeof sc === 'string' && sc) { focusScene = sc; break; } } } catch(e){}
        }
        if (!focusScene) {
          // fallback: map location name to scene id
          const loc = String(st.location || '');
          const scenes = st.scenes || {};
          for (const sid of Object.keys(scenes)) {
            try { const nm = String((scenes[sid]||{}).name || sid); if (nm === loc) { focusScene = sid; break; } } catch(e){}
          }
        }
        // Build view positions: if we know the focus scene, show only actors in that scene;
        // else, fall back to participants; if still not available, show all.
        let posView = {};
        if (focusScene) {
          for (const [nm, p] of Object.entries(posAll)) { if (String(sceneOf[nm]||'') === String(focusScene)) posView[nm] = p; }
        } else {
          const parts = Array.isArray(st.participants) ? st.participants.slice() : [];
          if (parts.length > 0) {
            const keep = new Set(parts.map(String));
            for (const [nm, p] of Object.entries(posAll)) { if (keep.has(String(nm))) posView[nm] = p; }
          } else {
            posView = posAll;
          }
        }
        // Also include entrance coordinates when computing bounds so we can
        // draw entrances even if no actors are present in the focus scene.
        const entsAll = (st.entrances || {});
        const entPoints = [];
        for (const [eid, e] of Object.entries(entsAll)) {
          try {
            const from = String((e || {}).from_scene || '');
            if (focusScene && from !== String(focusScene)) continue;
            const at = (e || {}).at;
            if (!Array.isArray(at) || at.length < 2) continue;
            const gx = parseInt(at[0], 10);
            const gy = parseInt(at[1], 10);
            if (Number.isFinite(gx) && Number.isFinite(gy)) entPoints.push([gx, gy]);
          } catch (_e) { /* ignore */ }
        }
        const posForBounds = Object.assign({}, posView);
        entPoints.forEach((xy, i) => { posForBounds[`__ent_${i}`] = xy; });
        const b = this._computeBounds(posForBounds);
        if (!b) {
          if (this.hint) this.hint.textContent = '暂无坐标/入口';
          return;
        }
        if (this.hint) this.hint.textContent = '';
        const pad = 24;
        const spanX = (b.maxX - b.minX + 1);
        const spanY = (b.maxY - b.minY + 1);
        const stepPx = Math.max(6, Math.min((w - pad*2) / spanX, (h - pad*2) / spanY));
        this._drawGrid(b, stepPx);
        // Render only filtered positions
        const stateView = Object.assign({}, st, { positions: posView });
        // Draw entrances for the focus scene before actors
        this._drawEntrances(stateView, b, stepPx, focusScene);
        this._drawActors(stateView, b, stepPx);
      }
      update(state) { this.render(state); }
    }
    return MapView;
  })();

  const mapView = (mapCanvas && mapCanvas.getContext) ? new MapView(mapCanvas, mapHint) : null;
  if (mapView) {
    window.addEventListener('resize', () => mapView.resize());
    // ResizeObserver fixes distortion when the container resizes without a window resize
    try {
      if (window.ResizeObserver && mapWrapEl) {
        const ro = new ResizeObserver(() => mapView.resize());
        ro.observe(mapWrapEl);
      }
    } catch(e){ throw e }
  }
  // Settings editor state
  let activeTab = 'story';
  const cfg = { story: null, weapons: null, characters: null };
  const original = { story: null, weapons: null, characters: null };
  let chActiveName = '';
  let chRelations = {};
  const dirty = { story: false, weapons: false, arts: false, characters: false };
  // Story container state for multi-story in single file
  let storyContainer = null;      // { stories: {id: story} }
  let storyContainerRaw = null;   // raw object from server to preserve unknown root keys
  let selectedStoryId = '';

  // Small helpers
  function deepClone(obj) { return JSON.parse(JSON.stringify(obj || {})); }
  function normalizeStoryContainer(data) {
    // Accept legacy single-story or container; ignore any legacy active_id
    if (data && typeof data === 'object' && data.stories && typeof data.stories === 'object') {
      return { stories: deepClone(data.stories) };
    }
    // legacy: wrap into default id
    return { stories: { 'default': deepClone(data || {}) } };
  }
  function updateStorySelectUI() {
    if (!stStorySelect) return;
    stStorySelect.innerHTML = '';
    if (!storyContainer || !storyContainer.stories) { stStorySelect.disabled = true; return; }
    const ids = Object.keys(storyContainer.stories);
    // keep selector visible to enable CRUD even if only one
    for (const id of ids) {
      const opt = document.createElement('option');
      opt.value = id; opt.textContent = id;
      stStorySelect.appendChild(opt);
    }
    stStorySelect.value = selectedStoryId || ids[0] || '';
  }
  function commitLocalStoryEdits() {
    try {
      if (!storyContainer || !selectedStoryId) return;
      const single = storyCollect();
      storyContainer.stories[selectedStoryId] = single;
    } catch(e){ throw e }
  }

  function setStatus(text) { statusEl.textContent = text; }
  function lineEl(html, cls='') {
    const div = document.createElement('div');
    div.className = `line ${cls}`;
    // Wrap content to be a single grid item so grid layout doesn't split text per element
    div.innerHTML = `<div class="content">${html}</div>`;
    return div;
  }
  function esc(s) { return s.replace(/[<>&]/g, m => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[m])); }
  function scrollToBottom(el) { el.scrollTop = el.scrollHeight; }
  function updateButtons() {
    // 软暂停：运行且未暂停 -> Start 禁用/Stop 启用；运行且已暂停 -> Start 启用(用于恢复)/Stop 禁用；未运行 -> Start 启用/Stop 禁用
    btnStart.disabled = (running && !paused) ? true : false;
    btnStop.disabled = (!running || paused) ? true : false;
    btnRestart.disabled = false;
    // 发送按钮仍由等待玩家输入信号控制
  }

  function renderHUD(state) {
    hudEl.innerHTML = '';
    if (!state || typeof state !== 'object') return;
    const kv = [];
    try {
      // 显示当前战局 ID（基于选择器的值）
      try {
        const sid = getSelectedStoryId && getSelectedStoryId();
        if (sid) kv.push(`<span class="pill">战局: ${esc(sid)}</span>`);
      } catch(e){ /* ignore */ }
      const inCombat = !!state.in_combat;
      const round = state.round ?? '';
      kv.push(`<span class="pill">战斗: ${inCombat ? '进行中' : '否'}</span>`);
      if (round) kv.push(`<span class="pill">回合: ${round}</span>`);
      const parts = (state.participants || []).join(', ');
      if (parts) kv.push(`<span class="pill">参战: ${esc(parts)}</span>`);
      const loc = state.location || '';
      if (loc) kv.push(`<span class="pill">位置: ${esc(loc)}</span>`);
      const timeMin = state.time_min;
      if (typeof timeMin === 'number') kv.push(`<span class="pill">时间: ${String(Math.floor(timeMin/60)).padStart(2,'0')}:${String(timeMin%60).padStart(2,'0')}</span>`);
      // 追加：目标状态
      const objs = Array.isArray(state.objectives) ? state.objectives : [];
      const objStatus = (state.objective_status || {});
      for (const o of objs.slice(0, 6)) {
        const st = String(objStatus[o] || 'pending');
        const label = st === 'done' ? '✓' : (st === 'blocked' ? '✗' : '…');
        kv.push(`<span class="pill">${esc(o)}:${label}</span>`);
      }
      // 追加：紧张度/标记
      if (typeof state.tension === 'number') kv.push(`<span class="pill">紧张度: ${state.tension}</span>`);
      if (Array.isArray(state.marks) && state.marks.length) kv.push(`<span class="pill">标记: ${state.marks.length}</span>`);
      // 追加：每个参与者的 HP 与坐标
      const chars = state.characters || {};
      const pos = state.positions || {};
      if (Array.isArray(state.participants)) {
        for (const nm of state.participants) {
          const st = chars[nm] || {};
          const hp = (st.hp != null && st.max_hp != null) ? `HP ${st.hp}/${st.max_hp}` : '';
          const dying = (st.dying_turns_left != null) ? `濒死${st.dying_turns_left}` : '';
          const coord = Array.isArray(pos[nm]) && pos[nm].length>=2 ? `@(${pos[nm][0]},${pos[nm][1]})` : '';
          const bits = [nm, hp, dying, coord].filter(Boolean).join(' ');
          if (bits) kv.push(`<span class="pill">${esc(bits)}</span>`);
        }
      }
      // 追加：守护关系
      const guards = state.guardians || {};
      try {
        const pairs = Object.entries(guards).slice(0, 6).map(([k,v])=>`${k}->${v}`);
        if (pairs.length) kv.push(`<span class="pill">守护: ${esc(pairs.join(' | '))}</span>`);
      } catch(e){ throw e }
    } catch(e){ throw e }
    hudEl.innerHTML = kv.join(' ');
  }

  // ---- Topbar story picker (runtime selection, not persisted) ----
  function getSelectedStoryId() {
    try { return storyPicker ? String(storyPicker.value || '').trim() : ''; } catch { return ''; }
  }
  async function initStoryPicker() {
    if (!storyPicker) return;
    try {
      const res = await fetch('/api/stories');
      const obj = await res.json();
      const ids = Array.isArray(obj.ids) ? obj.ids : [];
      const serverSel = typeof obj.selected === 'string' ? obj.selected : '';
      storyPicker.innerHTML = '';
      ids.forEach(id => { const opt = document.createElement('option'); opt.value = id; opt.textContent = id; storyPicker.appendChild(opt); });
      const local = (localStorage.getItem('storyPicker.selected') || '').trim();
      let chosen = '';
      if (local && ids.includes(local)) chosen = local; else if (serverSel && ids.includes(serverSel)) chosen = serverSel; else chosen = (ids[0] || '');
      storyPicker.value = chosen;
      if (chosen && chosen !== serverSel) {
        try { await fetch('/api/select_story', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: chosen }) }); } catch(e){ throw e }
      }
      // 初次选择后，若未运行则请求后台预览并渲染到信息栏/地图
      try { if (!running) await fetchPreviewAndRender(); } catch(e) { /* ignore */ }
      storyPicker.onchange = async () => {
        const id = getSelectedStoryId();
        try { localStorage.setItem('storyPicker.selected', id); } catch(e){ throw e }
        try { await fetch('/api/select_story', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id }) }); } catch(e){ throw e }
        // 切换战局后，若未运行则刷新预览
        try { if (!running) await fetchPreviewAndRender(); } catch(e) { /* ignore */ }
      };
    } catch(e){ throw e }
  }

  // 拉取后端可见快照（不启动）并渲染（地图仅使用该接口）
  async function fetchPreviewAndRender() {
    const res = await fetch('/api/visible_state');
    if (!res.ok) return;
    const obj = await res.json();
    if (obj && obj.state && !running) {
      renderHUD(obj.state);
      if (mapView) mapView.update(obj.state);
    }
  }

  async function updateMapFromVisible(actorName) {
    try {
      let url = '/api/visible_state';
      const nm = String(actorName || '').trim();
      if (nm) url += `?actor=${encodeURIComponent(nm)}`;
      const res = await fetch(url);
      if (!res.ok) return;
      const obj = await res.json();
      if (obj && obj.state && mapView) mapView.update(obj.state);
    } catch(e) { /* ignore */ }
  }

  function firstPlayerActor() {
    try {
      const st = lastState || {};
      const chars = st.characters || {};
      for (const nm of Object.keys(chars)) {
        const t = String(((chars[nm]||{}).type||'npc')).toLowerCase();
        if (t === 'player') return nm;
      }
    } catch(e) { /* ignore */ }
    return '';
  }

  function handleEvent(ev) {
    const t = ev.event_type;
    lastSeq = Math.max(lastSeq, ev.sequence || 0);
    if (t === 'state_update') {
      // 合并状态：既支持快照（state），也兼容 turn-state 的局部字段
      const st = ev.state || (ev.data && ev.data.state) || null;
      if (st && typeof st === 'object') {
        lastState = st;
      } else {
        // 可能是 turn-state：positions/in_combat/reaction_available
        const d = ev.data || {};
        if (Object.keys(d).length) {
          lastState = Object.assign({}, lastState);
          if (d.positions) lastState.positions = d.positions;
          if (typeof d.in_combat === 'boolean') lastState.in_combat = d.in_combat;
          if (d.reaction_available) lastState.reaction_available = d.reaction_available;
        }
      }
      renderHUD(lastState);
      // 地图仅用可见快照（优先固定玩家名）
      updateMapFromVisible(mapPlayer || firstPlayerActor());
      return;
    }
    // 精简叙事：展示对白；仅隐藏上下文/回合横幅/世界概要
    if (t === 'narrative') {
      const phase = String(ev.phase || '');
      if (phase.startsWith('context:') || phase === 'round-start' || phase === 'world-summary') return;
      const actor = ev.actor || '';
      const raw = (ev.text || (ev.data && ev.data.text) || '').toString();
      // 过滤叙事中的“理由/行动理由：...”段落，并将多行合并为单行
      const stripRationale = (s) => {
        if (!s) return '';
        let t = String(s);
        // 去掉结尾的“理由/行动理由：.../reason: ...”
        t = t.replace(/\s*(?:行动)?(?:理由|reason|Reason)[:：][\s\S]*$/, '');
        // 去掉仅包含理据的一整行
        if (/^(?:行动)?(?:理由|reason|Reason)[:：]/.test(t.trim())) return '';
        return t.trim();
      };
      const cleaned = raw.split(/\n+/).map(stripRationale).filter(Boolean).join(' ');
      if (!cleaned) return;
      const row = lineEl(`<span class="actor">${esc(actor)}:</span> ${esc(cleaned)}`, 'narrative out');
      storyEl.appendChild(row);
      if (storyEl.children.length > maxStory) storyEl.removeChild(storyEl.firstChild);
      scrollToBottom(storyEl.parentElement);
      return;
    }
    if (t === 'tool_call' || t === 'tool_result') {
      // 将工具调用与结果作为简洁叙事行追加
      try {
        const actor = ev.actor || '';
        const tool = (ev.tool || (ev.data && ev.data.tool) || '').toString();
        const params = (ev.params || (ev.data && ev.data.params) || {}) || {};
        const meta = (ev.metadata || (ev.data && ev.data.metadata) || null);
        const texts = (ev.text || (ev.data && ev.data.text) || []);
        const toolNameMap = {
          'perform_attack': '攻击',
          'advance_position': '移动',
          'adjust_relation': '调整关系',
          'transfer_item': '移交物品',
          'set_protection': '守护',
          'clear_protection': '清除守护',
        };
        const label = toolNameMap[tool] || tool;
        const brief = (() => {
          try {
            if (tool === 'perform_attack') {
              const a = params.attacker || actor; const d = params.defender || ''; const w = params.weapon || '';
              return `${a} -> ${d} 使用 ${w}`;
            }
            if (tool === 'advance_position') {
              const n = params.name || actor; const tgt = params.target; const steps = (params.steps != null ? params.steps : null);
              // Enforce [x,y] array for display; fall back to raw string if malformed
              const xy = (Array.isArray(tgt) && tgt.length >= 2) ? `(${tgt[0]},${tgt[1]})` : String(tgt || '');
              if (steps != null) return `${n} 向 ${xy} 前进 ${steps} 步`;
              return `${n} 向 ${xy} 前进`;
            }
            if (tool === 'adjust_relation') {
              const a = params.a || ''; const b = params.b || ''; const v = params.value;
              return `${a} 对 ${b} 关系设为 ${v}`;
            }
            if (tool === 'transfer_item') {
              const t = params.target || ''; const item = params.item || ''; const n = params.n != null ? params.n : 1;
              return `向 ${t} 移交 ${item} x${n}`;
            }
            if (tool === 'set_protection') {
              const g = params.guardian || ''; const p = params.protectee || '';
              return `${g} 守护 ${p}`;
            }
            if (tool === 'clear_protection') {
              const g = params.guardian || '*'; const p = params.protectee || '*';
              return `清除守护 ${g} -> ${p}`;
            }
          } catch(e) { return ''; }
          return '';
        })();
        if (t === 'tool_call') {
          const line = lineEl(`<span class="actor">${esc(actor)}</span> 发起 <b>${esc(label)}</b>${brief ? ' · ' + esc(brief) : ''}`, 'cmd');
          storyEl.appendChild(line);
        } else {
          // 结果：优先展示文本块；若无文本则展示 metadata 的关键字段
          let textOut = '';
          try {
            // 过滤“理由：...”等理据字段
            const stripReason = (s) => {
              if (!s) return s;
              let t = String(s);
              // 去掉结尾的“理由/行动理由：.../reason: ...”
              t = t.replace(/\s*(?:行动)?(?:理由|reason|Reason)[:：][\s\S]*$/,'');
              // 去掉单独一段“理由/行动理由：...”行
              if (/^(?:行动)?(?:理由|reason|Reason)[:：]/.test(t.trim())) return '';
              return t.trim();
            };
            if (Array.isArray(texts) && texts.length) {
              const cleaned = texts.map(stripReason).filter(Boolean);
              textOut = cleaned.join(' ');
            } else if (meta && typeof meta === 'object') {
              const keys = Object.keys(meta).slice(0, 4);
              textOut = keys.map(k => `${k}=${typeof meta[k]==='object'? JSON.stringify(meta[k]): String(meta[k])}`).join(' ');
              textOut = stripReason(textOut);
            }
          } catch(e){ throw e }
          const line = lineEl(`<span class="actor">${esc(actor)}</span> 结果 <b>${esc(label)}</b>${textOut ? ' · ' + esc(textOut) : ''}`, 'out');
          storyEl.appendChild(line);
        }
        if (storyEl.children.length > maxStory) storyEl.removeChild(storyEl.firstChild);
        scrollToBottom(storyEl.parentElement);
      } catch(e){ throw e }
      return;
    }
    if (t === 'error') {
      const msg = (ev.message != null ? ev.message : (ev.data && ev.data.message)) || 'error';
      const et = (ev.error_type != null ? ev.error_type : (ev.data && ev.data.error_type)) || '';
      const ph = ev.phase || '';
      const tail = `${et ? ` (${et})` : ''}${ph ? ` [${ph}]` : ''}`;
      storyEl.appendChild(lineEl(`error${tail}: ${esc(String(msg))}`, 'error'));
      if (storyEl.children.length > maxStory) storyEl.removeChild(storyEl.firstChild);
      scrollToBottom(storyEl.parentElement);
      return;
    }
  }

  function connectWS() {
    const wsProto = BACKEND_URL ? (BACKEND_URL.protocol === 'https:' ? 'wss' : 'ws') : (location.protocol === 'https:' ? 'wss' : 'ws');
    const wsHost = BACKEND_URL ? BACKEND_URL.host : location.host;
    const basePath = BACKEND_URL ? (BACKEND_URL.pathname || '').replace(/\/$/, '') : '';
    const sidQS = SID ? `&sid=${encodeURIComponent(SID)}` : '';
    const url = `${wsProto}://${wsHost}${basePath}/ws/events?since=${lastSeq}${sidQS}`;
    ws = new WebSocket(url);
    setStatus('连接中…');
    ws.onopen = () => { setStatus('已连接'); reconnectDelay = 500; };
    ws.onmessage = (m) => {
      try {
        const obj = JSON.parse(m.data);
        if (obj.type === 'hello') {
          if (typeof obj.last_sequence === 'number') lastSeq = Math.max(lastSeq, obj.last_sequence);
          if (obj.state) { renderHUD(obj.state); }
          // 地图仅用可见快照（优先固定玩家名）
          updateMapFromVisible(mapPlayer || firstPlayerActor());
          // 查询一次运行状态，刷新按钮
          paused = !!obj.paused;
          fetch('/api/state').then(r=>r.json()).then(st => {
            running = !!st.running;
            paused = !!st.paused;
            updateButtons(); if (running) setStatus(paused ? '已暂停' : '运行中');
          }).catch(()=>{ updateButtons(); });
          return;
        }
        if (obj.type === 'event' && obj.event) {
          if (debugMode) { try { console.debug('EVT', obj.event); } catch(e){ throw e } }
          handleEvent(obj.event);
          if (running) setStatus('运行中');
          // 如果是等待玩家输入的信号，提示一下，并开启发送按钮
          try {
            const ev = obj.event;
            if (ev && ev.event_type === 'system') {
              if (ev.phase === 'player_input') {
                waitingActor = String(ev.actor || '');
                mapPlayer = waitingActor || mapPlayer;
                playerHint.textContent = waitingActor ? `等待 ${waitingActor} 输入...` : '等待玩家输入...';
                btnSend.disabled = !waitingActor;
                if (waitingActor) txtPlayer.focus();
                if (cmdPrompt) cmdPrompt.textContent = (waitingActor ? `${waitingActor}>` : '>');
              } else if (ev.phase === 'player_input_end') {
                waitingActor = '';
                btnSend.disabled = true;
                playerHint.textContent = '';
                if (cmdPrompt) cmdPrompt.textContent = '>';
              }
            }
          } catch(e){ throw e }
          return;
        }
        if (obj.type === 'paused') {
          paused = true; updateButtons(); setStatus('已暂停');
          return;
        }
        if (obj.type === 'resumed') {
          paused = false; updateButtons(); setStatus('运行中');
          return;
        }
        if (obj.type === 'end') {
          setStatus('已结束');
          running = false; paused = false; updateButtons();
          return;
        }
      } catch(e){ throw e }
    };
    ws.onclose = () => {
      setStatus('已断开');
      ws = null;
      setTimeout(connectWS, reconnectDelay);
      reconnectDelay = Math.min(maxDelay, reconnectDelay * 2);
    };
    ws.onerror = () => { try { ws.close(); } catch(e){ throw e } };
  }

  async function postJSON(path) {
    const res = await fetch(path, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  btnStart.onclick = async () => {
    btnStart.disabled = true;
    try {
      const sid = getSelectedStoryId();
      const res = await fetch('/api/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ story_id: sid || undefined }) });
      if (!res.ok) throw new Error(await res.text());
      let data = {};
      try { data = await res.json(); } catch(e){ throw e }
      running = true;
      // 如果是恢复，则取消暂停标记
      if (data && data.message === 'resumed') paused = false;
      updateButtons(); setStatus(paused ? '已暂停' : '运行中');
      if (!ws) connectWS();
      // 已进入运行态
    } catch (e) {
      btnStart.disabled = false;
      alert('启动失败: ' + (e.message || e));
    }
  };

  // Sidebar toggle for better use of space
  if (btnToggleSide) {
    btnToggleSide.onclick = () => {
      document.body.classList.toggle('hide-side');
      setTimeout(() => { if (mapView) mapView.resize(); }, 60);
    };
  }
  // Initialize story picker once at startup
  initStoryPicker();
  // Enhance selects (after init, also watch async population)
  SelectUX.enhanceAll(document);
  SelectUX.startObserver();

  // Golden ratio layout: no sizer

  btnStop.onclick = async () => {
    btnStop.disabled = true;
    try {
      await postJSON('/api/stop');
      // 软暂停请求：等待服务器在安全点广播 paused，再更新按钮
      setStatus('待暂停…');
    } catch (e) {
      alert('终止失败: ' + (e.message || e));
    }
  };

  btnRestart.onclick = async () => {
    btnStart.disabled = true; btnStop.disabled = true; btnRestart.disabled = true;
    try {
      const sid = getSelectedStoryId();
      const res = await fetch('/api/restart', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ story_id: sid || undefined }) });
      if (!res.ok) throw new Error(await res.text());
      // UI 清空到初始状态
      storyEl.innerHTML = '';
      hudEl.innerHTML = '';
      playerHint.textContent = '';
      txtPlayer.value = '';
      lastSeq = 0; waitingActor = ''; btnSend.disabled = true;
      setStatus('restarting...');
      // 刷新一下状态
      try {
        const st = await (await fetch('/api/state')).json();
        if (st && st.state) { renderHUD(st.state); }
        running = !!(st && st.running);
        await updateMapFromVisible(firstPlayerActor());
      } catch(e){ throw e }
      if (!ws) connectWS();
      updateButtons();
    } catch (e) {
      alert('restart failed: ' + (e.message || e));
    } finally {
      btnRestart.disabled = false;
    }
  };

  async function sendPlayer() {
    const name = waitingActor || 'Doctor';
    const text = (txtPlayer.value || '').trim();
    if (!name) { alert('当前没有等待输入的玩家。'); return; }
    if (!text) return;
    try {
      const res = await fetch('/api/player_say', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, text }) });
      if (!res.ok) throw new Error(await res.text());
      // history push
      try { if (text && (cmdHist.length === 0 || cmdHist[cmdHist.length-1] !== text)) cmdHist.push(text); cmdIdx = cmdHist.length; } catch(e){ throw e }
      txtPlayer.value = '';
      playerHint.textContent = '';
      // 发送一次后关闭按钮，直到服务端再次下发等待提示
      waitingActor = '';
      btnSend.disabled = true;
    } catch (e) {
      alert('send failed: ' + (e.message || e));
    }
  }
  btnSend.onclick = sendPlayer;
  txtPlayer.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendPlayer(); return; }
    if (e.key === 'ArrowUp') {
      if (cmdHist.length) { cmdIdx = Math.max(0, cmdIdx - 1); txtPlayer.value = cmdHist[cmdIdx] || ''; setTimeout(()=> txtPlayer.setSelectionRange(txtPlayer.value.length, txtPlayer.value.length), 0); e.preventDefault(); }
      return;
    }
    if (e.key === 'ArrowDown') {
      if (cmdHist.length) { cmdIdx = Math.min(cmdHist.length, cmdIdx + 1); txtPlayer.value = (cmdIdx >= cmdHist.length) ? '' : (cmdHist[cmdIdx] || ''); setTimeout(()=> txtPlayer.setSelectionRange(txtPlayer.value.length, txtPlayer.value.length), 0); e.preventDefault(); }
      return;
    }
  });

  // handle window resize for map
  if (mapView) {
    window.addEventListener('resize', () => mapView.resize());
    // initial sizing in case canvas mounted before script
    setTimeout(()=> mapView.resize(), 0);
  }

  // connect on load to receive any state before clicking Start
  connectWS();
  // 初始化按钮状态（未知运行态 -> 拉一次 state）
  fetch('/api/state').then(r=>r.json()).then(st => {
    running = !!st.running; paused = !!st.paused;
    updateButtons();
    if (st && st.state) { renderHUD(st.state); if (mapView) mapView.update(st.state); }
    if (running) setStatus(paused ? '已暂停' : '运行中');
    // 若未运行且没有有效快照，补一次预览渲染
    if (!running && (!st || !st.state || !Object.keys(st.state||{}).length)) {
      fetchPreviewAndRender().catch(()=>{});
    }
  }).catch(()=>{ updateButtons(); });

  // ==== Settings drawer logic ====
  function drawerOpen() {
    if (!drawer) return;
    drawer.classList.remove('hidden');
    drawer.setAttribute('aria-hidden', 'false');
  }
  function drawerClose(force=false) {
    if (!drawer) return;
    if (!force && (dirty.story || dirty.weapons || dirty.characters)) {
      if (!confirm('有未保存的更改，确定关闭？')) return;
    }
    drawer.classList.add('hidden');
    drawer.setAttribute('aria-hidden', 'true');
  }
  function setActiveTab(name) {
    activeTab = name;
    for (const b of tabBtns) {
      const on = b.getAttribute('data-tab') === name;
      b.classList.toggle('active', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    }
    for (const p of panes) {
      const show = p.getAttribute('data-pane') === name;
      p.classList.toggle('hidden', !show);
    }
  }
  function markDirty(name) {
    dirty[name] = true;
  }

  function clearListEdit(el) { if (!el) return; el.innerHTML = ''; }
  function addListRow(el, value, onChange, onDelete) {
    const row = document.createElement('div');
    row.className = 'row';
    const inp = document.createElement('input');
    inp.type = 'text';
    inp.value = value || '';
    inp.addEventListener('input', () => onChange(inp.value));
    const del = document.createElement('button');
    del.className = 'sm'; del.textContent = '删除';
    del.onclick = onDelete;
    row.appendChild(inp); row.appendChild(del);
    el.appendChild(row);
  }

  function renderCharList(names) {
    if (!chListEl) return;
    chListEl.innerHTML = '';
    names.forEach(nm => {
      const it = document.createElement('div');
      it.className = 'item' + (nm === chActiveName ? ' active' : '');
      it.textContent = nm;
      it.onclick = () => { selectChar(nm); };
      chListEl.appendChild(it);
    });
  }

  function selectChar(name) {
    chActiveName = name;
    renderCharList(Object.keys(cfg.characters||{}));
    fillCharForm(name);
  }

  function ensureEntry(name) {
    cfg.characters = cfg.characters || {};
    if (!cfg.characters[name]) {
      cfg.characters[name] = {
        type: 'npc', persona: '', appearance: '', quotes: [],
        coc: { characteristics: { STR:50, DEX:50, CON:50, INT:50, POW:50, APP:50, EDU:60, SIZ:50, LUCK:50 }, skills: {}, terra: { infection:{ stage:0, stress:0, crystal_density:0 }, protection:{ physical_armor:0, arts_barrier:0 } } },
        inventory: {}
      };
    }
    return cfg.characters[name];
  }

  function fillCharForm(name) {
    const entry = ensureEntry(name);
    if (chName) chName.value = name;
    if (chType) {
      // Update native select value and notify custom SelectUX to sync its trigger label
      chType.value = (entry.type||'npc');
      try { chType.dispatchEvent(new Event('change', { bubbles: true })); } catch (e) { /* no-op */ }
    }
    if (chPersona) chPersona.value = entry.persona || '';
    if (chAppearance) chAppearance.value = entry.appearance || '';
    // quotes
    if (chQuotes) {
      chQuotes.innerHTML = '';
      const arr = Array.isArray(entry.quotes) ? entry.quotes.slice() : (entry.quotes? [String(entry.quotes)]: []);
      entry.quotes = arr;
      arr.forEach((q, idx) => addListRow(chQuotes, q, v => { entry.quotes[idx] = v; markDirty('characters'); }, () => { entry.quotes.splice(idx,1); fillCharForm(name); markDirty('characters'); }));
    }
    // CoC block
    const coc = entry.coc = Object.assign({ characteristics:{}, skills:{}, terra:{} }, entry.coc || {});
    const ch = coc.characteristics = Object.assign({ STR:50, DEX:50, CON:50, INT:50, POW:50, APP:50, EDU:60, SIZ:50, LUCK:50 }, coc.characteristics || {});
    if (cocSTR) cocSTR.value = ch.STR != null ? ch.STR : 50;
    if (cocDEX) cocDEX.value = ch.DEX != null ? ch.DEX : 50;
    if (cocCON) cocCON.value = ch.CON != null ? ch.CON : 50;
    if (cocINT) cocINT.value = ch.INT != null ? ch.INT : 50;
    if (cocPOW) cocPOW.value = ch.POW != null ? ch.POW : 50;
    if (cocAPP) cocAPP.value = ch.APP != null ? ch.APP : 50;
    if (cocEDU) cocEDU.value = ch.EDU != null ? ch.EDU : 60;
    if (cocSIZ) cocSIZ.value = ch.SIZ != null ? ch.SIZ : 50;
    if (cocLUCK) cocLUCK.value = ch.LUCK != null ? ch.LUCK : 50;
    const recomputeDerived = () => {
      const CON = parseInt(cocCON ? cocCON.value||'0' : '0', 10) || 0;
      const SIZ = parseInt(cocSIZ ? cocSIZ.value||'0' : '0', 10) || 0;
      const POW = parseInt(cocPOW ? cocPOW.value||'0' : '0', 10) || 0;
      const hp = Math.max(1, Math.floor((CON + SIZ) / 10));
      const mp = Math.max(0, Math.floor(POW / 5));
      if (cocDerived) cocDerived.textContent = `HP ≈ ${hp}，MP ≈ ${mp}`;
    };
    recomputeDerived();
    [cocSTR,cocDEX,cocCON,cocINT,cocPOW,cocAPP,cocEDU,cocSIZ,cocLUCK].forEach(el=>{ if (el) el.oninput = ()=>{ const k = el.id.replace('coc',''); coc.characteristics[k] = parseInt(el.value||'0',10)||0; recomputeDerived(); markDirty('characters'); }; });
    // Skills table
    if (chSkillsTable) {
      const tbody = chSkillsTable.querySelector('tbody');
      const skillListAll = ['Arts_Control','Arts_Offense','Perception','Dodge','FirstAid','Firearms_Handgun','Firearms_Rifle_Crossbow','Fighting_Blade','Fighting_Blunt','Fighting_DualBlade','Fighting_Polearm','Throwables_Explosives','Heavy_Weapons'];
      const fill = () => {
        tbody.innerHTML = '';
        const skills = coc.skills = Object.assign({}, coc.skills || {});
        Object.entries(skills).forEach(([sname, sval]) => {
          const tr = document.createElement('tr');
          const tdName = document.createElement('td');
          const sel = document.createElement('select');
          skillListAll.forEach(s=>{ const o=document.createElement('option'); o.value=s; o.textContent=s; sel.appendChild(o); });
          sel.value = String(sname);
          sel.onchange = ()=>{ const v = skills[sname]; delete skills[sname]; skills[sel.value] = v; fill(); markDirty('characters'); };
          tdName.appendChild(sel);
          const tdVal = document.createElement('td');
          const inp = document.createElement('input'); inp.type='number'; inp.value = String(sval||0); inp.oninput=()=>{ skills[sel.value] = parseInt(inp.value||'0',10)||0; markDirty('characters'); };
          tdVal.appendChild(inp);
          const tdOps = document.createElement('td'); const btn=document.createElement('button'); btn.className='sm'; btn.textContent='删除'; btn.onclick=()=>{ delete skills[sel.value]; fill(); markDirty('characters'); }; tdOps.appendChild(btn);
          tr.appendChild(tdName); tr.appendChild(tdVal); tr.appendChild(tdOps);
          tbody.appendChild(tr);
        });
      };
      fill();
      if (btnAddSkill) btnAddSkill.onclick = () => {
        const skills = coc.skills = Object.assign({}, coc.skills || {});
        const all = ['Arts_Control','Arts_Offense','Perception','Dodge','FirstAid','Firearms_Handgun','Firearms_Rifle_Crossbow','Fighting_Blade','Fighting_Blunt','Fighting_DualBlade','Fighting_Polearm','Throwables_Explosives','Heavy_Weapons'];
        const exist = new Set(Object.keys(skills));
        const candidate = all.find(s=>!exist.has(s)) || 'Perception';
        skills[candidate] = 50;
        fill(); markDirty('characters');
      };
    }
    // Terra
    const terra = coc.terra = Object.assign({ infection:{}, protection:{} }, coc.terra || {});
    const inf = terra.infection = Object.assign({ stage:0, stress:0, crystal_density:0 }, terra.infection || {});
    const prot = terra.protection = Object.assign({ physical_armor:0, arts_barrier:0 }, terra.protection || {});
    if (terraInfectStage) terraInfectStage.value = inf.stage != null ? inf.stage : 0;
    if (terraInfectStress) terraInfectStress.value = inf.stress != null ? inf.stress : 0;
    if (terraCrystal) terraCrystal.value = inf.crystal_density != null ? inf.crystal_density : 0;
    if (terraArmor) terraArmor.value = prot.physical_armor != null ? prot.physical_armor : 0;
    if (terraBarrier) terraBarrier.value = prot.arts_barrier != null ? prot.arts_barrier : 0;
    const bindCoCNum = (el, set) => { if (!el) return; el.addEventListener('input', ()=>{ if (!chActiveName) return; set(); markDirty('characters'); }); };
    bindCoCNum(terraInfectStage, ()=>{ ensureEntry(chActiveName).coc.terra.infection.stage = parseInt(terraInfectStage.value||'0',10)||0; });
    bindCoCNum(terraInfectStress, ()=>{ ensureEntry(chActiveName).coc.terra.infection.stress = parseInt(terraInfectStress.value||'0',10)||0; });
    bindCoCNum(terraCrystal, ()=>{ ensureEntry(chActiveName).coc.terra.infection.crystal_density = parseInt(terraCrystal.value||'0',10)||0; });
    bindCoCNum(terraArmor, ()=>{ ensureEntry(chActiveName).coc.terra.protection.physical_armor = parseInt(terraArmor.value||'0',10)||0; });
    bindCoCNum(terraBarrier, ()=>{ ensureEntry(chActiveName).coc.terra.protection.arts_barrier = parseInt(terraBarrier.value||'0',10)||0; });
    // inventory
    if (chInvTable) {
      const tbody = chInvTable.querySelector('tbody');
      tbody.innerHTML = '';
      const inv = entry.inventory = Object.assign({}, entry.inventory || {});
      Object.entries(inv).forEach(([iid, cnt]) => {
        const tr = document.createElement('tr');
        const tdId = document.createElement('td');
        const tdN = document.createElement('td');
        const tdOp = document.createElement('td');
        const inId = document.createElement('input'); inId.type='text'; inId.value=iid; inId.disabled=true; tdId.appendChild(inId);
        const inN  = document.createElement('input'); inN.type='number'; inN.value=(cnt!=null? cnt:1); inN.addEventListener('input', ()=>{ inv[iid] = parseInt(inN.value||'1',10); markDirty('characters'); }); tdN.appendChild(inN);
        const del = document.createElement('button'); del.className='sm'; del.textContent='删除'; del.onclick=()=>{ delete inv[iid]; fillCharForm(name); markDirty('characters'); };
        tdOp.appendChild(del);
        tr.appendChild(tdId); tr.appendChild(tdN); tr.appendChild(tdOp);
        tbody.appendChild(tr);
      });
    }
    // populate add-inventory select
    try {
      if (chInvIdSel) {
        const weaponIds = Object.keys(cfg.weapons||{});
        chInvIdSel.innerHTML = '';
        const ph = document.createElement('option'); ph.value=''; ph.textContent='选择武器…'; chInvIdSel.appendChild(ph);
        for (const wid of weaponIds) {
          const opt = document.createElement('option'); opt.value=wid; opt.textContent=wid; chInvIdSel.appendChild(opt);
        }
      }
    } catch(e){ throw e }
  }

  function renderStoryForm(data, stateSnap) {
    original.story = JSON.parse(JSON.stringify(data || {}));
    cfg.story = JSON.parse(JSON.stringify(data || {}));
    dirty.story = false;
    const scene = (cfg.story.scene = cfg.story.scene || {});
    stSceneName.value = scene.name || '';
    stSceneTime.value = scene.time || '';
    stSceneWeather.value = scene.weather || '';
    stSceneDesc.value = scene.description || '';
    // details
    const details = Array.isArray(scene.details) ? scene.details.slice() : [];
    clearListEdit(stDetails);
    details.forEach((val, idx) => addListRow(stDetails, val, v => { scene.details[idx] = v; markDirty('story'); }, () => {
      scene.details.splice(idx,1); renderStoryForm(cfg.story, stateSnap); markDirty('story');
    }));
    scene.details = details;
    // objectives
    const objs = Array.isArray(scene.objectives) ? scene.objectives.slice() : [];
    clearListEdit(stObjectives);
    objs.forEach((val, idx) => addListRow(stObjectives, val, v => { scene.objectives[idx] = v; markDirty('story'); }, () => {
      scene.objectives.splice(idx,1); renderStoryForm(cfg.story, stateSnap); markDirty('story');
    }));
    scene.objectives = objs;

    // endings
    function renderEndings(list) {
      if (!stEndingsBody) return;
      const arr = Array.isArray(list) ? list : [];
      cfg.story.endings = arr.map(e => Object.assign({ id:'', label:'', outcome:'neutral', priority:0 }, e||{}));
      stEndingsBody.innerHTML = '';
      const mkCell = () => document.createElement('td');
      const outcomes = ['success','failure','neutral'];
      cfg.story.endings.forEach((en, idx) => {
        const tr = document.createElement('tr');
        // id
        const tdId = mkCell(); const inId = document.createElement('input'); inId.type='text'; inId.value = en.id || ''; inId.addEventListener('input', ()=>{ cfg.story.endings[idx].id = inId.value.trim(); markDirty('story'); }); tdId.appendChild(inId);
        // label
        const tdLabel = mkCell(); const inLabel = document.createElement('input'); inLabel.type='text'; inLabel.value = en.label || ''; inLabel.addEventListener('input', ()=>{ cfg.story.endings[idx].label = inLabel.value; markDirty('story'); }); tdLabel.appendChild(inLabel);
        // outcome
        const tdOut = mkCell(); const selOut = document.createElement('select'); selOut.className='fit-select'; outcomes.forEach(v=>{ const o=document.createElement('option'); o.value=v; o.textContent=v; selOut.appendChild(o); }); selOut.value = (en.outcome||'neutral'); selOut.addEventListener('change', ()=>{ cfg.story.endings[idx].outcome = selOut.value; markDirty('story'); }); tdOut.appendChild(selOut);
        // priority
        const tdPr = mkCell(); const inPr = document.createElement('input'); inPr.type='number'; inPr.value = (typeof en.priority==='number'? en.priority:0); inPr.addEventListener('input', ()=>{ cfg.story.endings[idx].priority = parseInt(inPr.value||'0',10)||0; markDirty('story'); }); tdPr.appendChild(inPr);
        // when JSON + builder
        const tdWhen = mkCell();
        const ta = document.createElement('textarea'); ta.rows=3; ta.placeholder='{ "any": [ ... ] }'; ta.style.marginBottom='6px';
        try { ta.value = en.when ? JSON.stringify(en.when, null, 2) : ''; } catch { ta.value = ''; }
        const validate = () => { try { const obj = ta.value.trim()? JSON.parse(ta.value): null; ta.style.borderColor=''; cfg.story.endings[idx].when = obj; markDirty('story'); } catch(e){ ta.style.borderColor = '#e11d48'; } };
        ta.addEventListener('input', validate);
        const btnBuild = document.createElement('button'); btnBuild.className='sm'; btnBuild.textContent='编辑条件'; btnBuild.onclick = () => openWhenEditor(idx);
        tdWhen.appendChild(ta); tdWhen.appendChild(btnBuild);
        // ops
        const tdOps = mkCell(); const btnDel = document.createElement('button'); btnDel.className='sm'; btnDel.textContent='删除'; btnDel.onclick=()=>{ cfg.story.endings.splice(idx,1); renderEndings(cfg.story.endings); markDirty('story'); }; tdOps.appendChild(btnDel);
        tr.appendChild(tdId); tr.appendChild(tdLabel); tr.appendChild(tdOut); tr.appendChild(tdPr); tr.appendChild(tdWhen); tr.appendChild(tdOps);
        stEndingsBody.appendChild(tr);
      });
      if (btnAddEnding) btnAddEnding.onclick = () => { cfg.story.endings.push({ id:'', label:'', outcome:'neutral', priority:0, when:{"any":[]} }); renderEndings(cfg.story.endings); markDirty('story'); };
    }
    if (stEndingsBody) renderEndings((cfg.story||{}).endings || []);

    // scenes list UI
    function renderScenesList() {
      if (!stScenesTable) return;
      const tbody = stScenesTable.querySelector('tbody');
      tbody.innerHTML = '';
      const map = cfg.story.scenes = Object.assign({}, cfg.story.scenes || {});
      Object.entries(map).forEach(([sid, sc]) => {
        const tr = document.createElement('tr');
        const tdId=document.createElement('td'); tdId.textContent=sid; tr.appendChild(tdId);
        const tdName=document.createElement('td'); const inNm=document.createElement('input'); inNm.type='text'; inNm.value=String((sc||{}).name||''); inNm.addEventListener('input',()=>{ (cfg.story.scenes[sid]||(cfg.story.scenes[sid]={})).name=inNm.value; markDirty('story'); }); tdName.appendChild(inNm); tr.appendChild(tdName);
        const tdCnt=document.createElement('td'); try{ const n=Array.isArray((sc||{}).details)? (sc.details||[]).length:0; tdCnt.textContent=String(n);}catch(e){ tdCnt.textContent='0'; } tr.appendChild(tdCnt);
        const tdOp=document.createElement('td');
        const btnEd=document.createElement('button'); btnEd.className='sm'; btnEd.textContent='编辑'; btnEd.onclick=()=> openSceneEditor(sid);
        const btnDel=document.createElement('button'); btnDel.className='sm'; btnDel.textContent='删除'; btnDel.onclick=()=>{ delete cfg.story.scenes[sid]; renderScenesList(); try{renderScenePositions();}catch(_e){}; markDirty('story'); };
        tdOp.appendChild(btnEd); tdOp.appendChild(btnDel); tr.appendChild(tdOp);
        tbody.appendChild(tr);
      });
      if (btnAddScene) btnAddScene.onclick = () => {
        const id = prompt('新场景 ID (a-z0-9_-)');
        if (!id) return;
        if ((cfg.story.scenes||{})[id]) { alert('已存在同名场景'); return; }
        (cfg.story.scenes||(cfg.story.scenes={}))[id] = { name:'', details:[] };
        renderScenesList(); try{renderScenePositions();}catch(_e){}; markDirty('story');
      };
    }
    function openSceneEditor(sid) {
      if (!stSceneEditor) return;
      stSceneEditor.classList.remove('hidden');
      stSceneEditId && (stSceneEditId.value = sid);
      const sc = (cfg.story.scenes[sid] = Object.assign({ name:'', details:[] }, cfg.story.scenes[sid] || {}));
      if (stSceneEditName) {
        stSceneEditName.value = sc.name || '';
        stSceneEditName.oninput = () => { cfg.story.scenes[sid].name = stSceneEditName.value; markDirty('story'); };
      }
      if (stSceneEditDetails) {
        clearListEdit(stSceneEditDetails);
        const arr = Array.isArray(sc.details) ? sc.details.slice() : [];
        arr.forEach((val, idx) => addListRow(stSceneEditDetails, val, v => { cfg.story.scenes[sid].details[idx] = v; markDirty('story'); }, () => {
          cfg.story.scenes[sid].details.splice(idx,1); openSceneEditor(sid); markDirty('story');
        }));
        cfg.story.scenes[sid].details = arr;
        if (btnAddSceneDetail) btnAddSceneDetail.onclick = () => { cfg.story.scenes[sid].details.push(''); openSceneEditor(sid); markDirty('story'); };
      }
    }

    // entrances UI
    function renderEntrancesTable() {
      if (!stEntrTable) return;
      const tbody = stEntrTable.querySelector('tbody');
      tbody.innerHTML = '';
      const map = cfg.story.entrances = Object.assign({}, cfg.story.entrances || {});
      const mkInput=(type,val,on)=>{ const i=document.createElement('input'); i.type=type; i.value=(val!=null? String(val):''); i.addEventListener('input',()=>on(i.value)); return i; };
      const sceneIds = Object.keys(cfg.story.scenes || {});
      Object.entries(map).forEach(([eid, e]) => {
        const tr = document.createElement('tr');
        const tdId=document.createElement('td'); tdId.textContent=eid; tr.appendChild(tdId);
        const tdLabel=document.createElement('td'); const inLbl=mkInput('text', (e||{}).label||'', v=>{ (cfg.story.entrances[eid]||(cfg.story.entrances[eid]={})).label=v; markDirty('story'); }); tdLabel.appendChild(inLbl); tr.appendChild(tdLabel);
        // from_scene select
        const tdFrom=document.createElement('td');
        const selFrom=document.createElement('select');
        const phF=document.createElement('option'); phF.value=''; phF.textContent='选择场景…'; selFrom.appendChild(phF);
        sceneIds.forEach(id=>{ const o=document.createElement('option'); o.value=id; o.textContent=id; selFrom.appendChild(o); });
        selFrom.value=String((e||{}).from_scene||'');
        selFrom.addEventListener('change', ()=>{ (cfg.story.entrances[eid]||(cfg.story.entrances[eid]={})).from_scene=selFrom.value; markDirty('story'); });
        tdFrom.appendChild(selFrom); tr.appendChild(tdFrom);
        // to_scene select
        const tdTo=document.createElement('td');
        const selTo=document.createElement('select');
        const phT=document.createElement('option'); phT.value=''; phT.textContent='选择场景…'; selTo.appendChild(phT);
        sceneIds.forEach(id=>{ const o=document.createElement('option'); o.value=id; o.textContent=id; selTo.appendChild(o); });
        selTo.value=String((e||{}).to_scene||'');
        selTo.addEventListener('change', ()=>{ (cfg.story.entrances[eid]||(cfg.story.entrances[eid]={})).to_scene=selTo.value; markDirty('story'); });
        tdTo.appendChild(selTo); tr.appendChild(tdTo);
        const at = Array.isArray((e||{}).at) ? (e.at||[]) : [];
        const sp = Array.isArray((e||{}).spawn) ? (e.spawn||[]) : [];
        const tdAx=document.createElement('td'); const inAx=mkInput('number', (Array.isArray(at)&&at.length>0? String(at[0]) : ''), v=>{ const A=(cfg.story.entrances[eid]||(cfg.story.entrances[eid]={})); const arr=Array.isArray(A.at)?A.at:[0,0]; arr[0]=parseInt(v||'0',10)||0; A.at=arr; markDirty('story'); }); tdAx.appendChild(inAx); tr.appendChild(tdAx);
        const tdAy=document.createElement('td'); const inAy=mkInput('number', (Array.isArray(at)&&at.length>1? String(at[1]) : ''), v=>{ const A=(cfg.story.entrances[eid]||(cfg.story.entrances[eid]={})); const arr=Array.isArray(A.at)?A.at:[0,0]; arr[1]=parseInt(v||'0',10)||0; A.at=arr; markDirty('story'); }); tdAy.appendChild(inAy); tr.appendChild(tdAy);
        const tdSx=document.createElement('td'); const inSx=mkInput('number', (Array.isArray(sp)&&sp.length>0? String(sp[0]) : ''), v=>{ const A=(cfg.story.entrances[eid]||(cfg.story.entrances[eid]={})); const arr=Array.isArray(A.spawn)?A.spawn:[0,0]; arr[0]=parseInt(v||'0',10)||0; A.spawn=arr; markDirty('story'); }); tdSx.appendChild(inSx); tr.appendChild(tdSx);
        const tdSy=document.createElement('td'); const inSy=mkInput('number', (Array.isArray(sp)&&sp.length>1? String(sp[1]) : ''), v=>{ const A=(cfg.story.entrances[eid]||(cfg.story.entrances[eid]={})); const arr=Array.isArray(A.spawn)?A.spawn:[0,0]; arr[1]=parseInt(v||'0',10)||0; A.spawn=arr; markDirty('story'); }); tdSy.appendChild(inSy); tr.appendChild(tdSy);
        const tdDesc=document.createElement('td'); const inD=mkInput('text', (e||{}).desc||'', v=>{ (cfg.story.entrances[eid]||(cfg.story.entrances[eid]={})).desc=v; markDirty('story'); }); tdDesc.appendChild(inD); tr.appendChild(tdDesc);
        const tdOps=document.createElement('td'); const btnDel=document.createElement('button'); btnDel.className='sm'; btnDel.textContent='删除'; btnDel.onclick=()=>{ delete cfg.story.entrances[eid]; renderEntrancesTable(); markDirty('story'); }; tdOps.appendChild(btnDel); tr.appendChild(tdOps);
        tbody.appendChild(tr);
      });
      if (btnAddEntrance) btnAddEntrance.onclick = () => {
        const id = prompt('新入口 ID');
        if (!id) return;
        if ((cfg.story.entrances||{})[id]) { alert('已存在同名入口'); return; }
        (cfg.story.entrances||(cfg.story.entrances={}))[id] = { label:'', from_scene:'', to_scene:'', at:[0,0], spawn:[0,0], desc:'' };
        renderEntrancesTable(); markDirty('story');
      };
    }

    // initial scenes UI
    function renderInitialScenes() {
      if (!stInitScenesTable) return;
      const tbody = stInitScenesTable.querySelector('tbody');
      tbody.innerHTML = '';
      const map = cfg.story.initial_scenes = Object.assign({}, cfg.story.initial_scenes || {});
      Object.entries(map).forEach(([name, sid]) => {
        const tr=document.createElement('tr');
        const tdN=document.createElement('td'); tdN.textContent=String(name); tr.appendChild(tdN);
        const tdS=document.createElement('td'); const inS=document.createElement('input'); inS.type='text'; inS.value=String(sid||''); inS.addEventListener('input',()=>{ cfg.story.initial_scenes[name] = inS.value; markDirty('story'); }); tdS.appendChild(inS); tr.appendChild(tdS);
        const tdOp=document.createElement('td'); const btnDel=document.createElement('button'); btnDel.className='sm'; btnDel.textContent='删除'; btnDel.onclick=()=>{ delete cfg.story.initial_scenes[name]; renderInitialScenes(); markDirty('story'); }; tdOp.appendChild(btnDel); tr.appendChild(tdOp);
        tbody.appendChild(tr);
      });
      // populate actor select
      if (stInitSceneNameSel) {
        stInitSceneNameSel.innerHTML = '';
        const names = Object.keys(cfg.characters || {});
        const ph = document.createElement('option'); ph.value=''; ph.textContent='选择角色…'; stInitSceneNameSel.appendChild(ph);
        names.forEach(n=>{ const o=document.createElement('option'); o.value=n; o.textContent=n; stInitSceneNameSel.appendChild(o); });
      }
      if (btnSetInitScene) btnSetInitScene.onclick = () => {
        const nm = stInitSceneNameSel ? String(stInitSceneNameSel.value||'').trim() : '';
        const sid = stInitSceneId ? String(stInitSceneId.value||'').trim() : '';
        if (!nm || !sid) { alert('请选择角色并填写场景ID'); return; }
        (cfg.story.initial_scenes||(cfg.story.initial_scenes={}))[nm] = sid;
        renderInitialScenes(); markDirty('story');
      };
    }

    // scene positions UI
    function renderScenePositions() {
      if (!stScenePosTable) return;
      const scenes = Object.keys(cfg.story.scenes || {});
      if (stScenePosSel) {
        stScenePosSel.innerHTML = '';
        const ph=document.createElement('option'); ph.value=''; ph.textContent='选择场景…'; stScenePosSel.appendChild(ph);
        scenes.forEach(id=>{ const o=document.createElement('option'); o.value=id; o.textContent=id; stScenePosSel.appendChild(o); });
      }
      const ensure = (s)=>{ cfg.story.scene_positions = Object.assign({}, cfg.story.scene_positions || {}); if (!cfg.story.scene_positions[s]) cfg.story.scene_positions[s] = {}; return cfg.story.scene_positions[s]; };
      const renderFor = (sid) => {
        const tbody = stScenePosTable.querySelector('tbody');
        tbody.innerHTML = '';
        const mp = ensure(sid);
        Object.entries(mp).forEach(([nm, arr]) => {
          const tr=document.createElement('tr');
          const tdN=document.createElement('td'); tdN.textContent=String(nm); tr.appendChild(tdN);
          const tdX=document.createElement('td'); const inX=document.createElement('input'); inX.type='number'; inX.value = Array.isArray(arr)&&arr.length>0? String(arr[0]):''; inX.addEventListener('input',()=>{ const v=mp[nm]||[0,0]; v[0]=parseInt(inX.value||'0',10)||0; mp[nm]=v; markDirty('story'); }); tdX.appendChild(inX); tr.appendChild(tdX);
          const tdY=document.createElement('td'); const inY=document.createElement('input'); inY.type='number'; inY.value = Array.isArray(arr)&&arr.length>1? String(arr[1]):''; inY.addEventListener('input',()=>{ const v=mp[nm]||[0,0]; v[1]=parseInt(inY.value||'0',10)||0; mp[nm]=v; markDirty('story'); }); tdY.appendChild(inY); tr.appendChild(tdY);
          const tdOp=document.createElement('td'); const btnDel=document.createElement('button'); btnDel.className='sm'; btnDel.textContent='删除'; btnDel.onclick=()=>{ delete mp[nm]; renderFor(sid); markDirty('story'); }; tdOp.appendChild(btnDel); tr.appendChild(tdOp);
          tbody.appendChild(tr);
        });
        // populate actor select from characters
        if (stScenePosNameSel) {
          stScenePosNameSel.innerHTML='';
          const ph = document.createElement('option'); ph.value=''; ph.textContent='选择角色…'; stScenePosNameSel.appendChild(ph);
          Object.keys(cfg.characters||{}).forEach(n=>{ const o=document.createElement('option'); o.value=n; o.textContent=n; stScenePosNameSel.appendChild(o); });
        }
        if (btnAddScenePos) btnAddScenePos.onclick = () => {
          const nm = stScenePosNameSel ? String(stScenePosNameSel.value||'').trim() : '';
          const x = parseInt(stScenePosX ? stScenePosX.value||'0' : '0', 10) || 0;
          const y = parseInt(stScenePosY ? stScenePosY.value||'0' : '0', 10) || 0;
          if (!nm) { alert('请选择角色'); return; }
          mp[nm] = [x,y];
          renderFor(sid); markDirty('story');
        };
      };
      // wire change
      if (stScenePosSel) stScenePosSel.onchange = () => { const sid = String(stScenePosSel.value||''); if (sid) renderFor(sid); };
      // auto-select first scene
      try { if (stScenePosSel && !stScenePosSel.value && scenes.length>0) { stScenePosSel.value = scenes[0]; renderFor(scenes[0]); } } catch(e){}
    }

    renderScenesList();
    renderEntrancesTable();
    renderInitialScenes();
    renderScenePositions();
    try { renderTimelineForm((cfg.story||{}).events || []); } catch(e){}

    // positions
    const tbody = stTbl.querySelector('tbody');
    tbody.innerHTML = '';
    const pos = Object.assign({}, cfg.story.initial_positions || {});
    // seed from state participants if empty
    try {
      if ((!pos || Object.keys(pos).length === 0) && stateSnap && stateSnap.participants) {
        for (const nm of stateSnap.participants) {
          const p = (stateSnap.positions||{})[nm] || [0,0];
          pos[nm] = p;
        }
      }
    } catch(e){ throw e }
    cfg.story.initial_positions = pos;
    Object.entries(pos).forEach(([name, arr]) => {
      const tr = document.createElement('tr');
      const tdN = document.createElement('td');
      const tdX = document.createElement('td');
      const tdY = document.createElement('td');
      const tdOp = document.createElement('td');
      const inN = document.createElement('input'); inN.type = 'text'; inN.value = name; inN.disabled = true;
      const inX = document.createElement('input'); inX.type = 'number'; inX.value = (arr && arr[0] != null) ? arr[0] : 0;
      const inY = document.createElement('input'); inY.type = 'number'; inY.value = (arr && arr[1] != null) ? arr[1] : 0;
      inX.addEventListener('input', ()=>{ cfg.story.initial_positions[name] = [parseInt(inX.value||'0',10), parseInt(inY.value||'0',10)]; markDirty('story'); });
      inY.addEventListener('input', ()=>{ cfg.story.initial_positions[name] = [parseInt(inX.value||'0',10), parseInt(inY.value||'0',10)]; markDirty('story'); });
      const del = document.createElement('button'); del.className='sm'; del.textContent='删除'; del.onclick = ()=>{ delete cfg.story.initial_positions[name]; renderStoryForm(cfg.story, stateSnap); markDirty('story'); };
      tdN.appendChild(inN); tdX.appendChild(inX); tdY.appendChild(inY); tdOp.appendChild(del);
      tr.appendChild(tdN); tr.appendChild(tdX); tr.appendChild(tdY); tr.appendChild(tdOp);
      tbody.appendChild(tr);
    });
    // Populate name select from existing characters (exclude already-present)
    try {
      if (stPosNameSel) {
        const names = Object.keys(cfg.characters || {});
        const used = new Set(Object.keys(cfg.story.initial_positions || {}));
        stPosNameSel.innerHTML = '';
        const placeholder = document.createElement('option'); placeholder.value=''; placeholder.textContent='选择角色…'; stPosNameSel.appendChild(placeholder);
        for (const nm of names) {
          if (used.has(nm)) continue;
          const opt = document.createElement('option');
          opt.value = nm; opt.textContent = nm;
          stPosNameSel.appendChild(opt);
        }
      }
    } catch(e){ throw e }
  }

  function renderWeaponsForm(data) {
    original.weapons = JSON.parse(JSON.stringify(data || {}));
    cfg.weapons = JSON.parse(JSON.stringify(data || {}));
    dirty.weapons = false;
    const tbody = wpTable.querySelector('tbody');
    tbody.innerHTML = '';
    const rrOpt = (window.RR && window.RR.options) ? window.RR.options : {};
    const weaponSkillList = Array.isArray(rrOpt.weapon_hit_skills) ? rrOpt.weapon_hit_skills : ['Fighting_Blade','Fighting_Blunt','Fighting_DualBlade','Fighting_Polearm','Firearms_Handgun','Firearms_Rifle_Crossbow','Throwables_Explosives'];
    const defenseSkillList = Array.isArray(rrOpt.defense_skills) ? rrOpt.defense_skills : ['Dodge'];
    const dmgTypes = Array.isArray(rrOpt.weapon_damage_types) ? rrOpt.weapon_damage_types : ['physical','arts'];
    const ids = Object.keys(cfg.weapons || {});
    ids.forEach((id) => {
      const item = cfg.weapons[id] || {};
      const tr = document.createElement('tr');
      // id
      const tdId = document.createElement('td');
      const inId = document.createElement('input'); inId.type='text'; inId.value=id; tdId.appendChild(inId);
      inId.addEventListener('change', ()=>{
        const newId = String(inId.value||'').trim();
        const oldId = id;
        if (!newId) { alert('ID 不能为空'); inId.value = oldId; return; }
        if (newId === oldId) return;
        if ((cfg.weapons||{})[newId]) { alert('已存在同名武器 ID'); inId.value = oldId; return; }
        // rename in cfg.weapons
        cfg.weapons[newId] = Object.assign({}, cfg.weapons[oldId] || {});
        delete cfg.weapons[oldId];
        // offer to update character inventories
        try {
          let ref = 0;
          for (const [nm, ch] of Object.entries(cfg.characters || {})) {
            const inv = (ch||{}).inventory || {};
            if (inv[oldId] != null) ref++;
          }
          if (ref > 0 && confirm(`检测到有 ${ref} 个角色背包包含 ${oldId}，是否一并更新为 ${newId}？`)) {
            for (const [nm, ch] of Object.entries(cfg.characters || {})) {
              const inv = (ch||{}).inventory || {};
              if (inv[oldId] != null) {
                const count = inv[oldId] || 0;
                inv[newId] = (inv[newId] || 0) + count;
                delete inv[oldId];
              }
            }
          }
        } catch(e){ throw e }
        markDirty('weapons');
        // re-render to reflect sorted order and ids
        renderWeaponsForm(cfg.weapons);
      });
      // label
      const tdLabel = document.createElement('td');
      const inLabel = document.createElement('input'); inLabel.type='text'; inLabel.value=(item.label||''); inLabel.addEventListener('input',()=>{ (cfg.weapons[id]||(cfg.weapons[id]={})).label=inLabel.value; markDirty('weapons'); }); tdLabel.appendChild(inLabel);
      // reach
      const tdReach = document.createElement('td');
      const inReach = document.createElement('input'); inReach.type='number'; inReach.value = (item.reach_steps!=null? item.reach_steps:1); inReach.addEventListener('input',()=>{ (cfg.weapons[id]||(cfg.weapons[id]={})).reach_steps = parseInt(inReach.value||'1',10); markDirty('weapons'); }); tdReach.appendChild(inReach);
      // hit skill
      const tdHit = document.createElement('td');
      const selHit = document.createElement('select'); weaponSkillList.forEach(s=>{ const opt=document.createElement('option'); opt.value=s; opt.textContent=s; selHit.appendChild(opt); }); selHit.value=String(item.skill||'Fighting_Blade'); selHit.addEventListener('change',()=>{ (cfg.weapons[id]||(cfg.weapons[id]={})).skill = selHit.value; markDirty('weapons'); }); tdHit.appendChild(selHit);
      // defense skill
      const tdDef = document.createElement('td');
      const selDef = document.createElement('select'); defenseSkillList.forEach(s=>{ const opt=document.createElement('option'); opt.value=s; opt.textContent=s; selDef.appendChild(opt); }); selDef.value=String(item.defense_skill||'Dodge'); selDef.addEventListener('change',()=>{ (cfg.weapons[id]||(cfg.weapons[id]={})).defense_skill = selDef.value; markDirty('weapons'); }); tdDef.appendChild(selDef);
      // damage formula (NdM[+/-K])
      const tdDmg = document.createElement('td');
      const inDmg = document.createElement('input');
      inDmg.type='text';
      inDmg.placeholder='例如 1d6（不含属性加成）';
      // backend uses `damage` field; prefer it if present
      inDmg.value = (item.damage || '');
      const dmgValid = (s)=>{ return /^\s*\d*d\d+(?:[+-]\d+)?\s*$/i.test(String(s||'')); };
      const reflectDmgValid = ()=>{ try { inDmg.style.borderColor = inDmg.value && !dmgValid(inDmg.value) ? '#e11d48' : ''; } catch(e){} };
      inDmg.addEventListener('input',()=>{ (cfg.weapons[id]||(cfg.weapons[id]={})).damage = inDmg.value; reflectDmgValid(); markDirty('weapons'); });
      reflectDmgValid();
      tdDmg.appendChild(inDmg);
      // damage type
      const tdDmgType = document.createElement('td');
      const selType = document.createElement('select'); dmgTypes.forEach(t=>{ const opt=document.createElement('option'); opt.value=t; opt.textContent=(t==='arts'?'术伤':'物理'); selType.appendChild(opt); }); selType.value=String(item.damage_type||'physical'); selType.addEventListener('change',()=>{ (cfg.weapons[id]||(cfg.weapons[id]={})).damage_type = selType.value; markDirty('weapons'); }); tdDmgType.appendChild(selType);
      // ops
      const tdOps = document.createElement('td');
      const btnDel = document.createElement('button'); btnDel.className='sm'; btnDel.textContent='删除'; btnDel.onclick=()=>{ delete cfg.weapons[id]; renderWeaponsForm(cfg.weapons); markDirty('weapons'); };
      tdOps.appendChild(btnDel);
      tr.appendChild(tdId); tr.appendChild(tdLabel); tr.appendChild(tdReach); tr.appendChild(tdHit); tr.appendChild(tdDef); tr.appendChild(tdDmg); tr.appendChild(tdDmgType); tr.appendChild(tdOps);
      tbody.appendChild(tr);
    });
    // refresh characters inventory add-select (if visible)
    try { if (chActiveName) fillCharForm(chActiveName); } catch(e){ throw e }
  }

  function renderCharactersForm(data) {
    original.characters = JSON.parse(JSON.stringify(data || {}));
    chRelations = JSON.parse(JSON.stringify((data||{}).relations || {}));
    // exclude relations from editable set
    const map = {};
    Object.entries(data || {}).forEach(([k, v]) => { if (k !== 'relations') map[k] = v; });
    cfg.characters = map;
    dirty.characters = false;
    const names = Object.keys(cfg.characters || {});
    chActiveName = names[0] || '';
    renderCharList(names);
    if (chActiveName) fillCharForm(chActiveName);
  }

  async function loadAllConfigs() {
    // Load latest configs and state snapshot for helpers
    const [stRes, wpRes, chRes, stState, artsRes, optRes] = await Promise.all([
      fetch('/api/config/story').then(r=>r.json()).catch(()=>({data:{}})),
      fetch('/api/config/weapons').then(r=>r.json()).catch(()=>({data:{}})),
      fetch('/api/config/characters').then(r=>r.json()).catch(()=>({data:{}})),
      fetch('/api/state').then(r=>r.json()).catch(()=>({state:null})),
      fetch('/api/config/arts').then(r=>r.json()).catch(()=>({data:{}})),
      fetch('/api/options').then(r=>r.json()).catch(()=>({})),
    ]);
    window.RR = window.RR || {}; window.RR.options = optRes && optRes.ok ? optRes : (window.RR.options || {});
    lastState = (stState||{}).state || lastState || {};
    renderCharactersForm((chRes||{}).data||{});
    // Story: support container format
    storyContainerRaw = deepClone((stRes||{}).data || {});
    storyContainer = normalizeStoryContainer(storyContainerRaw);
    // Prefer server-selected story if available; otherwise the first id
    let ids = Object.keys(storyContainer.stories||{});
    let serverSelected = '';
    try { const si = await fetch('/api/stories').then(r=>r.json()); serverSelected = (si && si.selected) || ''; } catch(e){ throw e }
    selectedStoryId = serverSelected || selectedStoryId || ids[0] || '';
    updateStorySelectUI();
    // Render the selected story into the existing form
    original.story = deepClone(storyContainer.stories[selectedStoryId] || {});
    cfg.story = deepClone(storyContainer.stories[selectedStoryId] || {});
    dirty.story = false;
    renderStoryForm(cfg.story, lastState);
    // Weapons unchanged
    renderWeaponsForm((wpRes||{}).data||{});
    // Arts
    renderArtsForm((artsRes||{}).data||{});
  }

  function storyCollect() {
    // update scene fields from inputs
    const s = (cfg.story.scene = cfg.story.scene || {});
    s.name = (stSceneName.value || '').trim();
    s.time = (stSceneTime.value || '').trim();
    s.weather = (stSceneWeather.value || '').trim();
    s.description = (stSceneDesc.value || '').trim();
    // lists already bound; ensure arrays exist
    s.details = Array.isArray(s.details) ? s.details : [];
    s.objectives = Array.isArray(s.objectives) ? s.objectives : [];
    // positions bound via inputs; ensure ints
    const pos = {};
    for (const [k, v] of Object.entries(cfg.story.initial_positions || {})) {
      try { pos[String(k)] = [parseInt(v[0],10)||0, parseInt(v[1],10)||0]; } catch { pos[String(k)] = [0,0]; }
    }
    const out = JSON.parse(JSON.stringify(original.story || {}));
    out.scene = JSON.parse(JSON.stringify(s));
    out.initial_positions = pos;
    if (cfg.story.scenes) out.scenes = JSON.parse(JSON.stringify(cfg.story.scenes));
    if (cfg.story.entrances) out.entrances = JSON.parse(JSON.stringify(cfg.story.entrances));
    if (cfg.story.initial_scenes) out.initial_scenes = JSON.parse(JSON.stringify(cfg.story.initial_scenes));
    if (cfg.story.scene_positions) out.scene_positions = JSON.parse(JSON.stringify(cfg.story.scene_positions));
    if (Array.isArray(cfg.story.endings)) out.endings = JSON.parse(JSON.stringify(cfg.story.endings));
    if (Array.isArray(cfg.story.events)) out.events = JSON.parse(JSON.stringify(cfg.story.events));
    return out;
  }

  function weaponsCollect() {
    const out = {};
    // preserve unknown keys per weapon by merging original, but drop legacy proficient flag
    const orig = original.weapons || {};
    for (const id of Object.keys(cfg.weapons || {})) {
      const src = cfg.weapons[id] || {};
      const base = Object.assign({}, orig[id] || {});
      base.label = (src.label || '').trim();
      base.reach_steps = parseInt(src.reach_steps != null ? src.reach_steps : 1, 10) || 1;
      // Persist damage into standard backend field `damage`
      if (src.damage != null) base.damage = String(src.damage || '').trim();
      // Skills & damage type from UI (with defaults)
      base.skill = String(src.skill || base.skill || 'Fighting_Blade');
      base.defense_skill = String(src.defense_skill || base.defense_skill || 'Dodge');
      base.damage_type = String(src.damage_type || base.damage_type || 'physical');
      // no proficient flag anymore
      if ('proficient_default' in base) delete base.proficient_default;
      // drop any accidental UI-only keys to satisfy server validation
      if ('ability' in base) delete base.ability;
      if ('damage_expr' in base) delete base.damage_expr;
      out[id] = base;
    }
    return out;
  }

  function charactersCollect() {
    // Merge edited characters with preserved relations
    const out = {};
    const orig = original.characters || {};
    for (const [name, entry] of Object.entries(cfg.characters || {})) {
      const src = JSON.parse(JSON.stringify(entry || {}));
      const dst = {};
      dst.type = src.type || 'npc';
      dst.persona = src.persona || '';
      dst.appearance = src.appearance || '';
      // quotes normalize
      dst.quotes = Array.isArray(src.quotes) ? src.quotes : (src.quotes ? [String(src.quotes)] : []);
      // inventory as-is
      dst.inventory = Object.assign({}, src.inventory || {});
      // coc: overwrite main blocks, preserve extras
      const oCoc = (orig[name] && orig[name].coc) ? JSON.parse(JSON.stringify(orig[name].coc)) : {};
      const nCoc = (src.coc && typeof src.coc==='object') ? JSON.parse(JSON.stringify(src.coc)) : {};
      const ch = Object.assign({}, (nCoc.characteristics||{}));
      const skills = Object.assign({}, (nCoc.skills||{}));
      const terra = Object.assign({}, (nCoc.terra||{}));
      const extras = {};
      Object.keys(oCoc||{}).forEach(k => { if (!(k in {characteristics:1, skills:1, terra:1})) extras[k] = oCoc[k]; });
      dst.coc = Object.assign({}, extras, { characteristics: ch, skills, terra });
      out[name] = dst;
    }
    out.relations = JSON.parse(JSON.stringify(chRelations || {}));
    return out;
  }

  async function saveActive(restart) {
    try {
      let name = activeTab;
      // timeline edits are stored in story container; write to story endpoint
      const endpointName = (name === 'timeline') ? 'story' : name;
      let data = null;
      if (name === 'story' || name === 'timeline') {
        // commit local edits into container; never write legacy active_id
        commitLocalStoryEdits();
        let merged = {};
        if (storyContainerRaw && storyContainerRaw.stories) {
          merged = deepClone(storyContainerRaw);
          merged.stories = deepClone(storyContainer.stories || {});
          if ('active_id' in merged) delete merged.active_id;
        } else {
          merged = { stories: deepClone(storyContainer.stories || {}) };
        }
        data = merged;
      }
      else if (name === 'weapons') data = weaponsCollect();
      else if (name === 'arts') data = artsCollect();
      else if (name === 'characters') data = charactersCollect();
      const res = await fetch(`/api/config/${endpointName}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || '保存失败');
      }
      dirty[name] = false;
      if (restart) {
        // mimic btnRestart behaviour
        btnStart.disabled = true; btnStop.disabled = true; btnRestart.disabled = true;
        try {
          const sid = getSelectedStoryId();
          const r2 = await fetch('/api/restart', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ story_id: sid || undefined }) });
          if (!r2.ok) throw new Error(await r2.text());
          storyEl.innerHTML = '';
          hudEl.innerHTML = '';
          playerHint.textContent = '';
          txtPlayer.value = '';
          lastSeq = 0; waitingActor = ''; btnSend.disabled = true;
          setStatus('restarting...');
          try {
            const st = await (await fetch('/api/state')).json();
            if (st && st.state) renderHUD(st.state);
            running = !!(st && st.running);
          } catch(e){ throw e }
          if (!ws) connectWS();
          updateButtons();
        } catch (e) {
          alert('restart failed: ' + (e.message || e));
        } finally {
          btnRestart.disabled = false;
        }
      } else {
        alert('已保存');
      }
    } catch (e) {
      alert('保存失败: ' + (e.message || e));
    }
  }

  async function exportAll() {
    const names = ['story','weapons','arts','characters'];
    // If any section is dirty, confirm saving all before export
    const needSave = names.some(n => !!dirty[n]);
    if (needSave) {
      const ok = confirm('有未保存的更改，是否先保存全部再导出？');
      if (!ok) return;
      const prev = activeTab;
      try {
        for (const n of names) {
          if (dirty[n]) {
            activeTab = n; // saveActive reads activeTab to decide endpoint
            await saveActive(false);
          }
        }
      } finally {
        activeTab = prev;
      }
    }
    // Trigger four downloads from server endpoints (no front-end JSON involved)
    try {
      for (const n of names) {
        const url = withApiBase(`/api/export/${n}`);
        const a = document.createElement('a'); a.href = url; a.target = '_blank'; a.rel = 'noopener';
        document.body.appendChild(a); a.click(); a.remove();
      }
    } catch (e) {
      alert('导出失败: ' + (e.message || e));
    }
  }

  // Wire events
  if (btnSettings) btnSettings.onclick = async () => { setActiveTab('story'); drawerOpen(); await loadAllConfigs(); };
  if (btnCfgClose) btnCfgClose.onclick = () => drawerClose(false);
  if (btnCfgSave) btnCfgSave.onclick = () => saveActive(false);
  if (btnCfgSaveRestart) btnCfgSaveRestart.onclick = () => saveActive(true);
  if (btnCfgReset) btnCfgReset.onclick = async () => { await loadAllConfigs(); alert('已重置为服务器版本'); };
  if (btnCfgExport) btnCfgExport.onclick = () => exportAll();
  for (const b of tabBtns) {
    b.onclick = () => setActiveTab(b.getAttribute('data-tab'));
  }

  // ===== Arts form =====
  function renderArtsForm(data) {
    // Deep clone for editing
    original.arts = JSON.parse(JSON.stringify(data || {}));
    cfg.arts = JSON.parse(JSON.stringify(data || {}));
    dirty.arts = false;
    if (!artsTable) return;
    const tbody = artsTable.querySelector('tbody');
    const abilities = ['STR','DEX','CON','INT','POW'];
    const rrOptA = (window.RR && window.RR.options) ? window.RR.options : {};
    const skillList = Array.isArray(rrOptA.art_cast_skills) ? rrOptA.art_cast_skills : ['Arts_Control','Arts_Offense','Perception','Dodge','FirstAid','Firearms_Handgun','Firearms_Rifle_Crossbow'];
    const fill = () => {
      tbody.innerHTML = '';
      const rrOpt = (window.RR && window.RR.options) ? window.RR.options : {};
      const ctrlDefault = ['silenced','rooted','immobilized','restrained','stunned','paralyzed','sleep','frozen'];
      const ctrlOptions = [''].concat(Array.isArray(rrOpt.control_effects)? rrOpt.control_effects : ctrlDefault);
      const tagOptions = Array.isArray(rrOpt.art_tags) ? rrOpt.art_tags : ['no-guard-intercept','line-of-sight'];
      const dmgTypes = Array.isArray(rrOpt.art_damage_types) ? rrOpt.art_damage_types : ['arts','physical'];
      Object.entries(cfg.arts || {}).forEach(([id, a]) => {
        const tr = document.createElement('tr');
        const td = (el) => { const td=document.createElement('td'); td.appendChild(el); return td; };
        // ID (readonly)
        const inId = document.createElement('input'); inId.type='text'; inId.value=id; inId.disabled=true;
        // label
        const inLabel = document.createElement('input'); inLabel.type='text'; inLabel.value=(a.label||''); inLabel.oninput=()=>{ (cfg.arts[id]||(cfg.arts[id]={})).label=inLabel.value; markDirty('arts'); };
        // cast_skill
        const selCast = document.createElement('select'); skillList.forEach(s=>{ const o=document.createElement('option'); o.value=s; o.textContent=s; selCast.appendChild(o); }); selCast.value=String(a.cast_skill||'Arts_Control'); selCast.onchange=()=>{ (cfg.arts[id]||(cfg.arts[id]={})).cast_skill=selCast.value; markDirty('arts'); };
        // resist
        const selRes = document.createElement('select'); (Array.isArray(rrOptA.art_resist_skills)? rrOptA.art_resist_skills : ['Arts_Resist','Dodge']).forEach(s=>{ const o=document.createElement('option'); o.value=s; o.textContent=s; selRes.appendChild(o); }); selRes.value=String(a.resist||'Arts_Resist'); selRes.onchange=()=>{ (cfg.arts[id]||(cfg.arts[id]={})).resist=selRes.value; markDirty('arts'); };
        // range_steps
        const inRange = document.createElement('input'); inRange.type='number'; inRange.value=(a.range_steps!=null? a.range_steps:6); inRange.oninput=()=>{ const v=parseInt(inRange.value||'6',10)||6; (cfg.arts[id]||(cfg.arts[id]={})).range_steps=v; inRange.style.borderColor = (v<=0 ? '#e11d48' : ''); markDirty('arts'); };
        // damage_type select
        const selDType = document.createElement('select'); dmgTypes.forEach(t=>{ const o=document.createElement('option'); o.value=t; o.textContent=(t==='arts'?'术伤':'物理'); selDType.appendChild(o); }); selDType.value=String(a.damage_type||'arts'); selDType.onchange=()=>{ (cfg.arts[id]||(cfg.arts[id]={})).damage_type=selDType.value; markDirty('arts'); };
        // damage
        const inDmg = document.createElement('input'); inDmg.type='text'; inDmg.value=(a.damage||''); inDmg.placeholder='如 1d6+1d4'; inDmg.oninput=()=>{ const m=(cfg.arts[id]||(cfg.arts[id]={})); if (inDmg.value.trim()) m.damage=inDmg.value.trim(); else delete m.damage; markDirty('arts'); };
        // control.effect (select)
        const selCtl = document.createElement('select');
        ctrlOptions.forEach(v => { const o=document.createElement('option'); o.value=v; o.textContent=(v? v : '（无）'); selCtl.appendChild(o); });
        selCtl.value=String(((a.control||{}).effect||''));
        selCtl.onchange=()=>{ const m=(cfg.arts[id]||(cfg.arts[id]={})); m.control=m.control||{}; const v=selCtl.value||''; if (v) { m.control.effect=v; } else { delete m.control.effect; if (m.control && !m.control.duration) delete m.control; } markDirty('arts'); };
        // control.duration
        const inDur = document.createElement('input'); inDur.type='text'; inDur.value=((a.control||{}).duration||''); inDur.placeholder='1 或 表达式'; inDur.oninput=()=>{ const m=(cfg.arts[id]||(cfg.arts[id]={})); m.control=m.control||{}; m.control.duration=inDur.value.trim(); if (!m.control.duration) delete m.control.duration; const ok = /^\s*[0-9+\-*/()\s]*\s*$/.test(inDur.value||''); inDur.style.borderColor = ok ? '' : '#e11d48'; markDirty('arts'); };
        // mp (cost/variable/max)
        const inCost = document.createElement('input'); inCost.type='number'; inCost.value=((a.mp||{}).cost!=null? a.mp.cost:0); inCost.oninput=()=>{ const m=(cfg.arts[id]||(cfg.arts[id]={})); m.mp=m.mp||{}; m.mp.cost=parseInt(inCost.value||'0',10)||0; markDirty('arts'); };
        const inVar = document.createElement('input'); inVar.type='checkbox'; inVar.checked=!!((a.mp||{}).variable); inVar.onchange=()=>{ const m=(cfg.arts[id]||(cfg.arts[id]={})); m.mp=m.mp||{}; m.mp.variable=!!inVar.checked; markDirty('arts'); };
        const inMax = document.createElement('input'); inMax.type='number'; inMax.value=((a.mp||{}).max!=null? a.mp.max:0); inMax.oninput=()=>{ const m=(cfg.arts[id]||(cfg.arts[id]={})); m.mp=m.mp||{}; m.mp.max=parseInt(inMax.value||'0',10)||0; markDirty('arts'); };
        const mpWrap = document.createElement('div'); mpWrap.className='row'; mpWrap.appendChild(inCost); const lbl=document.createElement('label'); lbl.textContent=' 可变'; lbl.style.marginLeft='4px'; const wrapVar=document.createElement('span'); wrapVar.appendChild(inVar); wrapVar.appendChild(lbl); mpWrap.appendChild(wrapVar); mpWrap.appendChild(inMax);
        // tags (checkboxes for allowed options; preserve unknown tags)
        const tdTagsWrap = document.createElement('div');
        const curTags = Array.isArray(a.tags)? a.tags.slice(): [];
        const unknown = curTags.filter(t => !tagOptions.includes(String(t)));
        const rebuildTags = () => {
          const selected = Array.from(tdTagsWrap.querySelectorAll('input[type="checkbox"]')).filter(x => x.checked).map(x => x.value);
          const m = (cfg.arts[id]||(cfg.arts[id]={}));
          m.tags = selected.concat(unknown);
          markDirty('arts');
        };
        tagOptions.forEach(t => {
          const lab = document.createElement('label'); lab.style.marginRight='6px';
          const cb = document.createElement('input'); cb.type='checkbox'; cb.value=t; cb.checked=curTags.includes(t);
          cb.addEventListener('change', rebuildTags);
          lab.appendChild(cb); lab.appendChild(document.createTextNode(' '+t));
          tdTagsWrap.appendChild(lab);
        });
        if (unknown.length) {
          const span = document.createElement('span'); span.className='dim'; span.textContent = ' 其余: '+unknown.join(','); tdTagsWrap.appendChild(span);
        }
        // desc
        const inDesc = document.createElement('input'); inDesc.type='text'; inDesc.value=(a.desc||''); inDesc.oninput=()=>{ (cfg.arts[id]||(cfg.arts[id]={})).desc=inDesc.value; markDirty('arts'); };
        // ops
        const btnDel = document.createElement('button'); btnDel.className='sm'; btnDel.textContent='删除'; btnDel.onclick=()=>{ delete cfg.arts[id]; fill(); markDirty('arts'); };
        tr.appendChild(td(inId)); tr.appendChild(td(inLabel)); tr.appendChild(td(selCast)); tr.appendChild(td(selRes)); tr.appendChild(td(inRange)); tr.appendChild(td(selDType)); tr.appendChild(td(inDmg)); tr.appendChild(td(selCtl)); tr.appendChild(td(inDur)); tr.appendChild(td(mpWrap)); tr.appendChild(td(tdTagsWrap)); tr.appendChild(td(inDesc)); tr.appendChild(td(btnDel));
        tbody.appendChild(tr);
      });
    };
    fill();
    if (btnAddArt) btnAddArt.onclick = () => {
      let id = String(prompt('输入术式 ID（可留空自动生成）')||'').trim();
      if (!id) { const base='art_'; let i=1; id=base+i; while ((cfg.arts||{})[id]) { i++; id=base+i; } }
      if ((cfg.arts||{})[id]) { alert('已存在同名 ID'); return; }
      (cfg.arts||(cfg.arts={}))[id] = { label:'', cast_skill:'Arts_Control', resist:'Arts_Resist', range_steps:6, mp:{ cost:0, variable:false, max:0 }, tags:[] };
      fill(); markDirty('arts');
    };
  }

  function artsCollect() {
    const out = {};
    for (const id of Object.keys(cfg.arts || {})) {
      out[id] = JSON.parse(JSON.stringify(cfg.arts[id] || {}));
      // 清理空字段
      if (out[id].damage === '') delete out[id].damage;
      if (out[id].desc === '') delete out[id].desc;
      if (out[id].control && !out[id].control.effect && !out[id].control.duration) delete out[id].control;
      if (out[id].mp && out[id].mp.max==null && out[id].mp.variable==null && out[id].mp.cost==null) delete out[id].mp;
    }
    return out;
  }

  // ===== Timeline form =====
  function renderTimelineForm(list) {
    if (!tlTable) return;
    cfg.story.events = Array.isArray(list) ? JSON.parse(JSON.stringify(list)) : [];
    const tbody = tlTable.querySelector('tbody');
    const fill = () => {
      tbody.innerHTML = '';
      cfg.story.events.forEach((ev, idx) => {
        const tr = document.createElement('tr');
        const td = (el) => { const td=document.createElement('td'); td.appendChild(el); return td; };
        const inName = document.createElement('input'); inName.type='text'; inName.value=String(ev.name||''); inName.oninput=()=>{ cfg.story.events[idx].name = inName.value; markDirty('story'); };
        const inTime = document.createElement('input'); inTime.type='text'; inTime.placeholder='08:30'; inTime.value=String(ev.time || ev.time_str || ''); inTime.oninput=()=>{ cfg.story.events[idx].time = inTime.value.trim(); delete cfg.story.events[idx].at; markDirty('story'); };
        const inNote = document.createElement('input'); inNote.type='text'; inNote.value=String(ev.note||''); inNote.oninput=()=>{ cfg.story.events[idx].note = inNote.value; markDirty('story'); };
        const taEff = document.createElement('textarea'); taEff.rows=3; try{ taEff.value = ev.effects? JSON.stringify(ev.effects, null, 2) : ''; } catch { taEff.value=''; }
        taEff.oninput=()=>{ try { const arr = taEff.value.trim()? JSON.parse(taEff.value): []; taEff.style.borderColor=''; cfg.story.events[idx].effects = arr; markDirty('story'); } catch(e){ taEff.style.borderColor='#e11d48'; } };
        const btnDel = document.createElement('button'); btnDel.className='sm'; btnDel.textContent='删除'; btnDel.onclick=()=>{ cfg.story.events.splice(idx,1); fill(); markDirty('story'); };
        tr.appendChild(td(inName)); tr.appendChild(td(inTime)); tr.appendChild(td(inNote)); tr.appendChild(td(taEff)); tr.appendChild(td(btnDel));
        tbody.appendChild(tr);
      });
    };
    fill();
    if (btnAddEvent) btnAddEvent.onclick = () => { cfg.story.events.push({ name:'', time:'', note:'', effects:[] }); fill(); markDirty('story'); };
  }

  // ======== When Builder (完整树编辑器) ========
  let _whenDraft = null;          // internal tree being edited
  let _whenEditEndingIdx = -1;    // which ending we edit

  function _toInternalWhen(node) {
    // Convert engine shape -> internal { _type: 'any'|'all'|'not', children: [...] } or leaf { kind, ... }
    if (!node || typeof node !== 'object') return null;
    const keys = Object.keys(node);
    if (keys.length === 1 && (keys[0] === 'any' || keys[0] === 'all' || keys[0] === 'not')) {
      const k = keys[0];
      const raw = node[k];
      const children = Array.isArray(raw) ? raw.map(_toInternalWhen).filter(Boolean) : (raw ? [_toInternalWhen(raw)] : []);
      return { _type: k, children };
    }
    // leaf conditions: pass-through but tag with kind
    const leafKinds = ['objectives','actors_alive','actors_dead','hostiles_present','marks_contains','location_is','tension_at_least','tension_at_most','participants_alive_at_least','participants_alive_at_most','time_before','time_at_least'];
    for (const k of leafKinds) {
      if (k in node) return { kind: k, value: JSON.parse(JSON.stringify(node[k])) };
    }
    // direct leaf with fields (e.g., { time_before: '08:30' }) already handled above
    // unknown -> null
    return null;
  }

  function _toEngineWhen(internal) {
    if (!internal || typeof internal !== 'object') return null;
    if (internal._type) {
      const kids = Array.isArray(internal.children) ? internal.children.map(_toEngineWhen).filter(Boolean) : [];
      if (internal._type === 'not') {
        return { not: (kids[0] || null) };
      }
      return { [internal._type]: kids };
    }
    if (internal.kind) {
      return { [internal.kind]: JSON.parse(JSON.stringify(internal.value)) };
    }
    return null;
  }

  function openWhenEditor(endingIdx) {
    if (!whenModal || !whenTreeEl) return;
    _whenEditEndingIdx = endingIdx;
    const en = (cfg.story.endings || [])[endingIdx] || {};
    const w = en.when || { any: [] };
    _whenDraft = _toInternalWhen(w) || { _type: 'any', children: [] };
    whenModal.classList.remove('hidden');
    whenModal.setAttribute('aria-hidden', 'false');
    renderWhenTree();
  }
  function closeWhenEditor() {
    if (!whenModal) return;
    whenModal.classList.add('hidden');
    whenModal.setAttribute('aria-hidden', 'true');
    _whenDraft = null; _whenEditEndingIdx = -1;
  }

  function _arrayInput(value, placeholder, onChange) {
    const wrap = document.createElement('div');
    const inp = document.createElement('input');
    inp.type = 'text'; inp.placeholder = placeholder || 'a,b,c';
    inp.value = Array.isArray(value) ? value.join(',') : (value || '');
    inp.oninput = () => {
      const v = inp.value.trim();
      onChange(v ? v.split(/\s*,\s*/).filter(Boolean) : []);
    };
    wrap.appendChild(inp); return wrap;
  }

  function _namedSelect(options, value, onChange) {
    const sel = document.createElement('select');
    const ph = document.createElement('option'); ph.value=''; ph.textContent='请选择'; sel.appendChild(ph);
    options.forEach(v=>{ const o=document.createElement('option'); o.value=v; o.textContent=v; sel.appendChild(o); });
    sel.value = (Array.isArray(value)? value[0]: value) || '';
    sel.onchange = () => onChange(sel.value);
    return sel;
  }

  function renderWhenTree() {
    if (!whenTreeEl) return;
    whenTreeEl.innerHTML = '';
    const root = _whenDraft || { _type:'any', children: [] };
    whenTreeEl.appendChild(renderWhenNode(root, []));
  }

  function renderWhenNode(node, path) {
    const wrap = document.createElement('div');
    wrap.className = 'when-node';
    const head = document.createElement('div'); head.className='head'; wrap.appendChild(head);
    const actions = document.createElement('div'); actions.className='when-actions'; wrap.appendChild(actions);

    const suggest = {
      actors: Object.keys(cfg.characters || {}),
      objectives: ((cfg.story||{}).scene||{}).objectives || [],
      scenes: Object.keys((cfg.story||{}).scenes || {}),
    };

    // Helper to locate node by path
    const getNode = (p) => p.reduce((acc, i) => acc.children[i], _whenDraft);
    const setNode = (p, val) => {
      if (p.length === 0) { _whenDraft = val; return; }
      const parent = p.slice(0,-1).reduce((acc, i) => acc.children[i], _whenDraft);
      parent.children[p[p.length-1]] = val;
    };
    const removeNode = (p) => {
      if (p.length === 0) return; // do not remove root
      const parent = p.slice(0,-1).reduce((acc, i) => acc.children[i], _whenDraft);
      parent.children.splice(p[p.length-1], 1);
    };

    if (node._type) {
      // Group node
      const lab = document.createElement('span'); lab.textContent = '组：'; head.appendChild(lab);
      const sel = document.createElement('select'); sel.className='fit-select'; ['any','all','not'].forEach(t=>{ const o=document.createElement('option'); o.value=t; o.textContent=t; sel.appendChild(o); }); sel.value=node._type; sel.onchange=()=>{ node._type = sel.value; renderWhenTree(); }; head.appendChild(sel);
      if (path.length > 0) { const del=document.createElement('button'); del.className='sm'; del.textContent='删除本组'; del.onclick=()=>{ removeNode(path); renderWhenTree(); }; head.appendChild(del); }
      const kids = document.createElement('div'); kids.className='when-children'; wrap.appendChild(kids);
      node.children = Array.isArray(node.children) ? node.children : [];
      node.children.forEach((ch, idx) => { kids.appendChild(renderWhenNode(ch, path.concat(idx))); });
      // add child controls
      const addSel = document.createElement('select'); addSel.className='fit-select';
      ['any','all','not','objectives','time_before','time_at_least','actors_alive','actors_dead','participants_alive_at_least','participants_alive_at_most','hostiles_present','marks_contains','tension_at_least','tension_at_most','location_is'].forEach(k=>{ const o=document.createElement('option'); o.value=k; o.textContent=k; addSel.appendChild(o); });
      const btnAdd = document.createElement('button'); btnAdd.className='sm'; btnAdd.textContent='添加子条件'; btnAdd.onclick=()=>{
        const k = addSel.value;
        if (k==='any' || k==='all' || k==='not') node.children.push({ _type: k, children: [] });
        else node.children.push(defaultLeaf(k));
        renderWhenTree();
      };
      actions.appendChild(addSel); actions.appendChild(btnAdd);
      return wrap;
    }
    // Leaf nodes UI
    const kind = node.kind || 'objectives';
    const selK = document.createElement('select'); selK.className='fit-select';
    ['objectives','time_before','time_at_least','actors_alive','actors_dead','participants_alive_at_least','participants_alive_at_most','hostiles_present','marks_contains','tension_at_least','tension_at_most','location_is'].forEach(k=>{ const o=document.createElement('option'); o.value=k; o.textContent=k; selK.appendChild(o); });
    selK.value = kind;
    selK.onchange = () => {
      const repl = defaultLeaf(selK.value);
      setNode(path, repl); renderWhenTree();
    };
    head.appendChild(selK);
    if (path.length > 0) { const del=document.createElement('button'); del.className='sm'; del.textContent='删除'; del.onclick=()=>{ removeNode(path); renderWhenTree(); }; head.appendChild(del); }

    const form = document.createElement('div'); form.className='when-children'; wrap.appendChild(form);
    const v = node.value || {};

    const label = (t)=>{ const l=document.createElement('label'); l.className='lbl'; l.textContent=t; form.appendChild(l); };
    const addRow = (el)=>{ form.appendChild(el); };

    if (kind === 'objectives') {
      label('目标名称（逗号分隔）'); addRow(_arrayInput(v.names || suggest.objectives, '目标1,目标2', names=>{ node.value = Object.assign({}, v, { names }); }));
      label('要求'); const selReq=document.createElement('select'); selReq.className='fit-select'; ['all','any'].forEach(x=>{ const o=document.createElement('option'); o.value=x; o.textContent=x; selReq.appendChild(o); }); selReq.value = (v.require||'all'); selReq.onchange=()=>{ node.value = Object.assign({}, node.value, { require: selReq.value }); }; addRow(selReq);
      label('状态'); const selSt=document.createElement('select'); selSt.className='fit-select'; ['done','blocked','any'].forEach(x=>{ const o=document.createElement('option'); o.value=x; o.textContent=x; selSt.appendChild(o); }); selSt.value=(v.status||'done'); selSt.onchange=()=>{ node.value = Object.assign({}, node.value, { status: selSt.value }); }; addRow(selSt);
    } else if (kind === 'time_before' || kind === 'time_at_least') {
      label('时间（HH:MM 或 分钟）'); const inp=document.createElement('input'); inp.type='text'; inp.placeholder='08:30'; inp.value=String(v||''); inp.oninput=()=>{ node.value = inp.value; }; addRow(inp);
    } else if (kind === 'actors_alive' || kind === 'actors_dead') {
      label('角色（逗号分隔）'); addRow(_arrayInput((v.names||suggest.actors), 'Amiya,Doctor', names=>{ node.value = Object.assign({}, node.value, { names }); }));
      label('要求'); const selReq=document.createElement('select'); selReq.className='fit-select'; ['all','any'].forEach(x=>{ const o=document.createElement('option'); o.value=x; o.textContent=x; selReq.appendChild(o); }); selReq.value=(v.require||'all'); selReq.onchange=()=>{ node.value = Object.assign({}, node.value, { require: selReq.value }); }; addRow(selReq);
    } else if (kind === 'participants_alive_at_least' || kind === 'participants_alive_at_most') {
      label('人数'); const inp=document.createElement('input'); inp.type='number'; inp.value=String(v||0); inp.oninput=()=>{ node.value = parseInt(inp.value||'0',10)||0; }; addRow(inp);
    } else if (kind === 'hostiles_present') {
      label('是否存在敌对'); const sel=document.createElement('select'); sel.className='fit-select'; [{v:true,t:'是'}, {v:false,t:'否'}].forEach(o=>{ const op=document.createElement('option'); op.value=String(o.v); op.textContent=o.t; sel.appendChild(op); }); sel.value=String((typeof v==='object'? v.value : v) ?? true);
      sel.onchange=()=>{ const cur = (v && typeof v==='object')? v: { value: true }; const want=(sel.value==='true'); node.value = Object.assign({}, cur, { value: want }); }; addRow(sel);
      label('阈值（可选）'); const thr=document.createElement('input'); thr.type='number'; thr.placeholder='-10'; thr.value=String((v && v.threshold!=null) ? v.threshold : ''); thr.oninput=()=>{ const val=thr.value.trim(); const cur=(v&&typeof v==='object')? v: { value: (sel.value==='true') }; if (val==='') { delete cur.threshold; } else { cur.threshold=parseInt(val||'0',10)||0; } node.value = cur; }; addRow(thr);
    } else if (kind === 'marks_contains') {
      label('标记（逗号分隔）'); addRow(_arrayInput(v||[], 'mark1,mark2', arr=>{ node.value = arr; }));
    } else if (kind === 'tension_at_least' || kind === 'tension_at_most') {
      label('紧张度'); const inp=document.createElement('input'); inp.type='number'; inp.value=String(v||0); inp.oninput=()=>{ node.value = parseInt(inp.value||'0',10)||0; }; addRow(inp);
    } else if (kind === 'location_is') {
      label('地点'); addRow(_namedSelect(suggest.scenes, v, vv=>{ node.value = vv; }));
    }

    return wrap;
  }

  function defaultLeaf(kind) {
    switch(kind){
      case 'objectives': return { kind, value: { names: (((cfg.story||{}).scene||{}).objectives||[]), require:'all', status:'done' } };
      case 'time_before': return { kind, value: '08:30' };
      case 'time_at_least': return { kind, value: '08:30' };
      case 'actors_alive': return { kind, value: { names: Object.keys(cfg.characters||{}), require: 'all' } };
      case 'actors_dead': return { kind, value: { names: [], require: 'any' } };
      case 'participants_alive_at_least': return { kind, value: 1 };
      case 'participants_alive_at_most': return { kind, value: 0 };
      case 'hostiles_present': return { kind, value: { value: true, threshold: -10 } };
      case 'marks_contains': return { kind, value: [] };
      case 'tension_at_least': return { kind, value: 1 };
      case 'tension_at_most': return { kind, value: 1 };
      case 'location_is': return { kind, value: '' };
      default: return { kind: 'objectives', value: { names: [], require: 'all', status: 'done' } };
    }
  }

  // Wire modal buttons
  if (btnWhenCancel) btnWhenCancel.onclick = () => closeWhenEditor();
  if (btnWhenOk) btnWhenOk.onclick = () => {
    try {
      const eng = _toEngineWhen(_whenDraft);
      if (_whenEditEndingIdx >= 0 && cfg.story && Array.isArray(cfg.story.endings)) {
        cfg.story.endings[_whenEditEndingIdx].when = eng;
        // Refresh endings table and close
        renderStoryForm(cfg.story, lastState || null);
      }
    } catch(e) { /* ignore */ }
    closeWhenEditor();
  };
  // Story multi-selector events
  function sanitizeStoryId(s) {
    try { return String(s||'').trim().toLowerCase().replace(/\s+/g,'_'); } catch { return ''; }
  }
  function createEmptyStory() {
    return { meta: { title: '', style: '' }, scene: { name:'', description:'', objectives:[], time:'', weather:'', details:[] }, initial_positions: {} };
  }
  if (stStorySelect) stStorySelect.addEventListener('change', () => {
    if (!storyContainer) return;
    // stash current edits into container before switching
    commitLocalStoryEdits();
    const id = String(stStorySelect.value||'');
    selectedStoryId = id;
    original.story = deepClone(storyContainer.stories[id] || {});
    cfg.story = deepClone(storyContainer.stories[id] || {});
    renderStoryForm(cfg.story, lastState || null);
  });
  if (btnStoryNew) btnStoryNew.onclick = () => {
    if (!storyContainer) return;
    const nm = prompt('输入新故事 ID（小写字母数字与下划线/短横线）');
    if (!nm) return;
    const id = sanitizeStoryId(nm);
    if (!id || /[^a-z0-9_-]/.test(id)) { alert('无效 ID，允许 a-z0-9_-'); return; }
    if ((storyContainer.stories||{})[id]) { alert('已存在同名故事'); return; }
    commitLocalStoryEdits();
    storyContainer.stories[id] = createEmptyStory();
    selectedStoryId = id;
    updateStorySelectUI();
    original.story = deepClone(storyContainer.stories[id]);
    cfg.story = deepClone(storyContainer.stories[id]);
    renderStoryForm(cfg.story, lastState || null);
    markDirty('story');
  };
  if (btnStoryCopy) btnStoryCopy.onclick = () => {
    if (!storyContainer || !selectedStoryId) return;
    const nm = prompt('复制为新故事 ID');
    if (!nm) return;
    const id = sanitizeStoryId(nm);
    if (!id || /[^a-z0-9_-]/.test(id)) { alert('无效 ID，允许 a-z0-9_-'); return; }
    if ((storyContainer.stories||{})[id]) { alert('已存在同名故事'); return; }
    commitLocalStoryEdits();
    storyContainer.stories[id] = deepClone(storyContainer.stories[selectedStoryId] || createEmptyStory());
    selectedStoryId = id;
    updateStorySelectUI();
    original.story = deepClone(storyContainer.stories[id]);
    cfg.story = deepClone(storyContainer.stories[id]);
    renderStoryForm(cfg.story, lastState || null);
    markDirty('story');
  };
  if (btnStoryRename) btnStoryRename.onclick = () => {
    if (!storyContainer || !selectedStoryId) return;
    const nm = prompt(`重命名故事 ${selectedStoryId} 为`);
    if (!nm) return;
    const id = sanitizeStoryId(nm);
    if (!id || /[^a-z0-9_-]/.test(id)) { alert('无效 ID，允许 a-z0-9_-'); return; }
    if (id === selectedStoryId) return;
    if ((storyContainer.stories||{})[id]) { alert('已存在同名故事'); return; }
    commitLocalStoryEdits();
    storyContainer.stories[id] = deepClone(storyContainer.stories[selectedStoryId] || createEmptyStory());
    delete storyContainer.stories[selectedStoryId];
    selectedStoryId = id;
    updateStorySelectUI();
    original.story = deepClone(storyContainer.stories[id]);
    cfg.story = deepClone(storyContainer.stories[id]);
    renderStoryForm(cfg.story, lastState || null);
    markDirty('story');
  };
  if (btnStoryDelete) btnStoryDelete.onclick = () => {
    if (!storyContainer || !selectedStoryId) return;
    const ids = Object.keys(storyContainer.stories||{});
    if (ids.length <= 1) { alert('至少保留一个故事'); return; }
    if (!confirm(`确定删除故事 ${selectedStoryId} ？`)) return;
    delete storyContainer.stories[selectedStoryId];
    const rest = Object.keys(storyContainer.stories||{});
    selectedStoryId = rest[0] || '';
    updateStorySelectUI();
    original.story = deepClone(storyContainer.stories[selectedStoryId] || createEmptyStory());
    cfg.story = deepClone(storyContainer.stories[selectedStoryId] || createEmptyStory());
    renderStoryForm(cfg.story, lastState || null);
    markDirty('story');
  };
  if (btnAddDetail) btnAddDetail.onclick = () => { const scene = (cfg.story.scene = cfg.story.scene || {}); if (!Array.isArray(scene.details)) scene.details = []; scene.details.push(''); renderStoryForm(cfg.story, lastState || null); markDirty('story'); };
  if (btnAddObjective) btnAddObjective.onclick = () => { const scene = (cfg.story.scene = cfg.story.scene || {}); if (!Array.isArray(scene.objectives)) scene.objectives = []; scene.objectives.push(''); renderStoryForm(cfg.story, lastState || null); markDirty('story'); };
  if (btnAddPos) btnAddPos.onclick = () => {
    const nm = stPosNameSel ? String(stPosNameSel.value||'').trim() : '';
    const x = parseInt(stPosX.value||'0',10); const y = parseInt(stPosY.value||'0',10);
    if (!nm) { alert('请选择角色'); return; }
    cfg.story.initial_positions = cfg.story.initial_positions || {};
    cfg.story.initial_positions[nm] = [x,y];
    if (stPosNameSel) stPosNameSel.value=''; stPosX.value=''; stPosY.value='';
    renderStoryForm(cfg.story, lastState || null); markDirty('story');
  };
  if (stPosNameSel) stPosNameSel.addEventListener('change', () => {
    const nm = String(stPosNameSel.value||'').trim();
    if (!nm) return;
    try {
      const p = (lastState && lastState.positions) ? lastState.positions[nm] : null;
      if (Array.isArray(p) && p.length>=2) {
        stPosX.value = String(p[0]);
        stPosY.value = String(p[1]);
      }
    } catch(e){ throw e }
  });
  // Characters form events
  if (btnAddChar) btnAddChar.onclick = () => {
    const nm = prompt('输入新角色名称');
    if (!nm) return;
    const name = String(nm).trim();
    if (!name) return;
    if ((cfg.characters||{})[name]) { alert('已存在同名角色'); return; }
    ensureEntry(name);
    renderCharList(Object.keys(cfg.characters||{}));
    selectChar(name);
    // refresh story name select to include new role
    renderStoryForm(cfg.story, lastState || null);
    markDirty('characters');
  };
  if (btnDelChar) btnDelChar.onclick = () => {
    if (!chActiveName) return;
    if (!confirm(`确定删除 ${chActiveName} ？`)) return;
    delete (cfg.characters||{})[chActiveName];
    // cleanup relations entries referencing the deleted name
    try {
      delete chRelations[chActiveName];
      for (const a of Object.keys(chRelations)) {
        const m = chRelations[a] || {};
        if (m[chActiveName] != null) delete m[chActiveName];
      }
    } catch(e){ throw e }
    const names = Object.keys(cfg.characters||{});
    chActiveName = names[0] || '';
    renderCharList(names);
    if (chActiveName) fillCharForm(chActiveName);
    // refresh story name select to exclude removed role
    renderStoryForm(cfg.story, lastState || null);
    markDirty('characters');
  };
  if (chType) chType.addEventListener('change', ()=>{ if (!chActiveName) return; ensureEntry(chActiveName).type = chType.value; markDirty('characters'); });
  if (chPersona) chPersona.addEventListener('input', ()=>{ if (!chActiveName) return; ensureEntry(chActiveName).persona = chPersona.value; markDirty('characters'); });
  if (chAppearance) chAppearance.addEventListener('input', ()=>{ if (!chActiveName) return; ensureEntry(chActiveName).appearance = chAppearance.value; markDirty('characters'); });
  if (btnAddQuote) btnAddQuote.onclick = ()=>{ if (!chActiveName) return; const e=ensureEntry(chActiveName); if (!Array.isArray(e.quotes)) e.quotes=[]; e.quotes.push(''); fillCharForm(chActiveName); markDirty('characters'); };
  // Skill/save proficiency UI 已移除；CoC 属性在 fillCharForm 中绑定
  if (btnAddInv) btnAddInv.onclick = ()=>{
    if (!chActiveName) return;
    const id = chInvIdSel ? String(chInvIdSel.value||'').trim() : '';
    const n = parseInt(chInvCount.value||'1',10);
    if (!id) { alert('请选择武器'); return; }
    const e = ensureEntry(chActiveName);
    const cur = e.inventory[id] || 0;
    e.inventory[id] = (cur + (isNaN(n)? 0 : n > 0 ? n : 1));
    if (chInvIdSel) chInvIdSel.value=''; chInvCount.value='';
    fillCharForm(chActiveName); markDirty('characters');
  };
  if (stSceneName) stSceneName.addEventListener('input', ()=> markDirty('story'));
  if (stSceneTime) stSceneTime.addEventListener('input', ()=> markDirty('story'));
  if (stSceneWeather) stSceneWeather.addEventListener('input', ()=> markDirty('story'));
  if (stSceneDesc) stSceneDesc.addEventListener('input', ()=> markDirty('story'));
  if (btnAddWeapon) btnAddWeapon.onclick = () => {
    // ask for id first; allow auto if empty
    let id = String(prompt('输入武器 ID（可留空自动生成）')||'').trim();
    if (!id) {
      const base = 'weapon_'; let idx = 1; id = base+idx; while ((cfg.weapons||{})[id]) { idx++; id=base+idx; }
    } else {
      if ((cfg.weapons||{})[id]) { alert('已存在同名武器 ID'); return; }
    }
    // 新增武器：填入后端必需的字段默认值，伤害留空提示用户填写
    (cfg.weapons||(cfg.weapons={}))[id] = {
      label:'', reach_steps:1,
      // Backend-required keys with sensible defaults
      skill:'Fighting_Blade', defense_skill:'Dodge', damage_type:'physical',
      damage:''
    };
    renderWeaponsForm(cfg.weapons); markDirty('weapons');
  };
})();
