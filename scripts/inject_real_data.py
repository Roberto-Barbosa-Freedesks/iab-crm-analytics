#!/usr/bin/env python3
"""
inject_real_data.py — Replaces const DATA = {...} in output/index.html
with 100% real values from ga4_raw_data.json and crm_raw_data.json.
NO synthetic or demo data. NO estimates.

Run: python3 scripts/inject_real_data.py
"""
import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

BASE_DIR = Path(__file__).parent.parent
DATA_DIR  = BASE_DIR / "data"
HTML_FILE = BASE_DIR / "output" / "index.html"

# ── Load real data ─────────────────────────────────────────────────────────────
with open(DATA_DIR / "ga4_raw_data.json") as f:
    ga4 = json.load(f)
with open(DATA_DIR / "crm_raw_data.json") as f:
    crm = json.load(f)

# RD Station Marketing (available: workflows, landing pages, forms; analytics endpoints locked)
rds_marketing = {}
rds_marketing_file = DATA_DIR / "rdstation_marketing_data.json"
if rds_marketing_file.exists():
    with open(rds_marketing_file) as f:
        rds_marketing = json.load(f)
    print(f"✓ RD Station Marketing data loaded")
else:
    print("⚠ RD Station Marketing data not found — run 02_fetch_rdstation_marketing_data.py")

# RD Station Marketing — Email CSV exports (real opens, clicks, open rate, CTR, CTOR, delivery)
rds_email_exports = {}
rds_email_file = DATA_DIR / "rdstation_email_exports.json"
if rds_email_file.exists():
    with open(rds_email_file) as f:
        rds_email_exports = json.load(f)
    rds_t = rds_email_exports.get("totals", {})
    print(f"✓ RD Station Email exports loaded — {rds_t.get('total_campaigns',0)} campaigns, "
          f"open rate: {rds_t.get('avg_open_rate',0):.1f}%, "
          f"CTOR: {rds_t.get('avg_ctor',0):.2f}%")
else:
    print("⚠ RD Station Email exports not found — run scripts/05_parse_rdstation_exports.py")

meta = ga4.get("_meta", {})
print(f"✓ GA4 data loaded — fetched: {meta.get('fetched_at','?')[:19]}")
print(f"  Filter: {meta.get('source_filter','?')}")
print(f"✓ CRM data loaded")

# ── 1. MONTHLY TREND (real GA4) ────────────────────────────────────────────────
MO = {"01":"Jan","02":"Fev","03":"Mar","04":"Abr","05":"Mai","06":"Jun",
      "07":"Jul","08":"Ago","09":"Set","10":"Out","11":"Nov","12":"Dez"}

monthly = sorted(ga4['email_by_month'], key=lambda x: x['yearMonth'])
monthlyTrend = []
for m in monthly:
    ym = m['yearMonth']
    lbl = f"{MO[ym[4:6]]}/{ym[2:4]}"
    monthlyTrend.append({
        "month": lbl,
        "sessions": int(m['sessions']),
        "users": int(m['activeUsers']),
        "new_users": int(m.get('newUsers', 0)),
        "engaged": int(m.get('engagedSessions', 0)),
        "bounce_rate": round(float(m.get('bounceRate', 0)) * 100, 1),
        "avg_duration": int(round(float(m.get('averageSessionDuration', 0)))),
        "screen_views": int(m.get('screenPageViews', 0)),
        "conversions": int(m.get('conversions', 0))
    })

rdMonthly = [{"month": m["month"], "sessions": m["sessions"], "users": m["users"],
              "engaged": m["engaged"], "bounce_rate": m["bounce_rate"]} for m in monthlyTrend]

