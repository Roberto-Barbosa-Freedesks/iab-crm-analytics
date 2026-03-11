#!/usr/bin/env python3
"""
RD Station Marketing — Parse manual CSV exports.
Reads all period folders from rdstation-marketing-data/, normalises and
merges into a single JSON file: data/rdstation_email_exports.json

Exported periods:
  01-2025 a 02-2025  (Jan–Feb 2025)   ⚠  Entregues=0 (bug do RD Station)
  03-2025 a 05-2025  (Mar–Mai 2025)
  06-2025 a 08-2025  (Jun–Ago 2025)
  09-2025 a 11-2025  (Set–Nov 2025)
  12-2025 a 02-2026  (Dez 2025–Fev 2026)

Data quality note:
  Jan/Feb 2025 have Entregues=0 — RD Station did not populate delivery counts
  in that export period. For those campaigns we use Leads_selecionados as the
  denominator when computing open/click rates, and flag them as estimated.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from collections import defaultdict

BASE_DIR    = Path(__file__).parent.parent
EXPORTS_DIR = BASE_DIR / "rdstation-marketing-data"
DATA_DIR    = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── PERIOD ORDERING ───────────────────────────────────────────────────────────
PERIODS = [
    "01-2025 a 02-2025",
    "03-2025 a 05-2025",
    "06-2025 a 08-2025",
    "09-2025 a 11-2025",
    "12-2025 a 02-2026",
]

# ── HELPERS ───────────────────────────────────────────────────────────────────

def find_csv(period: str, keyword: str) -> Path | None:
    d = EXPORTS_DIR / period
    for f in d.iterdir():
        if keyword in f.name.lower() and f.suffix == ".csv":
            return f
    return None

def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def parse_dt(s: str) -> datetime | None:
    """Parse '2025-03-10 09:00:00 -0300' style timestamps."""
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            # Strip timezone manually if needed
            clean = s[:19]
            return datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return None

def safe_int(v) -> int:
    try:
        return int(v or 0)
    except (ValueError, TypeError):
        return 0

def safe_float(v) -> float:
    try:
        return float(v or 0)
    except (ValueError, TypeError):
        return 0.0

def pct(num: int, den: int, decimals: int = 2) -> float:
    return round(num / den * 100, decimals) if den else 0.0

# ── PARSE EMAILS ──────────────────────────────────────────────────────────────

def parse_emails() -> list[dict]:
    """Return normalised list of individual email campaigns, deduplicated."""
    seen   = set()
    emails = []

    for period in PERIODS:
        path = find_csv(period, "email")
        if not path:
            print(f"  ⚠ email CSV not found for {period}")
            continue

        for row in read_csv(path):
            dt = parse_dt(row.get("Data de envio", ""))
            if not dt:
                continue

            # Deduplication key
            key = (row.get("Data de envio", "")[:19], row.get("Nome do email", "").strip())
            if key in seen:
                continue
            seen.add(key)

            selecionados = safe_int(row.get("Leads selecionados"))
            entregues    = safe_int(row.get("Entregues"))
            bounce       = safe_int(row.get("Bounce (únicos)"))
            opens        = safe_int(row.get("Aberturas (únicas)"))
            clicks       = safe_int(row.get("Cliques (únicos)"))
            unsub        = safe_int(row.get("Descadastrados"))
            spam         = safe_int(row.get("Marcados como spam"))

            # Jan/Feb 2025: Entregues not populated — use Leads selecionados as estimate
            # Only flag as estimated for meaningful sends (> 100 leads); ignore test/1-lead sends
            data_quality = "ok"
            denominator  = entregues
            if entregues == 0 and selecionados > 100:
                denominator  = selecionados
                data_quality = "entregues_estimated"

            open_rate     = pct(opens,  denominator)
            ctr           = pct(clicks, denominator)
            ctor          = pct(clicks, opens) if opens else 0.0
            delivery_rate = pct(entregues, selecionados) if selecionados else 0.0

            emails.append({
                "sent_at":         dt.strftime("%Y-%m-%d %H:%M:%S"),
                "year_month":      dt.strftime("%Y-%m"),
                "name":            row.get("Nome do email", "").strip(),
                "period_label":    period,
                "selecionados":    selecionados,
                "entregues":       entregues,
                "bounce":          bounce,
                "opens":           opens,
                "clicks":          clicks,
                "unsub":           unsub,
                "spam":            spam,
                "open_rate":       open_rate,
                "ctr":             ctr,
                "ctor":            ctor,
                "delivery_rate":   delivery_rate,
                "data_quality":    data_quality,
            })

    emails.sort(key=lambda e: e["sent_at"])
    return emails

# ── MONTHLY AGGREGATES ────────────────────────────────────────────────────────

def aggregate_monthly(emails: list[dict]) -> list[dict]:
    m: dict[str, dict] = defaultdict(lambda: {
        "year_month": "", "campaigns": 0,
        "selecionados": 0, "entregues": 0, "bounce": 0,
        "opens": 0, "clicks": 0, "unsub": 0, "spam": 0,
        "has_estimated": False,
    })

    for e in emails:
        ym = e["year_month"]
        d  = m[ym]
        d["year_month"]    = ym
        d["campaigns"]    += 1
        d["selecionados"] += e["selecionados"]
        d["entregues"]    += e["entregues"]
        d["bounce"]       += e["bounce"]
        d["opens"]        += e["opens"]
        d["clicks"]       += e["clicks"]
        d["unsub"]        += e["unsub"]
        d["spam"]         += e["spam"]
        if e["data_quality"] == "entregues_estimated":
            d["has_estimated"] = True

    result = []
    for ym in sorted(m.keys()):
        d = m[ym]
        # Use selecionados as denom for months with estimated delivery
        denom        = d["selecionados"] if d["has_estimated"] else d["entregues"]
        denom_label  = "selecionados" if d["has_estimated"] else "entregues"
        d["open_rate"]     = pct(d["opens"],  denom)
        d["ctr"]           = pct(d["clicks"], denom)
        d["ctor"]          = pct(d["clicks"], d["opens"]) if d["opens"] else 0.0
        d["delivery_rate"] = pct(d["entregues"], d["selecionados"]) if d["selecionados"] else 0.0
        d["denom_label"]   = denom_label
        result.append(d)

    return result

# ── CHANNEL ANALYSIS ──────────────────────────────────────────────────────────

CHANNEL_MAP = {
    "Busca Orgânica":    "organica",
    "Tráfego Direto":    "direto",
    "Midia Paga":        "pago",
    "Referencias":       "referencia",
    "Email":             "email",
    "Outros Canais":     "outros",
    "Redes Sociais":     "social",
    "Display":           "display",
    "Outras Publicidades": "outras_pub",
    "Desconhecido":      "desconhecido",
}

def parse_channel_analysis() -> list[dict]:
    """Parse funnel by channel across all periods."""
    records = []
    for period in PERIODS:
        path = find_csv(period, "analise_canais")
        if not path:
            continue
        for row in read_csv(path):
            canal = row.get("Canal", "").strip()
            records.append({
                "period":      period,
                "channel":     canal,
                "channel_key": CHANNEL_MAP.get(canal, "outro"),
                "visits":      safe_int(row.get("Visitas")),
                "conv_rate":   safe_float(row.get("Taxa de Visitantes para Conversões")),
                "conversoes":  safe_int(row.get("Conversões")),
            })
    return records

def aggregate_channels_total(channel_records: list[dict]) -> list[dict]:
    """Sum visits + conversoes across all periods per channel."""
    agg: dict[str, dict] = defaultdict(lambda: {
        "channel": "", "channel_key": "", "visits": 0, "conversoes": 0
    })
    for r in channel_records:
        k = r["channel_key"]
        agg[k]["channel"]     = r["channel"]
        agg[k]["channel_key"] = k
        agg[k]["visits"]      += r["visits"]
        agg[k]["conversoes"]  += r["conversoes"]

    total_visits = sum(v["visits"] for v in agg.values())
    result = []
    for d in agg.values():
        d["visit_share"] = pct(d["visits"], total_visits)
        d["conv_rate"]   = pct(d["conversoes"], d["visits"])
        result.append(d)
    result.sort(key=lambda x: x["visits"], reverse=True)
    return result

# ── CAMPAIGN CATEGORIES (RDS-based) ───────────────────────────────────────────

def categorize_rds(name: str) -> str:
    n = name.lower()
    if any(k in n for k in ["adtech", "ia summit", "forum", "fórum", "bsb", "evento", "eventos", "régua"]):
        return "Eventos"
    elif any(k in n for k in ["relgov", "boletim de transparência", "relações governamentais"]):
        return "RelGov"
    elif any(k in n for k in ["curso", "masterclass", "certif", "educação", "in company"]):
        return "Educação"
    elif any(k in n for k in ["media solutions", "iab media"]):
        return "Mídia Solutions"
    elif any(k in n for k in ["iab news", "iab trends", "data stories", "radar iab", "follow iab",
                               "newsletter", "institucional", "associação", "patrocínio"]):
        return "Institucional / Newsletter"
    else:
        return "Outros"

def aggregate_campaign_categories(emails: list[dict]) -> list[dict]:
    """Aggregate emails by RDS category — opens, clicks, campaigns count."""
    agg: dict[str, dict] = defaultdict(lambda: {
        "name": "", "campaigns": 0, "selecionados": 0, "entregues": 0,
        "opens": 0, "clicks": 0
    })
    for e in emails:
        cat = e.get("category", "Outros")
        agg[cat]["name"]         = cat
        agg[cat]["campaigns"]   += 1
        agg[cat]["selecionados"]+= e["selecionados"]
        agg[cat]["entregues"]   += e["entregues"]
        agg[cat]["opens"]       += e["opens"]
        agg[cat]["clicks"]      += e["clicks"]

    result = []
    for d in agg.values():
        denom = d["entregues"] if d["entregues"] > 0 else d["selecionados"]
        d["open_rate"] = pct(d["opens"],  denom)
        d["ctor"]      = pct(d["clicks"], d["opens"]) if d["opens"] else 0.0
        result.append(d)
    result.sort(key=lambda x: x["opens"], reverse=True)
    return result

# ── FORMS ─────────────────────────────────────────────────────────────────────

def parse_forms_latest() -> list[dict]:
    """Use latest period's form data as current snapshot."""
    path = find_csv(PERIODS[-1], "forms")
    if not path:
        return []
    result = []
    for row in read_csv(path):
        name = row.get("Nome do formulário", "").strip()
        if not name or name == "-":
            continue
        result.append({
            "name":        name,
            "visitors":    safe_int(row.get("Visitantes")),
            "leads":       safe_int(row.get("Leads")),
            "conv_rate":   safe_float(row.get("Taxa de Visitantes para Leads")),
        })
    result.sort(key=lambda x: x["visitors"], reverse=True)
    return result

