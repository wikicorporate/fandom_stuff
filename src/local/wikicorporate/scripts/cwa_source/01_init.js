/* CrossWikiActivity - Глобальный трекер активности */
(async () => {
    'use strict';

    const targetContainer = document.querySelector('#cwa-app-container');
    if (!targetContainer || targetContainer.dataset.cwaMounted === 'true') {
        return;
    }
    targetContainer.dataset.cwaMounted = 'true';

    const localRequire = await mw.loader.using([
        'mediawiki.api',
        'mediawiki.ForeignApi',
        'mediawiki.util',
        'mediawiki.jqueryMsg',
        'vue'
    ]);
    const Vue = localRequire('vue');
