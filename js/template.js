/**
 * Global Site Navigation, Hover Dropdowns & Footer Template Engine
 * Islam Akef Ebeid Academic Website
 *
 * Dynamically renders head font/icon links, the sticky header, multi-level hover
 * dropdown menus (linking EVERY HTML page in the codebase), sub-page global
 * navigation bar, and footer directly from the SQLite database (`window.__SITE_DATABASE`).
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

    function getFallbackNavTree() {
        return [
            {
                nav_key: 'home', label: 'Home', folder: 'home', rel_path: 'pages/home/home.html',
                children: [
                    { label: 'Academic Homepage', sublabel: 'Biography, Research & Selected Papers', rel_path: 'pages/home/home.html', icon_class: 'fas fa-user-graduate', badge_text: 'Main' },
                    { label: 'Executive Personal Portal', sublabel: 'Encrypted Command Center, Bookmarks & Vault', rel_path: 'pages/portal/portal.html', icon_class: 'fas fa-shield-halved', badge_text: 'Private' },
                    { label: 'Root Entry (index.html)', sublabel: 'Canonical Root Redirect', rel_path: 'index.html', icon_class: 'fas fa-link', badge_text: 'Root' }
                ]
            },
            {
                nav_key: 'relations', label: 'Relations', folder: 'relations', rel_path: 'pages/relations/relations.html',
                children: [
                    { label: 'Relations & Academic Network', sublabel: 'Contact Directory, Mentors, Students & Family', rel_path: 'pages/relations/relations.html', icon_class: 'fas fa-address-book', badge_text: 'Directory' },
                    { label: 'Confidential Secure Drop-Box', sublabel: 'Zero-Trust Handshake & Direct Message Relay', rel_path: 'pages/relations/drop.html', icon_class: 'fas fa-key', badge_text: 'Encrypted' }
                ]
            },
            { nav_key: 'education', label: 'Education', folder: 'education', rel_path: 'pages/education/education.html', children: [] },
            {
                nav_key: 'research', label: 'Research', folder: 'research', rel_path: 'pages/research/research.html',
                children: [
                    { label: 'Research Portfolio & Grants', sublabel: 'Biomedical AI, GNNs, Data Quality & VR', rel_path: 'pages/research/research.html', icon_class: 'fas fa-project-diagram', badge_text: 'Portfolio' },
                    { label: 'Data2AI4LifeSciences Lab', sublabel: 'Official TWU Research Laboratory Portal', rel_path: 'pages/research/lab.html', icon_class: 'fas fa-flask', badge_text: 'Lab Site' },
                    { label: 'XLPM & VisInt-X 3D Viewer', sublabel: 'Interactive WebGL Protein Structure & Contact Map', rel_path: 'pages/research/xlpm/index.html', icon_class: 'fas fa-dna', badge_text: '3D Live App' }
                ]
            },
            { nav_key: 'scholarship', label: 'Scholarship', folder: 'scholarship', rel_path: 'pages/scholarship/scholarship.html', children: [] },
            { nav_key: 'teaching', label: 'Teaching', folder: 'teaching', rel_path: 'pages/teaching/teaching.html', children: [] },
            { nav_key: 'service', label: 'Service', folder: 'service', rel_path: 'pages/service/service.html', children: [] },
            {
                nav_key: 'business', label: 'Business', folder: 'business', rel_path: 'pages/business/business.html',
                children: [
                    { label: 'Unity Systems & Consulting', sublabel: 'Startup Profile, Telecom & Government Engineering', rel_path: 'pages/business/business.html', icon_class: 'fas fa-building', badge_text: 'Overview' },
                    { label: 'Unity Systems Storefront', sublabel: 'Commercial Software Catalog, SaaS & Licensing', rel_path: 'pages/business/storefront.html', icon_class: 'fas fa-store', badge_text: 'Storefront' }
                ]
            },
            { nav_key: 'hobbies', label: 'Hobbies', folder: 'hobbies', rel_path: 'pages/hobbies/hobbies.html', children: [] },
            {
                nav_key: 'media', label: 'Media', folder: 'media', rel_path: 'pages/media/media.html',
                children: [
                    { label: 'Media & Invited Talks', sublabel: 'Seminars, Press Features, Op-Eds & Interviews', rel_path: 'pages/media/media.html', icon_class: 'fas fa-newspaper', badge_text: 'Archive' },
                    { label: 'Faculty Presentations Portal', sublabel: 'Interactive Slide Decks Hub & Speaker Notes', rel_path: 'pages/media/talk/index.html', icon_class: 'fas fa-tv', badge_text: 'Portal' },
                    { label: '20-Min Committee Job Talk', sublabel: 'Full Reveal.js Interactive Faculty Slide Deck', rel_path: 'pages/media/talk/talk.html', icon_class: 'fas fa-chalkboard', badge_text: '20-Min Deck' },
                    { label: '10-Min Executive Brief', sublabel: 'Condensed Reveal.js High-Impact Research Deck', rel_path: 'pages/media/talk/summary.html', icon_class: 'fas fa-bolt', badge_text: '10-Min Brief' }
                ]
            },
            { nav_key: 'downloads', label: 'Downloads', folder: 'downloads', rel_path: 'pages/downloads/downloads.html', children: [] }
        ];
    }

    function ensureHeadLink(id, href) {
        if (!document.getElementById(id)) {
            const link = document.createElement('link');
            link.id = id;
            link.rel = 'stylesheet';
            link.href = href;
            document.head.appendChild(link);
        }
    }

    function ensureGlobalStylesAndFavicon(rootPrefix, db, activeSlug) {
        ensureHeadLink('sqlite-font-libertine', 'https://fonts.cdnfonts.com/css/linux-libertine');
        ensureHeadLink('sqlite-font-google', 'https://fonts.googleapis.com/css2?family=Georgia:wght@400;700&family=Cairo:wght@600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');
        ensureHeadLink('sqlite-icons-fa', 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css');

        if (activeSlug === 'xlpm') {
            ensureHeadLink('sqlite-icons-bi', 'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css');
        }

        let fav = document.querySelector("link[rel*='icon']");
        if (!fav) {
            fav = document.createElement('link');
            fav.rel = 'icon';
            document.head.appendChild(fav);
        }
        fav.type = 'image/x-icon';
        fav.href = `${rootPrefix}images/favicon.ico`;

        if (!document.getElementById('sqlite-global-base-style')) {
            const styleEl = document.createElement('style');
            styleEl.id = 'sqlite-global-base-style';
            const globalCss = (db && db.stylesheets && db.stylesheets.global_base && db.stylesheets.global_base.css_content)
                ? db.stylesheets.global_base.css_content
                : `
                body, button, input, select, textarea {
                    font-family: "Linux Libertine", "Linux Libertine O", Georgia, "Times New Roman", Times, serif;
                }
                .nav-dropdown-group:hover .nav-dropdown-menu {
                    opacity: 1 !important;
                    visibility: visible !important;
                    transform: translateY(0) !important;
                    pointer-events: auto !important;
                }
                .nav-dropdown-menu {
                    opacity: 0;
                    visibility: hidden;
                    transform: translateY(6px);
                    pointer-events: none;
                    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
                }
                `;
            styleEl.textContent = globalCss;
            document.head.appendChild(styleEl);
        }
    }

    function buildDesktopNavHTML(navTree, rootPrefix, activeSlug, darkTheme) {
        return navTree.map(item => {
            const children = item.children || [];
            const isChildActive = children.some(c => c.rel_path && c.rel_path.includes(activeSlug));
            const isActive = item.folder === activeSlug || item.nav_key === activeSlug || isChildActive;
            const href = `${rootPrefix}${item.rel_path}`;

            const activeClass = darkTheme
                ? 'text-sky-400 font-semibold transition inline-flex items-center gap-1'
                : 'text-sky-600 font-semibold transition inline-flex items-center gap-1';
            const inactiveClass = darkTheme
                ? 'text-slate-300 hover:text-white transition inline-flex items-center gap-1'
                : 'text-gray-600 hover:text-sky-600 transition inline-flex items-center gap-1';

            if (!children.length) {
                return `<a href="${href}" class="${isActive ? activeClass : inactiveClass}">${item.label}</a>`;
            }

            const dropdownItemsHTML = children.map(child => {
                const childHref = `${rootPrefix}${child.rel_path}`;
                const icon = child.icon_class || 'fas fa-file-code';
                const badge = child.badge_text
                    ? `<span class="text-[10px] font-mono uppercase tracking-wider px-1.5 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200 flex-shrink-0">${child.badge_text}</span>`
                    : '';
                return `
                    <a href="${childHref}" class="flex items-start gap-3 p-2.5 rounded-lg hover:bg-sky-50/90 transition group/item">
                        <div class="w-8 h-8 rounded-lg bg-slate-100 text-slate-600 group-hover/item:bg-sky-600 group-hover/item:text-white flex items-center justify-center flex-shrink-0 mt-0.5 transition">
                            <i class="${icon} text-xs"></i>
                        </div>
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center justify-between gap-2">
                                <span class="text-xs font-bold text-gray-900 group-hover/item:text-sky-700 truncate">${child.label}</span>
                                ${badge}
                            </div>
                            ${child.sublabel ? `<p class="text-[11px] text-gray-500 leading-snug mt-0.5 line-clamp-1" style="text-align:left;">${child.sublabel}</p>` : ''}
                        </div>
                    </a>
                `;
            }).join('');

            return `
                <div class="relative nav-dropdown-group py-2">
                    <a href="${href}" class="${isActive ? activeClass : inactiveClass}">
                        <span>${item.label}</span>
                        <i class="fas fa-chevron-down text-[9px] opacity-75 ml-0.5"></i>
                    </a>
                    <div class="nav-dropdown-menu absolute left-0 top-full pt-1 w-80 z-[9999]">
                        <div class="bg-white rounded-xl shadow-2xl border border-gray-200/90 p-2 space-y-1 text-left">
                            ${dropdownItemsHTML}
                        </div>
                    </div>
                </div>
            `;
        }).join('\n                    ');
    }

    function buildMobileNavHTML(navTree, rootPrefix, activeSlug) {
        return navTree.map(item => {
            const children = item.children || [];
            const isActive = item.folder === activeSlug || item.nav_key === activeSlug;
            const href = `${rootPrefix}${item.rel_path}`;
            const activeClass = 'block px-3 py-2 text-sky-600 font-semibold bg-sky-50 rounded';
            const inactiveClass = 'block px-3 py-2 text-gray-700 hover:bg-sky-50 rounded font-medium';

            let html = `<a href="${href}" class="${isActive ? activeClass : inactiveClass}">${item.label}</a>`;
            if (children.length > 0) {
                const subLinks = children.map(child => {
                    const cHref = `${rootPrefix}${child.rel_path}`;
                    return `<a href="${cHref}" class="block pl-7 pr-3 py-1.5 text-xs text-gray-600 hover:text-sky-600 hover:bg-sky-50/60 rounded flex items-center justify-between">
                        <span><i class="${child.icon_class || 'fas fa-angle-right'} w-4 text-sky-600"></i> ${child.label}</span>
                        ${child.badge_text ? `<span class="text-[10px] font-mono bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">${child.badge_text}</span>` : ''}
                    </a>`;
                }).join('\n');
                html += `\n<div class="space-y-0.5 border-l-2 border-sky-100 ml-3 mb-1">\n${subLinks}\n</div>`;
            }
            return html;
        }).join('\n                ');
    }

    function renderGlobalTemplate() {
        const db = window.__SITE_DATABASE || null;
        const rootPrefix = getRootPrefix();
        const activeSlug = getActivePageSlug();
        ensureGlobalStylesAndFavicon(rootPrefix, db, activeSlug);

        const navTree = (db && db.navigation_menu && db.navigation_menu.length)
            ? db.navigation_menu
            : getFallbackNavTree();

        const homeHref = `${rootPrefix}pages/home/home.html`;
        const portalHref = `${rootPrefix}pages/portal/portal.html`;
        const emblemSrc = `${rootPrefix}images/Islamic-Pattern-08-min.jpg`;
        const arabicNameSrc = `${rootPrefix}images/arabic-name.png`;
        const sitemapHref = `${rootPrefix}sitemap.xml`;
        const currentYear = (db && db.meta && db.meta.copyright_year) ? db.meta.copyright_year.value : new Date().getFullYear();

        // 1. Render Main Sticky Header (#navbar)
        const header = document.getElementById('navbar');
        if (header && !header.dataset.rendered) {
            header.dataset.rendered = 'true';
            header.className = 'sticky top-0 bg-white/90 backdrop-blur-sm shadow-lg z-50 transition-all duration-300';

            const desktopLinksHTML = buildDesktopNavHTML(navTree, rootPrefix, activeSlug, false);
            const mobileLinksHTML = buildMobileNavHTML(navTree, rootPrefix, activeSlug);

            let tpl = (db && db.html_templates && db.html_templates.global_header)
                ? db.html_templates.global_header.html
                : '';

            header.innerHTML = tpl
                .replace(/\{\{PORTAL_HREF\}\}/g, portalHref)
                .replace(/\{\{EMBLEM_SRC\}\}/g, emblemSrc)
                .replace(/\{\{HOME_HREF\}\}/g, homeHref)
                .replace(/\{\{ARABIC_NAME_SRC\}\}/g, arabicNameSrc)
                .replace(/\{\{DESKTOP_LINKS_HTML\}\}/g, desktopLinksHTML)
                .replace(/\{\{MOBILE_LINKS_HTML\}\}/g, mobileLinksHTML);

            window.addEventListener('scroll', function () {
                if (window.scrollY > 50) {
                    header.classList.add('scrolled');
                } else {
                    header.classList.remove('scrolled');
                }
            });

            const mobileMenuBtn = document.getElementById('mobile-menu-button');
            const mobileMenu = document.getElementById('mobile-menu');
            if (mobileMenuBtn && mobileMenu) {
                mobileMenuBtn.addEventListener('click', () => {
                    mobileMenu.classList.toggle('hidden');
                });
            }
        }

        // 2. Render Compact Global Navigation Bar on Sub-Pages (#global-subpage-nav)
        const subpageNav = document.getElementById('global-subpage-nav');
        if (subpageNav && !subpageNav.dataset.rendered) {
            subpageNav.dataset.rendered = 'true';
            const quickLinksHTML = buildDesktopNavHTML(navTree, rootPrefix, activeSlug, true);
            const pageObj = (db && db.pages) ? db.pages.find(p => p.slug === activeSlug) : null;
            const pageTitle = pageObj ? (pageObj.subtitle || pageObj.title) : document.title;

            let barTpl = (db && db.html_templates && db.html_templates.subpage_global_bar)
                ? db.html_templates.subpage_global_bar.html
                : '';

            subpageNav.innerHTML = barTpl
                .replace(/\{\{HOME_HREF\}\}/g, homeHref)
                .replace(/\{\{PAGE_TITLE\}\}/g, pageTitle)
                .replace(/\{\{SUBPAGE_QUICK_LINKS\}\}/g, quickLinksHTML);
        }

        // 3. Render Global Footer (#footer)
        const footer = document.getElementById('footer');
        if (footer && !footer.dataset.rendered) {
            footer.dataset.rendered = 'true';
            footer.className = 'bg-gray-800 text-white py-6';

            let footerTpl = (db && db.html_templates && db.html_templates.global_footer)
                ? db.html_templates.global_footer.html
                : '';

            footer.innerHTML = footerTpl
                .replace(/\{\{YEAR\}\}/g, currentYear)
                .replace(/\{\{SITEMAP_HREF\}\}/g, sitemapHref)
                .replace(/\{\{PORTAL_HREF\}\}/g, portalHref);
        }
    }

    window.__renderGlobalTemplate = renderGlobalTemplate;

    renderGlobalTemplate();
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', renderGlobalTemplate);
    }
})();
