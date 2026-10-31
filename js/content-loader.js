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
                <div class="bg-white p-6 rounded-xl shadow-md border-l-4 border-indigo-600 hover:shadow-lg transition">
                    <div class="flex items-center justify-between gap-2 mb-2">
                        <span class="text-xs font-mono font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded border border-indigo-200">${c.code}</span>
                        <span class="text-xs text-gray-500 font-medium">${c.institution}</span>
                    </div>
                    <h3 class="text-lg font-bold text-gray-900 mb-2">${c.title}</h3>
                    <p class="text-sm text-gray-600 mb-4">${c.description}</p>
                    ${c.syllabus_path ? `<a href="${ROOT_PREFIX}${c.syllabus_path}" target="_blank" class="inline-flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800"><i class="fas fa-file-pdf"></i> Download Official Syllabus</a>` : ''}
                </div>
            `).join('');
        }

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
