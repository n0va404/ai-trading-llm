#!/usr/bin/env python3
"""
Remote Control EA - HTTP to ZeroMQ Bridge
========================================

This bridge connects HTTP requests (curl) to ZeroMQ for MetaTrader 5 communication.

Setup:
1. Install dependencies: pip install pyzmq flask flask-cors
2. Start MT5 with RemoteControlEA loaded and ZeroMQ enabled
3. Run this bridge: python bridge.py
4. Use curl commands to interact with MT5

Author: Nova & Fath
Version: 1.0
"""

import zmq
import json
import time
import sys
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from datetime import datetime

# ============================================================================
# Configuration
# ============================================================================

# ZeroMQ connection settings
ZMQ_HOST = "localhost"      # MT5 machine IP (localhost if same machine)
ZMQ_PORT = 5555             # Must match RemoteControlEA setting
ZMQ_TIMEOUT = 5000          # milliseconds

# HTTP server settings
HTTP_HOST = "0.0.0.0"       # Listen on all interfaces
HTTP_PORT = 8080            # HTTP port for curl commands

# Security settings
API_KEY = None              # Set to string for API key auth, None to disable
ALLOWED_IPS = ["192.168.1.0/24", "127.0.0.1", "192.168.208.1"]          # Set to list of IPs for IP whitelist, None to disable
# Example: ALLOWED_IPS = ["192.168.1.0/24", "127.0.0.1"]

# Request logging
LOG_REQUESTS = True

# ============================================================================
# Flask App Setup
# ============================================================================

app = Flask(__name__)
CORS(app)

# Global ZeroMQ context and socket
zmq_context = None
zmq_socket = None
zmq_connected = False

def init_zmq():
    """Initialize ZeroMQ connection to MT5"""
    global zmq_context, zmq_socket, zmq_connected
    
    try:
        zmq_context = zmq.Context()
        zmq_socket = zmq_context.socket(zmq.REQ)
        zmq_socket.setsockopt(zmq.LINGER, 0)
        zmq_socket.setsockopt(zmq.RCVTIMEO, ZMQ_TIMEOUT)
        zmq_socket.setsockopt(zmq.SNDTIMEO, ZMQ_TIMEOUT)

        # --- ADD THESE LINES FOR KEEPALIVE ---
        # Checks connection every 60 seconds to keep it alive
        zmq_socket.setsockopt(zmq.TCP_KEEPALIVE, 1)
        zmq_socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
        zmq_socket.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 60)
        # -------------------------------------
        
        endpoint = f"tcp://{ZMQ_HOST}:{ZMQ_PORT}"
        zmq_socket.connect(endpoint)
        zmq_connected = True
        
        print(f"✅ Connected to MT5 at {endpoint}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to MT5: {e}")
        zmq_connected = False
        return False

