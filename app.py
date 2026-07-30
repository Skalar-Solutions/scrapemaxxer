"""
scrap — web UI

A thin Flask front-end over scrap_core, so the team can run filtered
scrapes from a browser instead of the CLI.

Local / LAN use:
    python3 app.py
    open http://localhost:5050

Behind a real domain: set SCRAP_AUTH_USER and SCRAP_AUTH_PASS so every
request needs HTTP Basic Auth. Without them the app runs open — fine on
a trusted LAN, not fine on the public internet.
"""
import os
import re
import hmac
from functools import wraps

from flask import Flask, request, jsonify, render_template, Response

from scrap_core import run_one

app = Flask(__name__)

MAX_URLS_PER_REQUEST = 20

AUTH_USER = os.environ.get("SCRAP_AUTH_USER")
AUTH_PASS = os.environ.get("SCRAP_AUTH_PASS")


def auth_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not AUTH_USER or not AUTH_PASS:
            return view(*args, **kwargs)  # no credentials configured -> open

        auth = request.authorization
        valid = (
            auth
            and hmac.compare_digest(auth.username, AUTH_USER)
            and hmac.compare_digest(auth.password, AUTH_PASS)
        )
        if not valid:
            return Response(
                "Login required.", 401,
                {"WWW-Authenticate": 'Basic realm="scrap"'},
            )
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
@auth_required
def index():
    return render_template("index.html")


@app.route("/api/run", methods=["POST"])
@auth_required
def api_run():
    data = request.get_json(silent=True) or {}

    raw_urls = data.get("urls", "")
    urls = [u.strip() for u in re.split(r"[\n,]+", raw_urls) if u.strip()]
    if not urls:
        return jsonify({"error": "Give at least one URL."}), 400
    urls = urls[:MAX_URLS_PER_REQUEST]

    mode = data.get("mode", "text")
    mode_value = (data.get("mode_value") or "").strip()
    mode_kwargs = {}
    if mode == "css":
        if not mode_value:
            return jsonify({"error": "CSS selector can't be empty."}), 400
        mode_kwargs["css"] = mode_value
    elif mode == "xpath":
        if not mode_value:
            return jsonify({"error": "XPath expression can't be empty."}), 400
        mode_kwargs["xpath"] = mode_value
    elif mode == "links":
        mode_kwargs["links"] = True
    elif mode == "images":
        mode_kwargs["images"] = True
    elif mode == "text":
        mode_kwargs["text"] = True
    # mode == "auto" -> no kwargs, falls back to title/description

    filter_kwargs = {
        "contains": (data.get("contains") or "").strip() or None,
        "regex": (data.get("regex") or "").strip() or None,
        "exclude": (data.get("exclude") or "").strip() or None,
    }

    try:
        limit = int(data.get("limit") or 0)
    except ValueError:
        limit = 0

    stealth = bool(data.get("stealth"))

    results = []
    for url in urls:
        results.append(run_one(
            url,
            mode_kwargs=mode_kwargs,
            filter_kwargs=filter_kwargs,
            limit=limit,
            stealth=stealth,
        ))

    return jsonify({"jobs": results})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
