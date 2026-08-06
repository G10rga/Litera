/* Litera — shared JavaScript */

document.addEventListener('DOMContentLoaded', () => {
    initScrollProgress();
    initNavbarScroll();
    initBentoCards();
    initFadeInSections();
    initDemoCard();
    initCharacterSearch();
    initContactForm();
    initExamPrepRadios();
    initModernTranslations();
    initStudyGuideNav();
    initSmoothAnchors();
    initSyllabusReveal();
    initTosScrollSpy();
    initStanzaCards();
    initPasswordToggles();
    initAuthFlashDismiss();
    initStanzaReveal();
    initChapterSelect();
});

function initScrollProgress() {
    const bars = [
        document.getElementById('progress-bar'),
        document.getElementById('scrollProgress'),
    ].filter(Boolean);

    if (!bars.length) return;

    window.addEventListener('scroll', () => {
        const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
        const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = height > 0 ? (winScroll / height) * 100 : 0;
        bars.forEach((bar) => {
            bar.style.width = scrolled + '%';
        });

        const modernBar = document.querySelector('.h-full.bg-primary');
        if (modernBar && modernBar.parentElement && modernBar.parentElement.classList.contains('bg-outline-variant')) {
            modernBar.style.width = scrolled + '%';
        }
    });
}

function initNavbarScroll() {
    const nav = document.getElementById('main-nav');
    if (!nav) return;

    window.addEventListener('scroll', () => {
        const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
        if (winScroll > 50) {
            nav.classList.add('bg-white/80', 'backdrop-blur-lg', 'shadow-sm');
            nav.classList.remove('bg-surface');
        } else {
            nav.classList.remove('bg-white/80', 'backdrop-blur-lg', 'shadow-sm');
            nav.classList.add('bg-surface');
        }
    });
}

function initBentoCards() {
    const cards = document.querySelectorAll('.bento-card');
    if (!cards.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('opacity-100', 'translate-y-0');
                entry.target.classList.remove('opacity-0', 'translate-y-10');
            }
        });
    }, { threshold: 0.1 });

    cards.forEach((card) => {
        card.classList.add('opacity-0', 'translate-y-10', 'transition-all', 'duration-700', 'ease-out');
        observer.observe(card);
    });
}

function initFadeInSections() {
    const sections = document.querySelectorAll('.legal-content section, .fade-on-scroll');
    if (!sections.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('opacity-100', 'translate-y-0');
                entry.target.classList.remove('opacity-0', 'translate-y-4');
            }
        });
    }, { threshold: 0.1 });

    sections.forEach((section) => {
        section.classList.add('transition-all', 'duration-700', 'opacity-0', 'translate-y-4');
        observer.observe(section);
    });
}

function initDemoCard() {
    const demoCard = document.querySelector('[data-demo-card]');
    if (!demoCard) return;

    demoCard.addEventListener('mouseenter', () => {
        demoCard.style.transform = 'translateY(-4px)';
        demoCard.style.boxShadow = '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)';
    });
    demoCard.addEventListener('mouseleave', () => {
        demoCard.style.transform = 'translateY(0)';
        demoCard.style.boxShadow = '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)';
    });
}

function initCharacterSearch() {
    const searchInput = document.querySelector('[data-character-search]');
    if (!searchInput) return;

    searchInput.addEventListener('focus', () => {
        searchInput.parentElement.classList.add('scale-105');
    });
    searchInput.addEventListener('blur', () => {
        searchInput.parentElement.classList.remove('scale-105');
    });
}

