#!/usr/bin/env python3
"""
GA4 Data API — Fetch email traffic analytics for IAB Brasil.
Pulls sessions, users, conversions from email/newsletter source.
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange, Dimension, Metric, RunReportRequest,
    FilterExpression, Filter, FilterExpressionList,
    OrderBy
)
from google.oauth2 import service_account

BASE_DIR = Path(__file__).parent.parent
CONFIG_FILE = BASE_DIR / "credentials" / "config.json"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

def get_ga4_client(config):
    sa_file = BASE_DIR / config["ga4"]["service_account_file"]
    if not sa_file.exists():
        print(f"❌ Service Account não encontrada: {sa_file}")
        print("   Siga o SETUP_GUIDE.md para criar a Service Account.")
        exit(1)

    credentials = service_account.Credentials.from_service_account_file(
        str(sa_file),
        scopes=["https://www.googleapis.com/auth/analytics.readonly"]
    )
    return BetaAnalyticsDataClient(credentials=credentials)

def run_report(client, property_id, dimensions, metrics, date_ranges,
               dimension_filter=None, order_bys=None, limit=10000):
    """Run a GA4 Data API report."""
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=date_ranges,
        dimension_filter=dimension_filter,
        order_bys=order_bys or [],
        limit=limit
    )
    response = client.run_report(request)
    return response

def response_to_dict(response):
    """Convert GA4 response to list of dicts."""
    rows = []
    dim_headers = [h.name for h in response.dimension_headers]
    met_headers = [h.name for h in response.metric_headers]

    for row in response.rows:
        r = {}
        for i, dim in enumerate(row.dimension_values):
            r[dim_headers[i]] = dim.value
        for i, met in enumerate(row.metric_values):
            r[met_headers[i]] = met.value
        rows.append(r)
    return rows

def email_source_filter():
    """Filter for email/newsletter traffic."""
    return FilterExpression(
        or_group=FilterExpressionList(
            expressions=[
                FilterExpression(
                    filter=Filter(
                        field_name="sessionDefaultChannelGroup",
                        string_filter=Filter.StringFilter(
                            value="Email",
                            match_type=Filter.StringFilter.MatchType.EXACT
                        )
                    )
                ),
                FilterExpression(
                    filter=Filter(
                        field_name="sessionMedium",
                        string_filter=Filter.StringFilter(
                            value="email",
                            match_type=Filter.StringFilter.MatchType.EXACT
                        )
                    )
                )
            ]
        )
    )

def fetch_all_ga4_data():
    config = load_config()
    property_id = config["ga4"]["property_id"]

    if not property_id or property_id == "SEU_PROPERTY_ID":
        print("❌ Configure o property_id do GA4 em credentials/config.json")
        exit(1)

    client = get_ga4_client(config)
    data = {}

    print("\n" + "=" * 60)
    print("  GA4 Data API — Coletando dados de tráfego email")
    print("=" * 60)
    print(f"  Property ID: {property_id}")

    # Date ranges: last 12 months + year ago comparison
    date_ranges_12m = [DateRange(start_date="365daysAgo", end_date="today")]
    date_ranges_compare = [
        DateRange(start_date="365daysAgo", end_date="today", name="current"),
        DateRange(start_date="730daysAgo", end_date="366daysAgo", name="previous")
    ]

    # 1. Overall email traffic overview
    print("\n📊 Tráfego geral por canal (últimos 365 dias)...")
    resp = run_report(client, property_id,
        dimensions=["sessionDefaultChannelGroup", "sessionMedium", "sessionSource"],
        metrics=["sessions", "activeUsers", "newUsers", "bounceRate",
                 "averageSessionDuration", "screenPageViewsPerSession"],
        date_ranges=date_ranges_12m
    )
    data["channel_overview"] = response_to_dict(resp)
    print(f"   → {len(data['channel_overview'])} rows")

    # 2. Email traffic by month (trend)
    print("\n📅 Tráfego de email por mês...")
    resp = run_report(client, property_id,
        dimensions=["yearMonth", "sessionDefaultChannelGroup"],
        metrics=["sessions", "activeUsers", "newUsers", "engagedSessions",
                 "bounceRate", "averageSessionDuration"],
        date_ranges=date_ranges_12m,
        dimension_filter=email_source_filter()
    )
    data["email_by_month"] = response_to_dict(resp)
    print(f"   → {len(data['email_by_month'])} rows")

    # 3. Email traffic: landing pages
    print("\n🌐 Landing pages de tráfego email...")
    resp = run_report(client, property_id,
        dimensions=["landingPage", "landingPagePlusQueryString"],
        metrics=["sessions", "activeUsers", "newUsers", "bounceRate",
                 "averageSessionDuration", "conversions", "totalRevenue"],
        date_ranges=date_ranges_12m,
        dimension_filter=email_source_filter(),
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
        limit=100
    )
    data["email_landing_pages"] = response_to_dict(resp)
    print(f"   → {len(data['email_landing_pages'])} landing pages")

    # 4. Email traffic by UTM campaign
    print("\n🎯 Campanhas por UTM (email)...")
    resp = run_report(client, property_id,
        dimensions=["sessionCampaignName", "sessionSource", "sessionMedium"],
        metrics=["sessions", "activeUsers", "newUsers", "bounceRate",
                 "averageSessionDuration", "engagedSessions", "conversions"],
        date_ranges=date_ranges_12m,
        dimension_filter=email_source_filter(),
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)],
        limit=200
    )
    data["email_campaigns_utm"] = response_to_dict(resp)
    print(f"   → {len(data['email_campaigns_utm'])} campanhas UTM")

    # 5. Email traffic by device
    print("\n📱 Dispositivos (tráfego email)...")
    resp = run_report(client, property_id,
        dimensions=["deviceCategory", "operatingSystem", "browser"],
        metrics=["sessions", "activeUsers", "bounceRate", "averageSessionDuration"],
        date_ranges=date_ranges_12m,
        dimension_filter=email_source_filter()
    )
    data["email_devices"] = response_to_dict(resp)
    print(f"   → {len(data['email_devices'])} rows")

    # 6. Email traffic by day of week
    print("\n📆 Tráfego email por dia da semana...")
    resp = run_report(client, property_id,
        dimensions=["dayOfWeek", "hour"],
        metrics=["sessions", "activeUsers", "engagedSessions", "bounceRate"],
        date_ranges=date_ranges_12m,
        dimension_filter=email_source_filter()
    )
    data["email_by_dayofweek"] = response_to_dict(resp)
    print(f"   → {len(data['email_by_dayofweek'])} rows")

    # 7. Events from email traffic
    print("\n⚡ Eventos de tráfego email...")
    resp = run_report(client, property_id,
        dimensions=["eventName", "pageTitle"],
        metrics=["eventCount", "totalUsers"],
        date_ranges=date_ranges_12m,
        dimension_filter=email_source_filter(),
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventCount"), desc=True)],
        limit=100
    )
    data["email_events"] = response_to_dict(resp)
    print(f"   → {len(data['email_events'])} eventos")

    # 8. Geographic distribution of email users
    print("\n🗺️  Distribuição geográfica...")
    resp = run_report(client, property_id,
        dimensions=["country", "region", "city"],
        metrics=["activeUsers", "sessions", "newUsers"],
        date_ranges=date_ranges_12m,
        dimension_filter=email_source_filter(),
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="activeUsers"), desc=True)],
        limit=50
    )
    data["email_geography"] = response_to_dict(resp)
    print(f"   → {len(data['email_geography'])} locations")

    # 9. Content engagement from email traffic
    print("\n📝 Páginas mais visitadas via email...")
    resp = run_report(client, property_id,
        dimensions=["pagePath", "pageTitle"],
        metrics=["screenPageViews", "activeUsers", "averageSessionDuration",
                 "bounceRate", "engagedSessions"],
        date_ranges=date_ranges_12m,
        dimension_filter=email_source_filter(),
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="screenPageViews"), desc=True)],
        limit=100
    )
    data["email_pages"] = response_to_dict(resp)
    print(f"   → {len(data['email_pages'])} páginas")

    # 10. Overall site metrics for benchmark
    print("\n📊 Benchmark geral do site...")
    resp = run_report(client, property_id,
        dimensions=["sessionDefaultChannelGroup"],
        metrics=["sessions", "activeUsers", "newUsers", "bounceRate",
                 "averageSessionDuration", "engagedSessions", "conversions"],
        date_ranges=date_ranges_12m,
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="sessions"), desc=True)]
    )
    data["site_benchmark"] = response_to_dict(resp)
    print(f"   → {len(data['site_benchmark'])} canais para benchmark")

    # Save all data
    output_file = DATA_DIR / "ga4_raw_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    print(f"\n✅ Dados GA4 salvos em: {output_file}")
    print(f"   Tamanho: {output_file.stat().st_size / 1024:.1f} KB")

    return data

if __name__ == "__main__":
    fetch_all_ga4_data()
