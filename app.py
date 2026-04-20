"""
Options Lotto Toolkit
=====================
Install: pip install -r requirements.txt
Run:     python app.py
Open:    http://localhost:5000
"""

from flask import Flask, jsonify, request, render_template
from modules import earnings, screener, iv_rank, tracker, analyzer, catalyst, technical
from modules.market_hours import market_status
from modules.screener import get_sp500_tickers, fetch_extended_tickers
import time
import threading

app = Flask(__name__)

# Simple in-memory cache: {key: (data, timestamp)}
_cache = {}
_cache_lock = threading.Lock()
CACHE_TTL = 300  # 5 minutes


def cached(key, fn, ttl=CACHE_TTL):
    with _cache_lock:
        if key in _cache:
            data, ts = _cache[key]
            if time.time() - ts < ttl:
                return data
    result = fn()
    with _cache_lock:
        _cache[key] = (result, time.time())
    return result


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/earnings")
def api_earnings():
    days = int(request.args.get("days", 21))
    key = f"earnings_{days}"
    try:
        data = cached(key, lambda: earnings.scan_upcoming_earnings(days), ttl=600)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/screen")
def api_screen():
    symbol = request.args.get("symbol", "").strip().upper()
    if not symbol:
        return jsonify({"ok": False, "error": "symbol required"}), 400
    max_price    = float(request.args.get("max_price", 1.00))
    min_price    = float(request.args.get("min_price", 0.01))
    max_dte      = int(request.args.get("max_dte", 60))
    min_dte      = int(request.args.get("min_dte", 1))
    min_otm      = float(request.args.get("min_otm", 2.0))
    opt_type     = request.args.get("type", "both")
    min_prob_itm = float(request.args.get("min_prob_itm", 0.0))
    mode         = request.args.get("mode", "lotto")

    key = f"screen_{symbol}_{max_price}_{min_price}_{max_dte}_{min_dte}_{min_otm}_{opt_type}_{min_prob_itm}_{mode}"
    try:
        data = cached(key, lambda: screener.screen_options(
            symbol, max_price, min_price, max_dte, min_dte, min_otm, opt_type, min_prob_itm, mode
        ), ttl=180)
        if "error" in data:
            return jsonify({"ok": False, "error": data["error"]}), 400
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/market_status")
def api_market_status():
    return jsonify({"ok": True, "data": market_status()})


@app.route("/api/strikes")
def api_strikes():
    symbol   = request.args.get("symbol", "").strip().upper()
    opt_type = request.args.get("type", "CALL").upper()
    expiry   = request.args.get("expiry", "")
    if not all([symbol, expiry]):
        return jsonify({"ok": False, "error": "symbol and expiry required"}), 400
    try:
        data = analyzer.get_strikes(symbol, opt_type, expiry)
        if "error" in data:
            return jsonify({"ok": False, "error": data["error"]}), 400
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/expiries/<symbol>")
def api_expiries(symbol):
    try:
        data = analyzer.get_expiries(symbol.strip().upper())
        if "error" in data:
            return jsonify({"ok": False, "error": data["error"]}), 400
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/analyze")
def api_analyze():
    symbol   = request.args.get("symbol", "").strip().upper()
    opt_type = request.args.get("type", "CALL").upper()
    strike   = request.args.get("strike")
    expiry   = request.args.get("expiry")
    if not all([symbol, strike, expiry]):
        return jsonify({"ok": False, "error": "symbol, strike, and expiry required"}), 400
    key = f"analyze_{symbol}_{opt_type}_{strike}_{expiry}"
    try:
        data = cached(key, lambda: analyzer.analyze_contract(symbol, opt_type, strike, expiry), ttl=120)
        if "error" in data:
            return jsonify({"ok": False, "error": data["error"]}), 400
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/sp500scan")
def api_sp500scan():
    max_price = float(request.args.get("max_price", 1.00))
    min_price = float(request.args.get("min_price", 0.01))
    min_dte   = int(request.args.get("min_dte", 7))
    max_dte   = int(request.args.get("max_dte", 45))
    min_otm   = float(request.args.get("min_otm", 5.0))
    mode      = request.args.get("mode", "lotto")
    key = f"sp500_{max_price}_{min_price}_{min_dte}_{max_dte}_{min_otm}_{mode}"
    try:
        data = cached(key, lambda: screener.scan_sp500_bullish(
            max_price, min_price, min_dte, max_dte, min_otm, mode
        ), ttl=3600)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/toppicks")
