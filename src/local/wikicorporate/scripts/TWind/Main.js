/* TWind (Tailwind-in-JS) Runtime Adapter (ES2024) */
(async () => {
    'use strict';

    if (window.fandomTwindLoaded) return;
    window.fandomTwindLoaded = true;

    const CONFIG = {
        localPage: 'Модуль:Twind/LocalConfig',
        centralPage: 'Модуль:Twind/GlobalConfig',
        centralApiUrl: 'https://wikicorporate.fandom.com/ru/api.php',
        cacheKey: 'fandom_twind_config',
        cacheTimeKey: 'fandom_twind_time',
        cacheTTL: 60 * 60 * 1000 // 1 час
    };

    const mergeConfigs = (global, local) => {
        const result = { ...global };
        for (const [key, val] of Object.entries(local ?? {})) {
            if (key === '__proto__' || key === 'constructor' || key === 'prototype') continue;
            if (typeof val === 'object' && val !== null && !Array.isArray(val)) {
                result[key] = mergeConfigs(result[key] ?? {}, val);
            } else {
                result[key] = val;
            }
        }
        return result;
    };

    const getCache = () => {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const wgAction = mw.config.get('wgAction');
            if (urlParams.has('clearcache') || wgAction === 'purge' || wgAction === 'edit') return null;

            const cachedConfig = localStorage.getItem(CONFIG.cacheKey);
            const cachedTime = localStorage.getItem(CONFIG.cacheTimeKey);
            if (cachedConfig && cachedTime && (Date.now() - parseInt(cachedTime, 10) < CONFIG.cacheTTL)) {
                return JSON.parse(cachedConfig);
            }
        } catch {}
        return null;
    };

    const setCache = (configObj) => {
        try {
            localStorage.setItem(CONFIG.cacheKey, JSON.stringify(configObj));
            localStorage.setItem(CONFIG.cacheTimeKey, Date.now().toString());
        } catch {}
    };

    const fetchSource = async (pageTitle, apiUrl = mw.util.wikiScript('api')) => {
        try {
            const params = new URLSearchParams({
                action: 'query',
                prop: 'revisions',
                titles: pageTitle,
                rvprop: 'content',
                rvslots: 'main',
                format: 'json',
                formatversion: '2',
                origin: '*'
            });
            const response = await fetch(`${apiUrl}?${params.toString()}`);
            if (!response.ok) return {};
            const data = await response.json();
            const rawContent = data.query?.pages?.[0]?.revisions?.[0]?.slots?.main?.content;
            if (!rawContent) return {};

            const match = rawContent.match(/\[(=*)\[\s*([\s\S]*?)\s*\]\1\]/);
            return match ? JSON.parse(match[2]) : {};
        } catch (error) {
            console.warn(`[Twind] Ошибка загрузки конфига ${pageTitle}:`, error);
            return {};
        }
    };

    // Фильтрация опасных произвольных классов Tailwind (например bg-[url(...)])
    const sanitizeClasses = (node) => {
        if (!node || node.nodeType !== 1) return;

        const cleanNode = (element) => {
            if (!element.hasAttribute('class')) return;
            const badClasses = Array.from(element.classList).filter(cls => {
                const lower = cls.toLowerCase();
                return (
                    lower.includes('url(') ||
                    lower.includes('expression(') ||
                    lower.includes('@import') ||
                    lower.includes('javascript:')
                );
            });
            if (badClasses.length > 0) {
                element.classList.remove(...badClasses);
                console.warn('[TWind Security] Вырезан запрещённый класс:', badClasses);
            }
        };

        cleanNode(node);
        node.querySelectorAll('[class]').forEach(cleanNode);
    };

    const initTwind = async () => {
        try {
            let finalConfig = getCache();

            if (!finalConfig) {
                const [globalConfig, localConfig] = await Promise.all([
                    fetchSource(CONFIG.centralPage, CONFIG.centralApiUrl),
                    fetchSource(CONFIG.localPage)
                ]);

                finalConfig = mergeConfigs(globalConfig, localConfig);
                setCache(finalConfig);
            }

            const [{ install }, { default: presetTailwind }] = await Promise.all([
                import('https://cdn.jsdelivr.net/npm/@twind/core@1.1.3/+esm'),
                import('https://cdn.jsdelivr.net/npm/@twind/preset-tailwind@1.1.4/+esm')
            ]);

            const rootElement = document.querySelector('.mw-parser-output');
            if (!rootElement) return;

            sanitizeClasses(rootElement);

            const securityObserver = new MutationObserver((mutations) => {
                for (const mutation of mutations) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                        sanitizeClasses(mutation.target);
                    } else if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach(sanitizeClasses);
                    }
                }
            });
            securityObserver.observe(rootElement, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['class']
            });

            install({
                target: rootElement,
                presets: [
                    presetTailwind({
                        preflight: false
                    })
                ],
                ...finalConfig
            });
        } catch (error) {
            console.error('[Twind Loader] Критическая ошибка:', error);
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTwind);
    } else {
        initTwind();
    }
})();