total_sessions = sum(m["sessions"] for m in monthlyTrend)
total_users    = sum(m["users"] for m in monthlyTrend)
total_engaged  = sum(m["engaged"] for m in monthlyTrend)
total_conversions = sum(m["conversions"] for m in monthlyTrend)
total_new_users = sum(m["new_users"] for m in monthlyTrend)
total_screen_views = sum(m["screen_views"] for m in monthlyTrend)
avg_bounce = sum(m["bounce_rate"] * m["sessions"] for m in monthlyTrend) / total_sessions
avg_dur    = sum(m["avg_duration"] * m["sessions"] for m in monthlyTrend) / total_sessions
print(f"\n✓ Monthly trend: {len(monthlyTrend)} months, {total_sessions:,} total sessions")
print(f"  Avg bounce: {avg_bounce:.1f}%, Avg duration: {avg_dur:.0f}s, Engaged: {total_engaged/total_sessions*100:.1f}%")

# ── 2. DAILY DATA (real GA4 — for period filtering) ───────────────────────────
daily_raw = sorted(ga4.get('email_by_date', []), key=lambda x: x['date'])
dailyData = []
for d in daily_raw:
    dailyData.append({
        "date": d['date'],
        "sessions": int(d['sessions']),
        "users": int(d['activeUsers']),
        "new_users": int(d.get('newUsers', 0)),
        "engaged": int(d.get('engagedSessions', 0)),
        "bounce_rate": round(float(d.get('bounceRate', 0)) * 100, 1),
        "avg_duration": int(round(float(d.get('averageSessionDuration', 0)))),
        "screen_views": int(d.get('screenPageViews', 0)),
        "conversions": int(d.get('conversions', 0))
    })
print(f"✓ Daily data: {len(dailyData)} days ({dailyData[0]['date'] if dailyData else 'N/A'} → {dailyData[-1]['date'] if dailyData else 'N/A'})")

# ── 3. CHANNELS (real GA4) ────────────────────────────────────────────────────
CHAN_COLORS = {
    "Organic Search":"#10B981","Direct":"#3B82F6","Email":"#FF6B35",
    "Referral":"#8B5CF6","Unassigned":"#64748B","Organic Social":"#EC4899",
    "Paid Search":"#F59E0B","Organic Video":"#06B6D4","Paid Social":"#EF4444",
    "Paid Other":"#84CC16","Organic Shopping":"#F97316"
}
by_ch = defaultdict(int)
for r in ga4['channel_overview']:
    by_ch[r.get('sessionDefaultChannelGroup', '?')] += int(r.get('sessions', 0))
total_ch = sum(by_ch.values())
channels = [{"name": ch, "sessions": s, "share": round(s / total_ch * 100, 1),
             "color": CHAN_COLORS.get(ch, "#94A3B8")}
            for ch, s in sorted(by_ch.items(), key=lambda x: x[1], reverse=True)]
email_pct = next((c['share'] for c in channels if c['name'] == 'Email'), 0)
print(f"✓ Channels: {len(channels)} channels, {total_ch:,} total site sessions, Email={email_pct}%")

# ── 4. DEVICES (real GA4) ─────────────────────────────────────────────────────
by_dev = defaultdict(int)
for r in ga4['email_devices']:
    by_dev[r.get('deviceCategory', '?')] += int(r.get('sessions', 0))
total_dev = sum(by_dev.values())
DEV = {"desktop": ("Desktop","#FF6B35"), "mobile": ("Mobile","#4ECDC4"), "tablet": ("Tablet","#64748B")}
devices = [{"name": DEV[d][0], "sessions": by_dev.get(d, 0),
            "share": round(by_dev.get(d, 0) / total_dev * 100, 1),
            "color": DEV[d][1]} for d in ['desktop','mobile','tablet'] if d in by_dev]
desktop_pct = next((d['share'] for d in devices if d['name'] == 'Desktop'), 0)
mobile_pct  = next((d['share'] for d in devices if d['name'] == 'Mobile'), 0)
print(f"✓ Devices: Desktop={desktop_pct}%, Mobile={mobile_pct}%")

# ── 5. DAYS & HOURS & HEATMAP (real GA4) ──────────────────────────────────────
DAY_NAMES = ['Dom','Seg','Ter','Qua','Qui','Sex','Sáb']
by_day = defaultdict(int)
by_hour = defaultdict(int)
heatmap_raw = defaultdict(lambda: defaultdict(int))

