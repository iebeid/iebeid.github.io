#!/usr/bin/env python3
"""
Idempotently injects (or updates) the `tab-projects` Projects & Drive Hub tab
and `#project-editor-modal` inside `portal.portal_app` in `data/content.db`.
"""

import re
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"

NAV_BUTTON_HTML = """<!-- PORTAL_PROJECTS_NAV_START -->
<button class="tab-btn px-4 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white transition flex items-center gap-2 flex-shrink-0" data-tab="tab-projects">
<i class="fas fa-project-diagram"></i> <span>Projects &amp; Drive Hub</span>
</button>
<!-- PORTAL_PROJECTS_NAV_END -->"""

FULL_STATE_BUTTONS_HTML = """<!-- PORTAL_FULL_STATE_IO_START -->
<button type="button" class="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold transition inline-flex items-center gap-1.5" onclick="exportFullPortalState()">
<i class="fas fa-file-export"></i> Export Full Portal State (.json)
</button>
<button type="button" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition inline-flex items-center gap-1.5" onclick="triggerImportPortalState()">
<i class="fas fa-file-import"></i> Import Portal State / Bookmarks (.json)
</button>
<input type="file" id="portal-state-import-file" accept=".json" class="hidden" onchange="handleImportPortalStateFile(event)" />
<!-- PORTAL_FULL_STATE_IO_END -->"""

GITHUB_SETTINGS_CARD_HTML = """<!-- PORTAL_GITHUB_SETTINGS_START -->
<div class="p-6 rounded-xl bg-slate-800/40 border border-slate-700/80 space-y-4">
  <div class="flex items-center justify-between gap-2">
    <h3 class="text-sm font-bold text-slate-200 flex items-center gap-2">
      <i class="fab fa-github text-sky-400"></i> GitHub Direct Publish (Zero-Server Sync)
    </h3>
    <span id="github-pat-status-badge" class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">Not Configured</span>
  </div>
  <p class="text-xs text-slate-400 leading-relaxed">
    Publish projects, website card placements, encrypted master records, and bookmarks directly from <code class="text-sky-300">https://iebeid.github.io/pages/portal/portal.html</code> with no local server. Stored only in your browser's localStorage.
  </p>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl">
    <div>
      <label class="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Repository (owner/repo)</label>
      <input id="settings-github-repo" type="text" value="iebeid/iebeid.github.io" class="w-full bg-slate-800 border border-slate-700 focus:border-sky-500 rounded-lg px-3 py-2 text-xs text-white outline-none font-mono" />
    </div>
    <div>
      <label class="block text-[11px] font-semibold text-slate-400 uppercase mb-1">Branch</label>
      <input id="settings-github-branch" type="text" value="main" class="w-full bg-slate-800 border border-slate-700 focus:border-sky-500 rounded-lg px-3 py-2 text-xs text-white outline-none font-mono" />
    </div>
  </div>
  <div class="space-y-2 max-w-2xl">
    <label class="block text-[11px] font-semibold text-slate-400 uppercase">Fine-Grained GitHub PAT (Contents: Read &amp; Write on this repo)</label>
    <div class="relative">
      <input id="settings-github-pat" type="password" placeholder="github_pat_..." class="w-full bg-slate-800 border border-slate-700 focus:border-sky-500 rounded-lg px-3 py-2 text-xs text-white outline-none font-mono pr-10" />
      <button type="button" onclick="toggleGithubPatVisibility()" class="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-200">
        <i id="github-pat-eye-icon" class="fas fa-eye text-xs"></i>
      </button>
    </div>
    <div id="github-pat-msg" class="text-xs hidden font-medium"></div>
    <div class="flex flex-wrap items-center gap-2 pt-1">
      <button type="button" onclick="saveGithubPublishSettings()" class="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold transition">
        <i class="fas fa-check mr-1"></i> Save GitHub Config
      </button>
      <button type="button" onclick="testGithubPublishConnection()" class="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold border border-slate-700 transition">
        <i class="fas fa-vial mr-1"></i> Test Connection
      </button>
      <button type="button" onclick="clearGithubPublishSettings()" class="px-3.5 py-2 bg-slate-800 hover:bg-rose-500/20 text-slate-400 hover:text-rose-400 rounded-lg text-xs font-semibold border border-slate-700 transition">
        Clear Token
      </button>
    </div>
  </div>
</div>
<!-- PORTAL_GITHUB_SETTINGS_END -->"""

