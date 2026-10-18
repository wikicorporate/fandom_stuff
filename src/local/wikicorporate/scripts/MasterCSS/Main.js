/* Master CSS Runtime Adapter (ES2024) */
(async () => {
    'use strict';
    if (window.fandomMasterCssLoaded) return;
    window.fandomMasterCssLoaded = true;

    const CONFIG = {
        localPage: 'Модуль:MasterCSS',
        centralPage: 'Модуль:GlobalMasterCSS',
        centralApiUrl: 'https://wikicorporate.fandom.com/ru/api.php',
        cdnUrl: 'https://cdn.jsdelivr.net/npm/@master/css-runtime@2.0.0-rc.33/+esm',
        cacheKey: 'fandom_mastercss_config',
        cacheTimeKey: 'fandom_mastercss_time',
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
        } catch {
            return {};
        }
    };

    // Санитайзер классов (защита от CSS-инъекций и внешней подгрузки через url())
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
                console.warn('[MasterCSS Security] Вырезан запрещённый класс:', badClasses);
            }
        };

        cleanNode(node);
        node.querySelectorAll('[class]').forEach(cleanNode);
    };

    const syncFandomDarkTheme = () => {
        document.documentElement.classList.toggle(
            'dark',
            document.body.classList.contains('theme-fandomdesktop-dark')
        );
    };

    const initMasterCSS = async () => {
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

            const { initCSSRuntime } = await import(CONFIG.cdnUrl);
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

            initCSSRuntime({
                root: rootElement,
                config: finalConfig
            });

            syncFandomDarkTheme();
            new MutationObserver(syncFandomDarkTheme).observe(document.body, {
                attributes: true,
                attributeFilter: ['class']
            });
        } catch (error) {
            console.error('[MasterCSS Error]', error);
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMasterCSS);
    } else {
        initMasterCSS();
    }
})();