for r in ga4['email_by_dayofweek']:
    day  = int(r.get('dayOfWeek', 0))
    hour = int(r.get('hour', 0))
    sess = int(r.get('sessions', 0))
    by_day[DAY_NAMES[day]] += sess
    by_hour[hour] += sess
    if 9 <= hour <= 18:
        heatmap_raw[DAY_NAMES[day]][hour] += sess

ga4Days = [{"day": d, "sessions": s}
           for d, s in sorted(by_day.items(), key=lambda x: x[1], reverse=True)]
ga4Hours = [{"hour": f"{h}h", "sessions": s}
            for h, s in sorted(by_hour.items(), key=lambda x: x[1], reverse=True)[:10]]

heatmap = {}
for day in DAY_NAMES:
    heatmap[day] = {h: heatmap_raw[day][h] for h in range(9, 19)}

rdOpensByDay  = [{"day": d, "sessions": s}
                 for d, s in sorted(by_day.items(), key=lambda x: x[1], reverse=True)]
rdOpensByHour = [{"hour": f"{h}h", "sessions": s}
                 for h, s in sorted(by_hour.items(), key=lambda x: x[1], reverse=True)[:10]]

top_day  = ga4Days[0]['day'] if ga4Days else 'Qui'
top_hour = ga4Hours[0]['hour'] if ga4Hours else '11h'
top2_hour= ga4Hours[1]['hour'] if len(ga4Hours) > 1 else '14h'
print(f"✓ Day/Hour: {top_day}={by_day[top_day]:,} (top), {top_hour}={by_hour[int(top_hour[:-1])]:,} (top hour)")

# ── 6. EVENTS (real GA4) ──────────────────────────────────────────────────────
EC = ["#FF6B35","#4ECDC4","#3B82F6","#8B5CF6","#10B981","#F59E0B","#EC4899","#06B6D4","#EF4444","#84CC16","#F97316","#94A3B8"]
events_raw = sorted(ga4['email_events'], key=lambda x: int(x.get('eventCount', 0)), reverse=True)
events = [{"name": e['eventName'], "count": int(e['eventCount']), "color": EC[i % len(EC)]}
          for i, e in enumerate(events_raw)]
print(f"✓ Events: {len(events)} types, top={events[0]['name']} ({events[0]['count']:,})")

# ── 7. CAMPAIGNS (real GA4) ───────────────────────────────────────────────────
def categorize(name):
    n = name.lower()
    if 'ia_summit' in n or 'ia summit' in n: return 'IA Summit'
    elif 'adtech' in n or 'branding' in n:   return 'AdTech & Branding'
    elif 'newsletter' in n or 'iab_news' in n or ('news' in n and 'iab' in n): return 'Newsletter'
    elif 'masterclass' in n or 'curso' in n or 'certif' in n or 'start' in n or 'combo' in n: return 'Cursos'
    elif 'associ' in n:  return 'Associação'
    elif 'relgov' in n:  return 'RelGov'
    elif 'forum' in n:   return 'Fórum'
    else:                return 'Outros'

campaigns_raw = sorted(ga4['email_campaigns_utm'], key=lambda x: int(x.get('sessions', 0)), reverse=True)
named_campaigns = [c for c in campaigns_raw if c.get('sessionCampaignName') not in ['(not set)', '(direct)']]
campaigns = []
for c in named_campaigns[:15]:
    name = c.get('sessionCampaignName', 'N/A')
    campaigns.append({
        "name": name, "category": categorize(name),
        "sessions": int(c.get('sessions', 0)), "users": int(c.get('activeUsers', 0)),
        "bounce_rate": round(float(c.get('bounceRate', 0)) * 100, 1),
        "avg_duration": int(round(float(c.get('averageSessionDuration', 0)))),
        "engaged": int(c.get('engagedSessions', 0))
    })

