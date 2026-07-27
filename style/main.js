/**
 * --------------------------------------------------------------------------
 * 1. TAILWIND CONFIGURATION
 * --------------------------------------------------------------------------
 * Unified configuration for Litera Platform.
 * Note: If using the Tailwind CDN, this should remain attached to the window object.
 */
window.tailwind = window.tailwind || {};
window.tailwind.config = {
    darkMode: "class",
    theme: {
        extend: {
            colors: {
                "surface-container-low": "#f6f3f2",
                "on-tertiary-fixed-variant": "#574500",
                "on-primary-container": "#ff828a",
                "surface": "#fcf9f8",
                "on-error": "#ffffff",
                "charcoal-muted": "#333333",
                "primary-container": "#800020",
                "crimson-dark": "#5B0016",
                "primary": "#570013",
                "on-secondary-container": "#636360",
                "on-surface-variant": "#584141",
                "on-surface": "#1c1b1b",
                "tertiary-container": "#cca730",
                "on-error-container": "#93000a",
                "surface-variant": "#e5e2e1",
                "on-secondary": "#ffffff",
                "inverse-on-surface": "#f3f0ef",
                "error": "#ba1a1a",
                "on-tertiary-fixed": "#241a00",
                "tertiary": "#735c00",
                "on-primary": "#ffffff",
                "on-primary-fixed-variant": "#8e0f28",
                "surface-dim": "#dcd9d9",
                "background": "#fcf9f8",
                "surface-container-high": "#eae7e7",
                "outline": "#8c7071",
                "secondary-fixed-dim": "#c8c6c3",
                "on-secondary-fixed-variant": "#474744",
                "inverse-surface": "#313030",
                "parchment-deep": "#F5F1E6",
                "surface-bright": "#fcf9f8",
                "surface-tint": "#af2b3e",
                "on-secondary-fixed": "#1b1c1a",
                "on-primary-fixed": "#40000b",
                "tertiary-fixed-dim": "#e9c349",
                "primary-fixed-dim": "#ffb3b5",
                "on-tertiary": "#ffffff",
                "secondary-fixed": "#e4e2de",
                "secondary-container": "#e1dfdc",
                "inverse-primary": "#ffb3b5",
                "surface-container-lowest": "#ffffff",
                "tertiary-fixed": "#ffe088",
                "on-background": "#1c1b1b",
                "secondary": "#5e5e5c",
                "error-container": "#ffdad6",
                "surface-container-highest": "#e5e2e1",
                "primary-fixed": "#ffdada",
                "on-tertiary-container": "#4f3d00",
                "outline-variant": "#e0bfbf",
                "surface-container": "#f0eded"
            },
            borderRadius: {
                "DEFAULT": "0.125rem",
                "lg": "0.25rem",
                "xl": "0.5rem",
                "full": "0.75rem"
            },
            spacing: {
                "unit": "8px",
                "margin-mobile": "16px",
                "gutter": "24px",
                "section-gap": "64px",
                "container-max": "1120px"
            },
            fontFamily: {
                "body-lg": ["Hanken Grotesk", "sans-serif"],
                "headline-md": ["EB Garamond", "serif"],
                "headline-sm": ["EB Garamond", "serif"],
                "display-lg-mobile": ["EB Garamond", "serif"],
                "display-lg": ["EB Garamond", "serif"],
                "body-md": ["Hanken Grotesk", "sans-serif"],
                "quote-display": ["EB Garamond", "serif"],
                "label-caps": ["Hanken Grotesk", "sans-serif"],
                "ebGaramond": ["EB Garamond", "serif"],
                "hankenGrotesk": ["Hanken Grotesk", "sans-serif"]
            },
            fontSize: {
                "body-lg": ["18px", { lineHeight: "28px", fontWeight: "400" }],
                "headline-md": ["32px", { lineHeight: "40px", fontWeight: "500" }],
                "headline-sm": ["24px", { lineHeight: "32px", fontWeight: "500" }],
                "display-lg-mobile": ["36px", { lineHeight: "44px", fontWeight: "600" }],
                "display-lg": ["48px", { lineHeight: "56px", letterSpacing: "-0.02em", fontWeight: "600" }],
                "body-md": ["16px", { lineHeight: "24px", fontWeight: "400" }],
                "quote-display": ["22px", { lineHeight: "32px", fontWeight: "400" }],
                "label-caps": ["12px", { lineHeight: "16px", letterSpacing: "0.1em", fontWeight: "600" }]
            }
        },
    },
};

