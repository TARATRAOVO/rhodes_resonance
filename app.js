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
  const btnToggleSide = document.getElementById('btnToggleSide');
  // Map elements
  const mapCanvas = document.getElementById('mapCanvas');
  const mapHint = document.getElementById('mapHint');
  // Settings drawer elements
  const drawer = document.getElementById('settingsDrawer');
  const tabBtns = drawer ? Array.from(drawer.querySelectorAll('.tab')) : [];
  const panes = drawer ? Array.from(drawer.querySelectorAll('.tabpane')) : [];
  const btnCfgClose = drawer ? drawer.querySelector('#btnCfgClose') : null;
  const btnCfgSave = drawer ? drawer.querySelector('#btnCfgSave') : null;
  const btnCfgSaveRestart = drawer ? drawer.querySelector('#btnCfgSaveRestart') : null;
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
  const chLvl = drawer ? drawer.querySelector('#chLvl') : null;
  const chAC = drawer ? drawer.querySelector('#chAC') : null;
  const chMaxHP = drawer ? drawer.querySelector('#chMaxHP') : null;
  const chMove = drawer ? drawer.querySelector('#chMove') : null;
  const chSTR = drawer ? drawer.querySelector('#chSTR') : null;
  const chDEX = drawer ? drawer.querySelector('#chDEX') : null;
  const chCON = drawer ? drawer.querySelector('#chCON') : null;
  const chINT = drawer ? drawer.querySelector('#chINT') : null;
  const chWIS = drawer ? drawer.querySelector('#chWIS') : null;
  const chCHA = drawer ? drawer.querySelector('#chCHA') : null;
  const chSkills = drawer ? drawer.querySelector('#chSkills') : null;
  const chSaves = drawer ? drawer.querySelector('#chSaves') : null;
  const btnAddSkill = drawer ? drawer.querySelector('#btnAddSkill') : null;
  const btnAddSave = drawer ? drawer.querySelector('#btnAddSave') : null;
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
  let running = false;
  const params = new URLSearchParams(location.search);
  const debugMode = params.get('debug') === '1' || params.get('debug') === 'true';
  let lastState = {};

  // ==== Simple Battle Map (static, no interaction/animation) ====
  const MapView = (() => {
    // Read CSS variables to keep canvas in sync with theme
    function cssVar(name, fallback) {
      try {
        const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
        return v || fallback;
      } catch { return fallback; }
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
        const positions = (state && state.positions) || (this._lastState && this._lastState.positions) || {};
        const b = this._computeBounds(positions);
        if (!b) {
          if (this.hint) this.hint.textContent = '暂无坐标';
          return;
        }
        if (this.hint) this.hint.textContent = '';
        const pad = 24;
        const spanX = (b.maxX - b.minX + 1);
        const spanY = (b.maxY - b.minY + 1);
        const stepPx = Math.max(6, Math.min((w - pad*2) / spanX, (h - pad*2) / spanY));
        this._drawGrid(b, stepPx);
        this._drawActors(this._lastState || {}, b, stepPx);
      }
      update(state) { this.render(state); }
    }
    return MapView;
  })();

  const mapView = (mapCanvas && mapCanvas.getContext) ? new MapView(mapCanvas, mapHint) : null;
  if (mapView) window.addEventListener('resize', () => mapView.resize());
  // Settings editor state
  let activeTab = 'story';
  const cfg = { story: null, weapons: null, characters: null };
  const original = { story: null, weapons: null, characters: null };
  let chActiveName = '';
  let chRelations = {};
  const dirty = { story: false, weapons: false, characters: false };

  function setStatus(text) { statusEl.textContent = text; }
  function lineEl(html, cls='') {
    const div = document.createElement('div');
    div.className = `line ${cls}`;
    div.innerHTML = html;
    return div;
  }
  function esc(s) { return s.replace(/[<>&]/g, m => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[m])); }
  function scrollToBottom(el) { el.scrollTop = el.scrollHeight; }
  function updateButtons() {
    // Start 与 Restart：未运行时都可用；运行时 Start 禁用、Restart 可用
    btnStart.disabled = running;
    btnStop.disabled = !running;
    btnRestart.disabled = false;
    // Send 按钮仍由等待玩家输入信号控制
  }

  function renderHUD(state) {
    hudEl.innerHTML = '';
    if (!state || typeof state !== 'object') return;
    const kv = [];
    try {
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
      } catch {}
    } catch {}
    hudEl.innerHTML = kv.join(' ');
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
      if (mapView) mapView.update(lastState);
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
      const row = lineEl(`<span class="actor">${esc(actor)}:</span> ${esc(cleaned)}`, 'narrative');
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
              const n = params.name || actor; const tgt = params.target || {}; const steps = params.steps != null ? params.steps : '';
              const xy = (tgt && typeof tgt === 'object') ? `(${tgt.x},${tgt.y})` : String(tgt || '');
              return `${n} 向 ${xy} 前进 ${steps} 步`;
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
          } catch {}
          // 默认兜底：列出少量参数键值
          try {
            const keys = Object.keys(params).slice(0, 3);
            const kv = keys.map(k => `${k}=${JSON.stringify(params[k])}`).join(', ');
            return kv;
          } catch { return ''; }
        })();
        if (t === 'tool_call') {
          const line = lineEl(`<span class="actor">${esc(actor)}</span> 发起 <b>${esc(label)}</b>${brief ? ' · ' + esc(brief) : ''}`);
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
          } catch {}
          const line = lineEl(`<span class="actor">${esc(actor)}</span> 结果 <b>${esc(label)}</b>${textOut ? ' · ' + esc(textOut) : ''}`);
          storyEl.appendChild(line);
        }
        if (storyEl.children.length > maxStory) storyEl.removeChild(storyEl.firstChild);
        scrollToBottom(storyEl.parentElement);
      } catch {}
      return;
    }
    if (t === 'error') {
      const msg = (ev.data && ev.data.message) || 'error';
      storyEl.appendChild(lineEl(`error: ${esc(String(msg))}`, 'error'));
      if (storyEl.children.length > maxStory) storyEl.removeChild(storyEl.firstChild);
      scrollToBottom(storyEl.parentElement);
      return;
    }
  }

  function connectWS() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const url = `${proto}://${location.host}/ws/events?since=${lastSeq}`;
    ws = new WebSocket(url);
    setStatus('连接中…');
    ws.onopen = () => { setStatus('已连接'); reconnectDelay = 500; };
    ws.onmessage = (m) => {
      try {
        const obj = JSON.parse(m.data);
        if (obj.type === 'hello') {
          if (typeof obj.last_sequence === 'number') lastSeq = Math.max(lastSeq, obj.last_sequence);
          if (obj.state) { renderHUD(obj.state); if (mapView) mapView.update(obj.state); }
          // 查询一次运行状态，刷新按钮
          fetch('/api/state').then(r=>r.json()).then(st => { running = !!st.running; updateButtons(); if (running) setStatus('运行中'); }).catch(()=>{});
          return;
        }
        if (obj.type === 'event' && obj.event) {
          if (debugMode) { try { console.debug('EVT', obj.event); } catch {} }
          handleEvent(obj.event);
          if (running) setStatus('运行中');
          // 如果是等待玩家输入的信号，提示一下，并开启发送按钮
          try {
            const ev = obj.event;
            if (ev && ev.event_type === 'system') {
              if (ev.phase === 'player_input') {
                waitingActor = String(ev.actor || '');
                playerHint.textContent = waitingActor ? `等待 ${waitingActor} 输入...` : '等待玩家输入...';
                btnSend.disabled = !waitingActor;
                if (waitingActor) txtPlayer.focus();
              } else if (ev.phase === 'player_input_end') {
                waitingActor = '';
                btnSend.disabled = true;
                playerHint.textContent = '';
              }
            }
          } catch {}
          return;
        }
        if (obj.type === 'end') {
          setStatus('已结束');
          running = false; updateButtons();
          return;
        }
      } catch (e) {}
    };
    ws.onclose = () => {
      setStatus('已断开');
      ws = null;
      setTimeout(connectWS, reconnectDelay);
      reconnectDelay = Math.min(maxDelay, reconnectDelay * 2);
    };
    ws.onerror = () => { try { ws.close(); } catch {} };
  }

  async function postJSON(path) {
    const res = await fetch(path, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  btnStart.onclick = async () => {
    btnStart.disabled = true;
    try {
      await postJSON('/api/start');
      running = true; updateButtons(); setStatus('运行中');
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

  // Golden ratio layout: no sizer

  btnStop.onclick = async () => {
    btnStop.disabled = true;
    try {
      await postJSON('/api/stop');
      setStatus('已停止');
    } catch (e) {
      alert('终止失败: ' + (e.message || e));
    } finally {
      running = false; updateButtons();
    }
  };

  btnRestart.onclick = async () => {
    btnStart.disabled = true; btnStop.disabled = true; btnRestart.disabled = true;
    try {
      const res = await fetch('/api/restart', { method: 'POST' });
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
        if (st && st.state) { renderHUD(st.state); if (mapView) mapView.update(st.state); }
        running = !!(st && st.running);
      } catch {}
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
  txtPlayer.addEventListener('keydown', (e) => { if (e.key === 'Enter') sendPlayer(); });

  // handle window resize for map
  if (mapView) {
    window.addEventListener('resize', () => mapView.resize());
    // initial sizing in case canvas mounted before script
    setTimeout(()=> mapView.resize(), 0);
  }

  // connect on load to receive any state before clicking Start
  connectWS();
  // 初始化按钮状态（未知运行态 -> 拉一次 state）
  fetch('/api/state').then(r=>r.json()).then(st => { running = !!st.running; updateButtons(); if (st && st.state) { renderHUD(st.state); if (mapView) mapView.update(st.state); } }).catch(()=>{ updateButtons(); });

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
        dnd: { level:1, ac:10, max_hp:8, abilities:{STR:10,DEX:10,CON:10,INT:10,WIS:10,CHA:10}, proficient_skills:[], proficient_saves:[], move_speed:6 },
        inventory: {}
      };
    }
    return cfg.characters[name];
  }

  function fillCharForm(name) {
    const entry = ensureEntry(name);
    if (chName) chName.value = name;
    if (chType) { chType.value = (entry.type||'npc'); }
    if (chPersona) chPersona.value = entry.persona || '';
    if (chAppearance) chAppearance.value = entry.appearance || '';
    // quotes
    if (chQuotes) {
      chQuotes.innerHTML = '';
      const arr = Array.isArray(entry.quotes) ? entry.quotes.slice() : (entry.quotes? [String(entry.quotes)]: []);
      entry.quotes = arr;
      arr.forEach((q, idx) => addListRow(chQuotes, q, v => { entry.quotes[idx] = v; markDirty('characters'); }, () => { entry.quotes.splice(idx,1); fillCharForm(name); markDirty('characters'); }));
    }
    const dnd = entry.dnd = Object.assign({ level:1, ac:10, max_hp:8, abilities:{}, proficient_skills:[], proficient_saves:[], move_speed:6 }, entry.dnd || {});
    const ab = dnd.abilities = Object.assign({STR:10,DEX:10,CON:10,INT:10,WIS:10,CHA:10}, dnd.abilities || {});
    if (chLvl) chLvl.value = dnd.level != null ? dnd.level : 1;
    if (chAC) chAC.value = dnd.ac != null ? dnd.ac : 10;
    if (chMaxHP) chMaxHP.value = dnd.max_hp != null ? dnd.max_hp : 8;
    if (chMove) chMove.value = dnd.move_speed != null ? dnd.move_speed : (dnd.move_speed_steps != null ? dnd.move_speed_steps : 6);
    if (chSTR) chSTR.value = ab.STR != null ? ab.STR : 10;
    if (chDEX) chDEX.value = ab.DEX != null ? ab.DEX : 10;
    if (chCON) chCON.value = ab.CON != null ? ab.CON : 10;
    if (chINT) chINT.value = ab.INT != null ? ab.INT : 10;
    if (chWIS) chWIS.value = ab.WIS != null ? ab.WIS : 10;
    if (chCHA) chCHA.value = ab.CHA != null ? ab.CHA : 10;
    // skills & saves
    if (chSkills) {
      chSkills.innerHTML = '';
      const arr = Array.isArray(dnd.proficient_skills) ? dnd.proficient_skills.slice() : [];
      dnd.proficient_skills = arr;
      arr.forEach((s, idx) => addListRow(chSkills, s, v => { dnd.proficient_skills[idx] = String(v||'').toLowerCase(); markDirty('characters'); }, () => { dnd.proficient_skills.splice(idx,1); fillCharForm(name); markDirty('characters'); }));
    }
    if (chSaves) {
      chSaves.innerHTML = '';
      const arr = Array.isArray(dnd.proficient_saves) ? dnd.proficient_saves.slice() : [];
      dnd.proficient_saves = arr;
      arr.forEach((s, idx) => addListRow(chSaves, s, v => { dnd.proficient_saves[idx] = String(v||'').toUpperCase(); markDirty('characters'); }, () => { dnd.proficient_saves.splice(idx,1); fillCharForm(name); markDirty('characters'); }));
    }
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
    } catch {}
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
    } catch {}
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
    } catch {}
  }

  function renderWeaponsForm(data) {
    original.weapons = JSON.parse(JSON.stringify(data || {}));
    cfg.weapons = JSON.parse(JSON.stringify(data || {}));
    dirty.weapons = false;
    const tbody = wpTable.querySelector('tbody');
    tbody.innerHTML = '';
    const abilities = ['STR','DEX','CON','INT','WIS','CHA'];
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
        } catch {}
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
      // ability
      const tdAb = document.createElement('td');
      const selAb = document.createElement('select'); abilities.forEach(ab=>{ const opt=document.createElement('option'); opt.value=ab; opt.textContent=ab; selAb.appendChild(opt); }); selAb.value=(String(item.ability||'STR').toUpperCase()); selAb.addEventListener('change',()=>{ (cfg.weapons[id]||(cfg.weapons[id]={})).ability = selAb.value; markDirty('weapons'); }); tdAb.appendChild(selAb);
      // damage expr
      const tdDmg = document.createElement('td');
      const inDmg = document.createElement('input'); inDmg.type='text'; inDmg.value=(item.damage_expr||''); inDmg.addEventListener('input',()=>{ (cfg.weapons[id]||(cfg.weapons[id]={})).damage_expr=inDmg.value; markDirty('weapons'); }); tdDmg.appendChild(inDmg);
      // prof
      const tdProf = document.createElement('td');
      const ck = document.createElement('input'); ck.type='checkbox'; ck.checked= !!item.proficient_default; ck.addEventListener('change',()=>{ (cfg.weapons[id]||(cfg.weapons[id]={})).proficient_default = !!ck.checked; markDirty('weapons'); }); tdProf.appendChild(ck);
      // ops
      const tdOps = document.createElement('td');
      const btnDel = document.createElement('button'); btnDel.className='sm'; btnDel.textContent='删除'; btnDel.onclick=()=>{ delete cfg.weapons[id]; renderWeaponsForm(cfg.weapons); markDirty('weapons'); };
      tdOps.appendChild(btnDel);
      tr.appendChild(tdId); tr.appendChild(tdLabel); tr.appendChild(tdReach); tr.appendChild(tdAb); tr.appendChild(tdDmg); tr.appendChild(tdProf); tr.appendChild(tdOps);
      tbody.appendChild(tr);
    });
    // refresh characters inventory add-select (if visible)
    try { if (chActiveName) fillCharForm(chActiveName); } catch {}
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
    const [stRes, wpRes, chRes, stState] = await Promise.all([
      fetch('/api/config/story').then(r=>r.json()).catch(()=>({data:{}})),
      fetch('/api/config/weapons').then(r=>r.json()).catch(()=>({data:{}})),
      fetch('/api/config/characters').then(r=>r.json()).catch(()=>({data:{}})),
      fetch('/api/state').then(r=>r.json()).catch(()=>({state:null})),
    ]);
    lastState = (stState||{}).state || lastState || {};
    renderCharactersForm((chRes||{}).data||{});
    renderStoryForm((stRes||{}).data||{}, lastState);
    renderWeaponsForm((wpRes||{}).data||{});
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
    return out;
  }

  function weaponsCollect() {
    const out = {};
    // preserve unknown keys per weapon by merging original
    const orig = original.weapons || {};
    for (const id of Object.keys(cfg.weapons || {})) {
      const src = cfg.weapons[id] || {};
      const base = Object.assign({}, orig[id] || {});
      base.label = (src.label || '').trim();
      base.reach_steps = parseInt(src.reach_steps != null ? src.reach_steps : 1, 10) || 1;
      base.ability = String(src.ability || 'STR').toUpperCase();
      base.damage_expr = (src.damage_expr || '').trim();
      base.proficient_default = !!src.proficient_default;
      out[id] = base;
    }
    return out;
  }

  function charactersCollect() {
    // Merge edited characters with preserved relations
    const out = {};
    for (const [name, entry] of Object.entries(cfg.characters || {})) {
      out[name] = JSON.parse(JSON.stringify(entry || {}));
      // normalize dnd.move_speed_steps alias to move_speed for file compatibility
      const d = out[name].dnd || {};
      if (d.move_speed_steps != null && d.move_speed == null) d.move_speed = d.move_speed_steps;
      // ensure arrays are arrays
      if (typeof out[name].quotes === 'string') out[name].quotes = [out[name].quotes];
    }
    out.relations = JSON.parse(JSON.stringify(chRelations || {}));
    return out;
  }

  async function saveActive(restart) {
    try {
      let name = activeTab;
      let data = null;
      if (name === 'story') data = storyCollect();
      else if (name === 'weapons') data = weaponsCollect();
      else if (name === 'characters') data = charactersCollect();
      const res = await fetch(`/api/config/${name}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || '保存失败');
      }
      dirty[name] = false;
      if (restart) {
        // mimic btnRestart behaviour
        btnStart.disabled = true; btnStop.disabled = true; btnRestart.disabled = true;
        try {
          const r2 = await fetch('/api/restart', { method: 'POST' });
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
          } catch {}
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

  // Wire events
  if (btnSettings) btnSettings.onclick = async () => { setActiveTab('story'); drawerOpen(); await loadAllConfigs(); };
  if (btnCfgClose) btnCfgClose.onclick = () => drawerClose(false);
  if (btnCfgSave) btnCfgSave.onclick = () => saveActive(false);
  if (btnCfgSaveRestart) btnCfgSaveRestart.onclick = () => saveActive(true);
  if (btnCfgReset) btnCfgReset.onclick = async () => { await loadAllConfigs(); alert('已重置为服务器版本'); };
  for (const b of tabBtns) {
    b.onclick = () => setActiveTab(b.getAttribute('data-tab'));
  }
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
    } catch {}
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
    } catch {}
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
  // dnd numeric & abilities
  const bindNum = (el, set) => { if (!el) return; el.addEventListener('input', ()=>{ if (!chActiveName) return; set(); markDirty('characters'); }); };
  bindNum(chLvl, ()=>{ ensureEntry(chActiveName).dnd.level = parseInt(chLvl.value||'1',10); });
  bindNum(chAC, ()=>{ ensureEntry(chActiveName).dnd.ac = parseInt(chAC.value||'10',10); });
  bindNum(chMaxHP, ()=>{ ensureEntry(chActiveName).dnd.max_hp = parseInt(chMaxHP.value||'8',10); });
  bindNum(chMove, ()=>{ ensureEntry(chActiveName).dnd.move_speed = parseInt(chMove.value||'6',10); });
  bindNum(chSTR, ()=>{ ensureEntry(chActiveName).dnd.abilities.STR = parseInt(chSTR.value||'10',10); });
  bindNum(chDEX, ()=>{ ensureEntry(chActiveName).dnd.abilities.DEX = parseInt(chDEX.value||'10',10); });
  bindNum(chCON, ()=>{ ensureEntry(chActiveName).dnd.abilities.CON = parseInt(chCON.value||'10',10); });
  bindNum(chINT, ()=>{ ensureEntry(chActiveName).dnd.abilities.INT = parseInt(chINT.value||'10',10); });
  bindNum(chWIS, ()=>{ ensureEntry(chActiveName).dnd.abilities.WIS = parseInt(chWIS.value||'10',10); });
  bindNum(chCHA, ()=>{ ensureEntry(chActiveName).dnd.abilities.CHA = parseInt(chCHA.value||'10',10); });
  if (btnAddSkill) btnAddSkill.onclick = ()=>{ if (!chActiveName) return; const d=ensureEntry(chActiveName).dnd; if (!Array.isArray(d.proficient_skills)) d.proficient_skills=[]; d.proficient_skills.push(''); fillCharForm(chActiveName); markDirty('characters'); };
  if (btnAddSave) btnAddSave.onclick = ()=>{ if (!chActiveName) return; const d=ensureEntry(chActiveName).dnd; if (!Array.isArray(d.proficient_saves)) d.proficient_saves=[]; d.proficient_saves.push(''); fillCharForm(chActiveName); markDirty('characters'); };
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
    (cfg.weapons||(cfg.weapons={}))[id] = { label:'', reach_steps:1, ability:'STR', damage_expr:'1d4+STR', proficient_default:false };
    renderWeaponsForm(cfg.weapons); markDirty('weapons');
  };
})();