def parse_forms_by_period() -> list[dict]:
    """Parse all forms across all periods, returning per-period lead counts."""
    MAILING_KEY = "mailing home site"
    result = []
    totals_by_form: dict[str, dict] = defaultdict(lambda: {
        "visitors": 0, "leads": 0
    })
    for period in PERIODS:
        path = find_csv(period, "forms")
        if not path:
            continue
        period_leads     = 0
        period_visitors  = 0
        for row in read_csv(path):
            name = row.get("Nome do formulário", "").strip()
            if not name:
                continue
            v = safe_int(row.get("Visitantes"))
            l = safe_int(row.get("Leads"))
            totals_by_form[name]["visitors"] += v
            totals_by_form[name]["leads"]    += l
            if MAILING_KEY in name.lower():
                period_leads    += l
                period_visitors += v
        result.append({
            "period":            period,
            "mailing_visitors":  period_visitors,
            "mailing_leads":     period_leads,
        })
    # Attach grand totals
    return result, dict(totals_by_form)

# ── LANDING PAGES ─────────────────────────────────────────────────────────────

def parse_landing_pages_all() -> list[dict]:
    """Aggregate landing page visitors across all periods (cumulative)."""
    agg: dict[str, dict] = defaultdict(lambda: {
        "name": "", "visitors": 0, "leads": 0
    })
    for period in PERIODS:
        path = find_csv(period, "landing_pages")
        if not path:
            continue
        for row in read_csv(path):
            name = row.get("Nome da Landing Page", "").strip()
            if not name:
                continue
            agg[name]["name"]     = name
            agg[name]["visitors"] += safe_int(row.get("Visitantes"))
            agg[name]["leads"]    += safe_int(row.get("Leads"))

    result = []
    for d in agg.values():
        d["conv_rate"] = pct(d["leads"], d["visitors"]) if d["visitors"] else 0.0
        result.append(d)
    result.sort(key=lambda x: x["visitors"], reverse=True)
    return [r for r in result if r["visitors"] > 0]  # exclude zero-traffic