/**
 * --------------------------------------------------------------------------
 * 2. MAIN JAVASCRIPT LOGIC
 * --------------------------------------------------------------------------
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('Litera Platform Initialized');

    // --- A. Micro-Interactions & Hover Effects ---

    // 1. Demo Card Reveal
    const demoCard = document.querySelector('.bg-white.rounded-lg.shadow-sm');
    if (demoCard) {
        demoCard.addEventListener('mouseenter', () => {
            demoCard.style.transform = 'translateY(-4px)';
            demoCard.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)';
        });
        demoCard.addEventListener('mouseleave', () => {
            demoCard.style.transform = 'translateY(0)';
            demoCard.style.boxShadow = '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)';
        });
    }

    // 2. Character Cards
    document.querySelectorAll('.character-card-hover').forEach(card => {
        card.addEventListener('mouseenter', () => {
            // Subtle lift or tone shift could be added here
        });
    });

    // 3. Search Bar Interaction
    const searchInput = document.querySelector('input[type="text"]');
    if (searchInput) {
        searchInput.addEventListener('focus', () => {
            searchInput.parentElement.classList.add('scale-105');
        });
        searchInput.addEventListener('blur', () => {
            searchInput.parentElement.classList.remove('scale-105');
        });
    }

    // 4. Verse Rows
    document.querySelectorAll('.group').forEach(row => {
        row.addEventListener('mouseenter', () => {
            const h3 = row.querySelector('h3');
            if (h3) {
                h3.style.transform = 'translateX(4px)';
                h3.style.transition = 'transform 0.3s ease';
            }
        });
        row.addEventListener('mouseleave', () => {
            const h3 = row.querySelector('h3');
            if (h3) {
                h3.style.transform = 'translateX(0)';
            }
        });
    });

    // --- B. Forms & Inputs ---

    // 1. Radio Button -> Textarea Placeholder Logic
    document.querySelectorAll('input[type="radio"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            if (e.target.checked) {
                const text = e.target.closest('label').querySelector('span').innerText;
                const textarea = document.querySelector('textarea');
                if (textarea) {
                    textarea.placeholder = `Drafting essay for: ${text}...`;
                    textarea.focus();
                }
            }
        });
    });

    // 2. Form Submission Simulation
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const btn = e.target.querySelector('button');
            if (!btn) return;

            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="material-symbols-outlined animate-spin">progress_activity</span> Sending...';
            btn.disabled = true;

            setTimeout(() => {
                btn.innerHTML = '<span class="material-symbols-outlined">check_circle</span> Message Sent';
                btn.classList.remove('bg-primary-container');
                btn.classList.add('bg-green-700');
                e.target.reset();

                setTimeout(() => {
                    btn.innerHTML = originalText;
                    btn.classList.add('bg-primary-container');
                    btn.classList.remove('bg-green-700');
                    btn.disabled = false;
                }, 3000);
            }, 1500);
        });
    }

    // --- C. Navigation ---

    // 1. Navigation Link Highlight
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', function(e) {
            // Prevent default only if it's purely a hash link acting as a tab
            if(this.getAttribute('href').startsWith('#')) {
                document.querySelectorAll('nav a').forEach(l => {
                    l.classList.remove('text-primary', 'font-semibold', 'border-b-2');
                    l.classList.add('text-on-surface-variant');
                });
                this.classList.add('text-primary', 'font-semibold', 'border-b-2');
                this.classList.remove('text-on-surface-variant');
            }
        });
    });

    // 2. Smooth Scrolling for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // --- D. Scroll Events (Unified) ---
    
    const sections = document.querySelectorAll('section');
    const navItems = document.querySelectorAll('.nav-item');
    const header = document.querySelector('header');
    const mainNav = document.getElementById('main-nav');
    const mainProgressBar = document.getElementById('progress-bar');
    const altProgressBar = document.querySelector('.h-full.bg-primary');

    window.addEventListener('scroll', () => {
        const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolledPercentage = (winScroll / height) * 100;

        // 1. Progress Bars
        if (mainProgressBar) mainProgressBar.style.width = scrolledPercentage + "%";
        if (altProgressBar) altProgressBar.style.width = scrolledPercentage + "%";

        // 2. Header Effects
        if (header) {
            if (winScroll > 20) {
                header.classList.add('shadow-md', 'bg-white/95');
                header.classList.remove('shadow-sm', 'bg-surface');
            } else {
                header.classList.remove('shadow-md', 'bg-white/95');
                header.classList.add('shadow-sm', 'bg-surface');
            }
        }

        // 3. Navbar Glassmorphism
        if (mainNav) {
            if (winScroll > 50) {
                mainNav.classList.add('bg-white/80', 'backdrop-blur-lg', 'shadow-sm');
                mainNav.classList.remove('bg-surface');
            } else {
                mainNav.classList.remove('bg-white/80', 'backdrop-blur-lg', 'shadow-sm');
                mainNav.classList.add('bg-surface');
            }
        }

        // 4. Scrollspy (Sidebar active state)
        let currentSectionId = "";
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            if (pageYOffset >= (sectionTop - 200)) {
                currentSectionId = section.getAttribute('id');
            }
        });

        navItems.forEach(item => {
            item.classList.remove('sticky-nav-active');
            if (currentSectionId && item.getAttribute('href')?.includes(currentSectionId)) {
                item.classList.add('sticky-nav-active');
            }
        });
    });

    // --- E. Intersection Observers (Unified Fade-ins) ---
    
    const observerOptions = { threshold: 0.1 };
    const fadeObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('opacity-100', 'translate-y-0');
                // Remove all variants of the initial hidden states
                entry.target.classList.remove('opacity-0', 'translate-y-4', 'translate-y-8', 'translate-y-10');
            }
        });
    }, observerOptions);

    // Apply specific initial states based on element type to maintain original design intent
    document.querySelectorAll('.bento-card').forEach(card => {
        card.classList.add('opacity-0', 'translate-y-10', 'transition-all', 'duration-700', 'ease-out');
        fadeObserver.observe(card);
    });

    document.querySelectorAll('section').forEach(section => {
        section.classList.add('transition-all', 'duration-700', 'opacity-0', 'translate-y-4');
        fadeObserver.observe(section);
    });

    document.querySelectorAll('.md\\:col-span-8, .md\\:col-span-4, .bg-surface-container-lowest').forEach(el => {
        el.classList.add('transition-all', 'duration-700', 'opacity-0', 'translate-y-8');
        fadeObserver.observe(el);
    });
});