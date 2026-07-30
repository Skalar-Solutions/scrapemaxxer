# scrap

Wrapper around [scrapling](https://github.com/D4Vinci/Scrapling) — fetch a page,
extract only what you asked for (links, images, text, or a css/xpath selector),
filter it, print it clean. Two ways to run it: CLI or a small web UI for the team.

## Setup (once per machine)

```bash
pip install "scrapling[shell]" flask rich click
scrapling install
```

If you're on macOS with the python.org build and get SSL cert errors during
`scrapling install`, run `/Applications/Python X.Y/Install Certificates.command` first.

## CLI

```bash
python3 scrap.py https://example.com --links --contains blog
python3 scrap.py https://example.com --css "h2.title::text" --format md -o titles.md
python3 scrap.py --file urls.txt --text --exclude cookie --limit 20
```

`python3 scrap.py --help` for all options.

## Web UI (for the team)

### Local / quick test

```bash
python3 app.py
```

Open `http://localhost:5050`. No auth by default — fine for testing on your
own machine, not fine once it's reachable from outside.

### On a real domain (VPS + subdomain)

1. **Point DNS.** Add an A record, e.g. `scrap.yourdomain.com` → your VPS IP.

2. **Turn on auth.** Set these before starting the app — once both are set,
   every request needs HTTP Basic Auth:
   ```bash
   export SCRAP_AUTH_USER=team
   export SCRAP_AUTH_PASS=<pick something real, not this>
   ```

3. **Run it with a real WSGI server**, not the Flask dev server:
   ```bash
   pip install gunicorn
   gunicorn -w 2 -b 127.0.0.1:5050 app:app
   ```

4. **Reverse proxy + HTTPS.** Easiest option is Caddy — it gets you a valid
   cert automatically, no certbot dance:
   ```
   # /etc/caddy/Caddyfile
   scrap.yourdomain.com {
       reverse_proxy 127.0.0.1:5050
   }
   ```
   `systemctl reload caddy` and it's live. (If your VPS already runs nginx for
   klay-server, an equivalent `proxy_pass http://127.0.0.1:5050;` server block
   plus `certbot --nginx` works the same way.)

5. **Keep it running** with a systemd unit so it survives reboots/crashes:
   ```
   # /etc/systemd/system/scrap.service
   [Unit]
   Description=scrap web UI
   After=network.target

   [Service]
   WorkingDirectory=/path/to/scrap-web
   Environment=SCRAP_AUTH_USER=team
   Environment=SCRAP_AUTH_PASS=<same as above>
   ExecStart=/usr/bin/gunicorn -w 2 -b 127.0.0.1:5050 app:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   ```bash
   systemctl enable --now scrap
   ```

Env-var auth is intentionally simple (one shared login for the team, not
per-user accounts). Good enough for an internal tool behind HTTPS. If you
later want per-person accounts or audit logs of who ran what, that's a
bigger change to `app.py`, not a config tweak — say so if you want it.

## Files

- `scrap_core.py` — the actual fetch/extract/filter logic, shared by both interfaces
- `scrap.py` — CLI (click + rich)
- `app.py` — Flask web app
- `templates/`, `static/` — web UI frontend