cat_sess = defaultdict(int); cat_cnt = defaultdict(int)
for c in campaigns_raw:
    cat = categorize(c.get('sessionCampaignName', ''))
    cat_sess[cat] += int(c.get('sessions', 0)); cat_cnt[cat] += 1

CAT_COLORS = {"AdTech & Branding":"#FF6B35","Newsletter":"#4ECDC4","IA Summit":"#3B82F6",
              "Outros":"#64748B","RelGov":"#8B5CF6","Cursos":"#10B981","Associação":"#F59E0B","Fórum":"#EC4899"}
campaignCategories = [{"name": cat, "sessions": s, "campaigns": cat_cnt[cat],
                       "color": CAT_COLORS.get(cat, "#94A3B8")}
                      for cat, s in sorted(cat_sess.items(), key=lambda x: x[1], reverse=True)]
total_named_campaigns = len(named_campaigns)
print(f"✓ Campaigns: {total_named_campaigns} named, {len(campaigns)} top, {len(campaignCategories)} categories")

# ── 8. LANDING PAGES (real GA4) ───────────────────────────────────────────────
lp = defaultdict(lambda: {"sessions":0,"users":0,"bsum":0,"bcnt":0,"dsum":0,"pv":0,"conv":0,"title":""})
for r in ga4['email_landing_pages']:
    p = r.get('landingPage', '?'); sess = int(r.get('sessions', 0))
    lp[p]["sessions"] += sess; lp[p]["users"] += int(r.get('activeUsers', 0))
    lp[p]["pv"] += int(r.get('screenPageViews', 0)); lp[p]["conv"] += int(r.get('conversions', 0))
    if r.get('bounceRate'):
        lp[p]["bsum"] += float(r['bounceRate']) * 100 * sess; lp[p]["bcnt"] += sess
    if r.get('averageSessionDuration'):
        lp[p]["dsum"] += float(r['averageSessionDuration']) * sess
    if r.get('pageTitle') and not lp[p]["title"]: lp[p]["title"] = r['pageTitle'][:60]

landingPages = []
for page, v in sorted(lp.items(), key=lambda x: x[1]['sessions'], reverse=True)[:10]:
    landingPages.append({
        "page": page, "title": v["title"] or page,
        "sessions": v["sessions"], "users": v["users"],
        "bounce_rate": round(v["bsum"] / v["bcnt"], 1) if v["bcnt"] else 0,
        "avg_duration": int(v["dsum"] / v["sessions"]) if v["sessions"] else 0,
        "page_views": v["pv"], "conversions": v["conv"]
    })
print(f"✓ Landing pages: {len(landingPages)} aggregated, top={landingPages[0]['page']} ({landingPages[0]['sessions']:,} sess)")

# ── 9. GEOGRAPHY (real GA4) ────────────────────────────────────────────────────
geo_raw = ga4.get('email_geography', [])
geo_by_country = defaultdict(lambda: {"sessions": 0, "users": 0, "new_users": 0})
for r in geo_raw:
    country = r.get('country', 'Desconhecido')
    geo_by_country[country]["sessions"]  += int(r.get('sessions', 0))
    geo_by_country[country]["users"]     += int(r.get('activeUsers', 0))
    geo_by_country[country]["new_users"] += int(r.get('newUsers', 0))

GEO_COLORS = ["#FF6B35","#4ECDC4","#3B82F6","#8B5CF6","#10B981","#F59E0B","#EC4899","#94A3B8"]
topCountries = [{"country": c, "sessions": v["sessions"], "users": v["users"],
                 "new_users": v["new_users"],
                 "color": GEO_COLORS[i % len(GEO_COLORS)]}
                for i, (c, v) in enumerate(sorted(geo_by_country.items(), key=lambda x: x[1]["sessions"], reverse=True)[:8])]

# Brazil regions
brazil_regions = []
for r in geo_raw:
    if r.get('country') == 'Brazil':
        brazil_regions.append({
            "region": r.get('region', 'Desconhecido').replace('State of ', '').replace(' State', ''),
            "sessions": int(r.get('sessions', 0)),
            "users": int(r.get('activeUsers', 0))
        })
