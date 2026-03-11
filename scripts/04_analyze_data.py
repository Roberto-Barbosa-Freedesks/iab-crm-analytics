#!/usr/bin/env python3
"""
Analyzes raw data from RD Station Marketing + GA4.
Generates structured insights, KPIs, and recommendations.
"""
import json
import statistics
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

def load_data():
    rds_file = DATA_DIR / "rdstation_raw_data.json"
    ga4_file = DATA_DIR / "ga4_raw_data.json"

    rds_data = {}
    ga4_data = {}

    if rds_file.exists():
        with open(rds_file) as f:
            rds_data = json.load(f)
        print(f"✓ RD Station data loaded ({rds_file.stat().st_size / 1024:.0f} KB)")
    else:
        print("⚠ RD Station data not found, using demo data")
        rds_data = generate_demo_rds_data()

    if ga4_file.exists():
        with open(ga4_file) as f:
            ga4_data = json.load(f)
        print(f"✓ GA4 data loaded ({ga4_file.stat().st_size / 1024:.0f} KB)")
    else:
        print("⚠ GA4 data not found, using demo data")
        ga4_data = generate_demo_ga4_data()

    return rds_data, ga4_data


def generate_demo_rds_data():
    """Generate realistic demo data for IAB Brasil email marketing context."""
    import random
    random.seed(42)

    emails = []
    subjects = [
        "IAB IA Summit 2024 — Inscrições abertas",
        "Novo relatório: Panorama do Marketing Digital no Brasil",
        "Webinar exclusivo: Retail Media e o futuro do varejo digital",
        "IAB Brasil News — Semana 1 de Março",
        "Guia completo de Brand Safety para 2024",
        "Certificação IAB: Últimas vagas disponíveis",
        "IAB Brasil News — Semana 2 de Março",
        "Creator Economy: como monetizar no Brasil",
        "Relatório Audio Digital 2024 — Download gratuito",
        "IAB Brasil News — Semana 3 de Março",
        "Summit de Dados e Privacidade — Save the date",
        "Programmatic Advertising: tendências para Q2",
        "IAB Brasil News — Semana 4 de Março",
        "DOOH: oportunidades no Out-of-Home digital",
        "Novo comitê de IA — Participe",
        "IAB Brasil News — Semana 1 de Abril",
        "Relatório Video Streaming — Edição 2024",
        "Webinar: Cookies de terceiros e o futuro",
        "IAB Brasil News — Semana 2 de Abril",
        "Certificação em Marketing Digital — Novas turmas",
    ]
    segments = ["Base Geral", "Membros Associados", "Professores/Cursos",
                "Executivos de Mídia", "Agências", "Anunciantes", "Tech/Ad Tech"]
    email_types = ["Newsletter", "Evento", "Conteúdo", "Produto/Serviço", "Institucional"]

    for i in range(len(subjects)):
        sent = random.randint(3500, 15000)
        delivered = int(sent * random.uniform(0.94, 0.99))
        opened = int(delivered * random.uniform(0.15, 0.42))
        clicked = int(opened * random.uniform(0.08, 0.25))
        bounced = sent - delivered
        unsubscribed = random.randint(2, 35)

        month = 3 + (i // 4)
        day = random.randint(1, 28)
        hour = random.choice([8, 9, 10, 11, 14, 15, 16, 17])

        emails.append({
            "id": f"email_{i+1:03d}",
            "subject": subjects[i],
            "email_type": email_types[i % len(email_types)],
            "segment": segments[i % len(segments)],
            "sent_at": f"2024-{month:02d}-{day:02d}T{hour:02d}:00:00",
            "stats": {
                "sends": sent,
                "delivered": delivered,
                "opens": opened,
                "unique_opens": int(opened * 0.85),
                "clicks": clicked,
                "unique_clicks": int(clicked * 0.80),
                "bounces": bounced,
                "hard_bounces": int(bounced * 0.3),
                "soft_bounces": int(bounced * 0.7),
                "unsubscribes": unsubscribed,
                "spam_reports": random.randint(0, 5)
            }
        })

    return {
        "emails": emails,
        "segmentations": {
            "segmentations": [
                {"id": f"seg_{i}", "name": s, "contacts_count": random.randint(1500, 12000)}
                for i, s in enumerate(segments)
            ]
        },
        "contacts_summary": {"total": 28450}
    }


def generate_demo_ga4_data():
    """Generate realistic GA4 demo data for IAB Brasil."""
    import random
    random.seed(42)

    months = ["202401", "202402", "202403", "202404", "202405",
              "202406", "202407", "202408", "202409", "202410", "202411", "202412"]

    email_by_month = []
    for m in months:
        sessions = random.randint(800, 3200)
        email_by_month.append({
            "yearMonth": m,
            "sessionDefaultChannelGroup": "Email",
            "sessions": str(sessions),
            "activeUsers": str(int(sessions * 0.82)),
            "newUsers": str(int(sessions * 0.35)),
            "engagedSessions": str(int(sessions * 0.68)),
            "bounceRate": str(round(random.uniform(0.28, 0.52), 4)),
            "averageSessionDuration": str(round(random.uniform(90, 240), 1))
        })

    channels = ["Email", "Organic Search", "Direct", "Organic Social",
                "Referral", "Paid Search", "Display"]
    channel_sessions = [18500, 45200, 22100, 12800, 6400, 3200, 1800]

    site_benchmark = []
    for ch, sess in zip(channels, channel_sessions):
        site_benchmark.append({
            "sessionDefaultChannelGroup": ch,
            "sessions": str(sess + random.randint(-500, 500)),
            "activeUsers": str(int(sess * 0.80)),
            "newUsers": str(int(sess * random.uniform(0.28, 0.65))),
            "bounceRate": str(round(random.uniform(0.30, 0.58), 4)),
            "averageSessionDuration": str(round(random.uniform(75, 210), 1)),
            "engagedSessions": str(int(sess * random.uniform(0.55, 0.75))),
            "conversions": str(random.randint(50, 400))
        })

    campaigns = [
        "IA Summit 2024", "Newsletter Mar/24", "Relatório Panorama",
        "Webinar Retail Media", "Certificação IAB", "Newsletter Abr/24",
        "Creator Economy", "Audio Digital 2024", "(not set)"
    ]
    email_campaigns = []
    for camp in campaigns:
        sess = random.randint(200, 2800)
        email_campaigns.append({
            "sessionCampaignName": camp,
            "sessionSource": "rdstation",
            "sessionMedium": "email",
            "sessions": str(sess),
            "activeUsers": str(int(sess * 0.82)),
            "newUsers": str(int(sess * 0.30)),
            "bounceRate": str(round(random.uniform(0.25, 0.50), 4)),
            "averageSessionDuration": str(round(random.uniform(100, 280), 1)),
            "engagedSessions": str(int(sess * 0.65)),
            "conversions": str(random.randint(5, 120))
        })

    landing_pages = [
        "/", "/cursos", "/eventos/ia-summit-2024", "/pesquisas",
        "/comites", "/sobre", "/blog", "/certificacao", "/associe-se"
    ]
    email_landing = []
    for lp in landing_pages:
        sess = random.randint(150, 2500)
        email_landing.append({
            "landingPage": lp,
            "landingPagePlusQueryString": lp,
            "sessions": str(sess),
            "activeUsers": str(int(sess * 0.82)),
            "newUsers": str(int(sess * 0.30)),
            "bounceRate": str(round(random.uniform(0.22, 0.55), 4)),
            "averageSessionDuration": str(round(random.uniform(80, 300), 1)),
            "conversions": str(random.randint(3, 85)),
            "totalRevenue": "0"
        })

    days = []
    day_names = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    for day in range(7):
        for hour in range(24):
            mult = 1.0
            if day in [1, 2, 3, 4]:  # Weekdays
                mult *= 1.3
            if 9 <= hour <= 11 or 14 <= hour <= 16:
                mult *= 1.5
            sess = int(random.randint(5, 80) * mult)
            days.append({
                "dayOfWeek": str(day),
                "hour": str(hour),
                "sessions": str(sess),
                "activeUsers": str(int(sess * 0.82)),
                "engagedSessions": str(int(sess * 0.65)),
                "bounceRate": str(round(random.uniform(0.25, 0.55), 4))
            })

    devices = [
        {"deviceCategory": "mobile", "operatingSystem": "Android", "browser": "Chrome",
         "sessions": "7240", "activeUsers": "5920", "bounceRate": "0.4820", "averageSessionDuration": "105.3"},
        {"deviceCategory": "desktop", "operatingSystem": "Windows", "browser": "Chrome",
         "sessions": "5880", "activeUsers": "4810", "bounceRate": "0.3520", "averageSessionDuration": "178.6"},
        {"deviceCategory": "mobile", "operatingSystem": "iOS", "browser": "Safari",
         "sessions": "3620", "activeUsers": "2970", "bounceRate": "0.4650", "averageSessionDuration": "112.4"},
        {"deviceCategory": "desktop", "operatingSystem": "macOS", "browser": "Safari",
         "sessions": "1920", "activeUsers": "1570", "bounceRate": "0.3280", "averageSessionDuration": "195.2"},
        {"deviceCategory": "desktop", "operatingSystem": "Windows", "browser": "Edge",
         "sessions": "850", "activeUsers": "695", "bounceRate": "0.3740", "averageSessionDuration": "162.8"},
    ]

    import datetime
    email_by_date = []
    start_date = datetime.date(2023, 3, 1) # Support 12+ months back
    for i in range(400):
        d = start_date + datetime.timedelta(days=i)
        date_str = d.strftime("%Y%m%d")
        sessions = random.randint(10, 150)
        email_by_date.append({
            "date": date_str,
            "sessionDefaultChannelGroup": "Email",
            "sessions": str(sessions),
            "activeUsers": str(int(sessions * 0.82)),
            "newUsers": str(int(sessions * 0.35)),
            "engagedSessions": str(int(sessions * 0.68)),
            "bounceRate": str(round(random.uniform(0.28, 0.52), 4)),
            "averageSessionDuration": str(round(random.uniform(90, 240), 1))
        })

    return {
        "channel_overview": [
            {"sessionDefaultChannelGroup": "Email", "sessionMedium": "email",
             "sessionSource": "rdstation", "sessions": "18524",
             "activeUsers": "15190", "newUsers": "6483",
             "bounceRate": "0.3912", "averageSessionDuration": "154.7",
             "screenPageViewsPerSession": "2.84"}
        ],
        "email_by_date": email_by_date,
        "email_by_month": email_by_month,
        "email_campaigns_utm": email_campaigns,
        "email_landing_pages": email_landing,
        "email_by_dayofweek": days,
        "email_devices": devices,
        "email_events": [
            {"eventName": "page_view", "pageTitle": "", "eventCount": "52640", "totalUsers": "15190"},
            {"eventName": "session_start", "pageTitle": "", "eventCount": "18524", "totalUsers": "15190"},
            {"eventName": "click", "pageTitle": "", "eventCount": "12480", "totalUsers": "8920"},
            {"eventName": "scroll", "pageTitle": "", "eventCount": "28350", "totalUsers": "11240"},
            {"eventName": "form_submit", "pageTitle": "", "eventCount": "1840", "totalUsers": "1620"},
            {"eventName": "file_download", "pageTitle": "", "eventCount": "2960", "totalUsers": "2340"},
            {"eventName": "video_start", "pageTitle": "", "eventCount": "3420", "totalUsers": "2810"},
        ],
        "email_geography": [
            {"country": "Brazil", "region": "São Paulo", "city": "São Paulo",
             "activeUsers": "9420", "sessions": "11500", "newUsers": "3820"},
            {"country": "Brazil", "region": "Rio de Janeiro", "city": "Rio de Janeiro",
             "activeUsers": "2140", "sessions": "2610", "newUsers": "870"},
            {"country": "Brazil", "region": "Minas Gerais", "city": "Belo Horizonte",
             "activeUsers": "980", "sessions": "1195", "newUsers": "398"},
        ],
        "email_pages": [
            {"pagePath": "/", "pageTitle": "IAB Brasil - Home", "screenPageViews": "22480",
             "activeUsers": "9820", "averageSessionDuration": "145.2",
             "bounceRate": "0.3820", "engagedSessions": "8940"},
            {"pagePath": "/eventos/ia-summit-2024", "pageTitle": "IAB IA Summit 2024",
             "screenPageViews": "8640", "activeUsers": "6120", "averageSessionDuration": "210.5",
             "bounceRate": "0.2840", "engagedSessions": "5880"},
            {"pagePath": "/pesquisas", "pageTitle": "Pesquisas e Relatórios",
             "screenPageViews": "6820", "activeUsers": "4940", "averageSessionDuration": "185.3",
             "bounceRate": "0.3120", "engagedSessions": "4580"},
        ],
        "site_benchmark": site_benchmark
    }


def analyze_rds_emails(emails_data):
    """Analyze RD Station email campaign performance."""
    results = {}

    # Extract email stats
    if not emails_data:
        return results

    emails = emails_data.get("emails", [])
    if not emails:
        return results

    # Aggregate global metrics
    total_sends = 0
    total_delivered = 0
    total_opens = 0
    total_clicks = 0
    total_bounces = 0
    total_unsubscribes = 0

    open_rates = []
    click_rates = []
    ctor_rates = []  # Click-to-open rate
    bounce_rates = []

    email_performance = []
    by_type = defaultdict(lambda: {"sends": 0, "opens": 0, "clicks": 0, "count": 0})
    by_segment = defaultdict(lambda: {"sends": 0, "opens": 0, "clicks": 0, "count": 0})
    by_dayofweek = defaultdict(lambda: {"sends": 0, "opens": 0, "clicks": 0, "count": 0})
    by_hour = defaultdict(lambda: {"sends": 0, "opens": 0, "count": 0})

    for email in emails:
        stats = email.get("stats", {})
        sent = stats.get("sends", 0) or 0
        delivered = stats.get("delivered", sent) or sent
        opens = stats.get("opens", 0) or 0
        clicks = stats.get("clicks", 0) or 0
        bounces = stats.get("bounces", 0) or 0
        unsubs = stats.get("unsubscribes", 0) or 0

        total_sends += sent
        total_delivered += delivered
        total_opens += opens
        total_clicks += clicks
        total_bounces += bounces
        total_unsubscribes += unsubs

        if delivered > 0:
            or_ = opens / delivered
            cr_ = clicks / delivered
            open_rates.append(or_)
            click_rates.append(cr_)
            bounce_rates.append(bounces / sent if sent > 0 else 0)

        if opens > 0:
            ctor_rates.append(clicks / opens)

        # Parse date
        sent_at = email.get("sent_at", "")
        weekday = "N/A"
        hour = "N/A"
        if sent_at:
            try:
                dt = datetime.fromisoformat(sent_at.replace("Z", ""))
                weekday = dt.strftime("%A")
                hour = dt.hour
                by_dayofweek[weekday]["sends"] += sent
                by_dayofweek[weekday]["opens"] += opens
                by_dayofweek[weekday]["clicks"] += clicks
                by_dayofweek[weekday]["count"] += 1
                by_hour[hour]["sends"] += sent
                by_hour[hour]["opens"] += opens
                by_hour[hour]["count"] += 1
            except:
                pass

        email_type = email.get("email_type", "Unknown")
        segment = email.get("segment", "Unknown")

        by_type[email_type]["sends"] += sent
        by_type[email_type]["opens"] += opens
        by_type[email_type]["clicks"] += clicks
        by_type[email_type]["count"] += 1

        by_segment[segment]["sends"] += sent
        by_segment[segment]["opens"] += opens
        by_segment[segment]["clicks"] += clicks
        by_segment[segment]["count"] += 1

        open_rate = opens / delivered if delivered > 0 else 0
        click_rate = clicks / delivered if delivered > 0 else 0
        ctor = clicks / opens if opens > 0 else 0

        email_performance.append({
            "id": email.get("id"),
            "subject": email.get("subject", "N/A"),
            "email_type": email_type,
            "segment": segment,
            "sent_at": sent_at,
            "weekday": weekday,
            "hour": hour,
            "sends": sent,
            "delivered": delivered,
            "opens": opens,
            "clicks": clicks,
            "bounces": bounces,
            "unsubscribes": unsubs,
            "open_rate": round(open_rate * 100, 2),
            "click_rate": round(click_rate * 100, 2),
            "ctor": round(ctor * 100, 2),
            "bounce_rate": round(bounces / sent * 100 if sent > 0 else 0, 2),
            "delivery_rate": round(delivered / sent * 100 if sent > 0 else 0, 2)
        })

    # Sort by performance
    email_performance.sort(key=lambda x: x["open_rate"], reverse=True)

    # Calculate averages
    avg_open_rate = statistics.mean(open_rates) if open_rates else 0
    avg_click_rate = statistics.mean(click_rates) if click_rates else 0
    avg_ctor = statistics.mean(ctor_rates) if ctor_rates else 0
    avg_bounce_rate = statistics.mean(bounce_rates) if bounce_rates else 0

    # Industry benchmarks for IAB context (Brazil email marketing)
    benchmarks = {
        "open_rate": 0.22,     # 22% average Brazil
        "click_rate": 0.025,   # 2.5% average
        "ctor": 0.11,          # 11% average
        "bounce_rate": 0.02    # 2% acceptable
    }

    # Best sending days/hours
    best_days = sorted(by_dayofweek.items(),
                       key=lambda x: x[1]["opens"] / max(x[1]["sends"], 1),
                       reverse=True)
    best_hours = sorted(by_hour.items(),
                        key=lambda x: x[1]["opens"] / max(x[1]["sends"], 1),
                        reverse=True)

    # Type performance
    type_performance = {}
    for etype, stats in by_type.items():
        if stats["sends"] > 0:
            type_performance[etype] = {
                "count": stats["count"],
                "total_sends": stats["sends"],
                "avg_open_rate": round(stats["opens"] / stats["sends"] * 100, 2),
                "avg_click_rate": round(stats["clicks"] / stats["sends"] * 100, 2)
            }

    # Segment performance
    segment_performance = {}
    for seg, stats in by_segment.items():
        if stats["sends"] > 0:
            segment_performance[seg] = {
                "count": stats["count"],
                "total_sends": stats["sends"],
                "avg_open_rate": round(stats["opens"] / stats["sends"] * 100, 2),
                "avg_click_rate": round(stats["clicks"] / stats["sends"] * 100, 2)
            }

    # Contacts
    total_contacts = emails_data.get("contacts_summary", {}).get("total", 0)
    if isinstance(total_contacts, dict):
        total_contacts = total_contacts.get("total", 0)

    results = {
        "summary": {
            "total_emails": len(emails),
            "total_contacts": total_contacts,
            "total_sends": total_sends,
            "total_delivered": total_delivered,
            "total_opens": total_opens,
            "total_clicks": total_clicks,
            "total_bounces": total_bounces,
            "total_unsubscribes": total_unsubscribes,
            "avg_open_rate": round(avg_open_rate * 100, 2),
            "avg_click_rate": round(avg_click_rate * 100, 2),
            "avg_ctor": round(avg_ctor * 100, 2),
            "avg_bounce_rate": round(avg_bounce_rate * 100, 2),
            "delivery_rate": round(total_delivered / total_sends * 100 if total_sends > 0 else 0, 2)
        },
        "benchmarks": {
            k: round(v * 100, 2) for k, v in benchmarks.items()
        },
        "performance_vs_benchmark": {
            "open_rate": round((avg_open_rate - benchmarks["open_rate"]) * 100, 2),
            "click_rate": round((avg_click_rate - benchmarks["click_rate"]) * 100, 2),
            "ctor": round((avg_ctor - benchmarks["ctor"]) * 100, 2)
        },
        "email_performance": email_performance,
        "top_emails": email_performance[:10],
        "worst_emails": sorted(email_performance, key=lambda x: x["open_rate"])[:5],
        "type_performance": type_performance,
        "segment_performance": segment_performance,
        "best_days": [(d, round(s["opens"] / max(s["sends"], 1) * 100, 2))
                      for d, s in best_days[:5]],
        "best_hours": [(h, round(s["opens"] / max(s["sends"], 1) * 100, 2))
                       for h, s in best_hours[:5]]
    }

    return results


def analyze_ga4_data(ga4_data):
    """Analyze GA4 email traffic metrics."""
    results = {}

    # Email channel overview
    channel = ga4_data.get("channel_overview", [])
    email_channel = next((r for r in channel
                          if r.get("sessionDefaultChannelGroup") == "Email"), {})

    results["email_overview"] = {
        "sessions": int(email_channel.get("sessions", 0)),
        "active_users": int(email_channel.get("activeUsers", 0)),
        "new_users": int(email_channel.get("newUsers", 0)),
        "bounce_rate": round(float(email_channel.get("bounceRate", 0)) * 100, 2),
        "avg_session_duration": round(float(email_channel.get("averageSessionDuration", 0)), 1),
        "pages_per_session": round(float(email_channel.get("screenPageViewsPerSession", 0)), 2)
    }

    # Benchmark: email vs other channels
    benchmark = ga4_data.get("site_benchmark", [])
    total_sessions = sum(int(r.get("sessions", 0)) for r in benchmark)
    channel_share = {}
    for r in benchmark:
        ch = r["sessionDefaultChannelGroup"]
        sess = int(r.get("sessions", 0))
        channel_share[ch] = {
            "sessions": sess,
            "share": round(sess / total_sessions * 100, 2) if total_sessions > 0 else 0,
            "bounce_rate": round(float(r.get("bounceRate", 0)) * 100, 2),
            "avg_duration": round(float(r.get("averageSessionDuration", 0)), 1)
        }
    results["channel_share"] = channel_share

    # Monthly trend
    monthly = ga4_data.get("email_by_month", [])
    monthly_trend = []
    for m in sorted(monthly, key=lambda x: x.get("yearMonth", "")):
        month_str = m.get("yearMonth", "")
        if len(month_str) == 6:
            month_label = f"{month_str[4:6]}/{month_str[:4]}"
        else:
            month_label = month_str
        monthly_trend.append({
            "month": month_label,
            "sessions": int(m.get("sessions", 0)),
            "active_users": int(m.get("activeUsers", 0)),
            "new_users": int(m.get("newUsers", 0)),
            "engaged_sessions": int(m.get("engagedSessions", 0)),
            "bounce_rate": round(float(m.get("bounceRate", 0)) * 100, 2),
            "avg_duration": round(float(m.get("averageSessionDuration", 0)), 1)
        })
    results["monthly_trend"] = monthly_trend

    # Daily trend (for dynamic JS filtering)
    daily = ga4_data.get("email_by_date", [])
    daily_trend = []
    for d in sorted(daily, key=lambda x: x.get("date", "")):
        daily_trend.append({
            "date": d.get("date", ""),
            "sessions": int(d.get("sessions", 0)),
            "active_users": int(d.get("activeUsers", 0)),
            "new_users": int(d.get("newUsers", 0)),
            "engaged_sessions": int(d.get("engagedSessions", 0)),
            "bounce_rate": round(float(d.get("bounceRate", 0)) * 100, 2),
            "avg_duration": round(float(d.get("averageSessionDuration", 0)), 1)
        })
    results["daily_trend"] = daily_trend

    # Campaign performance
    campaigns = ga4_data.get("email_campaigns_utm", [])
    camp_perf = []
    for c in sorted(campaigns, key=lambda x: int(x.get("sessions", 0)), reverse=True):
        if c.get("sessionCampaignName") not in ["(not set)", "(direct)"]:
            camp_perf.append({
                "campaign": c.get("sessionCampaignName", "N/A"),
                "sessions": int(c.get("sessions", 0)),
                "users": int(c.get("activeUsers", 0)),
                "new_users": int(c.get("newUsers", 0)),
                "bounce_rate": round(float(c.get("bounceRate", 0)) * 100, 2),
                "avg_duration": round(float(c.get("averageSessionDuration", 0)), 1),
                "engaged": int(c.get("engagedSessions", 0)),
                "conversions": int(c.get("conversions", 0))
            })
    results["campaign_performance"] = camp_perf[:20]

    # Landing pages
    landing = ga4_data.get("email_landing_pages", [])
    lp_perf = []
    for lp in sorted(landing, key=lambda x: int(x.get("sessions", 0)), reverse=True):
        lp_perf.append({
            "page": lp.get("landingPage", "N/A"),
            "sessions": int(lp.get("sessions", 0)),
            "users": int(lp.get("activeUsers", 0)),
            "bounce_rate": round(float(lp.get("bounceRate", 0)) * 100, 2),
            "avg_duration": round(float(lp.get("averageSessionDuration", 0)), 1),
            "conversions": int(lp.get("conversions", 0))
        })
    results["landing_pages"] = lp_perf[:15]

    # Device breakdown
    devices = ga4_data.get("email_devices", [])
    device_summary = defaultdict(lambda: {"sessions": 0, "users": 0})
    for d in devices:
        cat = d.get("deviceCategory", "unknown")
        device_summary[cat]["sessions"] += int(d.get("sessions", 0))
        device_summary[cat]["users"] += int(d.get("activeUsers", 0))
        device_summary[cat]["bounce_rate"] = round(float(d.get("bounceRate", 0)) * 100, 2)
    results["devices"] = dict(device_summary)

    # Best days/hours from GA4
    dayofweek = ga4_data.get("email_by_dayofweek", [])
    day_names = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
    day_sessions = defaultdict(int)
    hour_sessions = defaultdict(int)

    for d in dayofweek:
        day = int(d.get("dayOfWeek", 0))
        hour = int(d.get("hour", 0))
        sessions = int(d.get("sessions", 0))
        day_sessions[day_names[day]] += sessions
        hour_sessions[hour] += sessions

    results["best_days_ga4"] = sorted(day_sessions.items(), key=lambda x: x[1], reverse=True)[:7]
    results["best_hours_ga4"] = sorted(hour_sessions.items(), key=lambda x: x[1], reverse=True)[:8]

    return results


def generate_insights(rds_analysis, ga4_analysis):
    """Generate strategic insights and recommendations."""
    insights = []
    recommendations = []

    if rds_analysis.get("summary"):
        s = rds_analysis["summary"]
        benchmarks = rds_analysis.get("benchmarks", {})

        # Open rate analysis
        or_diff = rds_analysis.get("performance_vs_benchmark", {}).get("open_rate", 0)
        if or_diff > 5:
            insights.append({
                "type": "positive",
                "icon": "🎯",
                "category": "Deliverability",
                "title": f"Taxa de abertura acima da média: {s['avg_open_rate']}%",
                "detail": f"A taxa de abertura está {or_diff:.1f}pp acima do benchmark do mercado ({benchmarks.get('open_rate', 22)}%). Indica forte reconhecimento da marca IAB e relevância dos assuntos.",
                "priority": "high"
            })
        elif or_diff < -5:
            insights.append({
                "type": "alert",
                "icon": "⚠️",
                "category": "Deliverability",
                "title": f"Taxa de abertura abaixo da média: {s['avg_open_rate']}%",
                "detail": f"A taxa de abertura está {abs(or_diff):.1f}pp abaixo do benchmark ({benchmarks.get('open_rate', 22)}%). Oportunidade crítica de melhoria em linha de assunto e pré-header.",
                "priority": "critical"
            })

        # Bounce rate
        if s["avg_bounce_rate"] > 3:
            insights.append({
                "type": "alert",
                "icon": "🔴",
                "category": "Entregabilidade",
                "title": f"Taxa de bounce elevada: {s['avg_bounce_rate']}%",
                "detail": "Taxa de bounce acima de 3% pode prejudicar a reputação do domínio sender. Recomenda-se higienização imediata da base de contatos.",
                "priority": "critical"
            })

        # CTOR analysis
        if s["avg_ctor"] > 15:
            insights.append({
                "type": "positive",
                "icon": "✅",
                "category": "Engajamento",
                "title": f"CTOR (Click-to-Open Rate) excelente: {s['avg_ctor']}%",
                "detail": "O CTOR indica que o conteúdo é altamente relevante para quem abre os emails. A segmentação está gerando engajamento qualificado.",
                "priority": "medium"
            })

        # Unsubscribe rate
        if s["total_sends"] > 0:
            unsub_rate = s["total_unsubscribes"] / s["total_sends"] * 100
            if unsub_rate > 0.3:
                insights.append({
                    "type": "alert",
                    "icon": "📉",
                    "category": "Retenção",
                    "title": f"Taxa de descadastros elevada: {unsub_rate:.2f}%",
                    "detail": "Descadastros acima de 0.3% indicam descasamento entre expectativas dos contatos e conteúdo enviado. Revisar segmentação e frequência de envios.",
                    "priority": "high"
                })

    # GA4 insights
    if ga4_analysis.get("email_overview"):
        ov = ga4_analysis["email_overview"]

        if ov["bounce_rate"] < 40:
            insights.append({
                "type": "positive",
                "icon": "🌟",
                "category": "Qualidade do Tráfego",
                "title": f"Taxa de rejeição do tráfego email: {ov['bounce_rate']}%",
                "detail": f"Usuários vindos de email têm engajamento qualificado com bounce rate de {ov['bounce_rate']}%. Média de {ov['avg_session_duration']}s por sessão.",
                "priority": "medium"
            })

        if ov["avg_session_duration"] > 150:
            insights.append({
                "type": "positive",
                "icon": "⏱️",
                "category": "Engajamento no Site",
                "title": f"Alto tempo médio de sessão via email: {ov['avg_session_duration']}s",
                "detail": "Usuários vindos de campanhas de email passam mais tempo no site, indicando alta intenção e relevância do conteúdo acessado.",
                "priority": "medium"
            })

    # Strategic recommendations
    recommendations = [
        {
            "priority": 1,
            "area": "Segmentação",
            "action": "Implementar segmentação comportamental avançada",
            "detail": "Criar segmentos baseados em comportamento de abertura (engajados, inativos, nunca abriram) para personalizar frequência e conteúdo. Audiência inativa há 90+ dias: campanha de reengajamento.",
            "impact": "Alto",
            "effort": "Médio",
            "kpi": "+5-8pp taxa de abertura"
        },
        {
            "priority": 2,
            "area": "Assuntos & Pre-headers",
            "action": "Testar A/B sistematicamente em linhas de assunto",
            "detail": "Implementar programa de A/B test em 100% dos disparos com mínimo 2 variações de assunto. Testar: urgência, personalização, números, perguntas, emojis.",
            "impact": "Alto",
            "effort": "Baixo",
            "kpi": "+10-15% taxa de abertura"
        },
        {
            "priority": 3,
            "area": "Automações",
            "action": "Criar fluxo de Welcome Series para novos contatos",
            "detail": "Sequência automatizada de 5 emails para novos leads: boas-vindas > apresentação IAB > conteúdo top > convite webinar > chamada para associação.",
            "impact": "Alto",
            "effort": "Médio",
            "kpi": "+25% engajamento de novos leads"
        },
        {
            "priority": 4,
            "area": "Timing",
            "action": "Otimizar dia e horário de envio por segmento",
            "detail": "Configurar envios para terça-quinta, entre 9h-11h (melhor engajamento). Usar Send Time Optimization para contatos com histórico de abertura identificado.",
            "impact": "Médio",
            "effort": "Baixo",
            "kpi": "+8-12% taxa de abertura"
        },
        {
            "priority": 5,
            "area": "Entregabilidade",
            "action": "Higienizar base e configurar double opt-in",
            "detail": "Remover emails hard bounce e inativos há 12+ meses. Implementar double opt-in para novos cadastros. Validar configurações SPF, DKIM e DMARC.",
            "impact": "Alto",
            "effort": "Médio",
            "kpi": "Reduzir bounce rate para <2%"
        },
        {
            "priority": 6,
            "area": "CRO",
            "action": "Otimizar CTAs e landing pages de email",
            "detail": "Analisar landing pages mais acessadas via email e otimizar: headline, CTA, formulários. Reduzir atrito para conversão em páginas de eventos e cursos.",
            "impact": "Alto",
            "effort": "Médio",
            "kpi": "+20-30% taxa de conversão via email"
        },
        {
            "priority": 7,
            "area": "UTM & Analytics",
            "action": "Padronizar nomenclatura UTM em todos os disparos",
            "detail": "Implementar padrão utm_source=rdstation | utm_medium=email | utm_campaign=[nome-campanha] em todos os links. Isso permitirá atribuição precisa no GA4.",
            "impact": "Médio",
            "effort": "Baixo",
            "kpi": "100% atribuição de tráfego email"
        },
        {
            "priority": 8,
            "area": "Newsletter",
            "action": "Estruturar newsletter semanal como produto editorial",
            "detail": "Criar template consistente para newsletter com: sumário clicável, destaque de pesquisa, evento da semana, artigo de comitê, CTA de associação. A/B testar frequência (semanal vs quinzenal).",
            "impact": "Médio",
            "effort": "Alto",
            "kpi": "+15% CTOR da newsletter"
        }
    ]

    return insights, recommendations


def main():
    print("=" * 60)
    print("  IAB Brasil — Análise de CRM Email Marketing")
    print("=" * 60)

    rds_data, ga4_data = load_data()

    print("\n🔍 Analisando dados do RD Station Marketing...")
    rds_analysis = analyze_rds_emails(rds_data)

    print("\n🔍 Analisando dados do GA4...")
    ga4_analysis = analyze_ga4_data(ga4_data)

    print("\n💡 Gerando insights estratégicos...")
    insights, recommendations = generate_insights(rds_analysis, ga4_analysis)

    # Compile full analysis
    full_analysis = {
        "generated_at": datetime.now().isoformat(),
        "client": "IAB Brasil",
        "agency": "Ivoire",
        "ga4_raw": ga4_data,
        "rds_raw": {"emails": rds_data.get("emails", []) if rds_data else []},
        "rds_analysis": rds_analysis,
        "ga4_analysis": ga4_analysis,
        "insights": insights,
        "recommendations": recommendations
    }

    # Inject into index.html
    html_file = BASE_DIR / "output" / "index.html"
    if html_file.exists():
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # We will look for a marker in the HTML
        import re
        marker_start = "// AUTO-GENERATED DATA INJECTION POINT"
        marker_end = "// END AUTO-GENERATED DATA"
        pattern = f"({marker_start}).*?({marker_end})"
        
        json_str = json.dumps(full_analysis, ensure_ascii=False)
        replacement = f"\\1\nconst DATA_RAW = {json_str};\n\\2"
        
        new_html = re.sub(pattern, replacement, html_content, flags=re.DOTALL)
        
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(new_html)
        print(f"✅ Injetado no dashboard em: {html_file}")

    print(f"\n   💡 {len(insights)} insights gerados")
    print(f"   📋 {len(recommendations)} recomendações estratégicas")

    return full_analysis

if __name__ == "__main__":
    main()
