const AppMethodsApi = {
        getForeignApi(cleanDomain, anonymous = false) {
            const cacheKey = `${cleanDomain}:${anonymous ? 'anon' : 'auth'}`;
            return (this.apiCache[cacheKey] ??= new mw.ForeignApi(
                `https://${cleanDomain}/api.php`,
                anonymous ? { anonymous: true } : {}
            ));
        },

        async fetchConfig() {
            try {
                const api = new mw.Api();
                const res = await api.get({
                    action: 'expandtemplates',
                    text: '{{#invoke:CrossWikiActivity|toJSON}}',
                    prop: 'wikitext',
                    formatversion: 2,
                    _: Date.now()
                });
                const rawText = res?.expandtemplates?.wikitext?.trim();
                if (rawText) {
                    const parsed = JSON.parse(rawText);
                    this.wikis = Array.isArray(parsed.wikis) ? parsed.wikis : [];
                    if (parsed.settings && typeof parsed.settings === 'object') {
                        Object.assign(this.settings, parsed.settings);
                    }
                }
            } catch (e) {
                console.error('[CWA] Ошибка загрузки конфига:', e);
            }
        },

        async fetchData() {
            if (this.wikis.length === 0) {
                await this.fetchConfig();
                this.setupAutoRefresh();
            }

            this.isLoading = true;
            this.failedWikis = [];

            try {
                const editsMap = new Map();
                const endDate = new Date();
                endDate.setDate(endDate.getDate() - (this.settings.days || 3));
                const rcend = endDate.toISOString();

                const rcshow = [];
                if (this.settings.showBots === false) rcshow.push('!bot');
                if (this.settings.showMinor === false) rcshow.push('!minor');

                const fetchPromises = this.wikis.map((rawDomain, index) => new Promise((resolve) => {
                    setTimeout(async () => {
                        let cleanDomain;
                        try {
                            cleanDomain = this.formatWikiUrl(rawDomain);
                        } catch {
                            if (!this.failedWikis.includes(rawDomain)) this.failedWikis.push(rawDomain);
                            return resolve([]);
                        }

                        const wikiEdits = [];
                        let currentWikiName = cleanDomain;

                        try {
                            const baseParams = {
                                action: 'query',
                                list: 'recentchanges',
                                meta: 'siteinfo',
                                siprop: 'general',
                                rclimit: this.settings.limit || 4000,
                                rctype: 'edit|new|log',
                                rcend,
                                formatversion: 2,
                                _: Date.now()
                            };
                            if (rcshow.length > 0) baseParams.rcshow = rcshow.join('|');

                            const anonProps = 'user|title|ids|sizes|timestamp|loginfo|parsedcomment|flags';
                            const rcPromise = this.canPatrol
                                ? this.getForeignApi(cleanDomain, false)
                                    .get({ ...baseParams, rcprop: `${anonProps}|patrolled` })
                                    .catch(() => this.getForeignApi(cleanDomain, true).get({ ...baseParams, rcprop: anonProps }).catch(() => null))
                                : this.getForeignApi(cleanDomain, true).get({ ...baseParams, rcprop: anonProps }).catch(() => null);

                            const discLimit = Math.min(this.settings.limit || 100, 100);
                            const discPromise = fetch(
                                `https://${cleanDomain}/wikia.php?controller=DiscussionPost&method=getPosts&limit=${discLimit}&viewableOnly=true&format=json&cb=${Date.now()}`,
                                { mode: 'cors' }
                            ).then(r => (r.ok ? r.json() : null)).catch(() => null);

                            const [res, discData] = await Promise.all([rcPromise, discPromise]);

                            if (res?.query?.recentchanges) {
                                currentWikiName = res.query.general?.sitename || cleanDomain;
                                const rcEdits = res.query.recentchanges;

                                if (this.canPatrol && rcEdits.length > 0) {
                                    const trustedGroups = new Set([
                                        'sysop', 'content-moderator', 'rollback', 'staff',
                                        'wiki-representative', 'soap', 'wiki-specialist',
                                        'bot', 'autopatrolled', 'vanguard', 'voldev',
                                        'global-discussions-moderator'
                                    ]);
                                    const trustedUsers = new Set([
                                        'GlobalJSReviewer', 'Fandom', 'Fandombot', 'Wikia', 'WikiaBot', 'Default',
                                        mw.config.get('wgUserName')
                                    ]);

                                    const uniqueUsers = [...new Set(rcEdits.map(rc => rc.user).filter(Boolean))];
                                    const uApi = this.getForeignApi(cleanDomain, true);
                                    const userChunks = Array.from(
                                        { length: Math.ceil(uniqueUsers.length / 50) },
                                        (_, i) => uniqueUsers.slice(i * 50, i * 50 + 50)
                                    );

                                    const uResults = await Promise.all(
                                        userChunks.map(chunk => uApi.get({
                                            action: 'query',
                                            list: 'users',
                                            ususers: chunk.join('|'),
                                            usprop: 'groups',
                                            formatversion: 2
                                        }).catch(() => null))
                                    );

                                    for (const uRes of uResults) {
                                        for (const u of uRes?.query?.users ?? []) {
                                            if (u.groups?.some(g => trustedGroups.has(g))) {
                                                trustedUsers.add(u.name);
                                            }
                                        }
                                    }

                                    for (const rc of rcEdits) {
                                        if (trustedUsers.has(rc.user)) delete rc.unpatrolled;
                                    }
                                }

                                wikiEdits.push(...rcEdits.map(rc => this.normalizeData(rc, cleanDomain, currentWikiName)));
                            } else if (!this.failedWikis.includes(rawDomain)) {
                                this.failedWikis.push(rawDomain);
                            }

                            if (discData) {
                                const posts = discData._embedded?.['doc:posts'] ?? [];
                                const uniqueIds = [...new Set(
                                    posts
                                        .filter(p => p._embedded?.thread?.[0]?.containerType === 'ARTICLE_COMMENT')
                                        .map(p => p.forumId)
                                        .filter(Boolean)
                                )];
                                let articleData = {};

                                if (uniqueIds.length > 0) {
                                    try {
                                        const artRes = await fetch(
                                            `https://${cleanDomain}/wikia.php?controller=FeedsAndPosts&method=getArticleNamesAndUsernames&stablePageIds=${uniqueIds.join(',')}&format=json&cb=${Date.now()}`,
                                            { mode: 'cors' }
                                        );
                                        if (artRes.ok) {
                                            articleData = (await artRes.json()).articleNames ?? {};
                                        }
                                    } catch {}
                                }

                                for (const p of posts) {
                                    try {
                                        wikiEdits.push(this.normalizeDiscussion(p, cleanDomain, articleData, currentWikiName));
                                    } catch {}
                                }
                            }

                            resolve(wikiEdits);
                        } catch {
                            if (!this.failedWikis.includes(rawDomain)) this.failedWikis.push(rawDomain);
                            resolve([]);
                        }
                    }, index * 50);
                }));

                const results = await Promise.all(fetchPromises);
                for (const e of this.edits) editsMap.set(e.id, e);
                for (const wikiEdits of results) {
                    for (const e of wikiEdits) editsMap.set(e.id, e);
                }

                this.edits = Array.from(editsMap.values())
                    .filter(edit => new Date(edit.timestamp) >= endDate)
                    .toSorted((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            } finally {
                this.isLoading = false;
            }
        },

        normalizeData(rc, wikiDomain, wikiName) {
            const serverUrl = `https://${wikiDomain}`;
            const articlePath = `${serverUrl}/wiki/`;

            let category = 'content';
            let groupWithID = rc.title;
            const isBot = Boolean(rc.bot);

            const mediaNs = [-2, 6];
            const systemNs = [-1, 2, 8, 828];
            const socialNs = [119, 500, 501, 502, 503, 1200, 1201, 1202, 2000, 2001, 2002];

            if (rc.type === 'log') {
                groupWithID = rc.logtype;
                if (rc.logtype === 'upload' || mediaNs.includes(rc.ns)) category = 'media';
                else if (rc.ns % 2 !== 0 || socialNs.includes(rc.ns)) category = 'social';
                else category = 'system';
            } else if (mediaNs.includes(rc.ns)) {
                category = 'media';
            } else if (rc.ns % 2 !== 0 || socialNs.includes(rc.ns)) {
                category = 'social';
            } else if (systemNs.includes(rc.ns)) {
                category = 'system';
            }

            const flagsArr = [];
            if (rc.type === 'new') flagsArr.push({ text: 'Н', title: 'Новая страница' });
            if (rc.minor) flagsArr.push({ text: 'м', title: 'Малая правка' });
            if (isBot) flagsArr.push({ text: 'б', title: 'Правка бота' });

            let actionTitle = null;
            let socialContext = null;

            if (category === 'social') {
                const isMessage = [1200, 1201, 1202].includes(rc.ns);
                const isPost = [2000, 2001, 2002].includes(rc.ns);
                const isBlog = [500, 501, 502, 503].includes(rc.ns);
                const isTalk = !isMessage && !isPost && !isBlog;

                let act = 'Изменение';
                let actKey = 'update';
                if (rc.type === 'new') {
                    act = 'Новый';
                    actKey = 'create';
                } else if (rc.type === 'log') {
                    act = CwaDicts.logActMap[rc.logaction] ?? 'Изменение';
                    const logKeyMap = { delete: 'delete', restore: 'undelete', protect: 'lock', unprotect: 'unlock' };
                    actKey = logKeyMap[rc.logaction] ?? 'update';
                }

                const cType = isTalk ? 'talk' : isBlog ? 'blog' : isMessage ? 'message' : 'post';
                const iconContentBase = isTalk ? 'comment' : cType;
                const isReply = (isBlog && (rc.ns === 501 || rc.ns === 503)) || (isMessage && rc.ns === 1201) || (isPost && rc.ns === 2001);

                socialContext = {
                    activityType: actKey,
                    contentType: `${iconContentBase}${isReply ? '-reply' : ''}`
                };

                if (act === 'Новый' && isReply) {
                    const replyMap = { blog: 'Ответ на блог', message: 'Ответ на сообщение', post: 'Ответ на пост' };
                    actionTitle = replyMap[cType] ?? 'Новое обсуждение';
                } else {
                    actionTitle = CwaDicts.socialTitleMap?.[cType]?.[act] ?? 'Изменение';
                }
            } else if (rc.type === 'new') {
                actionTitle = rc.ns === 6 ? 'Загружен новый файл' : 'Создана новая страница';
            } else if (rc.type === 'log') {
                actionTitle = CwaDicts.logMap[`${rc.logtype}/${rc.logaction}`] ?? `${rc.logtype} / ${rc.logaction}`;
            } else {
                actionTitle = rc.ns === 6 ? 'Отредактирован файл' : 'Отредактирована страница';
            }

            const targetId = rc.rcid || rc.logid || rc.revid;
            const fallbackLogComment = rc.type === 'log'
                ? (CwaDicts.logNamesMap[rc.logtype] ?? `Журнал: ${mw.html.escape(String(rc.logtype ?? ''))} (${mw.html.escape(String(rc.logaction ?? ''))})`)
                : '';

            return Object.freeze({
                id: rc.rcid || rc.logid || Math.random().toString(36).slice(2, 9),
                revid: rc.revid,
                rcid: rc.rcid,
                old_revid: rc.old_revid,
                pageid: rc.pageid,
                unpatrolled: rc.unpatrolled !== undefined && !this.patrolledIds.includes(targetId),
                type: rc.type,
                logtype: rc.logtype,
                logaction: rc.logaction,
                ns: rc.ns,
                title: rc.title,
                user: rc.user,
                timestamp: rc.timestamp,
                time: new Date(rc.timestamp).toLocaleTimeString(navigator.language, { hour: '2-digit', minute: '2-digit' }),
                parsedComment: rc.parsedcomment || fallbackLogComment,
                sizeDiff: (rc.newlen ?? 0) - (rc.oldlen ?? 0),
                flags: flagsArr,
                wikiDomain,
                wikiName: wikiName || wikiDomain,
                wikiFavicon: `${serverUrl}/wiki/Special:FilePath/Site-favicon.ico`,
                pageUrl: `${articlePath}${encodeURIComponent(rc.title)}`,
                userUrl: `${articlePath}User:${encodeURIComponent(rc.user)}`,
                userTalkUrl: `${articlePath}User_talk:${encodeURIComponent(rc.user)}`,
                userContribsUrl: `${articlePath}Special:Contributions/${encodeURIComponent(rc.user)}`,
                userBlockUrl: `${articlePath}Special:Block/${encodeURIComponent(rc.user)}`,
                undoUrl: rc.revid && rc.old_revid ? `${articlePath}${encodeURIComponent(rc.title)}?action=edit&undo=${rc.revid}&undoafter=${rc.old_revid}` : null,
                category,
                groupWithID,
                actionTitle,
                socialContext
            });
        },

        normalizeDiscussion(post, wikiDomain, articleData, wikiName) {
            const thread = post._embedded?.thread?.[0] ?? {};
            const createdEpoch = post.creationDate?.epochSecond ?? 0;
            const modifiedEpoch = post.modificationDate?.epochSecond ?? createdEpoch;
            const date = new Date((modifiedEpoch || createdEpoch) * 1000);
            const isReply = post.position > 1;
            const containerType = thread.containerType || 'FORUM';

            let pageUrl = '';
            let contentType = 'post';
            let displayTitle = thread.title || post.title;

            if (containerType === 'ARTICLE_COMMENT') {
                contentType = (displayTitle?.startsWith('User blog:') || displayTitle?.startsWith('Блог участника:')) ? 'blog' : 'comment';
                const info = articleData?.[post.forumId] ?? null;
                if (info) {
                    pageUrl = `https://${wikiDomain}/wiki/${encodeURIComponent(info.title.replaceAll(' ', '_'))}?commentId=${encodeURIComponent(post.threadId)}${isReply ? `&replyId=${encodeURIComponent(post.id)}` : ''}`;
                    displayTitle = info.title;
                } else {
                    pageUrl = `https://${wikiDomain}/f/p/${encodeURIComponent(post.threadId)}`;
                    displayTitle = post.forumName || 'Комментарий к статье';
                }
            } else if (containerType === 'WALL' || containerType === 'MESSAGE_WALL') {
                const cleanWallName = (post.forumName ?? '').replace(/ Message Wall$/, '').replace(/^Стена обсуждения:/, '');
                pageUrl = `https://${wikiDomain}/wiki/Message_Wall:${encodeURIComponent(cleanWallName.replaceAll(' ', '_'))}?threadId=${encodeURIComponent(post.threadId)}${isReply ? `#${encodeURIComponent(post.id)}` : ''}`;
                if (!displayTitle || displayTitle.startsWith('@')) displayTitle = 'Стена обсуждения';
                contentType = 'message';
            } else {
                pageUrl = `https://${wikiDomain}/f/p/${encodeURIComponent(post.threadId)}${isReply ? `/r/${encodeURIComponent(post.id)}` : ''}`;
                displayTitle ||= 'Обсуждение на форуме';
            }

            let summary = post.snippet || post.rawContent || post.body;
            if (!summary && post.jsonModel) {
                try {
                    const texts = [];
                    JSON.parse(post.jsonModel, (key, value) => {
                        if (key === 'text' && typeof value === 'string') texts.push(value);
                        return value;
                    });
                    summary = texts.join(' ').replace(/\s+/g, ' ').trim();
                } catch {}
            }

            summary ||= '(Вложение / Опрос)';
            if (summary.length > 85) summary = `${summary.slice(0, 85)}...`;

            let act = 'Новый';
            let activityType = 'create';
            if (post.isDeleted) {
                act = 'Удаление';
                activityType = 'delete';
            } else if (post.isLocked) {
                act = 'Закрытие';
                activityType = 'lock';
            } else if (modifiedEpoch - createdEpoch > 60) {
                act = 'Изменение';
                activityType = 'update';
            }

            const safeContentType = ['comment', 'message', 'blog', 'post'].includes(contentType) ? contentType : 'post';
            const replyMap = {
                comment: 'Ответ на комментарий',
                message: 'Ответ на сообщение',
                blog: 'Ответ на блог',
                post: 'Ответ на пост'
            };
            const actionTitle = (act === 'Новый' && isReply)
                ? replyMap[safeContentType]
                : (CwaDicts.socialTitleMap?.[safeContentType]?.[act] ?? 'Изменение');

            const userName = post.createdBy?.name || 'Аноним';

            return Object.freeze({
                id: `disc-${post.id}`,
                revid: null,
                rcid: null,
                old_revid: null,
                pageid: null,
                unpatrolled: false,
                type: 'discussion',
                logtype: '',
                logaction: '',
                ns: -5234,
                title: displayTitle,
                actionTitle,
                user: userName,
                timestamp: date.toISOString(),
                time: date.toLocaleTimeString(navigator.language, { hour: '2-digit', minute: '2-digit' }),
                parsedComment: mw.html.escape(summary),
                sizeDiff: 0,
                flags: [],
                wikiDomain,
                wikiName: wikiName || wikiDomain,
                wikiFavicon: `https://${wikiDomain}/wiki/Special:FilePath/Site-favicon.ico`,
                pageUrl,
                userUrl: `https://${wikiDomain}/wiki/User:${encodeURIComponent(userName)}`,
                userTalkUrl: `https://${wikiDomain}/wiki/User_talk:${encodeURIComponent(userName)}`,
                userContribsUrl: `https://${wikiDomain}/wiki/Special:Contributions/${encodeURIComponent(userName)}`,
                userBlockUrl: `https://${wikiDomain}/wiki/Special:Block/${encodeURIComponent(userName)}`,
                category: 'social',
                groupWithID: `disc-${post.threadId}`,
                socialContext: {
                    activityType,
                    contentType: `${safeContentType}${isReply ? '-reply' : ''}`
                },
                jsonModel: post.jsonModel,
                rawContent: post.rawContent
            });
        }
    };