def send_to_mt5(command_dict):
    """Send command to MT5 and return response"""
    global zmq_socket, zmq_connected
    
    if not zmq_connected:
        return {"success": False, "error": "Not connected to MT5"}
    
    try:
        # Send request
        zmq_socket.send_json(command_dict)
        
        # Receive response
        if zmq_socket.poll(ZMQ_TIMEOUT):
            response = zmq_socket.recv_json()
            return response
        else:
            return {"success": False, "error": "Timeout waiting for MT5"}
            
    except zmq.error.Again:
        # Timeout - recreate socket
        zmq_connected = False
        zmq_socket.close()
        init_zmq()
        return {"success": False, "error": "Request timeout"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_auth():
    """Check API key authentication"""
    if API_KEY is None:
        return True
    
    key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if key != API_KEY:
        return False
    return True

def log_request(endpoint, data):
    """Log request for debugging"""
    if LOG_REQUESTS:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {endpoint}: {json.dumps(data, indent=2)[:200]}")

# ============================================================================
# API Routes
# ============================================================================

@app.route('/')
def index():
    """API documentation"""
    return jsonify({
        "name": "MT5 Remote Control Bridge",
        "version": "1.0",
        "endpoints": {
            "/ping": "Check if MT5 is responding",
            "/account": "Get account information",
            "/positions": "Get open positions",
            "/orders": "Get pending orders",
            "/symbols": "Get available symbols",
            "/tick/<symbol>": "Get current tick for symbol",
            "/ticks/<symbol>": "Get last N ticks (param: count)",
            "/ohlc/<symbol>": "Get OHLC data (params: tf, count)",
            "/place": "Place order (POST)",
            "/pending": "Place pending order (POST)",
            "/close": "Close position (POST)",
            "/close_all": "Close all positions (POST)",
            "/modify": "Modify position SL/TP (POST)"
        },
        "connected": zmq_connected
    })

@app.route('/ping')
def ping():
    """Ping MT5 to check connection"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    response = send_to_mt5({"cmd": "ping", "auth": "ignored"})
    return jsonify(response)

@app.route('/account')
def account():
    """Get account information"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    log_request("/account", {})
    response = send_to_mt5({"cmd": "account", "auth": ""})
    return jsonify(response)

@app.route('/positions')
def positions():
    """Get open positions"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    log_request("/positions", {})
    response = send_to_mt5({"cmd": "positions", "auth": ""})
    return jsonify(response)

@app.route('/orders')
def orders():
    """Get pending orders"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    log_request("/orders", {})
    response = send_to_mt5({"cmd": "orders", "auth": ""})
    return jsonify(response)

@app.route('/symbols')
def symbols():
    """Get available symbols"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    log_request("/symbols", {})
    response = send_to_mt5({"cmd": "symbols", "auth": ""})
    return jsonify(response)

@app.route('/tick/<symbol>')
def tick(symbol):
    """Get current tick data for symbol"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    data = {"cmd": "tick", "auth": "", "symbol": symbol}
    log_request("/tick", data)
    response = send_to_mt5(data)
    return jsonify(response)

@app.route('/ohlc/<symbol>')
def ohlc(symbol):
    """Get OHLC data for symbol"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    tf = request.args.get('tf', '60')      # Timeframe in minutes
    count = request.args.get('count', '100')  # Number of bars
    
    data = {
        "cmd": "ohlc",
        "auth": "",
        "symbol": symbol,
        "tf": int(tf),
        "count": int(count)
    }
    log_request("/ohlc", data)
    response = send_to_mt5(data)
    return jsonify(response)

@app.route('/ticks/<symbol>')
def ticks_history(symbol):
    """Get last N ticks for a symbol"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    count = request.args.get('count', '10')
    
    data = {
        "cmd": "ticks", 
        "auth": "", 
        "symbol": symbol,
        "count": int(count)
    }
    log_request("/ticks", data)
    response = send_to_mt5(data)
    return jsonify(response)

@app.route('/pending', methods=['POST'])
def pending():
    """Place a pending order"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    params = request.get_json() or request.form.to_dict() or {}
    
    # Order Type Mapping (String to MT5 Integer)
    ORDER_TYPES = {
        "BUY_LIMIT": 2,
        "SELL_LIMIT": 3,
        "BUY_STOP": 4,
        "SELL_STOP": 5
    }
    
    type_raw = params.get('type', '')
    type_int = 0
    
    # Handle string inputs (e.g., "buy_limit" or "BUY_LIMIT")
    if isinstance(type_raw, str):
        type_str = type_raw.upper()
        if type_str in ORDER_TYPES:
            type_int = ORDER_TYPES[type_str]
        else:
            return jsonify({"success": False, "error": f"Invalid order type: {type_raw}"}), 400
    else:
        type_int = int(type_raw)

    data = {
        "cmd": "pending",
        "auth": params.get('auth', ''),
        "symbol": params.get('symbol', ''),
        "type": type_int,
        "volume": float(params.get('volume', 0.01)),
        "price": float(params.get('price', 0)),
        "sl": float(params.get('sl', 0)),
        "tp": float(params.get('tp', 0)),
        "comment": params.get('comment', '')
    }
    
    log_request("/pending", data)
    response = send_to_mt5(data)
    return jsonify(response)

@app.route('/place', methods=['POST'])
def place():
    """Place new order"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    params = request.get_json() or request.form.to_dict() or {}
    
    data = {
        "cmd": "place",
        "auth": params.get('auth', ''),
        "symbol": params.get('symbol', ''),
        "type": int(params.get('type', 0)),
        "volume": float(params.get('volume', 0.01)),
        "price": float(params.get('price', 0)),
        "sl": float(params.get('sl', 0)),
        "tp": float(params.get('tp', 0)),
        "comment": params.get('comment', '')
    }
    
    log_request("/place", data)
    response = send_to_mt5(data)
    return jsonify(response)

@app.route('/close', methods=['POST'])
def close():
    """Close specific position"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    params = request.get_json() or request.form.to_dict() or {}
    
    data = {
        "cmd": "close",
        "auth": params.get('auth', ''),
        "ticket": int(params.get('ticket', 0)),
        "volume": float(params.get('volume', 0))
    }
    
    log_request("/close", data)
    response = send_to_mt5(data)
    return jsonify(response)

@app.route('/close_all', methods=['POST'])
def close_all():
    """Close all positions (optionally filtered by symbol)"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    params = request.get_json() or request.form.to_dict() or {}
    
    data = {
        "cmd": "close_all",
        "auth": params.get('auth', ''),
        "symbol": params.get('symbol', '')
    }
    
    log_request("/close_all", data)
    response = send_to_mt5(data)
    return jsonify(response)

@app.route('/modify', methods=['POST'])
def modify():
    """Modify position SL/TP"""
    if not check_auth():
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    
    params = request.get_json() or request.form.to_dict() or {}
    
    data = {
        "cmd": "modify",
        "auth": params.get('auth', ''),
        "ticket": int(params.get('ticket', 0)),
        "sl": float(params.get('sl', -1)),
        "tp": float(params.get('tp', -1))
    }
    
    log_request("/modify", data)
    response = send_to_mt5(data)
    return jsonify(response)

# ============================================================================
# Health check endpoint
# ============================================================================

@app.route('/health')
def health():
    """Health check endpoint"""
    status = {
        "status": "healthy" if zmq_connected else "disconnected",
        "mt5_connection": zmq_connected,
        "timestamp": datetime.now().isoformat()
    }
    code = 200 if zmq_connected else 503
    return jsonify(status), code

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("MT5 Remote Control - HTTP Bridge")
    print("=" * 60)
    print(f"ZeroMQ:  tcp://{ZMQ_HOST}:{ZMQ_PORT}")
    print(f"HTTP:    http://{HTTP_HOST}:{HTTP_PORT}")
    print(f"Auth:    {'Enabled' if API_KEY else 'Disabled'}")
    print("=" * 60)
    
    # Initialize ZeroMQ
    if not init_zmq():
        print("\n⚠️  Warning: Could not connect to MT5")
        print("   Make sure RemoteControlEA is running in MT5")
        print("   The bridge will keep trying to reconnect")
    
    # Start HTTP server
    print(f"\n🚀 Starting HTTP server on {HTTP_HOST}:{HTTP_PORT}")
    print("   Try: curl http://localhost:8080/ping")
    print("=" * 60)
    
    # Run Flask with threaded support for concurrent requests
    app.run(host=HTTP_HOST, port=HTTP_PORT, threaded=True, debug=False)