TAB_MAIN_HTML = """<!-- PORTAL_PROJECTS_TAB_START -->
<!-- ============================================================= -->
<!-- TAB 7: MASTER PROJECTS & WEBSITE PLACEMENTS HUB -->
<!-- ============================================================= -->
<main class="tab-content hidden flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6" id="tab-projects">
  <!-- Mode & Action Bar -->
  <section class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
      <div class="space-y-1">
        <div class="flex flex-wrap items-center gap-2">
          <span class="px-2.5 py-0.5 rounded-full text-[10px] font-mono uppercase tracking-wider bg-sky-500/10 text-sky-300 border border-sky-500/30">Master Portfolio Subschema</span>
          <span id="projects-mode-badge" class="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">Checking backend...</span>
        </div>
        <h2 class="text-xl font-bold text-white">Projects, Google Drive Artifacts &amp; Website Card Routing</h2>
        <p class="text-xs text-slate-400">Browse all canonical and Drive-discovered projects, manage Drive artifact links, and choose exactly which website pages display each card.</p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <button type="button" onclick="openProjectEditorModal()" class="px-3.5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold flex items-center gap-1.5 shadow">
          <i class="fas fa-plus"></i> New Project
        </button>
        <button type="button" id="projects-github-publish-btn" onclick="publishPortalToGithub()" class="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1.5 shadow">
          <i class="fab fa-github"></i> Publish to GitHub <span id="projects-pending-badge" class="hidden px-1.5 py-0.5 rounded bg-slate-950/40 text-[10px] font-mono">0</span>
        </button>
        <button type="button" id="projects-watch-btn" onclick="triggerPortalDriveWatch()" class="hidden px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-500/30 text-xs font-semibold flex items-center gap-1.5">
          <i class="fab fa-google-drive"></i> Scan Drive Updates
        </button>
        <button type="button" id="projects-sync-btn" onclick="triggerPortalSiteSync()" class="hidden px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-emerald-300 border border-emerald-500/30 text-xs font-semibold flex items-center gap-1.5">
          <i class="fas fa-sync-alt"></i> Local SQLite Sync
        </button>
        <button type="button" id="projects-export-patch-btn" onclick="exportPortalProjectPatch()" class="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-semibold flex items-center gap-1.5">
          <i class="fas fa-download"></i> Export Patch <span id="projects-patch-count" class="hidden px-1.5 py-0.5 rounded bg-emerald-500/20 text-[10px] font-mono">0</span>
        </button>
      </div>
    </div>

    <!-- Stats Row -->
    <div id="projects-stats-bar" class="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2 border-t border-slate-800/80">
      <div class="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
        <div class="text-[10px] uppercase tracking-wider text-slate-400">Master Projects</div>
        <div id="proj-stat-total" class="text-lg font-bold text-white mt-0.5">0</div>
      </div>
      <div class="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
        <div class="text-[10px] uppercase tracking-wider text-slate-400">Public on Site</div>
        <div id="proj-stat-public" class="text-lg font-bold text-emerald-400 mt-0.5">0</div>
      </div>
      <div class="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
        <div class="text-[10px] uppercase tracking-wider text-slate-400">Discovered Drafts</div>
        <div id="proj-stat-discovered" class="text-lg font-bold text-amber-400 mt-0.5">0</div>
      </div>
      <div class="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
        <div class="text-[10px] uppercase tracking-wider text-slate-400">Drive Artifacts</div>
        <div id="proj-stat-gdrive" class="text-lg font-bold text-sky-400 mt-0.5">0</div>
      </div>
      <div class="bg-slate-950/60 border border-slate-800 rounded-xl p-3">
        <div class="text-[10px] uppercase tracking-wider text-slate-400">Active Card Slots</div>
        <div id="proj-stat-placements" class="text-lg font-bold text-purple-400 mt-0.5">0</div>
      </div>
    </div>
  </section>

  <!-- Static-Mode Unlock Prompt (shown only if encrypted bundle isn't unlocked in memory yet) -->
  <section id="projects-unlock-card" class="hidden bg-slate-900 border border-amber-500/40 rounded-2xl p-6 shadow-xl">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <h3 class="text-sm font-bold text-amber-300 flex items-center gap-2"><i class="fas fa-lock"></i> Unlock Encrypted Master Portfolio</h3>
        <p class="text-xs text-slate-400 mt-1">Your full Drive project catalog in static mode is AES-256-GCM encrypted. Enter your portal passcode to decrypt all private &amp; discovered projects locally.</p>
      </div>
      <form onsubmit="unlockPortalProjectsBundle(event)" class="flex items-center gap-2">
        <input type="password" id="projects-unlock-pass" placeholder="Master passcode" class="px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-sky-500" required />
        <button type="submit" class="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold">Decrypt</button>
      </form>
    </div>
  </section>

  <!-- Filter & Search Controls -->
  <section id="projects-controls-bar" class="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg space-y-3">
    <div class="flex flex-col md:flex-row gap-3">
      <div class="relative flex-1">
        <i class="fas fa-search absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-xs"></i>
        <input type="text" id="projects-search-input" oninput="onPortalProjectsFilterChange()" placeholder="Search title, slug, summary, tags, Drive path..." class="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500" />
      </div>
      <select id="projects-slot-filter" onchange="onPortalProjectsFilterChange()" class="px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-sky-500">
        <option value="">All Website Placement Slots</option>
      </select>
      <select id="projects-kind-filter" onchange="onPortalProjectsFilterChange()" class="px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-sky-500">
        <option value="">All Project Kinds</option>
        <option value="research">Research</option>
        <option value="software">Software</option>
        <option value="scholarship">Scholarship &amp; Essays</option>
        <option value="poetry">Poetry &amp; Creative</option>
        <option value="teaching">Teaching &amp; Courseware</option>
        <option value="business">Business &amp; Consulting</option>
        <option value="service">Service &amp; Leadership</option>
        <option value="hobby">Hobbies &amp; Travel</option>
        <option value="education">Education</option>
        <option value="relations">Relations &amp; Meetups</option>
        <option value="career">Career Dossier</option>
      </select>
    </div>
    <div class="flex flex-wrap items-center gap-2 text-xs" id="projects-status-pills">
      <button type="button" data-pfilter="all" onclick="setPortalProjectsStatusFilter('all')" class="proj-pill active px-3 py-1 rounded-full bg-sky-600 text-white font-semibold">All</button>
      <button type="button" data-pfilter="placed" onclick="setPortalProjectsStatusFilter('placed')" class="proj-pill px-3 py-1 rounded-full bg-slate-800 text-slate-300 hover:bg-slate-700">Placed on Website</button>
      <button type="button" data-pfilter="discovered" onclick="setPortalProjectsStatusFilter('discovered')" class="proj-pill px-3 py-1 rounded-full bg-slate-800 text-slate-300 hover:bg-slate-700">Discovered Drafts</button>
      <button type="button" data-pfilter="public" onclick="setPortalProjectsStatusFilter('public')" class="proj-pill px-3 py-1 rounded-full bg-slate-800 text-slate-300 hover:bg-slate-700">Public</button>
      <button type="button" data-pfilter="private" onclick="setPortalProjectsStatusFilter('private')" class="proj-pill px-3 py-1 rounded-full bg-slate-800 text-slate-300 hover:bg-slate-700">Private</button>
      <span id="projects-result-count" class="ml-auto text-[11px] font-mono text-slate-400"></span>
    </div>
  </section>

  <!-- Projects List Container -->
  <section id="projects-list-container" class="space-y-3"></section>
  <div id="projects-pagination-bar" class="flex items-center justify-center gap-2 pt-2"></div>
</main>

<!-- Modal: Project Editor, Drive Artifacts & Website Card Placements -->
<div id="project-editor-modal" class="fixed inset-0 z-50 hidden items-center justify-center bg-slate-950/85 backdrop-blur-sm p-4 overflow-y-auto">
  <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-4xl w-full p-6 shadow-2xl space-y-5 my-8 max-h-[90vh] overflow-y-auto">
    <div class="flex items-center justify-between border-b border-slate-800 pb-3">
      <div>
        <h3 id="proj-modal-heading" class="text-lg font-bold text-white">Edit Project</h3>
        <p class="text-xs text-slate-400">Update master record, Drive artifacts, and choose where this project renders on the live site.</p>
      </div>
      <button type="button" onclick="closeProjectEditorModal()" class="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"><i class="fas fa-times"></i></button>
    </div>

    <form id="project-editor-form" onsubmit="submitProjectEditorForm(event)" class="space-y-4">
      <input type="hidden" id="pe-id" />
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1">Title *</label>
          <input type="text" id="pe-title" required class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-sky-500" />
        </div>
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1">Slug</label>
          <input type="text" id="pe-slug" placeholder="auto-generated-from-title" class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs font-mono text-slate-200 focus:outline-none focus:border-sky-500" />
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-4 gap-3">
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1">Project Kind</label>
          <select id="pe-kind" class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white">
            <option value="research">research</option>
            <option value="software">software</option>
            <option value="scholarship">scholarship</option>
            <option value="poetry">poetry</option>
            <option value="teaching">teaching</option>
            <option value="business">business</option>
            <option value="service">service</option>
            <option value="hobby">hobby</option>
            <option value="education">education</option>
            <option value="relations">relations</option>
            <option value="career">career</option>
          </select>
        </div>
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1">Category</label>
          <input type="text" id="pe-category" class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white" />
        </div>
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1">Status</label>
          <input type="text" id="pe-status" placeholder="Active / Published / Draft" class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white" />
        </div>
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1">Discovery State</label>
          <select id="pe-discovery" class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white">
            <option value="canonical">canonical</option>
            <option value="reviewed">reviewed</option>
            <option value="discovered">discovered</option>
            <option value="archived">archived</option>
          </select>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-4 gap-3">
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1">Year Start</label>
          <input type="number" id="pe-year-start" class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white" />
        </div>
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1">Year End</label>
          <input type="number" id="pe-year-end" class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white" />
        </div>
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1">Display Order</label>
          <input type="number" id="pe-order" value="50" class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white" />
        </div>
        <div class="flex items-end pb-2">
          <label class="inline-flex items-center gap-2 text-xs font-semibold text-emerald-300 cursor-pointer">
            <input type="checkbox" id="pe-public" class="accent-emerald-500 w-4 h-4" />
            Public on Website (`is_public`)
          </label>
        </div>
      </div>

      <div>
        <label class="block text-[11px] font-semibold text-slate-300 mb-1">Tagline</label>
        <input type="text" id="pe-tagline" class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white" />
      </div>

      <div>
        <label class="block text-[11px] font-semibold text-slate-300 mb-1">Short Summary *</label>
        <textarea id="pe-summary" rows="2" required class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white"></textarea>
      </div>

      <div>
        <label class="block text-[11px] font-semibold text-slate-300 mb-1">Full Description</label>
        <textarea id="pe-description" rows="3" class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white"></textarea>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1">Tech Stack (comma-separated)</label>
          <input type="text" id="pe-tech" placeholder="Python, PyTorch, ..." class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white" />
        </div>
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1">Tags (comma-separated)</label>
          <input type="text" id="pe-tags" placeholder="Poetry, AI, Grant, ..." class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white" />
        </div>
        <div>
          <label class="block text-[11px] font-semibold text-slate-300 mb-1">Institution / Grant</label>
          <input type="text" id="pe-org" placeholder="TWU / NSF ..." class="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white" />
        </div>
      </div>

      <!-- Website Card Placements Matrix -->
      <div class="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-2">
        <div class="flex items-center justify-between">
          <h4 class="text-xs font-bold text-sky-300 uppercase tracking-wider"><i class="fas fa-th mr-1.5"></i> Website Card Placements</h4>
          <span class="text-[11px] text-slate-400">Checked slots render this project as a card on that page</span>
        </div>
        <div id="pe-placements-grid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-52 overflow-y-auto pr-1"></div>
      </div>

      <!-- Artifacts Panel (Available when editing an existing project) -->
      <div id="pe-artifacts-section" class="bg-slate-950/70 border border-slate-800 rounded-xl p-4 space-y-3">
        <div class="flex items-center justify-between">
          <h4 class="text-xs font-bold text-emerald-300 uppercase tracking-wider"><i class="fab fa-google-drive mr-1.5"></i> Linked Artifacts (Drive URLs, GitHub, Repo)</h4>
          <span class="text-[11px] text-slate-400">Toggle `Public` to control which links export to `public_content.json`</span>
        </div>
        <div id="pe-artifacts-list" class="space-y-1.5 max-h-48 overflow-y-auto"></div>
        <div class="grid grid-cols-1 sm:grid-cols-12 gap-2 pt-2 border-t border-slate-800">
          <select id="pa-type" class="sm:col-span-3 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white">
            <option value="gdrive_folder">gdrive_folder</option>
            <option value="doc">doc / gdoc</option>
            <option value="manuscript">manuscript</option>
            <option value="poem_draft">poem_draft</option>
            <option value="paper_pdf">paper_pdf</option>
            <option value="slides">slides</option>
            <option value="video">video</option>
            <option value="github_repo">github_repo</option>
            <option value="code_repo">code_repo</option>
            <option value="dataset">dataset</option>
            <option value="live_demo">live_demo</option>
          </select>
          <input type="text" id="pa-label" placeholder="Artifact label" class="sm:col-span-3 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white" />
          <input type="text" id="pa-url" placeholder="https://drive.google.com/... or repo path" class="sm:col-span-4 px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white" />
          <button type="button" onclick="addArtifactFromEditor()" class="sm:col-span-2 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold">+ Link</button>
        </div>
      </div>

      <div class="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
        <button type="button" onclick="closeProjectEditorModal()" class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold">Cancel</button>
        <button type="submit" class="px-5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold shadow">Save Project &amp; Placements</button>
      </div>
    </form>
  </div>
</div>
<!-- PORTAL_PROJECTS_TAB_END -->"""


