/**
 * Dr. Islam Akef Ebeid - Unified SQLite DOM, CSS & Content Loader Engine
 *
 * Reconstructs 100% of each webpage (CSS stylesheets, HTML templates,
 * navigation chrome, modular sections, metadata, and inline interactive scripts)
 * directly from the SQLite database bundle (`window.__SITE_DATABASE` / `data/content.db`).
 */

(function () {
    'use strict';

    function getRootPrefix() {
        if (document.documentElement && document.documentElement.getAttribute('data-root')) {
            return document.documentElement.getAttribute('data-root');
        }
        if (document.body && document.body.getAttribute('data-root')) {
            return document.body.getAttribute('data-root');
        }
        const path = window.location.pathname.replace(/\\/g, '/').toLowerCase();
        if (path.includes('/pages/research/xlpm/') || path.includes('/pages/media/talk/')) {
            return '../../../';
        }
        if (path.includes('/pages/')) {
            return '../../';
        }
        return './';
    }

    function getActivePageSlug() {
        if (document.documentElement && document.documentElement.getAttribute('data-page')) {
            return document.documentElement.getAttribute('data-page').toLowerCase();
        }
        if (document.body && document.body.getAttribute('data-page')) {
            return document.body.getAttribute('data-page').toLowerCase();
        }
        return 'home';
    }

    const ROOT_PREFIX = getRootPrefix();
    const DATA_URL = `${ROOT_PREFIX}data/public_content.json`;

    function injectStylesheets(db, pageSlug) {
        if (!db || !db.stylesheets) return;

        // 1. Global base stylesheet
        if (db.stylesheets.global_base && !document.getElementById('sqlite-style-global_base')) {
            const globalStyle = document.createElement('style');
            globalStyle.id = 'sqlite-style-global_base';
            globalStyle.textContent = db.stylesheets.global_base.css_content;
            document.head.appendChild(globalStyle);
        }

        // 2. External library stylesheets stored in SQLite (e.g. Reveal.js for talk-deck & talk-summary)
        if (pageSlug === 'talk-deck' || pageSlug === 'talk-summary') {
            const revealKeys = [
                'file_pages_media_talk_reveal_css_reveal_css',
                'file_pages_media_talk_reveal_css_theme_black_css',
                'file_pages_media_talk_reveal_lib_css_zenburn_css',
                'file_pages_media_talk_reveal_css_custom_css'
            ];
            revealKeys.forEach(rk => {
                const rSheet = db.stylesheets[rk];
                if (rSheet && rSheet.css_content && !document.getElementById(`sqlite-${rk}`)) {
                    const st = document.createElement('style');
                    st.id = `sqlite-${rk}`;
                    st.textContent = rSheet.css_content.replace(/\.\.\/\.\.\/lib\/font\//g, 'reveal/lib/font/');
                    document.head.appendChild(st);
                }
            });
        }

        // 3. Page-specific stylesheet
        const styleKey = `style_${pageSlug.replace(/-/g, '_')}`;
        const sheet = db.stylesheets[styleKey];
        if (sheet && sheet.css_content && !document.getElementById(`sqlite-${styleKey}`)) {
            const pageStyle = document.createElement('style');
            pageStyle.id = `sqlite-${styleKey}`;
            pageStyle.textContent = sheet.css_content;
            document.head.appendChild(pageStyle);
        }
    }

    function renderDynamicContent(db) {
        if (!db || window.__SQLITE_DOM_MOUNTED) return;
        window.__SQLITE_DOM_MOUNTED = true;

        const pageSlug = getActivePageSlug();
        const page = (db.pages || []).find(p => p.slug === pageSlug);

        // 1. Inject CSS Stylesheets from SQLite `stylesheets` table
        injectStylesheets(db, pageSlug);

        // 2. Apply page-level HTML/Body classes, Title, Head JSON-LD, and Body Template from SQLite `pages` table
        if (page) {
            if (page.title) {
                document.title = page.title;
            }
            if (page.html_classes && document.documentElement) {
                page.html_classes.split(/\s+/).filter(Boolean).forEach(cls => {
                    document.documentElement.classList.add(cls);
                });
            }
            if (page.body_classes && document.body) {
                page.body_classes.split(/\s+/).filter(Boolean).forEach(cls => {
                    document.body.classList.add(cls);
                });
            }
            if (page.head_html && document.head && !document.getElementById('sqlite-head-extra')) {
                const headContainer = document.createElement('div');
                headContainer.id = 'sqlite-head-extra';
                headContainer.innerHTML = page.head_html;
                while (headContainer.firstChild) {
                    document.head.appendChild(headContainer.firstChild);
                }
            }
            if (page.body_template_html && document.body && document.querySelectorAll('[data-db-section]').length === 0) {
                document.body.insertAdjacentHTML('afterbegin', page.body_template_html);
            }
        }

        // 3. Populate all modular HTML sections [data-db-section="slug.section_key"] from SQLite `page_sections` table
        document.querySelectorAll('[data-db-section]').forEach(el => {
            const attr = el.getAttribute('data-db-section');
            if (!attr || !attr.includes('.')) return;
            const dotIdx = attr.indexOf('.');
            const targetSlug = attr.substring(0, dotIdx);
            const secKey = attr.substring(dotIdx + 1);
            const targetPage = (db.pages || []).find(p => p.slug === targetSlug);
            if (targetPage && targetPage.sections) {
                const section = targetPage.sections.find(s => s.section_key === secKey);
                if (section && section.content_html) {
                    el.outerHTML = section.content_html;
                }
            }
        });

        // 4. Render Global Header, Hover Dropdown Menu Bar, Subpage Bar & Footer from SQLite `navigation_menu` & `html_templates`
        if (typeof window.__renderGlobalTemplate === 'function') {
            window.__renderGlobalTemplate();
        }

        // 5. Populate text and attribute bindings [data-db="site_meta.key"]
        document.querySelectorAll('[data-db]').forEach(el => {
            const key = el.getAttribute('data-db');
            if (key && key.startsWith('site_meta.')) {
                const metaKey = key.replace('site_meta.', '');
                if (db.meta && db.meta[metaKey]) {
                    const val = db.meta[metaKey].value;
                    if (el.tagName.toLowerCase() === 'img') {
                        el.src = val;
                    } else if (el.tagName.toLowerCase() === 'a' && el.getAttribute('data-db-type') === 'href') {
                        el.href = val;
                    } else {
                        el.textContent = val;
                    }
                }
            }
        });

        // 6. Dynamic Publications, Courses & Contacts Containers
        const pubsContainer = document.querySelector('[data-db-container="publications"]');
        if (pubsContainer && db.publications) {
            pubsContainer.innerHTML = db.publications.map(pb => `
                <div class="bg-white p-6 rounded-xl shadow-md border-l-4 border-sky-600 hover:shadow-lg transition">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                        <span class="text-xs font-bold uppercase tracking-wider text-sky-700 font-mono bg-sky-50 px-2.5 py-0.5 rounded border border-sky-200">
                            ${pb.venue} (${pb.year})
                        </span>
                        ${pb.doi ? `<a href="https://doi.org/${pb.doi}" target="_blank" class="text-xs text-slate-500 hover:text-sky-600 font-mono">DOI: ${pb.doi}</a>` : ''}
                    </div>
                    <h3 class="text-lg font-bold text-gray-900 mb-2">${pb.title}</h3>
                    <p class="text-sm text-gray-600 mb-4">${pb.authors}</p>
                    <div class="flex items-center gap-3 pt-3 border-t border-gray-100">
                        ${pb.pdf_path ? `<a href="${ROOT_PREFIX}${pb.pdf_path}" target="_blank" class="text-xs font-semibold text-sky-600 hover:text-sky-800 flex items-center gap-1.5"><i class="fas fa-file-pdf"></i> Read PDF</a>` : ''}
                        ${pb.url ? `<a href="${pb.url}" target="_blank" class="text-xs font-semibold text-slate-600 hover:text-sky-800 flex items-center gap-1.5"><i class="fas fa-external-link-alt"></i> Publisher Link</a>` : ''}
                    </div>
                </div>
            `).join('');
        }

        const coursesContainer = document.querySelector('[data-db-container="courses"]');
        if (coursesContainer && db.courses) {
            coursesContainer.innerHTML = db.courses.map(c => `
                <div class="bg-white p-6 rounded-xl shadow-md border-l-4 border-sky-600 hover:shadow-lg transition">
                    <div class="flex items-center justify-between gap-2 mb-2">
                        <span class="text-xs font-mono font-bold text-sky-700 bg-sky-50 px-2.5 py-1 rounded border border-sky-200">${c.code}</span>
                        <span class="text-xs text-gray-500 font-medium">${c.institution}</span>
                    </div>
                    <h3 class="text-lg font-bold text-gray-900 mb-2">${c.title}</h3>
                    <p class="text-sm text-gray-600 mb-4">${c.description}</p>
                    ${c.syllabus_path ? `<a href="${ROOT_PREFIX}${c.syllabus_path}" target="_blank" class="inline-flex items-center gap-1.5 text-xs font-semibold text-sky-600 hover:text-sky-800"><i class="fas fa-file-pdf"></i> Download Official Syllabus</a>` : ''}
                </div>
            `).join('');
        }

        // 6b. Dynamic Master Project Backbone Containers (`[data-db-projects]`)
        renderProjectContainers(db, ROOT_PREFIX);

        // 7. Execute Page-Specific Interactive Scripts stored in SQLite (`pages.inline_scripts`)
        if (page && page.inline_scripts && page.inline_scripts.trim()) {
            try {
                const scriptEl = document.createElement('script');
                scriptEl.setAttribute('data-sqlite-inline-script', pageSlug);
                scriptEl.textContent = page.inline_scripts;
                document.body.appendChild(scriptEl);
            } catch (err) {
                console.error(`[ContentLoader] Error executing inline script for ${pageSlug}:`, err);
            }
        }
    }

    function escapeProjectHtml(str) {
        return String(str == null ? '' : str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function resolveArtifactHref(url, rootPrefix) {
        if (!url) return '#';
        if (/^(https?:\/\/|mailto:|#)/i.test(url)) return url;
        return `${rootPrefix}${url.replace(/^\.\//, '')}`;
    }

    function getArtifactIcon(type) {
        const map = {
            live_demo: 'fas fa-cube',
            github_repo: 'fab fa-github',
            source_zip: 'fas fa-file-archive',
            dataset: 'fas fa-database',
            paper_pdf: 'fas fa-file-pdf',
            publisher_url: 'fas fa-external-link-alt',
            slides: 'fas fa-chalkboard',
            poster: 'fas fa-image',
            video: 'fas fa-play-circle',
            design_doc: 'fas fa-file-alt',
            lab_portal: 'fas fa-flask',
            pip_command: 'fas fa-terminal'
        };
        return map[type] || 'fas fa-link';
    }

    function formatArtifactLinksHTML(proj, rootPrefix, maxLinks) {
        const links = [];
        // Publications first
        (proj.publications || []).forEach(pub => {
            if (pub.doi) {
                links.push(`<a href="https://doi.org/${escapeProjectHtml(pub.doi)}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-xs font-semibold text-sky-700 hover:underline"><i class="fas fa-book-open"></i> Paper (${escapeProjectHtml(pub.year || '')})</a>`);
            } else if (pub.pdf_path) {
                links.push(`<a href="${resolveArtifactHref(pub.pdf_path, rootPrefix)}" target="_blank" class="inline-flex items-center gap-1 text-xs font-semibold text-sky-700 hover:underline"><i class="fas fa-file-pdf"></i> Paper PDF</a>`);
            }
        });
        // Project artifacts (skip screenshot images in link bar since cards render them visually)
        (proj.artifacts || []).forEach(art => {
            if (art.type === 'screenshot' || art.type === 'thumbnail') return;
            if (art.type === 'pip_command') {
                links.push(`<code class="text-[11px] bg-slate-100 text-slate-800 px-2 py-0.5 rounded border border-slate-200 font-mono">${escapeProjectHtml(art.url)}</code>`);
                return;
            }
            const href = resolveArtifactHref(art.url, rootPrefix);
            const isExt = /^https?:\/\//i.test(art.url) || art.type === 'paper_pdf' || art.type === 'slides' || art.type === 'poster';
            const cls = art.type === 'live_demo'
                ? 'inline-flex items-center gap-1 text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-2 py-0.5 rounded border border-emerald-200 transition'
                : 'inline-flex items-center gap-1 text-xs font-semibold text-sky-700 hover:underline';
            links.push(`<a href="${escapeProjectHtml(href)}" ${isExt ? 'target="_blank" rel="noopener noreferrer"' : ''} class="${cls}"><i class="${getArtifactIcon(art.type)}"></i> ${escapeProjectHtml(art.label)}</a>`);
        });
        const sliced = maxLinks ? links.slice(0, maxLinks) : links;
        return sliced.join('<span class="text-gray-300">&bull;</span>');
    }

    function renderHomeCompactProjects(projects, rootPrefix) {
        return projects.map((p, idx) => {
            const isEmerald = (p.domain_stage === '03_visualization_kpi' || p.category.includes('Bioinformatics') || idx % 2 === 1);
            const iconBg = isEmerald ? 'bg-emerald-100 text-emerald-700' : 'bg-sky-100 text-sky-700';
            const tagCls = isEmerald ? 'tag tag-emerald' : 'tag';
            const iconCls = p.category.includes('Bioinformatics') ? 'fas fa-dna'
                : p.category.includes('Data') ? 'fas fa-layer-group'
                : p.category.includes('Visualization') ? 'fas fa-eye'
                : 'fas fa-project-diagram';
            const badgeText = p.grant_award ? p.grant_award.split('(')[0].trim() : p.category;
            return `
                <div class="bg-slate-50 p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col justify-between hover:border-sky-300 transition">
                    <div>
                        <div class="flex items-center gap-3 mb-3">
                            <div class="w-10 h-10 rounded-lg ${iconBg} flex items-center justify-center flex-shrink-0">
                                <i class="${iconCls}"></i>
                            </div>
                            <div class="min-w-0">
                                <span class="${tagCls}">${escapeProjectHtml(badgeText)}</span>
                                <h3 class="text-xl font-bold text-gray-900 leading-snug">${escapeProjectHtml(p.title)}</h3>
                            </div>
                        </div>
                        <p class="text-gray-700 text-sm leading-relaxed mb-4">${escapeProjectHtml(p.short_summary)}</p>
                    </div>
                    <div class="pt-4 border-t border-slate-200 flex flex-wrap items-center gap-2">
                        ${formatArtifactLinksHTML(p, rootPrefix, 3)}
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderResearchCards(projects, rootPrefix, borderColorClass) {
        const bCls = borderColorClass || 'border-sky-600';
        return projects.map(p => {
            const techPills = (p.tech_stack || []).slice(0, 4).map(t => `<span class="text-[10px] font-mono bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-200">${escapeProjectHtml(t)}</span>`).join('');
            const yearRange = p.year_start ? (p.year_end && p.year_end !== p.year_start ? `${p.year_start}–${p.year_end}` : `${p.year_start}`) : p.status;
            const badgeCls = (p.grant_award && p.grant_award.includes('NSF')) ? 'tag tag-emerald' : 'tag';
            const shots = (p.artifacts || []).filter(a => a.type === 'screenshot' || a.type === 'thumbnail').slice(0, 3);
            const shotsHTML = shots.length > 0
                ? `<div class="grid grid-cols-${shots.length} gap-2 mb-3">${shots.map(s => `<img src="${escapeProjectHtml(resolveArtifactHref(s.url, rootPrefix))}" alt="${escapeProjectHtml(s.label)}" class="h-24 w-full object-contain rounded border border-slate-200 bg-slate-50 p-1">`).join('')}</div>`
                : '';
            return `
                <div class="bg-white p-6 rounded-lg shadow-md border-t-4 ${bCls} flex flex-col justify-between">
                    <div>
                        <div class="flex items-start justify-between gap-2 mb-2">
                            <h3 class="text-xl font-bold text-gray-900">${escapeProjectHtml(p.title)}</h3>
                            <span class="${badgeCls} flex-shrink-0">${escapeProjectHtml(yearRange)}</span>
                        </div>
                        ${p.tagline ? `<p class="text-xs font-semibold text-sky-700 mb-2">${escapeProjectHtml(p.tagline)}</p>` : ''}
                        ${shotsHTML}
                        <p class="text-gray-600 text-sm leading-relaxed mb-3">${escapeProjectHtml(p.short_summary)}</p>
                        ${techPills ? `<div class="flex flex-wrap gap-1.5 mb-4">${techPills}</div>` : ''}
                    </div>
                    <div class="pt-3 border-t border-gray-100 flex flex-wrap items-center gap-2 text-sm">
                        ${formatArtifactLinksHTML(p, rootPrefix, 6)}
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderResearchCodeZips(projects, rootPrefix) {
        const items = [];
        projects.forEach(p => {
            (p.artifacts || []).filter(a => a.type === 'source_zip').forEach(a => {
                items.push({ proj: p, art: a });
            });
        });
        return items.map(({ proj, art }) => {
            const iconCls = art.url.toLowerCase().includes('earth') ? 'fas fa-globe'
                : art.url.toLowerCase().includes('eye') ? 'fas fa-eye'
                : 'fab fa-python';
            return `
                <div class="bg-slate-50 p-5 rounded-lg border border-slate-200 shadow-sm flex flex-col justify-between">
                    <div>
                        <div class="flex items-center gap-3 mb-2">
                            <i class="${iconCls} text-2xl text-slate-700"></i>
                            <h3 class="font-bold text-gray-900 text-base">${escapeProjectHtml(art.label)}</h3>
                        </div>
                        <p class="text-xs text-gray-600 mb-4">From <strong>${escapeProjectHtml(proj.title)}</strong>: ${escapeProjectHtml(proj.short_summary)}</p>
                    </div>
                    <a class="inline-flex items-center gap-2 text-slate-700 hover:text-slate-900 font-bold text-xs uppercase tracking-wider" href="${escapeProjectHtml(resolveArtifactHref(art.url, rootPrefix))}">
                        <i class="fas fa-download"></i> Download Archive (.zip)
                    </a>
                </div>
            `;
        }).join('');
    }

    function renderStorefrontCatalog(projects, rootPrefix) {
        const sfList = projects.filter(p => p.is_storefront);
        const catCounts = { ALL_SYSTEMS: sfList.length, DATA_CURATION: 0, MODELING_ENGINES: 0, VISUALIZATION_REPORTING: 0 };
        sfList.forEach(p => {
            const cats = (p.storefront_category || '').split(/\s+/).filter(Boolean);
            cats.forEach(c => {
                if (catCounts[c] !== undefined) catCounts[c]++;
            });
        });

        const modalSelect = document.getElementById('selected-product');
        if (modalSelect && !modalSelect.dataset.syncedFromDb) {
            modalSelect.dataset.syncedFromDb = 'true';
            modalSelect.innerHTML = sfList.map(p => {
                const label = p.price_display && p.price_display.startsWith('$')
                    ? `${p.title} (${p.price_display})`
                    : `${p.title} (Custom Seat / Enterprise)`;
                return `<option value="${escapeProjectHtml(label)}">${escapeProjectHtml(label)}</option>`;
            }).join('') + '<option value="Custom Research Paper Implementation / Enterprise MSA">Custom Research Paper Implementation / Enterprise MSA</option>';
        }

        const filterBar = `
            <div class="matrix-controls">
                <button class="filter-btn active" onclick="filterSystem('ALL_SYSTEMS', this)">ALL_SYSTEMS (${catCounts.ALL_SYSTEMS})</button>
                <button class="filter-btn" onclick="filterSystem('DATA_CURATION', this)">DATA_CURATION (${catCounts.DATA_CURATION})</button>
                <button class="filter-btn" onclick="filterSystem('MODELING_ENGINES', this)">MODELING_ENGINES (${catCounts.MODELING_ENGINES})</button>
                <button class="filter-btn" onclick="filterSystem('VISUALIZATION_REPORTING', this)">VISUALIZATION_REPORTING (${catCounts.VISUALIZATION_REPORTING})</button>
            </div>
        `;

        const cardsHTML = sfList.map(p => {
            const catAttr = p.storefront_category || 'DATA_CURATION';
            const primaryCatBadge = catAttr.split(/\s+/)[0] || 'SOFTWARE';
            const stackText = (p.tech_stack || []).join(' / ');
            const liveDemo = (p.artifacts || []).find(a => a.type === 'live_demo');
            const repoArt = (p.artifacts || []).find(a => a.type === 'github_repo');
            const primaryLink = liveDemo || repoArt;
            const linkHref = primaryLink ? resolveArtifactHref(primaryLink.url, rootPrefix) : 'https://github.com/iebeid';
            const linkLabel = liveDemo ? 'Launch Live Demo' : 'Source Code';
            const linkIcon = liveDemo ? 'fas fa-cube' : 'fab fa-github';
            const modalLabel = (p.price_display && p.price_display.startsWith('$'))
                ? `${p.title} (${p.price_display})`
                : `${p.title} (Custom Seat / Enterprise)`;
            const priceHTML = (p.price_display && p.price_display.includes('/'))
                ? `$${escapeProjectHtml(p.price_display.replace(/^\$/, '').split('/')[0])}<span>/${escapeProjectHtml(p.price_display.split('/')[1])}</span>`
                : `<span>${escapeProjectHtml(p.price_display || 'Custom Seat / MSA')}</span>`;

            return `
                <article class="product-card" data-category="${escapeProjectHtml(catAttr)}">
                    <div class="card-header">
                        <div class="tag-container">
                            <span class="tech-tag lifecycle">${escapeProjectHtml(primaryCatBadge)}</span>
                            <span class="tech-tag stack">${escapeProjectHtml(stackText)}</span>
                        </div>
                        <h3>${escapeProjectHtml(p.title)}</h3>
                        <p class="description">${escapeProjectHtml(p.full_description || p.short_summary)}</p>
                    </div>
                    ${p.code_snippet ? `<div class="snippet-container"><pre>${escapeProjectHtml(p.code_snippet)}</pre></div>` : ''}
                    <div class="card-footer">
                        <div class="licensing-box">
                            <div class="license-type">${escapeProjectHtml(p.license_model || 'Dual-Licensed: AGPLv3 / Commercial')}</div>
                            <div class="price-tag">${priceHTML}</div>
                        </div>
                        <div class="action-row">
                            <a class="btn btn-oss" href="${escapeProjectHtml(linkHref)}" ${liveDemo ? '' : 'target="_blank" rel="noopener noreferrer"'}><i class="${linkIcon}"></i> ${linkLabel}</a>
                            <button class="btn btn-commercial" onclick="openLicenseModal('${escapeProjectHtml(modalLabel)}')" type="button"><i class="fas fa-key"></i> License Codebase</button>
                        </div>
                    </div>
                </article>
            `;
        }).join('');

        return `${filterBar}<div class="solution-grid">${cardsHTML}</div>`;
    }

    function renderProjectContainers(db, rootPrefix) {
        const projects = (db && Array.isArray(db.projects)) ? db.projects : [];
        if (projects.length === 0) return;

        document.querySelectorAll('[data-db-projects]').forEach(container => {
            const mode = (container.getAttribute('data-db-projects') || 'all').trim();
            const view = (container.getAttribute('data-view') || 'research-cards').trim();
            const filterCat = (container.getAttribute('data-filter-category') || '').trim();
            const filterSlugs = (container.getAttribute('data-filter-slugs') || '').trim();
            const borderCls = container.getAttribute('data-border-class') || 'border-sky-600';
            const limit = parseInt(container.getAttribute('data-limit') || '0', 10);

            let list = [...projects];
            if (mode === 'featured') {
                list = list.filter(p => p.is_featured);
            } else if (mode === 'storefront') {
                list = list.filter(p => p.is_storefront);
            }
            if (filterCat) {
                const allowedCats = filterCat.split('|').map(c => c.trim().toLowerCase());
                list = list.filter(p => allowedCats.includes((p.category || '').toLowerCase()));
            }
            if (filterSlugs) {
                const slugs = filterSlugs.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
                list = list.filter(p => slugs.includes(p.slug.toLowerCase()));
                list.sort((a, b) => slugs.indexOf(a.slug.toLowerCase()) - slugs.indexOf(b.slug.toLowerCase()));
            }
            if (limit > 0) {
                list = list.slice(0, limit);
            }

            if (view === 'home-compact') {
                container.innerHTML = renderHomeCompactProjects(list, rootPrefix);
            } else if (view === 'research-code-zips') {
                container.innerHTML = renderResearchCodeZips(projects, rootPrefix);
            } else if (view === 'storefront-catalog') {
                container.innerHTML = renderStorefrontCatalog(projects, rootPrefix);
            } else {
                container.innerHTML = renderResearchCards(list, rootPrefix, borderCls);
            }
        });
    }

    async function bootDatabaseEngine() {
        if (window.__SITE_DATABASE) {
            renderDynamicContent(window.__SITE_DATABASE);
            return;
        }
        try {
            const resp = await fetch(DATA_URL);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();
            window.__SITE_DATABASE = data;
            renderDynamicContent(data);
        } catch (err) {
            console.warn('[ContentLoader] Could not fetch public_content.json. Ensure data/public_content.js is included.', err);
        }
    }

    // Run synchronously if body is already present so DOM is fully populated before DOMContentLoaded handlers fire
    if (document.body && window.__SITE_DATABASE) {
        renderDynamicContent(window.__SITE_DATABASE);
    } else if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootDatabaseEngine);
    } else {
        bootDatabaseEngine();
    }
})();
