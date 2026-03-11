#!/usr/bin/env python3
"""
GA4 Data API — Fetch RD Station email traffic analytics for IAB Brasil.
Filter: sessionSource EXACT "RD Station" AND sessionMedium EXACT "email"
Auth: OAuth2 refresh token from credentials/ga4_token.json
"""
import json
from pathlib import Path
from datetime import datetime, timedelta, date

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest,
    FilterExpression, Filter, FilterExpressionList, OrderBy
)
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

BASE_DIR  = Path(__file__).parent.parent
CREDS_DIR = BASE_DIR / "credentials"
DATA_DIR  = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

PROPERTY_ID = (CREDS_DIR / "ga4_property_id.txt").read_text().strip()
TOKEN_FILE  = CREDS_DIR / "ga4_token.json"

# ── AUTH ─────────────────────────────────────────────────────────────────────

def get_client():
    with open(TOKEN_FILE) as f:
        tok = json.load(f)

    creds = Credentials(
        token             = tok.get("token"),
        refresh_token     = tok["refresh_token"],
        token_uri         = tok.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id         = tok["client_id"],
        client_secret     = tok["client_secret"],
        scopes            = tok.get("scopes", ["https://www.googleapis.com/auth/analytics.readonly"]),
        quota_project_id  = "iab-data-analytics"
    )
    if not creds.valid:
        creds.refresh(Request())
        tok["token"] = creds.token
        with open(TOKEN_FILE, "w") as f:
            json.dump(tok, f, indent=2)

    return BetaAnalyticsDataClient(credentials=creds)

# ── HELPERS ───────────────────────────────────────────────────────────────────

def run_report(client, dims, mets, date_ranges, fltr=None, order_bys=None, limit=10000):
    req = RunReportRequest(
        property    = f"properties/{PROPERTY_ID}",
        dimensions  = [Dimension(name=d) for d in dims],
        metrics     = [Metric(name=m) for m in mets],
        date_ranges = date_ranges,
        dimension_filter = fltr,
        order_bys   = order_bys or [],
        limit       = limit
    )
    resp = client.run_report(req)
    dim_h = [h.name for h in resp.dimension_headers]
    met_h = [h.name for h in resp.metric_headers]
    rows  = []
    for row in resp.rows:
        r = {dim_h[i]: row.dimension_values[i].value for i in range(len(dim_h))}
        r.update({met_h[i]: row.metric_values[i].value for i in range(len(met_h))})
        rows.append(r)
    return rows

def rds_email_filter():
    """RD Station / email — the ONLY email UTM from RD Station Marketing."""
    return FilterExpression(
        and_group=FilterExpressionList(expressions=[
            FilterExpression(filter=Filter(
                field_name="sessionSource",
                string_filter=Filter.StringFilter(
                    value="RD Station",
                    match_type=Filter.StringFilter.MatchType.EXACT))),
            FilterExpression(filter=Filter(
                field_name="sessionMedium",
                string_filter=Filter.StringFilter(
                    value="email",
                    match_type=Filter.StringFilter.MatchType.EXACT)))
        ])
    )

def date_ranges_from(start="365daysAgo", end="yesterday"):
    return [DateRange(start_date=start, end_date=end)]

def order_desc(metric):
    return [OrderBy(metric=OrderBy.MetricOrderBy(metric_name=metric), desc=True)]

def order_asc(metric):
    return [OrderBy(metric=OrderBy.MetricOrderBy(metric_name=metric), desc=False)]

def order_dim_asc(dimension):
    return [OrderBy(dimension=OrderBy.DimensionOrderBy(dimension_name=dimension), desc=False)]

# ── MAIN FETCH ────────────────────────────────────────────────────────────────

