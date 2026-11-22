#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Portal Dashboard Weather & Gemini Semantic Curated News Widgets
======================================================================================
Idempotently injects the Weather/Forecast/Location widget and the Gemini Semantic
Curated News widget into `portal.portal_app` inside `data/content.db`.

Usage:
    python scripts/setup_portal_dashboard_widgets.py
"""

import re
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"

WIDGETS_START = "<!-- PORTAL_DASHBOARD_WIDGETS_START -->"
WIDGETS_END = "<!-- PORTAL_DASHBOARD_WIDGETS_END -->"

DASHBOARD_WIDGETS_HTML = f"""{WIDGETS_START}
<!-- Executive Intelligence Row: Live Weather/Forecast & Gemini Semantic Curated News -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-6" id="dashboard-intel-row">
  <!-- Widget 1: Weather, 5-Day Forecast & Location -->
  <section id="dashboard-weather-widget" class="lg:col-span-5 bg-slate-900 p-6 rounded-2xl border border-slate-800/80 shadow-sm flex flex-col justify-between gap-4">
    <div class="flex items-start justify-between gap-3">
      <div class="flex items-center gap-2.5 min-w-0">
        <div class="w-9 h-9 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center text-base flex-shrink-0">
          <i class="fas fa-cloud-sun"></i>
        </div>
        <div class="min-w-0">
          <h2 class="serif-heading text-base font-bold text-white flex items-center gap-2 truncate">
            Weather &amp; Forecast
            <span id="weather-loc-source" class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700/70">Auto</span>
          </h2>
          <p id="weather-location-label" class="text-xs text-sky-300/90 font-medium truncate mt-0.5">Detecting your location...</p>
        </div>
      </div>
      <div class="flex items-center gap-1.5 flex-shrink-0">
        <button type="button" id="weather-unit-btn" onclick="toggleDashboardWeatherUnit()" class="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-[11px] font-mono font-bold text-slate-300 border border-slate-700/70 transition" title="Toggle °F / °C">°F</button>
        <button type="button" onclick="detectDashboardWeatherLocation(true)" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-sky-400 hover:text-sky-300 border border-slate-700/70 text-xs transition" title="Use my current location"><i class="fas fa-crosshairs"></i></button>
        <button type="button" onclick="refreshDashboardWeather(true)" class="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/70 text-xs transition" title="Refresh weather"><i class="fas fa-sync-alt"></i></button>
      </div>
    </div>

    <!-- City Search Override -->
    <form onsubmit="searchDashboardWeatherCity(event)" class="flex items-center gap-2">
      <div class="relative flex-1">
        <i class="fas fa-map-marker-alt absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 text-xs"></i>
        <input type="text" id="weather-city-input" placeholder="Switch city (e.g. Denton, TX or Cairo)..." class="w-full bg-slate-950/80 border border-slate-800 focus:border-sky-500 rounded-xl pl-8 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 outline-none transition" />
      </div>
      <button type="submit" class="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-sky-600 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700/80 transition">Set</button>
    </form>

    <!-- Current Conditions Hero -->
    <div id="weather-current-box" class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 flex items-center justify-between gap-4">
      <div class="flex items-center gap-3.5">
        <div id="weather-current-icon" class="w-12 h-12 rounded-2xl bg-sky-500/10 text-sky-400 flex items-center justify-center text-2xl flex-shrink-0">
          <i class="fas fa-spinner fa-spin"></i>
        </div>
        <div>
          <div id="weather-current-temp" class="text-3xl font-bold text-white tracking-tight">--°</div>
          <div id="weather-current-desc" class="text-xs text-slate-300 font-medium">Loading live weather...</div>
        </div>
      </div>
      <div id="weather-current-meta" class="text-right text-[11px] text-slate-400 space-y-1 font-mono">
        <div>Feels --°</div>
        <div>Humidity --%</div>
        <div>Wind --</div>
      </div>
    </div>

    <!-- 5-Day Forecast Strip -->
    <div>
      <div class="flex items-center justify-between mb-2">
        <span class="text-[10px] uppercase tracking-wider font-bold text-slate-400">5-Day Forecast</span>
        <span id="weather-updated-at" class="text-[10px] font-mono text-slate-500"></span>
      </div>
      <div id="weather-forecast-grid" class="grid grid-cols-5 gap-2">
        <div class="bg-slate-950/50 border border-slate-800/70 rounded-xl p-2 text-center text-[11px] text-slate-500 col-span-5">Loading 5-day forecast...</div>
      </div>
    </div>
  </section>

  <!-- Widget 2: Gemini Semantic Curated News -->
  <section id="dashboard-news-widget" class="lg:col-span-7 bg-slate-900 p-6 rounded-2xl border border-slate-800/80 shadow-sm flex flex-col gap-4">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="flex items-center gap-2.5 min-w-0">
        <div class="w-9 h-9 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center text-base flex-shrink-0">
          <i class="fas fa-newspaper"></i>
        </div>
        <div class="min-w-0">
          <h2 class="serif-heading text-base font-bold text-white flex flex-wrap items-center gap-2">
            Daily Investigative News Digest
            <span id="news-date-badge" class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-300 border border-purple-500/30">Gemini Semantic</span>
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">Website + 431 bookmarks (companies &amp; domains) + UN, humanitarian &amp; anti-trafficking focus.</p>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-1.5 flex-shrink-0">
        <button type="button" onclick="toggleSemanticInterestDrawer()" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/70 text-[11px] font-semibold transition flex items-center gap-1" title="Inspect Gemini's semantic description of your interests & inferred companies">
          <i class="fas fa-brain text-purple-400"></i> <span>Profile</span>
        </button>
        <button type="button" onclick="copyDashboardNewsMarkdown()" class="px-2 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/70 text-[11px] font-semibold transition flex items-center gap-1" title="Copy formatted Markdown briefing with citations">
          <i class="fas fa-copy text-sky-400"></i> <span>MD</span>
        </button>
        <button type="button" onclick="emailDashboardNewsDigest()" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-emerald-600/80 text-emerald-300 hover:text-white border border-emerald-500/30 text-[11px] font-semibold transition flex items-center gap-1" title="Draft Daily Investigative News Digest email to islam.akef@gmail.com">
          <i class="fas fa-envelope"></i> <span>Email</span>
        </button>
        <button type="button" id="news-rebuild-profile-btn" onclick="refreshDashboardCuratedNews(true)" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-purple-600/80 text-purple-300 hover:text-white border border-purple-500/30 text-[11px] font-semibold transition flex items-center gap-1" title="Re-parse website + bookmarks and rebuild Gemini interest profile + news">
          <i class="fas fa-magic"></i> <span>Rebuild</span>
        </button>
        <button type="button" id="news-refresh-btn" onclick="refreshDashboardCuratedNews(false)" class="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-[11px] font-bold shadow transition flex items-center gap-1" title="Fetch today's top curated investigative briefing">
          <i class="fas fa-sync-alt"></i> <span>Refresh</span>
        </button>
      </div>
    </div>

    <!-- Collapsible Semantic Interest Profile Inspector -->
    <div id="news-profile-drawer" class="hidden bg-slate-950/80 border border-purple-500/30 rounded-xl p-3.5 space-y-2.5 text-xs">
      <div class="flex items-center justify-between gap-2">
        <span class="text-[10px] uppercase tracking-wider font-bold text-purple-300"><i class="fas fa-fingerprint mr-1"></i> Gemini Semantic Interest Profile (Website + Bookmarks + Humanitarian/UN)</span>
        <span id="news-profile-meta" class="text-[10px] font-mono text-slate-500"></span>
      </div>
      <p id="news-profile-summary" class="text-slate-300 leading-relaxed text-[11px]">Click &quot;Refresh&quot; or &quot;Rebuild&quot; to synthesize your semantic interest profile from your website, bookmarks, and humanitarian/UN focus.</p>
      <div id="news-profile-themes" class="flex flex-wrap gap-1.5 pt-0.5"></div>
      <div id="news-profile-companies" class="hidden flex flex-wrap items-center gap-1.5 pt-1 border-t border-slate-800/80"></div>
    </div>

    <!-- Status Banner -->
    <div id="news-status-banner" class="hidden text-[11px] font-mono bg-purple-500/10 border border-purple-500/30 text-purple-200 rounded-xl px-3.5 py-2"></div>

    <!-- Curated News Stories List -->
    <div id="dashboard-news-list" class="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
      <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-5 text-center text-xs text-slate-400">
        Loading your semantic daily news briefing...
      </div>
    </div>

    <!-- Grounded Sources Footer -->
    <div id="news-sources-bar" class="hidden pt-2 border-t border-slate-800/80 flex flex-wrap items-center gap-1.5 text-[10px] text-slate-400"></div>
  </section>
</div>
{WIDGETS_END}"""


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"[ERROR] Database not found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id, content_html FROM page_sections WHERE page_slug='portal' AND section_key='portal_app'"
    ).fetchone()
    if not row:
        raise SystemExit("[ERROR] portal.portal_app section not found")
    sid, html = row

    pattern = re.compile(re.escape(WIDGETS_START) + r".*?" + re.escape(WIDGETS_END), re.S)
    if pattern.search(html):
        new_html = pattern.sub(lambda _: DASHBOARD_WIDGETS_HTML, html, count=1)
    else:
        anchor = "<!-- Remember / Save for Later Section -->"
        idx = html.find(anchor)
        if idx == -1:
            raise SystemExit(f"[ERROR] Anchor not found in portal.portal_app: {anchor}")
        new_html = html[:idx] + DASHBOARD_WIDGETS_HTML + "\n" + html[idx:]

    cur.execute("UPDATE page_sections SET content_html = ? WHERE id = ?", (new_html, sid))
    conn.commit()
    conn.close()
    print("[OK] Injected Weather & Gemini Semantic Curated News widgets into portal.portal_app.")


if __name__ == "__main__":
    main()