brazil_regions.sort(key=lambda x: x['sessions'], reverse=True)
print(f"✓ Geography: {len(topCountries)} countries, {len(brazil_regions)} Brazil regions")

# ── 10. CRM DATA (real CRM) ──────────────────────────────────────────────────
contacts_list = crm.get('contacts', [])
deals_list    = crm.get('deals', [])
sources_list  = crm.get('sources', [])
products_list = crm.get('products', [])
funnels_raw   = crm.get('funnels', {})
orgs_list     = crm.get('organizations', [])
segments_list = crm.get('segments', [])

# Contacts by month
mo_cnt = defaultdict(int)
for c in contacts_list:
    ca = c.get('created_at', '')
    if ca:
        try:
            dt = datetime.fromisoformat(ca.replace('Z', ''))
            mo_cnt[f"{MO[f'{dt.month:02d}']}/{str(dt.year)[2:]}"] += 1
        except: pass

def month_sort_key(label):
    parts = label.split('/')
    if len(parts) != 2: return 0
    month_names = list(MO.values())
    try:
        mi = month_names.index(parts[0])
        yr = int(parts[1])
        return yr * 12 + mi
    except: return 0

crmContacts = [{"month": k, "contacts": v} for k, v in sorted(
    mo_cnt.items(), key=lambda x: month_sort_key(x[0])) if v > 0]

# Deals by status
deal_status = defaultdict(int)
for d in deals_list: deal_status[d.get('status', '?')] += 1
SL = {"ongoing":"Em Andamento","won":"Ganhos","lost":"Perdidos","paused":"Pausados"}
SC = {"ongoing":"#3B82F6","won":"#10B981","lost":"#EF4444","paused":"#F59E0B"}
dealsByStatus = [{"name": SL.get(s, s), "count": c, "color": SC.get(s, "#94A3B8")}
                 for s, c in sorted(deal_status.items(), key=lambda x: x[1], reverse=True) if c > 0]

# Deals by source
src_map = {s['id']: s['name'] for s in sources_list}
deal_src = defaultdict(int)
for d in deals_list:
    sid = d.get('source_id', '')
    deal_src[src_map.get(sid, 'Desconhecida') if sid else 'Desconhecida'] += 1
SRC_C = ["#64748B","#FF6B35","#10B981","#4ECDC4","#8B5CF6","#F59E0B","#EC4899"]
dealsBySource = [{"name": k, "count": v, "color": SRC_C[i % len(SRC_C)]}
                 for i, (k, v) in enumerate(sorted(deal_src.items(), key=lambda x: x[1], reverse=True))]

# Products by category
pcat = defaultdict(int)
for p in products_list:
    n = p.get('name', '').lower()
    if 'associ' in n:                                                   pcat['Associação'] += 1
    elif 'patrocin' in n:                                               pcat['Patrocínio'] += 1
    elif any(k in n for k in ['evento','summit','forum','webinar']):    pcat['Eventos'] += 1
    elif any(k in n for k in ['curso','masterclass','certif','start','combo']): pcat['Cursos'] += 1
    else:                                                               pcat['Outros'] += 1
PC = {"Associação":"#FF6B35","Outros":"#64748B","Patrocínio":"#8B5CF6","Eventos":"#4ECDC4","Cursos":"#10B981"}
productCategories = [{"name": k, "count": v, "color": PC.get(k, "#94A3B8")}
                     for k, v in sorted(pcat.items(), key=lambda x: x[1], reverse=True)]

# Job titles
titles = Counter(c.get('job_title', '') for c in contacts_list if c.get('job_title', ''))
jobTitles = [{"title": t, "count": c} for t, c in titles.most_common(8)]

# Funnels
funnel_list = funnels_raw.get('data', []) if isinstance(funnels_raw, dict) else []
funnels_data = [{"name": f.get('name', '?'), "stages": len(f.get('stage_ids', []))} for f in funnel_list]