function initContactForm() {
    const form = document.querySelector('[data-contact-form]');
    if (!form) return;

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const btn = e.target.querySelector('button[type="submit"], button');
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

function initExamPrepRadios() {
    const radios = document.querySelectorAll('[data-exam-radio]');
    if (!radios.length) return;

    radios.forEach((radio) => {
        radio.addEventListener('change', (e) => {
            if (!e.target.checked) return;
            const label = e.target.closest('label');
            const span = label && label.querySelector('span');
            const textarea = document.querySelector('[data-exam-textarea]');
            if (!span || !textarea) return;
            textarea.placeholder = `Drafting essay for: ${span.innerText}...`;
            textarea.focus();
        });
    });
}

function initModernTranslations() {
    const rows = document.querySelectorAll('[data-verse-row]');
    rows.forEach((row) => {
        const heading = row.querySelector('h3');
        if (!heading) return;
        row.addEventListener('mouseenter', () => {
            heading.style.transform = 'translateX(4px)';
            heading.style.transition = 'transform 0.3s ease';
        });
        row.addEventListener('mouseleave', () => {
            heading.style.transform = 'translateX(0)';
        });
    });
}

function initStudyGuideNav() {
    const links = document.querySelectorAll('[data-study-nav] a');
    if (!links.length) return;

    links.forEach((link) => {
        link.addEventListener('click', function () {
            links.forEach((l) => {
                l.classList.remove('text-primary', 'font-semibold', 'border-b-2');
                l.classList.add('text-on-surface-variant');
            });
            this.classList.add('text-primary', 'font-semibold', 'border-b-2');
            this.classList.remove('text-on-surface-variant');
        });
    });
}

function initSmoothAnchors() {
    document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (!href || href === '#') return;
            const target = document.querySelector(href);
            if (!target) return;
            e.preventDefault();
            target.scrollIntoView({ behavior: 'smooth' });
        });
    });
}

function initSyllabusReveal() {
    const els = document.querySelectorAll('[data-reveal]');
    if (!els.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('opacity-100', 'translate-y-0');
                entry.target.classList.remove('opacity-0', 'translate-y-8');
            }
        });
    }, { threshold: 0.1 });

    els.forEach((el) => {
        el.classList.add('transition-all', 'duration-700', 'opacity-0', 'translate-y-8');
        observer.observe(el);
    });
}

function initTosScrollSpy() {
    const sections = document.querySelectorAll('[data-tos-section]');
    const navItems = document.querySelectorAll('.nav-item');
    if (!sections.length || !navItems.length) return;

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach((section) => {
            if (window.pageYOffset >= section.offsetTop - 200) {
                current = section.getAttribute('id') || '';
            }
        });

        navItems.forEach((item) => {
            item.classList.remove('sticky-nav-active');
            const href = item.getAttribute('href') || '';
            if (current && href.includes(current)) {
                item.classList.add('sticky-nav-active');
            }
        });
    });
}

function initStanzaCards() {
    document.querySelectorAll('.stanza-card-container').forEach((card) => {
        card.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                card.classList.toggle('is-flipped');
            }
        });
        card.addEventListener('click', () => {
            card.classList.toggle('is-flipped');
        });
    });
}

function initPasswordToggles() {
    document.querySelectorAll('[data-password-toggle]').forEach((toggleBtn) => {
        const field = toggleBtn.parentElement && toggleBtn.parentElement.querySelector('input[type="password"], input[type="text"]');
        if (!field) return;

        toggleBtn.addEventListener('click', () => {
            const showing = field.type === 'text';
            field.type = showing ? 'password' : 'text';
            toggleBtn.innerHTML = `<span class="material-symbols-outlined text-[20px]">${showing ? 'visibility' : 'visibility_off'}</span>`;
        });
    });
}

function initAuthFlashDismiss() {
    document.querySelectorAll('.auth-flash').forEach((flash) => {
        setTimeout(() => {
            flash.style.opacity = '0';
            flash.style.transition = 'opacity 0.4s ease';
            setTimeout(() => flash.remove(), 400);
        }, 4000);
    });
}

/* Fade stanzas in as they scroll into view (vefxistyaosani chapter view). */
function initStanzaReveal() {
    const stanzas = document.querySelectorAll('[data-stanza]');
    if (!stanzas.length) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    stanzas.forEach((stanza) => {
        stanza.style.opacity = '0.4';
        stanza.style.transform = 'translateY(10px)';
        stanza.style.transition = 'all 0.6s cubic-bezier(0.16, 1, 0.3, 1)';
        observer.observe(stanza);
    });
}

/* Chapter / work jump menus: navigate on change, highlight on focus. */
function initChapterSelect() {
    const selects = document.querySelectorAll('[data-chapter-select]');
    if (!selects.length) return;

    selects.forEach((select) => {
        select.addEventListener('change', () => {
            if (select.value) window.location.href = select.value;
        });
        select.addEventListener('focus', () => {
            if (select.parentElement) select.parentElement.classList.add('ring-2', 'ring-primary');
        });
        select.addEventListener('blur', () => {
            if (select.parentElement) select.parentElement.classList.remove('ring-2', 'ring-primary');
        });
    });
}
