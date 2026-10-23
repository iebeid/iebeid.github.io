/**
 * Global Site Navigation & Footer Template
 * Islam Akef Ebeid Academic Website
 *
 * =========================================================================
 * SINGLE SOURCE OF TRUTH:
 * To update the top header, navigation links, logo/emblem, or footer
 * across ALL pages of the website, edit THIS SINGLE FILE ONLY.
 * =========================================================================
 */

(function () {
    // ---------------------------------------------------------------------
    // 1. CONFIGURATION: Navigation Menu Items (Order & Destinations)
    // ---------------------------------------------------------------------
    const navItems = [
        { name: 'Home', folder: 'home', file: 'home.html' },
        { name: 'Relations', folder: 'relations', file: 'relations.html' },
        { name: 'Education', folder: 'education', file: 'education.html' },
        { name: 'Research', folder: 'research', file: 'research.html' },
        { name: 'Scholarship', folder: 'scholarship', file: 'scholarship.html' },
        { name: 'Teaching', folder: 'teaching', file: 'teaching.html' },
        { name: 'Service', folder: 'service', file: 'service.html' },
        { name: 'Business', folder: 'business', file: 'business.html' },
        { name: 'Hobbies', folder: 'hobbies', file: 'hobbies.html' },
        { name: 'Media', folder: 'media', file: 'media.html' },
        { name: 'Downloads', folder: 'downloads', file: 'downloads.html' }
    ];

    // ---------------------------------------------------------------------
    // 2. HELPER: Determine Base Path and Active Page
    // ---------------------------------------------------------------------
    function getRootPrefix() {
        const path = window.location.pathname.replace(/\\/g, '/').toLowerCase();
        if (path.endsWith('/index.html') || path.endsWith('/') || !path.includes('/pages/')) {
            return './';
        }
        return '../../';
    }

    function getActivePageFolder() {
        if (document.body && document.body.getAttribute('data-page')) {
            return document.body.getAttribute('data-page').toLowerCase();
        }
        const path = window.location.pathname.replace(/\\/g, '/').toLowerCase();
        for (const item of navItems) {
            if (path.includes('/' + item.folder + '/') || path.endsWith('/' + item.file)) {
                return item.folder;
            }
        }
        return 'home';
    }

    const rootPrefix = getRootPrefix();
    const activeFolder = getActivePageFolder();

    // ---------------------------------------------------------------------
    // 3. GENERATE NAVIGATION LINKS
    // ---------------------------------------------------------------------
    const desktopLinksHTML = navItems.map(item => {
        const isActive = item.folder === activeFolder;
        const href = rootPrefix === './' ? `pages/${item.folder}/${item.file}` : `../${item.folder}/${item.file}`;
        const activeClass = 'text-sky-600 font-semibold transition';
        const inactiveClass = 'text-gray-600 hover:text-sky-600 transition';
        return `<a href="${href}" class="${isActive ? activeClass : inactiveClass}">${item.name}</a>`;
    }).join('\n                    ');

    const mobileLinksHTML = navItems.map(item => {
        const isActive = item.folder === activeFolder;
        const href = rootPrefix === './' ? `pages/${item.folder}/${item.file}` : `../${item.folder}/${item.file}`;
        const activeClass = 'block px-3 py-2 text-sky-600 font-semibold bg-sky-50 rounded';
        const inactiveClass = 'block px-3 py-2 text-gray-600 hover:bg-sky-50 rounded';
        return `<a href="${href}" class="${isActive ? activeClass : inactiveClass}">${item.name}</a>`;
    }).join('\n                ');

    // ---------------------------------------------------------------------
    // 4. HEADER HTML TEMPLATE (Islamic-Pattern-08-min.jpg Emblem + Branding)
    // ---------------------------------------------------------------------
    const homeHref = rootPrefix === './' ? 'pages/home/home.html' : '../home/home.html';
    const portalHref = rootPrefix === './' ? 'pages/portal/portal.html' : '../portal/portal.html';
    const emblemSrc = `${rootPrefix}images/Islamic-Pattern-08-min.jpg`;
    const arabicNameSrc = `${rootPrefix}images/arabic-name.png`;

    const headerContent = `
        <div class="container mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between h-16">
                <div class="flex-shrink-0 flex items-center gap-2.5 sm:gap-3">
                    <!-- Circular Emblem Logo Linking to Personal Portal Login -->
                    <a href="${portalHref}" rel="nofollow" title="Open Personal Portal" class="relative w-9 h-9 sm:w-10 sm:h-10 rounded-full overflow-hidden flex-shrink-0 block hover:ring-2 hover:ring-sky-500 hover:scale-105 transition duration-300">
                        <img src="${emblemSrc}" alt="Islamic Pattern Emblem" class="w-full h-full object-cover">
                    </a>
                    <!-- Name & Arabic Calligraphy Linking to Home Page -->
                    <a href="${homeHref}" class="flex items-center gap-2 group">
                        <span class="text-lg sm:text-xl font-bold text-gray-800 group-hover:text-sky-700 transition">Islam Akef Ebeid</span>
                        <img src="${arabicNameSrc}" alt="Arabic Name" class="inline-block h-7 sm:h-8 ml-0.5">
                    </a>
                </div>
                <nav class="hidden md:flex md:items-center md:space-x-8">
                    ${desktopLinksHTML}
                </nav>
                <div class="md:hidden flex items-center">
                    <button id="mobile-menu-button" class="text-gray-600 hover:text-gray-900 focus:outline-none" aria-label="Toggle menu">
                        <i class="fas fa-bars text-xl"></i>
                    </button>
                </div>
            </div>
            <!-- Mobile Menu -->
            <div id="mobile-menu" class="hidden md:hidden pb-4 space-y-2 border-t border-gray-100 pt-2">
                ${mobileLinksHTML}
            </div>
        </div>
    `;

    // ---------------------------------------------------------------------
    // 5. FOOTER HTML TEMPLATE
    // ---------------------------------------------------------------------
    const currentYear = new Date().getFullYear();
    const sitemapHref = `${rootPrefix}sitemap.xml`;
    const portalHref = rootPrefix === './' ? 'pages/portal/portal.html' : '../portal/portal.html';
    const footerContent = `
        <div class="container mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm">
            <p>&copy; <span id="year">${currentYear}</span> Islam Akef Ebeid. All Rights Reserved. <span class="mx-2 text-gray-500">&bull;</span> <a href="${sitemapHref}" target="_blank" class="text-gray-400 hover:text-sky-400 transition underline underline-offset-2">Sitemap</a> <span class="mx-2 text-gray-500">&bull;</span> <a href="${portalHref}" class="text-gray-400 hover:text-sky-400 transition underline underline-offset-2" title="Private Executive Portal"><i class="fas fa-lock text-[10px] mr-0.5"></i> Portal</a></p>
        </div>
    `;

    // ---------------------------------------------------------------------
    // 6. RENDER LOGIC & EVENT LISTENERS
    // ---------------------------------------------------------------------
    
    // Ensure Favicon Tab Icon in <head>
    // Ensure Linux Libertine font & Fallback Stack in <head>
    function ensureFont() {
        if (!document.querySelector('link[href*="linux-libertine"]')) {
            const fontLink = document.createElement('link');
            fontLink.rel = 'stylesheet';
            fontLink.href = 'https://fonts.cdnfonts.com/css/linux-libertine';
            document.head.appendChild(fontLink);
        }
        if (!document.getElementById('site-global-font-style')) {
            const style = document.createElement('style');
            style.id = 'site-global-font-style';
            style.textContent = `
                body, button, input, select, textarea {
                    font-family: "Linux Libertine", "Linux Libertine O", Georgia, "Times New Roman", Times, serif !important;
                }
            `;
            document.head.appendChild(style);
        }
    }

    function ensureFavicon() {
        let link = document.querySelector("link[rel*='icon']");
        if (!link) {
            link = document.createElement('link');
            link.rel = 'icon';
            document.head.appendChild(link);
        }
        link.type = 'image/x-icon';
        link.href = `${rootPrefix}images/favicon.ico`;
    }

    function renderComponents() {
        document.title = 'Islam Akef Ebeid';
        ensureFont();
        ensureFavicon();
        const header = document.getElementById('navbar') || document.querySelector('header');
        if (header && !header.dataset.rendered) {
            header.dataset.rendered = 'true';
            header.className = 'sticky top-0 bg-white/90 backdrop-blur-sm shadow-lg z-50 transition-all duration-300';
            header.innerHTML = headerContent;

            // Scroll blur/shadow behavior
            window.addEventListener('scroll', function () {
                if (window.scrollY > 50) {
                    header.classList.add('scrolled');
                } else {
                    header.classList.remove('scrolled');
                }
            });

            // Mobile menu toggle behavior
            const mobileMenuBtn = document.getElementById('mobile-menu-button');
            const mobileMenu = document.getElementById('mobile-menu');
            if (mobileMenuBtn && mobileMenu) {
                mobileMenuBtn.addEventListener('click', () => {
                    mobileMenu.classList.toggle('hidden');
                });
                const mobileLinks = mobileMenu.getElementsByTagName('a');
                for (let link of mobileLinks) {
                    link.addEventListener('click', () => {
                        mobileMenu.classList.add('hidden');
                    });
                }
            }
        }

        const footer = document.getElementById('footer') || document.querySelector('footer');
        if (footer && !footer.dataset.rendered) {
            footer.dataset.rendered = 'true';
            footer.className = 'bg-gray-800 text-white py-6';
            footer.innerHTML = footerContent;
        }
    }

    // Run as early as possible
    renderComponents();
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', renderComponents);
    }
})();