# Pipeline revenue — exclude obvious data entry errors (> R$10M for a single deal)
REVENUE_THRESHOLD = 10_000_000
valid_revenue_deals  = [(d['name'], float(d.get('total_price', 0) or 0)) for d in deals_list
                        if 0 < float(d.get('total_price', 0) or 0) <= REVENUE_THRESHOLD]
invalid_revenue_deals= [(d['name'], float(d.get('total_price', 0) or 0)) for d in deals_list
                        if float(d.get('total_price', 0) or 0) > REVENUE_THRESHOLD]
pipeline_revenue     = sum(p for _, p in valid_revenue_deals)
ongoing_deals        = sum(1 for d in deals_list if d.get('status') == 'ongoing')
won_deals            = sum(1 for d in deals_list if d.get('status') == 'won')

print(f"✓ CRM: {len(contacts_list)} contacts, {len(deals_list)} deals ({ongoing_deals} ongoing, {won_deals} won)")
print(f"  Products: {len(products_list)}, Orgs: {len(orgs_list)}, Segments: {len(segments_list)}")
print(f"  Pipeline revenue: R$ {pipeline_revenue:,.0f} (excl. {len(invalid_revenue_deals)} data-entry outlier(s))")
if invalid_revenue_deals:
    for name, val in invalid_revenue_deals:
        print(f"  ⚠ Outlier excluído: '{name[:50]}' = R$ {val:,.0f} (requer correção no CRM)")

# ── 11. COMPUTE GLOBAL KPIs ───────────────────────────────────────────────────
top_cat = campaignCategories[0] if campaignCategories else {"name":"AdTech & Branding","sessions":0}
top_cat_pct = round(top_cat['sessions'] / total_sessions * 100, 0)

print(f"\n📊 KEY KPIs (GA4 real data):")
print(f"  Sessions:     {total_sessions:,}")
print(f"  Users:        {total_users:,}")
print(f"  New users:    {total_new_users:,}")
print(f"  Engaged:      {total_engaged:,} ({total_engaged/total_sessions*100:.1f}%)")
print(f"  Bounce rate:  {avg_bounce:.1f}%")
print(f"  Avg duration: {avg_dur:.0f}s")
print(f"  Email share:  {email_pct}% of all site traffic")
print(f"  Desktop:      {desktop_pct}%, Mobile: {mobile_pct}%")
print(f"  Top day/hour: {top_day} / {top_hour}")
print(f"  Top category: {top_cat['name']} ({top_cat['sessions']:,} sess, {top_cat_pct:.0f}%)")
print(f"  Named campaigns: {total_named_campaigns}")

