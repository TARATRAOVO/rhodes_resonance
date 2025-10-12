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
      kv.push(`<span class="pill">combat: ${inCombat}</span>`);
      if (round) kv.push(`<span class="pill">round: ${round}</span>`);
      const parts = (state.participants || []).join(', ');
      if (parts) kv.push(`<span class="pill">actors: ${esc(parts)}</span>`);
      const loc = state.location || '';
      if (loc) kv.push(`<span class="pill">location: ${esc(loc)}</span>`);
      const timeMin = state.time_min;
      if (typeof timeMin === 'number') kv.push(`<span class="pill">time: ${String(Math.floor(timeMin/60)).padStart(2,'0')}:${String(timeMin%60).padStart(2,'0')}</span>`);
      // 追加：目标状态
      const objs = Array.isArray(state.objectives) ? state.objectives : [];
      const objStatus = (state.objective_status || {});
      for (const o of objs.slice(0, 6)) {
        const st = String(objStatus[o] || 'pending');
        const label = st === 'done' ? '✓' : (st === 'blocked' ? '✗' : '…');
        kv.push(`<span class="pill">${esc(o)}:${label}</span>`);
      }
      // 追加：紧张度/标记
      if (typeof state.tension === 'number') kv.push(`<span class="pill">tension: ${state.tension}</span>`);
      if (Array.isArray(state.marks) && state.marks.length) kv.push(`<span class="pill">marks: ${state.marks.length}</span>`);
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
        if (pairs.length) kv.push(`<span class="pill">guard: ${esc(pairs.join(' | '))}</span>`);
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
    setStatus('connecting...');
    ws.onopen = () => { setStatus('connected'); reconnectDelay = 500; };
    ws.onmessage = (m) => {
      try {
        const obj = JSON.parse(m.data);
        if (obj.type === 'hello') {
          if (typeof obj.last_sequence === 'number') lastSeq = Math.max(lastSeq, obj.last_sequence);
          if (obj.state) renderHUD(obj.state);
          // 查询一次运行状态，刷新按钮
          fetch('/api/state').then(r=>r.json()).then(st => { running = !!st.running; updateButtons(); if (running) setStatus('running'); }).catch(()=>{});
          return;
        }
        if (obj.type === 'event' && obj.event) {
          if (debugMode) { try { console.debug('EVT', obj.event); } catch {} }
          handleEvent(obj.event);
          if (running) setStatus('running');
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
          setStatus('finished');
          running = false; updateButtons();
          return;
        }
      } catch (e) {}
    };
    ws.onclose = () => {
      setStatus('disconnected');
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
      running = true; updateButtons(); setStatus('running');
      if (!ws) connectWS();
      // 已进入运行态
    } catch (e) {
      btnStart.disabled = false;
      alert('start failed: ' + (e.message || e));
    }
  };

  btnStop.onclick = async () => {
    btnStop.disabled = true;
    try {
      await postJSON('/api/stop');
      setStatus('stopped');
    } catch (e) {
      alert('stop failed: ' + (e.message || e));
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

  // connect on load to receive any state before clicking Start
  connectWS();
  // 初始化按钮状态（未知运行态 -> 拉一次 state）
  fetch('/api/state').then(r=>r.json()).then(st => { running = !!st.running; updateButtons(); if (st && st.state) renderHUD(st.state); }).catch(()=>{ updateButtons(); });
})();