def fetch_all():
    print("\n" + "="*60)
    print("  GA4 Data API — IAB Brasil · RD Station / email only")
    print("="*60)
    print(f"  Property: {PROPERTY_ID}")
    print(f"  Filter:   sessionSource='RD Station' AND sessionMedium='email'")
    print(f"  Period:   365 dias → yesterday ({date.today() - timedelta(1)})")

    client = get_client()
    dr     = date_ranges_from("365daysAgo", "yesterday")
    fltr   = rds_email_filter()
    data   = {}

    # 1. Channel overview (all sources — for benchmark comparison)
    print("\n📊 1. Channel overview (all sources, benchmark)...")
    data["channel_overview"] = run_report(client,
        dims=["sessionDefaultChannelGroup", "sessionSource", "sessionMedium"],
        mets=["sessions","activeUsers","newUsers","bounceRate",
              "averageSessionDuration","engagedSessions","conversions"],
        date_ranges=dr,
        order_bys=order_desc("sessions"))
    print(f"   → {len(data['channel_overview'])} rows")

    # 2. RD Station email by month
    print("\n📅 2. RD Station/email por mês...")
    data["email_by_month"] = run_report(client,
        dims=["yearMonth"],
        mets=["sessions","activeUsers","newUsers","engagedSessions",
              "bounceRate","averageSessionDuration","screenPageViews","conversions"],
        date_ranges=dr, fltr=fltr,
        order_bys=order_dim_asc("yearMonth"))
    print(f"   → {len(data['email_by_month'])} months")

    # 3. RD Station email by date (daily granularity for custom filter)
    print("\n📅 3. RD Station/email diário (granularidade para filtro customizado)...")
    data["email_by_date"] = run_report(client,
        dims=["date"],
        mets=["sessions","activeUsers","newUsers","engagedSessions",
              "bounceRate","averageSessionDuration","screenPageViews","conversions"],
        date_ranges=dr, fltr=fltr,
        order_bys=order_dim_asc("date"), limit=400)
    print(f"   → {len(data['email_by_date'])} days")

    # 4. UTM campaigns (from RD Station / email)
    print("\n🎯 4. Campanhas UTM (RD Station / email)...")
    data["email_campaigns_utm"] = run_report(client,
        dims=["sessionCampaignName"],
        mets=["sessions","activeUsers","newUsers","bounceRate",
              "averageSessionDuration","engagedSessions","conversions"],
        date_ranges=dr, fltr=fltr,
        order_bys=order_desc("sessions"), limit=300)
    print(f"   → {len(data['email_campaigns_utm'])} campaigns")

    # 5. Landing pages (daily for period filter)
    print("\n🌐 5. Landing pages diário...")
    data["email_landing_pages"] = run_report(client,
        dims=["date","landingPage","pageTitle"],
        mets=["sessions","activeUsers","bounceRate",
              "averageSessionDuration","conversions","screenPageViews"],
        date_ranges=dr, fltr=fltr,
        order_bys=order_desc("sessions"), limit=2000)
    print(f"   → {len(data['email_landing_pages'])} rows")

    # 6. Day of week + hour (daily granularity preserved for period filter)
    print("\n📆 6. Dia da semana e hora (diário)...")
    data["email_by_dayofweek"] = run_report(client,
        dims=["date","dayOfWeek","hour"],
        mets=["sessions","activeUsers","engagedSessions","bounceRate"],
        date_ranges=dr, fltr=fltr, limit=15000)
    print(f"   → {len(data['email_by_dayofweek'])} rows")

    # 7. Devices (daily)
    print("\n📱 7. Dispositivos (diário)...")
    data["email_devices"] = run_report(client,
        dims=["date","deviceCategory"],
        mets=["sessions","activeUsers","bounceRate","averageSessionDuration"],
        date_ranges=dr, fltr=fltr)
    print(f"   → {len(data['email_devices'])} rows")

    # 8. Events
    print("\n⚡ 8. Eventos...")
    data["email_events"] = run_report(client,
        dims=["eventName"],
        mets=["eventCount","totalUsers","conversions"],
        date_ranges=dr, fltr=fltr,
        order_bys=order_desc("eventCount"), limit=50)
    print(f"   → {len(data['email_events'])} events")

    # 9. Pages
    print("\n📝 9. Páginas visitadas (diário)...")
    data["email_pages"] = run_report(client,
        dims=["date","pagePath","pageTitle"],
        mets=["screenPageViews","activeUsers","averageSessionDuration",
              "bounceRate","engagedSessions"],
        date_ranges=dr, fltr=fltr,
        order_bys=order_desc("screenPageViews"), limit=2000)
    print(f"   → {len(data['email_pages'])} rows")

    # 10. Geography
    print("\n🗺  10. Distribuição geográfica...")
    data["email_geography"] = run_report(client,
        dims=["country","region"],
        mets=["activeUsers","sessions","newUsers"],
        date_ranges=dr, fltr=fltr,
        order_bys=order_desc("activeUsers"), limit=50)
    print(f"   → {len(data['email_geography'])} locations")

    # Save metadata
    data["_meta"] = {
        "fetched_at"   : datetime.now().isoformat(),
        "property_id"  : PROPERTY_ID,
        "source_filter": "sessionSource='RD Station' AND sessionMedium='email'",
        "period_start" : "365daysAgo",
        "period_end"   : "yesterday",
        "period_label" : f"até {date.today() - timedelta(1)}"
    }

    out = DATA_DIR / "ga4_raw_data.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n✅ Salvo em: {out}  ({out.stat().st_size/1024:.1f} KB)")
    return data

if __name__ == "__main__":
    fetch_all()