# ── 12. BUILD REAL DATA OBJECT ────────────────────────────────────────────────
# Insights and recommendations are preserved from the existing HTML.
# Run this script to update all computed/API fields only.
DATA = {
    "rdMonthly": rdMonthly,
    "monthlyTrend": monthlyTrend,
    "dailyData": dailyData,
    "channels": channels,
    "ga4Days": ga4Days,
    "ga4Hours": ga4Hours,
    "rdOpensByDay": rdOpensByDay,
    "rdOpensByHour": rdOpensByHour,
    "heatmap": heatmap,
    "campaigns": campaigns,
    "campaignCategories": campaignCategories,
    "totalNamedCampaigns": total_named_campaigns,
    "landingPages": landingPages,
    "devices": devices,
    "events": events,
    "emailGeography": topCountries,
    "brazilRegions": brazil_regions,
    "crmContacts": crmContacts,
    "dealsByStatus": dealsByStatus,
    "productCategories": productCategories,
    "dealsBySource": dealsBySource,
    "jobTitles": jobTitles,
    "funnels": funnels_data,

    # RD Station Marketing — Email CSV exports (real data: opens, clicks, rates)
    "rdsEmailMonthly":   rds_email_exports.get("email_monthly", []),
    "rdsTopCampaigns":   rds_email_exports.get("top_campaigns", [])[:15],
    "rdsChannels":       rds_email_exports.get("channels", []),
    "rdsTotals":         rds_email_exports.get("totals", {}),

    # RD Station Marketing — list assets (analytics endpoints locked at current plan)
    "rdsWorkflows": [
        {"name": w.get("name","?"), "status": w.get("configurations",{}).get("status","?"),
         "updated_at": w.get("updated_at","")[:10]}
        for w in rds_marketing.get("workflows", [])
    ],
    "rdsLandingPages": [
        {"title": lp.get("title","?")[:60], "status": lp.get("status","?"),
         "conversion_id": lp.get("conversion_identifier","?")}
        for lp in rds_marketing.get("landing_pages", []) if lp.get("status") == "PUBLISHED"
    ][:20],
    "rdsForms": [
        {"title": f.get("title","?")[:60], "status": f.get("status","?")}
        for f in rds_marketing.get("forms", [])
    ],
    "rdsAnalyticsNote": rds_marketing.get("_meta", {}).get("analytics_note",
        "Endpoints de analytics requerem plano Enterprise RD Station. Use GA4 como fonte principal."),

    "_meta": {
        "fetched_at": meta.get('fetched_at', '')[:10],
        "property_id": meta.get('property_id', ''),
        "source_filter": meta.get('source_filter', ''),
        "period": f"{meta.get('period_start','?')} → {meta.get('period_label','?')}",
        "total_sessions": total_sessions,
        "total_users": total_users,
        "total_engaged": total_engaged,
        "avg_bounce": round(avg_bounce, 1),
        "avg_duration": round(avg_dur, 0),
        "email_pct": email_pct,
        "desktop_pct": desktop_pct,
        "mobile_pct": mobile_pct,
        "top_day": top_day,
        "top_hour": top_hour,
        "pipeline_revenue": int(pipeline_revenue),
        "pipeline_revenue_note": f"{len(invalid_revenue_deals)} deal(s) with value > R$10M excluded as data-entry outliers",
        "total_named_campaigns": total_named_campaigns,
        "crm_contacts": len(contacts_list),
        "crm_deals": len(deals_list),
        "crm_products": len(products_list),
        "crm_orgs": len(orgs_list),
        "crm_segments": len(segments_list),
        "rds_workflows": len(rds_marketing.get("workflows", [])),
        "rds_landing_pages": len(rds_marketing.get("landing_pages", [])),
        "rds_forms": len(rds_marketing.get("forms", [])),
        "rds_analytics_available": rds_marketing.get("_meta", {}).get("analytics_available", False),
        # Email CSV exports — real metrics
        "rds_total_campaigns":   rds_email_exports.get("totals", {}).get("total_campaigns", 0),
        "rds_total_entregues":   rds_email_exports.get("totals", {}).get("total_entregues", 0),
        "rds_total_opens":       rds_email_exports.get("totals", {}).get("total_opens", 0),
        "rds_total_clicks":      rds_email_exports.get("totals", {}).get("total_clicks", 0),
        "rds_total_unsub":       rds_email_exports.get("totals", {}).get("total_unsub", 0),
        "rds_max_list_size":     rds_email_exports.get("totals", {}).get("max_list_size", 0),
        "rds_avg_open_rate":     rds_email_exports.get("totals", {}).get("avg_open_rate", 0),
        "rds_avg_ctr":           rds_email_exports.get("totals", {}).get("avg_ctr", 0),
        "rds_avg_ctor":          rds_email_exports.get("totals", {}).get("avg_ctor", 0),
        "rds_avg_delivery_rate": rds_email_exports.get("totals", {}).get("avg_delivery_rate", 0),
    },
    # Insights and recommendations will be preserved from existing HTML
    "insights": [],
    "recommendations": []
}

