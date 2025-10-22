Rhodes Resonance 部署速记（前端 GitHub Pages + 后端服务器 + Quick Tunnel）

重要：本文件包含敏感信息（服务器密码、API Key）。请妥善保管，建议后续更换为更安全的凭据管理（SSH Key、密码/密钥轮换）。

一、仓库与前端
- 代码仓库： https://github.com/TARATRAOVO/rhodes_resonance
- GitHub Pages： https://taratraovo.github.io/rhodes_resonance/
  - 已配置默认后端，无需再带 `?backend=` 参数。默认后端在 `web/config.js` 的 `window.RR.backendOrigin` 中设置。
  - 当前默认后端：`https://inspector-aye-graphs-spend.trycloudflare.com`
  - 仍然保留覆盖能力：可通过 `?backend=https://<your-backend-domain>` 临时指定后端（优先级高于 config.js）。

二、服务器（后端）
- 公网 IP：47.239.28.170
- SSH：
  - 用户名：root
  - 密码：Dk@202411
  - 建议后续改为 SSH Key 登录，并更换此密码。

- 代码目录与运行时：
  - 代码路径：/opt/rhodes_resonance
  - Python venv：/opt/rhodes_resonance/.venv
  - 主程序：/opt/rhodes_resonance/src/main.py（FastAPI + WebSocket）
  - 监听地址：127.0.0.1:8000（仅本机，供隧道转发）

- 环境变量（仅后端读取）：
  - 文件：/etc/rhodes_resonance.env
  - 内容：
    MOONSHOT_API_KEY=sk-2GzAKgtJ5OM86CD6poT3wv0B0NMqRW0xk97YbbYsHFAFp6Sw
  - 建议：尽快在 Kimi 控制台重置该密钥，并只在后端以环境变量方式使用。

- systemd 服务（常用命令）：
  1) 后端服务：rhodes-resonance
     - 查看状态：
       sudo systemctl status rhodes-resonance
     - 重启：
       sudo systemctl restart rhodes-resonance
     - 实时日志：
       sudo journalctl -u rhodes-resonance -f

  2) Quick Tunnel 服务：cloudflared-quick（提供受信任的 HTTPS 域名）
     - 查看状态：
       sudo systemctl status cloudflared-quick
     - 重启：
       sudo systemctl restart cloudflared-quick
     - 获取当前 trycloudflare 域名：
       sudo journalctl -u cloudflared-quick -n 200 | grep -o 'https://[^ ]*trycloudflare.com' | tail -n1

- 当前 Quick Tunnel 域名（随重启可能变化）：
  https://inspector-aye-graphs-spend.trycloudflare.com

三、前后端联通用法
- 直接访问：
  https://taratraovo.github.io/rhodes_resonance/
  （已在 `web/config.js` 中写入默认后端）
- 成功标志：
  - 页面状态“已连接”；
  - DevTools 中 /api/state 请求 200；
  - WebSocket 连接到 wss://…/ws/events；
  - 点击“开始行动”有响应。

四、后端更新
- 拉取并重启（在服务器上）：
  cd /opt/rhodes_resonance
  sudo git fetch --all --prune
  sudo git reset --hard origin/main
  sudo /opt/rhodes_resonance/.venv/bin/pip install -r requirements.txt
  sudo systemctl restart rhodes-resonance

五、无域名的说明与替代
- 为什么需要 Quick Tunnel：GitHub Pages 是 HTTPS，浏览器会拦截对纯 HTTP 后端的访问；Tunnel 提供受信任的 HTTPS 域名（支持 WebSocket）。
- 若日后有域名：建议使用 Cloudflare Named Tunnel 或 Nginx + Let's Encrypt，在固定子域（如 api.example.com）下提供 HTTPS，前端即可不再依赖临时域名。

六、默认后端更新指引（当 Quick Tunnel 域名变化时）
- 获取最新域名：
  - `sudo journalctl -u cloudflared-quick -n 200 | grep -o 'https://[^ ]*trycloudflare.com' | tail -n1`
- 修改前端默认后端并发布：
  1) 编辑仓库 `web/config.js`，将 `window.RR.backendOrigin = "..."` 改为新的域名；
  2) 提交并推送：`git commit -am "web: update backendOrigin" && git push`；
  3) 等待 GitHub Pages 刷新（通常数十秒）；
  4) 期间可用 `?backend=` 参数临时覆盖。

七、常见问题
- GH Pages 打开没反应：确认 URL 是否带了正确的 ?backend= 参数，或在 web/config.js 中设置 window.RR.backendOrigin。
- /api/state 正常但 WS 不连：检查 cloudflared 服务与日志（是否有新的 trycloudflare 域名）。
- 更换 Kimi 密钥：
  - 编辑 /etc/rhodes_resonance.env
  - sudo systemctl restart rhodes-resonance

八、安全建议（重要）
- 服务器登录建议改为 SSH Key，并尽快更换当前密码；
- 立即在 Kimi 控制台重置本文中明文出现的 API Key，并仅在后端以环境变量形式使用；
- 将 `docs/deploy-notes.md` 的敏感字段做脱敏或迁移到私有文档；
- 若采用固定域名，请为后端仅开放 127.0.0.1 监听，并通过反代/Tunnel 暴露 HTTPS。

（完）
