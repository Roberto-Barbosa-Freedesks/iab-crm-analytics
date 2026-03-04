#!/usr/bin/env python3
"""
RD Station Marketing — Fetch all email marketing analytics data.
Pulls: emails, campaigns, sends, opens, clicks, bounces, unsubscribes.
"""
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent.parent
TOKEN_FILE = BASE_DIR / "credentials" / "rdstation_tokens.json"
CONFIG_FILE = BASE_DIR / "credentials" / "config.json"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

RDS_API_BASE = "https://api.rd.services/platform"

class RDStationClient:
    def __init__(self):
        self.tokens = self._load_tokens()
        self.config = self._load_config()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.tokens['access_token']}",
            "Content-Type": "application/json"
        })

    def _load_tokens(self):
        if not TOKEN_FILE.exists():
            print("❌ Token não encontrado. Execute: python3 scripts/01_rdstation_auth.py")
            exit(1)
        with open(TOKEN_FILE) as f:
            return json.load(f)

    def _load_config(self):
        with open(CONFIG_FILE) as f:
            return json.load(f)

    def _refresh_token_if_needed(self):
        config = self.config["rdstation"]
        url = "https://api.rd.services/auth/token"
        payload = {
            "client_id": config["client_id"],
            "client_secret": config["client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": self.tokens.get("refresh_token", "")
        }
        resp = requests.post(url, json=payload)
        if resp.ok:
            self.tokens = resp.json()
            with open(TOKEN_FILE, "w") as f:
                json.dump(self.tokens, f, indent=2)
            self.session.headers.update({
                "Authorization": f"Bearer {self.tokens['access_token']}"
            })
            print("  ✓ Token renovado")

    def get(self, endpoint, params=None, retry=True):
        url = f"{RDS_API_BASE}/{endpoint}"
        resp = self.session.get(url, params=params)
        if resp.status_code == 401 and retry:
            self._refresh_token_if_needed()
            return self.get(endpoint, params=params, retry=False)
        if not resp.ok:
            print(f"  ⚠ Error {resp.status_code} for {endpoint}: {resp.text[:200]}")
            return None
        return resp.json()

    def get_paginated(self, endpoint, params=None, page_size=200):
        """Fetch all pages from a paginated endpoint."""
        results = []
        page = 1
        params = params or {}
        params["page_size"] = page_size

        while True:
            params["page"] = page
            data = self.get(endpoint, params=params)
            if not data:
                break

            # Handle different response structures
            items = (data.get("platform_emails") or
                     data.get("emails") or
                     data.get("segmentations") or
                     data.get("contacts") or
                     (data if isinstance(data, list) else []))

            if isinstance(data, dict) and "total" in data:
                total = data.get("total", 0)
                print(f"    Page {page}: {len(items)} items (total: {total})")

            results.extend(items if isinstance(items, list) else [])

            # Check pagination
            has_more = (
                (isinstance(data, dict) and data.get("next_page")) or
                (isinstance(items, list) and len(items) == page_size)
            )
            if not has_more:
                break
            page += 1
            time.sleep(0.3)  # Rate limiting

        return results

def fetch_all_data():
    client = RDStationClient()
    data = {}

    print("\n" + "=" * 60)
    print("  RD Station Marketing — Coletando dados")
    print("=" * 60)

    # 1. List all email campaigns/sends
    print("\n📧 Buscando emails/campanhas...")
    emails = client.get_paginated("emails")
    data["emails"] = emails
    print(f"   → {len(emails)} emails encontrados")

    # 2. Email analytics (marketing sends statistics)
    print("\n📊 Buscando estatísticas de email marketing...")
    email_analytics = client.get("analytics/emails", params={
        "per_page": 200,
        "order": "desc"
    })
    data["email_analytics"] = email_analytics
    if email_analytics:
        print(f"   → Dados de analytics obtidos")

    # 3. Workflow email analytics (automation)
    print("\n⚙️  Buscando analytics de automações...")
    workflow_analytics = client.get("analytics/workflow_emails", params={
        "per_page": 200
    })
    data["workflow_analytics"] = workflow_analytics
    if workflow_analytics:
        print(f"   → Dados de automações obtidos")

    # 4. Segmentations
    print("\n🎯 Buscando segmentações...")
    segmentations = client.get("segmentations")
    data["segmentations"] = segmentations
    if segmentations:
        segs = segmentations.get("segmentations", segmentations if isinstance(segmentations, list) else [])
        print(f"   → {len(segs)} segmentações encontradas")

    # 5. Landing pages & conversions funnel
    print("\n📈 Buscando analytics do funil...")
    funnel = client.get("analytics/funnel")
    data["funnel"] = funnel
    if funnel:
        print(f"   → Dados do funil obtidos")

    # 6. Contacts summary (top-level stats)
    print("\n👥 Buscando resumo de contatos...")
    contacts_summary = client.get("contacts", params={"per_page": 1})
    data["contacts_summary"] = contacts_summary
    if contacts_summary:
        total = contacts_summary.get("total", "N/A")
        print(f"   → Total de contatos: {total}")

    # 7. Email sends detail (per email stats)
    if emails:
        print(f"\n📬 Buscando métricas detalhadas para {min(len(emails), 100)} emails...")
        email_details = []
        for i, email in enumerate(emails[:100]):  # Limit to 100 most recent
            email_id = email.get("id") or email.get("uuid")
            if email_id:
                detail = client.get(f"emails/{email_id}")
                if detail:
                    email_details.append(detail)
                if (i + 1) % 10 == 0:
                    print(f"    Processado {i+1}/{min(len(emails), 100)}...")
                time.sleep(0.2)
        data["email_details"] = email_details
        print(f"   → {len(email_details)} emails com detalhes")

    # Save all data
    output_file = DATA_DIR / "rdstation_raw_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n✅ Dados salvos em: {output_file}")
    print(f"   Tamanho: {output_file.stat().st_size / 1024:.1f} KB")

    return data

if __name__ == "__main__":
    fetch_all_data()
