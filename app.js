(() => {
  const btnStart = document.getElementById('btnStart');
  const btnStop  = document.getElementById('btnStop');
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

  function setStatus(text) { statusEl.textContent = text; }
  function lineEl(html, cls='') {
    const div = document.createElement('div');
    div.className = `line ${cls}`;
    div.innerHTML = html;
    return div;
  }
  function esc(s) { return s.replace(/[<>&]/g, m => ({'<':'&lt;','>':'&gt;','&':'&amp;'}[m])); }
  function scrollToBottom(el) { el.scrollTop = el.scrollHeight; }

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
    } catch {}
    hudEl.innerHTML = kv.join(' ');
  }

  function handleEvent(ev) {
    const t = ev.event_type;
    lastSeq = Math.max(lastSeq, ev.sequence || 0);
    if (t === 'state_update') {
      const st = ev.state || (ev.data && ev.data.state) || null;
      renderHUD(st);
      return;
    }
    // 精简叙事：只展示玩家/NPC对白；系统或上下文、回合提示等全部隐藏
    if (t === 'narrative') {
      const phase = String(ev.phase || '');
      if (phase.startsWith('context:') || phase === 'round-start' || phase === 'world-summary') return;
      const actor = ev.actor || '';
      const raw = (ev.text || (ev.data && ev.data.text) || '').toString();
      if (!phase.startsWith('npc:') && !phase.startsWith('player:')) {
        // 非对白（例如 Host 提示）一律忽略，保持简洁
        return;
      }
      const row = lineEl(`<span class="actor">${esc(actor)}:</span> ${esc(raw)}`, 'narrative');
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
            if (Array.isArray(texts) && texts.length) {
              textOut = texts.join(' ');
            } else if (meta && typeof meta === 'object') {
              const keys = Object.keys(meta).slice(0, 4);
              textOut = keys.map(k => `${k}=${typeof meta[k]==='object'? JSON.stringify(meta[k]): String(meta[k])}`).join(' ');
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
          return;
        }
        if (obj.type === 'event' && obj.event) {
          handleEvent(obj.event);
          // 如果是等待玩家输入的信号，提示一下，并开启发送按钮
          try {
            const ev = obj.event; if (ev && ev.event_type === 'system' && ev.phase === 'player_input') {
              waitingActor = String(ev.actor || '');
              playerHint.textContent = waitingActor ? `等待 ${waitingActor} 输入...` : '等待玩家输入...';
              btnSend.disabled = !waitingActor;
              if (waitingActor) txtPlayer.focus();
            }
          } catch {}
          return;
        }
        if (obj.type === 'end') {
          setStatus('finished');
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
      btnStop.disabled = false;
      if (!ws) connectWS();
      setStatus('starting...');
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
      btnStart.disabled = false;
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
})();