# ── 13. SAVE computed_data.json ───────────────────────────────────────────────
computed = {
    "total_sessions": total_sessions, "total_users": total_users,
    "total_engaged": total_engaged, "total_new_users": total_new_users,
    "total_screen_views": total_screen_views, "total_conversions": total_conversions,
    "avg_bounce": round(avg_bounce, 1), "avg_duration": round(avg_dur, 0),
    "desktop_pct": desktop_pct, "mobile_pct": mobile_pct, "email_pct": email_pct,
    "top_day": top_day, "top_hour": top_hour, "top2_hour": top2_hour,
    "top_cat": top_cat['name'], "top_cat_pct": int(top_cat_pct),
    "pipeline_revenue": int(pipeline_revenue),
    "crm_contacts": len(contacts_list), "crm_deals": len(deals_list),
    "crm_products": len(products_list), "crm_orgs": len(orgs_list),
    "crm_segments": len(segments_list),
    "total_named_campaigns": total_named_campaigns,
    "fetched_at": meta.get('fetched_at','')[:10]
}
with open(DATA_DIR / "computed_data.json", "w") as f:
    json.dump(computed, f, indent=2)
print(f"\n✅ Computed data saved to data/computed_data.json")

# ── 14. INJECT INTO index.html ────────────────────────────────────────────────
if not HTML_FILE.exists():
    print(f"❌ HTML not found: {HTML_FILE}")
    exit(1)

with open(HTML_FILE, "r", encoding="utf-8") as f:
    html = f.read()

# --- Preserve existing insights and recommendations from HTML ---
def extract_js_array(html_content, key):
    """Extract a JS array value from the DATA block in the HTML."""
    pattern = rf'"{key}":\s*(\[.*?\])\s*[,\}}]'
    m = re.search(pattern, html_content, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except:
            pass
    return []

existing_insights = extract_js_array(html, "insights")
existing_recs     = extract_js_array(html, "recommendations")
if existing_insights:
    DATA["insights"] = existing_insights
    print(f"  Preserved {len(existing_insights)} insights from HTML")
if existing_recs:
    DATA["recommendations"] = existing_recs
    print(f"  Preserved {len(existing_recs)} recommendations from HTML")

# --- Build the DATA JS block ---
data_json = json.dumps(DATA, ensure_ascii=False, indent=2, default=str)

# Build the full script block replacement
new_data_block = f"""const DATA = {data_json};

DATA.opensHeatmap = DATA.heatmap; // Real GA4 sessions data"""

# --- Find and replace the DATA block in HTML ---
# Pattern: from "const DATA = {" to "DATA.opensHeatmap = DATA.heatmap;"
pattern = r'const DATA = \{.*?\};\s*\n\s*DATA\.opensHeatmap = DATA\.heatmap;[^\n]*'
if re.search(pattern, html, re.DOTALL):
    new_html = re.sub(pattern, new_data_block, html, count=1, flags=re.DOTALL)
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"✅ Dashboard updated: {HTML_FILE}")
    print(f"   Data size: {len(data_json):,} chars")
else:
    # Fallback: try to find just "const DATA = {"
    pattern2 = r'const DATA = \{.*?^\};'
    if re.search(pattern2, html, re.DOTALL | re.MULTILINE):
        new_html = re.sub(pattern2, f"const DATA = {data_json};", html, count=1, flags=re.DOTALL | re.MULTILINE)
        # Add alias after
        new_html = new_html.replace(
            f"const DATA = {data_json};",
            f"const DATA = {data_json};\n\nDATA.opensHeatmap = DATA.heatmap; // Real GA4 sessions data"
        )
        with open(HTML_FILE, "w", encoding="utf-8") as f:
            f.write(new_html)
        print(f"✅ Dashboard updated (fallback pattern): {HTML_FILE}")
    else:
        print(f"❌ Could not find DATA block in HTML. Manual injection required.")
        print(f"   Save the following to replace 'const DATA = {{...}};' in index.html:")
        print(f"\n{new_data_block[:500]}...")

print(f"\n📊 Data is 100% real from:")
print(f"  GA4 Property {meta.get('property_id','?')}: {meta.get('source_filter','?')}")
print(f"  Period: {meta.get('period_start','?')} → {meta.get('period_label','?')}")
print(f"  RD Station CRM: {len(contacts_list)} contacts, {len(deals_list)} deals, {len(orgs_list)} orgs")