def upsert_block(text: str, start_marker: str, end_marker: str, block: str, fallback_anchor: str, insert_before: bool = True) -> str:
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
    if pattern.search(text):
        return pattern.sub(lambda _: block, text, count=1)
    idx = text.find(fallback_anchor)
    if idx == -1:
        raise RuntimeError(f"Anchor not found: {fallback_anchor}")
    if insert_before:
        return text[:idx] + block + "\n" + text[idx:]
    after = idx + len(fallback_anchor)
    return text[:after] + "\n" + block + text[after:]


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    row = cur.execute(
        "SELECT content_html FROM page_sections WHERE page_slug = ? AND section_key = ?",
        ("portal", "portal_app"),
    ).fetchone()
    if not row:
        raise RuntimeError("portal.portal_app section not found in content.db")

    html = row[0]
    html = upsert_block(
        html,
        "<!-- PORTAL_PROJECTS_NAV_START -->",
        "<!-- PORTAL_PROJECTS_NAV_END -->",
        NAV_BUTTON_HTML,
        '<button class="tab-btn px-4 py-1.5 rounded-lg text-xs font-medium text-slate-300 hover:text-white transition flex items-center gap-2 flex-shrink-0" data-tab="tab-settings">',
        insert_before=True,
    )
    html = upsert_block(
        html,
        "<!-- PORTAL_PROJECTS_TAB_START -->",
        "<!-- PORTAL_PROJECTS_TAB_END -->",
        TAB_MAIN_HTML,
        "<!-- Modal: Add / Edit Credential -->",
        insert_before=True,
    )
    html = upsert_block(
        html,
        "<!-- PORTAL_FULL_STATE_IO_START -->",
        "<!-- PORTAL_FULL_STATE_IO_END -->",
        FULL_STATE_BUTTONS_HTML,
        '<a class="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold border border-slate-700 transition inline-flex items-center gap-1.5" href="../../sitemap.xml"',
        insert_before=True,
    )
    html = upsert_block(
        html,
        "<!-- PORTAL_GITHUB_SETTINGS_START -->",
        "<!-- PORTAL_GITHUB_SETTINGS_END -->",
        GITHUB_SETTINGS_CARD_HTML,
        "<!-- Card 3: Secret Messaging Protocol & Shared Handshake Configuration -->",
        insert_before=True,
    )

    cur.execute(
        "UPDATE page_sections SET content_html = ? WHERE page_slug = ? AND section_key = ?",
        (html, "portal", "portal_app"),
    )
    conn.commit()
    conn.close()
    print("[OK] Updated portal.portal_app with Projects & Drive Hub tab and editor modal.")


if __name__ == "__main__":
    main()
