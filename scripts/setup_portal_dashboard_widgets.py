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
        <div class="w-9 h-9 rounded-xl bg-teal-500/10 text-teal-400 flex items-center justify-center text-base flex-shrink-0">
          <i class="fas fa-newspaper"></i>
        </div>
        <div class="min-w-0">
          <h2 class="serif-heading text-base font-bold text-white flex flex-wrap items-center gap-2">
            Daily Investigative News Digest
            <span id="news-date-badge" class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-teal-500/15 text-teal-300 border border-teal-500/30">Gemini Semantic</span>
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">Website + 431 bookmarks (companies &amp; domains) + UN, humanitarian &amp; anti-trafficking focus.</p>
        </div>
      </div>
      <div class="flex flex-wrap items-center gap-1.5 flex-shrink-0">
        <button type="button" onclick="toggleSemanticInterestDrawer()" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/70 text-[11px] font-semibold transition flex items-center gap-1" title="Inspect Gemini's semantic description of your interests & inferred companies">
          <i class="fas fa-brain text-teal-400"></i> <span>Profile</span>
        </button>
        <button type="button" onclick="copyDashboardNewsMarkdown()" class="px-2 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/70 text-[11px] font-semibold transition flex items-center gap-1" title="Copy formatted Markdown briefing with citations">
          <i class="fas fa-copy text-sky-400"></i> <span>MD</span>
        </button>
        <button type="button" onclick="emailDashboardNewsDigest()" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-emerald-600/80 text-emerald-300 hover:text-white border border-emerald-500/30 text-[11px] font-semibold transition flex items-center gap-1" title="Draft Daily Investigative News Digest email to islam.akef@gmail.com">
          <i class="fas fa-envelope"></i> <span>Email</span>
        </button>
        <button type="button" id="news-rebuild-profile-btn" onclick="refreshDashboardCuratedNews(true)" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-teal-600/80 text-teal-300 hover:text-white border border-teal-500/30 text-[11px] font-semibold transition flex items-center gap-1" title="Re-parse website + bookmarks and rebuild Gemini interest profile + news">
          <i class="fas fa-magic"></i> <span>Rebuild</span>
        </button>
        <button type="button" id="news-refresh-btn" onclick="refreshDashboardCuratedNews(false)" class="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white text-[11px] font-bold shadow transition flex items-center gap-1" title="Fetch today's top curated investigative briefing">
          <i class="fas fa-sync-alt"></i> <span>Refresh</span>
        </button>
      </div>
    </div>

    <!-- Collapsible Semantic Interest Profile Inspector -->
    <div id="news-profile-drawer" class="hidden bg-slate-950/80 border border-teal-500/30 rounded-xl p-3.5 space-y-2.5 text-xs">
      <div class="flex items-center justify-between gap-2">
        <span class="text-[10px] uppercase tracking-wider font-bold text-teal-300"><i class="fas fa-fingerprint mr-1"></i> Gemini Semantic Interest Profile (Website + Bookmarks + Humanitarian/UN)</span>
        <span id="news-profile-meta" class="text-[10px] font-mono text-slate-400"></span>
      </div>
      <p id="news-profile-summary" class="text-slate-300 leading-relaxed text-[11px]">Click &quot;Refresh&quot; or &quot;Rebuild&quot; to synthesize your semantic interest profile from your website, bookmarks, and humanitarian/UN focus.</p>
      <div id="news-profile-themes" class="flex flex-wrap gap-1.5 pt-0.5"></div>
      <div id="news-profile-companies" class="hidden flex flex-wrap items-center gap-1.5 pt-1 border-t border-slate-800/80"></div>
    </div>

    <!-- Status Banner -->
    <div id="news-status-banner" class="hidden text-[11px] font-mono bg-teal-500/10 border border-teal-500/30 text-teal-200 rounded-xl px-3.5 py-2"></div>

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