# ── TOTALS ────────────────────────────────────────────────────────────────────

def compute_totals(emails: list[dict]) -> dict:
    """
    Overall KPIs for the full period.
    For open/click rates we use only months where Entregues > 0 (Mar 2025+).
    """
    total_campaigns    = len(emails)
    total_selecionados = sum(e["selecionados"] for e in emails)
    total_unsub        = sum(e["unsub"] for e in emails)

    # Use only months with real Entregues (no estimated) for rate KPIs
    clean = [e for e in emails if e["data_quality"] == "ok"]
    clean_entregues = sum(e["entregues"] for e in clean)
    clean_opens     = sum(e["opens"]     for e in clean)
    clean_clicks    = sum(e["clicks"]    for e in clean)
    clean_bounce    = sum(e["bounce"]    for e in clean)

    # Largest audience seen in any single campaign
    max_list_size = max((e["selecionados"] for e in emails), default=0)

    # Weighted avg open rate: total opens / total entregues (clean months only)
    avg_open_rate  = pct(clean_opens,  clean_entregues)
    avg_ctr        = pct(clean_clicks, clean_entregues)
    avg_ctor       = pct(clean_clicks, clean_opens) if clean_opens else 0.0
    avg_bounce_rate = pct(clean_bounce, clean_entregues)
    avg_delivery    = pct(clean_entregues,
                          sum(e["selecionados"] for e in clean))

    return {
        "total_campaigns":      total_campaigns,
        "total_selecionados":   total_selecionados,
        "total_entregues":      clean_entregues,
        "total_opens":          sum(e["opens"]  for e in emails),
        "total_clicks":         sum(e["clicks"] for e in emails),
        "total_unsub":          total_unsub,
        "total_spam":           sum(e["spam"] for e in emails),
        "max_list_size":        max_list_size,
        "avg_open_rate":        avg_open_rate,
        "avg_ctr":              avg_ctr,
        "avg_ctor":             avg_ctor,
        "avg_bounce_email":     avg_bounce_rate,
        "avg_delivery_rate":    avg_delivery,
        "period_start":         emails[0]["sent_at"][:10] if emails else "",
        "period_end":           emails[-1]["sent_at"][:10] if emails else "",
        "rates_based_on":       "entregues (Mar 2025 – Feb 2026, Entregues > 0)",
    }

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  RD Station Marketing — CSV Exports Parser")
    print("=" * 60)

    # 1. Emails — add category field to each campaign
    print("\n📧 Parsing email campaigns...")
    emails = parse_emails()
    for e in emails:
        e["category"] = categorize_rds(e["name"])
    monthly = aggregate_monthly(emails)
    totals  = compute_totals(emails)
    print(f"   → {totals['total_campaigns']} unique campaigns")
    print(f"   → {totals['total_entregues']:,} delivered (clean months)")
    print(f"   → Avg open rate: {totals['avg_open_rate']:.1f}%")
    print(f"   → Avg CTR: {totals['avg_ctr']:.2f}%  |  CTOR: {totals['avg_ctor']:.2f}%")

    # 2. Top 20 campaigns (by opens, all campaigns including estimated)
    top_campaigns = sorted(emails, key=lambda e: e["opens"], reverse=True)[:20]
    print(f"\n🏆 Top 20 campaigns by opens captured")

    # 3. Campaign categories (RDS-based)
    campaign_categories = aggregate_campaign_categories(emails)
    print(f"\n🏷️  Campaign categories:")
    for cat in campaign_categories:
        print(f"   {cat['name']:<28}: {cat['campaigns']:>3} camps | {cat['opens']:>6,} opens | {cat['open_rate']:.1f}% OR")

    # 4. Channels
    print("\n📊 Parsing channel analysis...")
    channel_records  = parse_channel_analysis()
    channels_total   = aggregate_channels_total(channel_records)
    print(f"   → {len(channels_total)} channels")
    for c in channels_total:
        if c["visits"] > 0:
            print(f"     {c['channel']:<22}: {c['visits']:>7,} visitas ({c['visit_share']:.1f}%)")

    # 5. Forms
    print("\n📋 Parsing forms (latest period + by period)...")
    forms = parse_forms_latest()
    forms_by_period, forms_totals_by_name = parse_forms_by_period()
    total_form_leads    = sum(f["leads"]    for f in forms)
    total_form_visitors = sum(f["visitors"] for f in forms)
    total_mailing_leads = sum(p["mailing_leads"] for p in forms_by_period)
    print(f"   → {len(forms)} forms, {total_form_visitors:,} visitors, {total_form_leads:,} leads")
    print(f"   → Mailing Home Site leads (all periods): {total_mailing_leads:,}")

    # Aggregate all forms across all periods for complete totals
    forms_all_periods = []
    for name, d in forms_totals_by_name.items():
        d["name"] = name
        d["conv_rate"] = pct(d["leads"], d["visitors"]) if d["visitors"] else 0.0
        forms_all_periods.append(d)
    forms_all_periods.sort(key=lambda x: x["visitors"], reverse=True)

    # 6. Landing pages
    print("\n🌐 Parsing landing pages (cumulative)...")
    landing_pages = parse_landing_pages_all()
    total_lp_visitors = sum(lp["visitors"] for lp in landing_pages)
    total_lp_leads    = sum(lp["leads"]    for lp in landing_pages)
    print(f"   → {len(landing_pages)} active LPs, {total_lp_visitors:,} visitors, {total_lp_leads:,} leads")

    # ── BUILD OUTPUT ──────────────────────────────────────────────────────────
    output = {
        "_meta": {
            "parsed_at":    datetime.now().isoformat(),
            "source":       "manual CSV exports from RD Station Marketing",
            "periods":      PERIODS,
            "total_emails": totals["total_campaigns"],
            "data_quality_note": (
                "Jan/Feb 2025 exports have Entregues=0 (RD Station export bug). "
                "Open/click rate KPIs use only Mar 2025–Feb 2026 where Entregues > 0. "
                "Jan/Feb 2025 shown in charts with visual indicator (has_estimated=True)."
            ),
        },
        "totals":              totals,
        "email_monthly":       monthly,
        "emails":              emails,
        "top_campaigns":       top_campaigns,
        "campaign_categories": campaign_categories,
        "channels":            channels_total,
        "channel_by_period":   channel_records,
        "forms":               forms,
        "forms_all_periods":   forms_all_periods,
        "forms_by_period":     forms_by_period,
        "landing_pages":       landing_pages,
    }

    out_path = DATA_DIR / "rdstation_email_exports.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)

    size_kb = out_path.stat().st_size / 1024
    print(f"\n✅ Saved: {out_path}  ({size_kb:.0f} KB)")

    # Summary
    print("\n── SUMMARY ──────────────────────────────────────────────")
    print(f"  Period:         {totals['period_start']} → {totals['period_end']}")
    print(f"  Campaigns:      {totals['total_campaigns']}")
    print(f"  Max list size:  {totals['max_list_size']:,} leads")
    print(f"  Total opens:    {totals['total_opens']:,} (all 14 months)")
    print(f"  Total clicks:   {totals['total_clicks']:,}")
    print(f"  Avg open rate:  {totals['avg_open_rate']:.1f}%  (Mar 2025–Feb 2026 clean)")
    print(f"  Avg CTR:        {totals['avg_ctr']:.2f}%")
    print(f"  Avg CTOR:       {totals['avg_ctor']:.2f}%")
    print(f"  Avg delivery:   {totals['avg_delivery_rate']:.1f}%")
    print(f"  Total unsubs:   {totals['total_unsub']:,}")
    print(f"  Forms leads (Mailing, all periods): {total_mailing_leads:,}")
    print(f"  Landing pages active: {len(landing_pages):,} ({total_lp_visitors:,} visitors)")

    return output


if __name__ == "__main__":
    main()
