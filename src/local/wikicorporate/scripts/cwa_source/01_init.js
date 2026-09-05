/* CrossWikiActivity - Глобальный трекер активности */
(async () => {
    'use strict';
    const localRequire = await mw.loader.using(["mediawiki.api", "mediawiki.ForeignApi", "mediawiki.util", "vue"]);
    const Vue = localRequire("vue");