<!-- Widget 3: Gmail Inbox Internal News Briefing -->
<section id="dashboard-inbox-news-widget" class="bg-slate-900 p-6 rounded-2xl border border-slate-800/80 shadow-sm space-y-4">
  <div class="flex flex-wrap items-start justify-between gap-3">
    <div class="flex items-center gap-2.5 min-w-0">
      <div class="w-9 h-9 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-base flex-shrink-0">
        <i class="fas fa-inbox"></i>
      </div>
      <div class="min-w-0">
        <h2 class="serif-heading text-base font-bold text-white flex flex-wrap items-center gap-2">
          Inbox Internal News Briefing
          <span id="inbox-news-badge" class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">Gmail Bridge</span>
        </h2>
        <p id="inbox-news-subtitle" class="text-xs text-slate-400 mt-0.5">AI-distilled executive briefing from your Gmail inbox: action items, institutional updates, opportunities &amp; FYI digest.</p>
      </div>
    </div>
    <div class="flex flex-wrap items-center gap-1.5 flex-shrink-0">
      <button type="button" onclick="toggleInboxBridgeConfigDrawer()" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/70 text-[11px] font-semibold transition flex items-center gap-1" title="Configure Gmail Apps Script Bridge">
        <i class="fas fa-plug text-emerald-400"></i> <span>Connect</span>
      </button>
      <button type="button" onclick="copyInboxNewsMarkdown()" class="px-2 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700/70 text-[11px] font-semibold transition flex items-center gap-1" title="Copy Inbox Internal News briefing as Markdown">
        <i class="fas fa-copy text-sky-400"></i> <span>MD</span>
      </button>
      <button type="button" id="inbox-news-refresh-btn" onclick="refreshDashboardInboxNews(true)" class="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-bold shadow transition flex items-center gap-1" title="Fetch recent Gmail threads and synthesize Internal News briefing">
        <i class="fas fa-sync-alt"></i> <span>Scan Inbox</span>
      </button>
    </div>
  </div>

  <!-- Collapsible Gmail Apps Script Bridge Configuration Drawer -->
  <div id="inbox-bridge-config-drawer" class="hidden bg-slate-950/85 border border-emerald-500/30 rounded-xl p-4 space-y-3 text-xs">
    <div class="flex flex-wrap items-center justify-between gap-2">
      <span class="text-[11px] uppercase tracking-wider font-bold text-emerald-300"><i class="fas fa-shield-alt mr-1"></i> Read-Only Gmail Apps Script Bridge</span>
      <button type="button" onclick="copyGmailAppsScriptCode()" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-sky-600 text-sky-300 hover:text-white border border-sky-500/30 text-[11px] font-semibold transition flex items-center gap-1">
        <i class="fas fa-code"></i> Copy Apps Script Code
      </button>
    </div>
    <p class="text-[11px] text-slate-400 leading-relaxed">
      Paste the bridge code into <a href="https://script.google.com" target="_blank" rel="noopener noreferrer" class="text-sky-400 hover:underline font-medium">script.google.com</a>, set your <code class="text-emerald-300">BRIDGE_SECRET</code>, deploy as <strong>Web app</strong> (Execute as: <em>Me</em>, Access: <em>Anyone</em>), and save the <code class="text-slate-200">/exec</code> URL &amp; secret token below. Credentials stay strictly in your browser <code class="text-slate-300">localStorage</code>.
    </p>
    <form onsubmit="saveInboxBridgeConfig(event)" class="grid grid-cols-1 md:grid-cols-12 gap-2.5">
      <div class="md:col-span-6">
        <label class="block text-[10px] uppercase tracking-wider text-slate-400 mb-1">Apps Script Web App URL</label>
        <input type="url" id="inbox-bridge-url-input" placeholder="https://script.google.com/macros/s/.../exec" class="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-lg px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 outline-none" required />
      </div>
      <div class="md:col-span-3">
        <label class="block text-[10px] uppercase tracking-wider text-slate-400 mb-1">Bridge Secret Token</label>
        <input type="password" id="inbox-bridge-token-input" placeholder="Your BRIDGE_SECRET" class="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-lg px-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 outline-none" required />
      </div>
      <div class="md:col-span-3 grid grid-cols-2 gap-2">
        <div>
          <label class="block text-[10px] uppercase tracking-wider text-slate-400 mb-1">Lookback</label>
          <select id="inbox-bridge-days-select" class="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-lg px-2 py-1.5 text-xs text-slate-100 outline-none">
            <option value="3">3 days</option>
            <option value="7" selected>7 days</option>
            <option value="14">14 days</option>
          </select>
        </div>
        <div>
          <label class="block text-[10px] uppercase tracking-wider text-slate-400 mb-1">Max Threads</label>
          <select id="inbox-bridge-limit-select" class="w-full bg-slate-900 border border-slate-700 focus:border-emerald-500 rounded-lg px-2 py-1.5 text-xs text-slate-100 outline-none">
            <option value="15">15</option>
            <option value="25" selected>25</option>
            <option value="40">40</option>
          </select>
        </div>
      </div>
      <div class="md:col-span-12 flex flex-wrap items-center justify-between gap-2 pt-1">
        <label class="flex items-center gap-2 text-[11px] text-slate-300 cursor-pointer select-none">
          <input type="checkbox" id="inbox-bridge-unread-check" class="rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-emerald-500" />
          Unread emails only
        </label>
        <div class="flex items-center gap-2">
          <button type="button" onclick="clearInboxBridgeConfig()" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-rose-600/80 text-slate-300 hover:text-white text-[11px] font-semibold transition">Disconnect</button>
          <button type="submit" class="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-bold shadow transition">Save &amp; Scan Inbox</button>
        </div>
      </div>
    </form>
  </div>

  <!-- Status Banner -->
  <div id="inbox-news-status-banner" class="hidden text-[11px] font-mono bg-emerald-500/10 border border-emerald-500/30 text-emerald-200 rounded-xl px-3.5 py-2"></div>

  <!-- Filter Pills -->
  <div id="inbox-news-filters" class="hidden flex flex-wrap items-center justify-between gap-2">
    <div class="flex flex-wrap items-center gap-1.5">
      <button type="button" data-inbox-filter="all" onclick="setInboxNewsFilter('all')" class="inbox-news-pill px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-600 text-white">All Briefing</button>
      <button type="button" data-inbox-filter="action" onclick="setInboxNewsFilter('action')" class="inbox-news-pill px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700">Action Required</button>
      <button type="button" data-inbox-filter="updates" onclick="setInboxNewsFilter('updates')" class="inbox-news-pill px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700">Work &amp; Research</button>
      <button type="button" data-inbox-filter="opportunities" onclick="setInboxNewsFilter('opportunities')" class="inbox-news-pill px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700">Opportunities &amp; Events</button>
      <button type="button" data-inbox-filter="raw" onclick="setInboxNewsFilter('raw')" class="inbox-news-pill px-2.5 py-1 rounded-full text-[11px] font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700">Recent Threads</button>
    </div>
    <span id="inbox-news-meta" class="text-[10px] font-mono text-slate-400"></span>
  </div>

  <!-- Inbox Internal News Content -->
  <div id="dashboard-inbox-news-body" class="space-y-3">
    <div class="bg-slate-950/60 border border-slate-800/80 rounded-xl p-5 text-center space-y-2.5">
      <p class="text-xs text-slate-300">Connect your read-only <strong>Gmail Apps Script Bridge</strong> to generate a daily <strong>Internal News Briefing</strong> directly from your inbox.</p>
      <button type="button" onclick="toggleInboxBridgeConfigDrawer(true)" class="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold">Connect Gmail Bridge</button>
    </div>
  </div>
</section>
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
