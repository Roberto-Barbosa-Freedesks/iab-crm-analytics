#!/usr/bin/env python3
"""
Fetch all data from RD Station CRM via MCP.
Extracts: contacts, deals, campaigns, sources, funnels, tasks, users.
"""
import asyncio
import json
from pathlib import Path
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL = "https://mcp.rdstationmentor.com/crm/mcp?key=019cb63e-2cac-7c02-b51f-632b00407a7b"
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

async def call_tool(session, tool_name, args=None):
    result = await session.call_tool(tool_name, arguments=args or {})
    if result.content:
        text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
        try:
            return json.loads(text)
        except:
            return text
    return None

async def fetch_paginated(session, tool_name, args=None, page_size=200):
    """Fetch all pages from a paginated CRM tool."""
    all_items = []
    page_num = 1
    args = args or {}

    while True:
        params = {**args, "page": {"number": page_num, "size": page_size}}
        result = await call_tool(session, tool_name, params)

        if not result:
            break

        # Handle different response shapes
        items = []
        if isinstance(result, list):
            items = result
        elif isinstance(result, dict):
            # Try common response keys
            for key in ["contacts", "deals", "campaigns", "tasks", "organizations",
                        "sources", "segments", "products", "users", "lost_reasons",
                        "custom_fields", "funnels", "funnel_stages", "notes"]:
                if key in result:
                    items = result[key]
                    break
            if not items and "data" in result:
                items = result["data"]
            elif not items:
                items = [result] if result else []

        if not items:
            break

        all_items.extend(items)
        print(f"    página {page_num}: +{len(items)} (total: {len(all_items)})")

        # Check if has more pages
        total = None
        if isinstance(result, dict):
            total = result.get("total") or result.get("total_count")

        if total and len(all_items) >= total:
            break
        if len(items) < page_size:
            break

        page_num += 1
        await asyncio.sleep(0.2)

    return all_items

async def main():
    print("=" * 60)
    print("  RD Station CRM — Coleta via MCP")
    print("=" * 60)

    data = {}

    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✓ Conectado ao MCP RD Station CRM\n")

            # 1. Users
            print("👥 Buscando usuários...")
            users = await fetch_paginated(session, "users_list")
            data["users"] = users
            print(f"   → {len(users)} usuários\n")

            # 2. Contacts (with email data)
            print("📧 Buscando contatos...")
            contacts = await fetch_paginated(session, "contacts_list", page_size=200)
            data["contacts"] = contacts
            print(f"   → {len(contacts)} contatos\n")

            # 3. Deals / Oportunidades
            print("💼 Buscando deals/oportunidades...")
            deals = await fetch_paginated(session, "deals_list", page_size=200)
            data["deals"] = deals
            print(f"   → {len(deals)} deals\n")

            # 4. Campaigns (CRM campaigns)
            print("📣 Buscando campanhas CRM...")
            campaigns = await fetch_paginated(session, "campaigns_list")
            data["campaigns"] = campaigns
            print(f"   → {len(campaigns)} campanhas\n")

            # 5. Funnels / Pipelines
            print("🔄 Buscando funis de vendas...")
            funnels = await call_tool(session, "funnel_list")
            data["funnels"] = funnels
            if isinstance(funnels, list):
                print(f"   → {len(funnels)} funis")
                # Get stages for each funnel
                funnel_stages = {}
                for funnel in funnels[:5]:
                    fid = funnel.get("id")
                    if fid:
                        stages = await call_tool(session, "funnel_stages_list", {"pipeline_id": fid})
                        funnel_stages[fid] = stages
                data["funnel_stages"] = funnel_stages
            print()

            # 6. Deal sources (lead origins)
            print("🔍 Buscando fontes de leads...")
            sources = await fetch_paginated(session, "sources_list")
            data["sources"] = sources
            print(f"   → {len(sources)} fontes\n")

            # 7. Lost reasons
            print("❌ Buscando motivos de perda...")
            lost_reasons = await fetch_paginated(session, "lost_reasons_list")
            data["lost_reasons"] = lost_reasons
            print(f"   → {len(lost_reasons)} motivos\n")

            # 8. Segments (organizations)
            print("🏢 Buscando segmentos...")
            segments = await fetch_paginated(session, "segments_list")
            data["segments"] = segments
            print(f"   → {len(segments)} segmentos\n")

            # 9. Organizations
            print("🏛️  Buscando organizações...")
            orgs = await fetch_paginated(session, "organizations_list", page_size=200)
            data["organizations"] = orgs
            print(f"   → {len(orgs)} organizações\n")

            # 10. Tasks (recent)
            print("📋 Buscando tarefas recentes...")
            tasks = await fetch_paginated(session, "tasks_list")
            data["tasks"] = tasks
            print(f"   → {len(tasks)} tarefas\n")

            # 11. Custom fields
            print("⚙️  Buscando campos customizados...")
            custom_fields = await fetch_paginated(session, "custom_fields_list")
            data["custom_fields"] = custom_fields
            print(f"   → {len(custom_fields)} campos customizados\n")

            # 12. Products
            print("📦 Buscando produtos...")
            products = await fetch_paginated(session, "products_list")
            data["products"] = products
            print(f"   → {len(products)} produtos\n")

            # 13. Teams
            print("👨‍👩‍👧 Buscando equipes...")
            teams = await call_tool(session, "teams_list")
            data["teams"] = teams
            print(f"   → {len(teams) if isinstance(teams, list) else '?'} equipes\n")

            # 14. Sample deal details (for deeper analysis)
            if deals:
                print("🔎 Coletando detalhes de deals (amostra)...")
                deal_details = []
                sample = deals[:50]  # first 50 for detail
                for i, deal in enumerate(sample):
                    did = deal.get("id")
                    if did:
                        detail = await call_tool(session, "deals_get", {"id": did})
                        if detail:
                            deal_details.append(detail)
                    if (i+1) % 10 == 0:
                        print(f"    {i+1}/{len(sample)}...")
                    await asyncio.sleep(0.1)
                data["deal_details"] = deal_details
                print(f"   → {len(deal_details)} deals detalhados\n")

    # Save
    output = DATA_DIR / "crm_raw_data.json"
    with open(output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    size_kb = output.stat().st_size / 1024
    print(f"✅ Dados CRM salvos: {output}")
    print(f"   Tamanho: {size_kb:.1f} KB")
    print(f"\nResumo:")
    for k, v in data.items():
        count = len(v) if isinstance(v, list) else ("dict" if isinstance(v, dict) else "?")
        print(f"  {k}: {count}")

    return data

if __name__ == "__main__":
    asyncio.run(main())