def api_toppicks():
    max_price = float(request.args.get("max_price", 1.00))
    min_price = float(request.args.get("min_price", 0.01))
    min_dte   = int(request.args.get("min_dte", 7))
    max_dte   = int(request.args.get("max_dte", 45))
    min_otm   = float(request.args.get("min_otm", 5.0))
    mode      = request.args.get("mode", "lotto")
    key = f"toppicks_{max_price}_{min_price}_{min_dte}_{max_dte}_{min_otm}_{mode}"
    try:
        data = cached(key, lambda: screener.scan_top_bullish(
            max_price, min_price, min_dte, max_dte, min_otm, mode
        ), ttl=300)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/iv_scan")
def api_iv_scan():
    source = request.args.get("source", "sp500")
    key = f"iv_scan_{source}"
    try:
        def _do_scan():
            if source == "active":
                tickers, _ = fetch_extended_tickers(count=150)
            else:
                tickers, _ = get_sp500_tickers()
            return {
                "results": iv_rank.scan_iv_rank(tickers, top_n=50),
                "total_scanned": len(tickers),
            }
        payload = cached(key, _do_scan, ttl=3600)
        return jsonify({"ok": True, "data": payload["results"], "source": source,
                        "total_scanned": payload["total_scanned"]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/technical/<symbol>")
def api_technical(symbol):
    symbol = symbol.strip().upper()
    key = f"ta_{symbol}"
    try:
        data = cached(key, lambda: technical.fetch_and_analyze(symbol), ttl=300)
        if "error" in data:
            return jsonify({"ok": False, "error": data["error"]}), 400
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/iv/<symbol>")
def api_iv(symbol):
    symbol = symbol.strip().upper()
    key = f"iv_{symbol}"
    try:
        data = cached(key, lambda: iv_rank.get_iv_rank(symbol), ttl=300)
        if "error" in data:
            return jsonify({"ok": False, "error": data["error"]}), 400
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/positions", methods=["GET"])
def api_positions_get():
    try:
        positions = tracker.get_all_positions()
        summary = tracker.get_summary(positions)
        return jsonify({"ok": True, "positions": positions, "summary": summary})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/positions", methods=["POST"])
def api_positions_post():
    data = request.get_json()
    required = ["symbol", "type", "strike", "expiry", "contracts", "entry_price"]
    for field in required:
        if field not in data:
            return jsonify({"ok": False, "error": f"Missing field: {field}"}), 400
    try:
        position = tracker.add_position(data)
        return jsonify({"ok": True, "position": position})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/positions/<position_id>/close", methods=["POST"])
def api_positions_close(position_id):
    data = request.get_json()
    exit_price = data.get("exit_price")
    if exit_price is None:
        return jsonify({"ok": False, "error": "exit_price required"}), 400
    try:
        tracker.close_position(position_id, exit_price)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/positions/<position_id>", methods=["DELETE"])
def api_positions_delete(position_id):
    try:
        tracker.delete_position(position_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/catalyst")
def api_catalyst():
    symbol       = request.args.get("symbol", "").strip().upper()
    side         = request.args.get("side", "CALL").upper()
    stock_price  = float(request.args.get("stock_price", 0))
    strike       = float(request.args.get("strike", 0))
    break_even   = float(request.args.get("break_even", 0))
    break_even_pct = float(request.args.get("break_even_pct", 0))
    expiry       = request.args.get("expiry", "")
    dte          = int(request.args.get("dte", 0))
    iv           = float(request.args.get("iv", 0))
    ta_score     = int(request.args.get("ta_score", 0))
    if not symbol:
        return jsonify({"ok": False, "error": "symbol required"}), 400
    key = f"catalyst_{symbol}_{side}_{strike}_{expiry}_{ta_score}"
    try:
        data = cached(key, lambda: catalyst.get_catalyst_analysis(
            symbol, side, stock_price, strike, break_even,
            break_even_pct, expiry, dte, iv, ta_score
        ), ttl=300)
        return jsonify({"ok": True, "data": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("\n  Options Lotto Toolkit")
    print("  ---------------------")
    print("  Open: http://localhost:5000\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
