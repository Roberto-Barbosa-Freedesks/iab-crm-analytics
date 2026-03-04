#!/usr/bin/env python3
"""
RD Station Marketing - OAuth2 Authentication Flow
Generates access_token and refresh_token for the Marketing API.
"""
import json
import os
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import requests

CREDENTIALS_FILE = Path(__file__).parent.parent / "credentials" / "config.json"
TOKEN_FILE = Path(__file__).parent.parent / "credentials" / "rdstation_tokens.json"
REDIRECT_URI = "http://localhost:8080/callback"

def load_config():
    if not CREDENTIALS_FILE.exists():
        print("❌ Arquivo credentials/config.json não encontrado!")
        print("   Siga o SETUP_GUIDE.md para configurar as credenciais.")
        exit(1)
    with open(CREDENTIALS_FILE) as f:
        return json.load(f)

class CallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            CallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"""
            <html><body style="font-family:sans-serif;text-align:center;padding:50px">
            <h2>&#10003; Autoriza&ccedil;&atilde;o conclu&iacute;da!</h2>
            <p>Pode fechar esta janela e voltar ao terminal.</p>
            </body></html>
            """)
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress server logs

def get_authorization_url(client_id):
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code"
    }
    base_url = "https://app.rdstation.com.br/api/platform/auth/dialog"
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(client_id, client_secret, auth_code):
    url = "https://api.rd.services/auth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()

def main():
    config = load_config()
    client_id = config["rdstation"]["client_id"]
    client_secret = config["rdstation"]["client_secret"]

    if not client_id or client_id == "SEU_CLIENT_ID":
        print("❌ Configure o client_id no arquivo credentials/config.json")
        exit(1)

    print("=" * 60)
    print("  RD Station Marketing — Autenticação OAuth2")
    print("=" * 60)
    print("\n1. Abrindo o navegador para autorização...")

    auth_url = get_authorization_url(client_id)
    webbrowser.open(auth_url)
    print(f"\n   URL: {auth_url}")

    print("\n2. Aguardando callback na porta 8080...")
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.handle_request()

    if not CallbackHandler.auth_code:
        print("❌ Não foi possível obter o código de autorização.")
        exit(1)

    print("\n3. Trocando código por tokens...")
    tokens = exchange_code_for_token(client_id, client_secret, CallbackHandler.auth_code)

    TOKEN_FILE.parent.mkdir(exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

    print(f"\n✅ Tokens salvos em: {TOKEN_FILE}")
    print(f"   access_token: {tokens.get('access_token', '')[:20]}...")
    print(f"   expires_in: {tokens.get('expires_in', 'N/A')} segundos")

if __name__ == "__main__":
    main()
