#!/usr/bin/env python3
"""
GA4 OAuth2 Login — Authenticate with any Google account that has GA4 access.
Opens browser → user signs in → token saved → lists GA4 properties.
"""
import json
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient

BASE_DIR = Path(__file__).parent.parent
CLIENT_SECRETS = BASE_DIR / "credentials" / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "credentials" / "ga4_token.json"
PROPERTY_ID_FILE = BASE_DIR / "credentials" / "ga4_property_id.txt"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
]

def main():
    print("=" * 60)
    print("  GA4 OAuth2 Authentication")
    print("=" * 60)
    print("\nUma janela do browser vai abrir.")
    print("Faça login com: adalgisa.caruso@ivoire.ag")
    print("(conta que tem acesso ao GA4 do IAB Brasil)\n")

    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRETS),
        scopes=SCOPES
    )

    # Run local server to capture callback
    creds = flow.run_local_server(
        host="127.0.0.1",
        port=8080,
        prompt="consent",
        authorization_prompt_message="\nAbrindo browser para autenticação GA4...\n",
        success_message="✓ Autenticação concluída! Pode fechar esta aba.",
        open_browser=True
    )

    # Save token
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes) if creds.scopes else SCOPES
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    print(f"\n✅ Token salvo em: {TOKEN_FILE}")

    # List GA4 properties
    print("\n📊 Propriedades GA4 acessíveis com esta conta:")
    print("-" * 60)

    client = AnalyticsAdminServiceClient(credentials=creds)
    iab_props = []

    try:
        for account in client.list_account_summaries():
            for prop in account.property_summaries:
                prop_id = prop.property.split("/")[-1]
                print(f"  [{prop_id}] {prop.display_name} (Conta: {account.display_name})")
                if "iab" in prop.display_name.lower() or "iab" in account.display_name.lower():
                    iab_props.append((prop_id, prop.display_name))
    except Exception as e:
        print(f"Erro ao listar propriedades: {e}")

    if iab_props:
        print(f"\n🎯 Propriedades IAB identificadas:")
        for pid, name in iab_props:
            print(f"   Property ID: {pid} — {name}")

        # Auto-save the first IAB property ID
        with open(PROPERTY_ID_FILE, "w") as f:
            f.write(iab_props[0][0])
        print(f"\n✅ Property ID {iab_props[0][0]} salvo automaticamente.")
    else:
        pid = input("\nNenhuma propriedade IAB encontrada automaticamente.\nDigite o Property ID correto: ").strip()
        with open(PROPERTY_ID_FILE, "w") as f:
            f.write(pid)
        print(f"✅ Property ID {pid} salvo.")

if __name__ == "__main__":
    main()
