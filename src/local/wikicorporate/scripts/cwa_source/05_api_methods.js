const AppMethodsApi = {
        async fetchConfig() {
            try {
                const api = new mw.Api();
                const res = await api.get({
                    action: 'expandtemplates', text: '{' + '{#invoke:CrossWikiActivity|toJSON}}', prop: 'wikitext', formatversion: 2, _: Date.now()
                });
                if (res?.expandtemplates?.wikitext) {
                    const parsed = JSON.parse(res.expandtemplates.wikitext.trim());
                    this.wikis = parsed.wikis || [];
                    if (parsed.settings) Object.assign(this.settings, parsed.settings);
                }
            } catch (e) { console.error('[CWA] Ошибка загрузки конфига:', e); }
        },
        
        async fetchData() {
            if (this.wikis.length === 0) {
                await this.fetchConfig();
                this.setupAutoRefresh();
            }
            
            this.isLoading = true; this.failedWikis = [];
            
            try {
                const editsMap = new Map();

                let endDate = new Date();
                endDate.setDate(endDate.getDate() - (this.settings.days || 3));
                const rcend = endDate.toISOString();
                
                let rcshow = [];
                if (this.settings.showBots === false) rcshow.push('!bot');
                if (this.settings.showMinor === false) rcshow.push('!minor');

                const fetchPromises = this.wikis.map((rawDomain, index) => {
                    return new Promise((resolve) => {
                        setTimeout(async () => {
                            const cleanDomain = this.formatWikiUrl(rawDomain);
                            let wikiEdits = [];
                            let currentWikiName = cleanDomain;
                            
                            try {
                                const baseParams = {
                                    action: 'query', list: 'recentchanges',
                                    meta: 'siteinfo', siprop: 'general',
                                    rclimit: this.settings.limit || 4000,
                                    rctype: 'edit|new|log', rcend: rcend, formatversion: 2,
                                    _: Date.now() 
                                };
                                if (rcshow.length > 0) baseParams.rcshow = rcshow.join('|');
                                
                                let rcPromise;
                                
                                if (this.canPatrol) {
                                    const apiAuth = new mw.ForeignApi(`https://${cleanDomain}/api.php`);
                                    rcPromise = apiAuth.get({ ...baseParams, rcprop: 'user|title|ids|sizes|timestamp|loginfo|parsedcomment|flags|patrolled' })
                                        .catch(() => {
                                            const apiAnon = new mw.ForeignApi(`https://${cleanDomain}/api.php`, { anonymous: true });
                                            return apiAnon.get({ ...baseParams, rcprop: 'user|title|ids|sizes|timestamp|loginfo|parsedcomment|flags' }).catch(() => null);
                                        });
                                } else {
                                    const apiAnon = new mw.ForeignApi(`https://${cleanDomain}/api.php`, { anonymous: true });
                                    rcPromise = apiAnon.get({ ...baseParams, rcprop: 'user|title|ids|sizes|timestamp|loginfo|parsedcomment|flags' }).catch(() => null);
                                }
                                
                                const discLimit = Math.min(this.settings.limit || 100, 100); 
                                const discPromise = fetch(`https://${cleanDomain}/wikia.php?controller=DiscussionPost&method=getPosts&limit=${discLimit}&viewableOnly=true&format=json&cb=${Date.now()}`, { mode: 'cors' })
                                    .then(r => r.ok ? r.json() : null)
                                    .catch(() => null);

                                const [res, discData] = await Promise.all([rcPromise, discPromise]);
                                
                                if (res) {
                                    if (res?.query?.general?.sitename) {
                                        currentWikiName = res.query.general.sitename;
                                    }
                                    if (res?.query?.recentchanges) {
                                        let rcEdits = res.query.recentchanges;
                                        
                                        if (this.canPatrol && rcEdits.length > 0) {
                                            const trustedGroups = ['sysop', 'content-moderator', 'rollback', 'staff', 'wiki-representative', 'soap', 'wiki-specialist', 'bot', 'autopatrolled', 'vanguard', 'voldev', 'global-discussions-moderator'];
                                            const systemUsers = ['GlobalJSReviewer', 'Fandom', 'Fandombot', 'Wikia', 'WikiaBot', 'Default'];
                                            const uniqueUsers = [...new Set(rcEdits.map(rc => rc.user))];
                                            const trustedUsers = new Set();
                                            
                                            const chunkArray = (arr, size) => Array.from({ length: Math.ceil(arr.length / size) }, (v, i) => arr.slice(i * size, i * size + size));
                                            const userChunks = chunkArray(uniqueUsers, 50);
                                            
                                            const uApi = new mw.ForeignApi(`https://${cleanDomain}/api.php`, { anonymous: true });
                                            const userPromises = userChunks.map(chunk => 
                                                uApi.get({ action: 'query', list: 'users', ususers: chunk.join('|'), usprop: 'groups', formatversion: 2 }).catch(() => null)
                                            );
                                            
                                            const uResults = await Promise.all(userPromises);
                                            uResults.forEach(uRes => {
                                                if (uRes?.query?.users) {
                                                    uRes.query.users.forEach(u => {
                                                        if (u.groups && u.groups.some(g => trustedGroups.includes(g))) {
                                                            trustedUsers.add(u.name);
                                                        }
                                                    });
                                                }
                                            });
                                            
                                            rcEdits.forEach(rc => {
                                                if (trustedUsers.has(rc.user) || systemUsers.includes(rc.user) || rc.user === mw.config.get('wgUserName')) {
                                                    delete rc.unpatrolled;
                                                }
                                            });
                                        }

                                        wikiEdits.push(...rcEdits.map(rc => this.normalizeData(rc, cleanDomain, currentWikiName)));
                                    } else {
                                        if (!this.failedWikis.includes(rawDomain)) this.failedWikis.push(rawDomain);
                                    }
                                } else {
                                    if (!this.failedWikis.includes(rawDomain)) this.failedWikis.push(rawDomain);
                                }
                                
                                if (discData) {
                                    const posts = discData?._embedded?.['doc:posts'] || [];
                                    const articleIds = posts.filter(p => p._embedded?.thread?.[0]?.containerType === 'ARTICLE_COMMENT').map(p => p.forumId).filter(Boolean);
                                    let articleData = {};
                                    
                                    if (articleIds.length > 0) {
                                        try {
                                            const uniqueIds = [...new Set(articleIds)];
                                            const artRes = await fetch(`https://${cleanDomain}/wikia.php?controller=FeedsAndPosts&method=getArticleNamesAndUsernames&stablePageIds=${uniqueIds.join(',')}&format=json&cb=${Date.now()}`, { mode: 'cors' });
                                            if (artRes.ok) {
                                                const artJson = await artRes.json();
                                                articleData = artJson.articleNames || {};
                                            }
                                        } catch(e) {}
                                    }

                                    posts.forEach(p => {
                                        try {
                                            wikiEdits.push(this.normalizeDiscussion(p, cleanDomain, articleData, currentWikiName));
                                        } catch(err) {}
                                    });
                                }
                                
                                resolve(wikiEdits);
                            } catch (e) {
                                if (!this.failedWikis.includes(rawDomain)) this.failedWikis.push(rawDomain);
                                resolve([]);
                            }
                        }, index * 50); 
                    });
                });
                
                const results = await Promise.all(fetchPromises);
                
                this.edits.forEach(e => editsMap.set(e.id, e));
                results.forEach(wikiEdits => {
                    wikiEdits.forEach(e => editsMap.set(e.id, e));
                });
                
                let allEdits = Array.from(editsMap.values());
                allEdits = allEdits.filter(edit => new Date(edit.timestamp) >= endDate);
                allEdits.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                this.edits = allEdits;
                
            } finally {
                this.isLoading = false;
            }
        },
        
        normalizeData(rc, wikiDomain, wikiName) {
            const serverUrl = `https://${wikiDomain}`;
            const articlePath = `${serverUrl}/wiki/`;
            
            let category = 'content';
            let groupWithID = rc.title; 
            let isBot = !!rc.bot; 
            
            const mediaNs = [-2, 6];
            const systemNs = [-1, 2, 8, 828];
            const socialNs = [119, 500, 501, 502, 503, 1200, 1201, 1202, 2000, 2001, 2002]; 
            
            if (rc.type === 'log') {
                groupWithID = rc.logtype; 
                if (['upload'].includes(rc.logtype) || mediaNs.includes(rc.ns)) category = 'media';
                else if (rc.ns % 2 !== 0 || socialNs.includes(rc.ns)) category = 'social';
                else category = 'system';
            } else {
                if (mediaNs.includes(rc.ns)) category = 'media';
                else if (rc.ns % 2 !== 0 || socialNs.includes(rc.ns)) category = 'social';
                else if (systemNs.includes(rc.ns)) category = 'system'; 
                else category = 'content'; 
            }
            
            let flagsArr = [];
            if (rc.type === 'new') flagsArr.push({ text: 'Н', title: 'Новая страница' });
            if (rc.minor) flagsArr.push({ text: 'м', title: 'Малая правка' });
            if (isBot) flagsArr.push({ text: 'б', title: 'Правка бота' });

            let actionTitle = null;
            if (category === 'social') {
                let isMessage = (rc.ns === 1200 || rc.ns === 1201 || rc.ns === 1202);
                let isPost = (rc.ns === 2000 || rc.ns === 2001 || rc.ns === 2002);
                let isBlog = (rc.ns === 500 || rc.ns === 501 || rc.ns === 502 || rc.ns === 503);
                let isTalk = (!isMessage && !isPost && !isBlog);

                let act = 'Изменение';
                if (rc.type === 'new') act = 'Новый';
                else if (rc.type === 'log') act = CwaDicts.logActMap[rc.logaction] || 'Изменение';

                let cType = isTalk ? 'talk' : isBlog ? 'blog' : isMessage ? 'message' : 'post';
                let isReply = false;
                if (isBlog) isReply = (rc.ns === 501 || rc.ns === 503);
                if (isMessage) isReply = (rc.ns === 1201);
                if (isPost) isReply = (rc.ns === 2001);

                if (act === 'Новый' && isReply) {
                    const replyMap = { 'blog': 'Ответ на блог', 'message': 'Ответ на сообщение', 'post': 'Ответ на пост' };
                    actionTitle = replyMap[cType] || 'Новое обсуждение';
                } else {
                    actionTitle = CwaDicts.socialTitleMap[cType]?.[act] || 'Изменение';
                }
            } else {
                if (rc.type === 'new') {
                    actionTitle = (rc.ns === 6) ? 'Загружен новый файл' : 'Создана новая страница';
                } else if (rc.type === 'log') {
                    const logAct = rc.logtype + '/' + rc.logaction;
                    actionTitle = CwaDicts.logMap[logAct] || (rc.logtype + ' / ' + rc.logaction);
                } else {
                    actionTitle = (rc.ns === 6) ? 'Отредактирован файл' : 'Отредактирована страница';
                }
            }
            
            const targetId = rc.rcid || rc.logid || rc.revid;

            return Object.freeze({
                id: rc.rcid || rc.logid || Math.random().toString(36).substring(2, 9),
                revid: rc.revid, rcid: rc.rcid, old_revid: rc.old_revid, pageid: rc.pageid,
                unpatrolled: rc.unpatrolled !== undefined && !this.patrolledIds.includes(targetId),
                type: rc.type, logtype: rc.logtype, logaction: rc.logaction,
                ns: rc.ns, title: rc.title, user: rc.user, timestamp: rc.timestamp,
                time: new Date(rc.timestamp).toLocaleTimeString(navigator.language, { hour: '2-digit', minute: '2-digit' }),
                parsedComment: rc.parsedcomment || (rc.type === 'log' ? (CwaDicts.logNamesMap[rc.logtype] || `Журнал: ${rc.logtype} (${rc.logaction})`) : ''),
                sizeDiff: rc.newlen !== undefined && rc.oldlen !== undefined ? rc.newlen - rc.oldlen : 0,
                flags: flagsArr, wikiDomain: wikiDomain,
                wikiName: wikiName || wikiDomain,
                wikiFavicon: `${serverUrl}/wiki/Special:FilePath/Site-favicon.ico`,
                pageUrl: `${articlePath}${encodeURIComponent(rc.title)}`,
                userUrl: `${articlePath}User:${encodeURIComponent(rc.user)}`,
                userTalkUrl: `${articlePath}User_talk:${encodeURIComponent(rc.user)}`,
                userContribsUrl: `${articlePath}Special:Contributions/${encodeURIComponent(rc.user)}`,
                userBlockUrl: `${articlePath}Special:Block/${encodeURIComponent(rc.user)}`,
                undoUrl: rc.revid && rc.old_revid ? `${articlePath}${encodeURIComponent(rc.title)}?action=edit&undo=${rc.revid}&undoafter=${rc.old_revid}` : null,
                category: category, groupWithID: groupWithID,
                actionTitle: actionTitle
            });
        },
        
        normalizeDiscussion(post, wikiDomain, articleData, wikiName) {
            const thread = post._embedded?.thread?.[0] || {};
            const date = new Date((post.modificationDate?.epochSecond || post.creationDate?.epochSecond) * 1000);
            const isReply = post.position > 1;
            const containerType = thread.containerType || "FORUM";
            
            let pageUrl = '';
            let contentType = 'post';
            let displayTitle = thread.title || post.title;
            
            if (containerType === 'ARTICLE_COMMENT') {
                if (displayTitle && (displayTitle.startsWith('User blog:') || displayTitle.startsWith('Блог участника:'))) {
                    contentType = 'blog';
                } else {
                    contentType = 'comment';
                }
                const info = articleData && articleData[post.forumId] ? articleData[post.forumId] : null;
                if (info) {
                    pageUrl = `https://${wikiDomain}/wiki/${encodeURIComponent(info.title.replace(/ /g, '_'))}?commentId=${post.threadId}${isReply ? '&replyId=' + post.id : ''}`;
                    displayTitle = info.title;
                } else {
                    pageUrl = `https://${wikiDomain}/f/p/${post.threadId}`;
                    displayTitle = post.forumName || 'Комментарий к статье';
                }
            } else if (containerType === 'WALL' || containerType === 'MESSAGE_WALL') {
                const cleanWallName = (post.forumName || "").replace(/ Message Wall$/, "").replace(/^Стена обсуждения:/, "");
                pageUrl = `https://${wikiDomain}/wiki/Message_Wall:${encodeURIComponent(cleanWallName.replace(/ /g, '_'))}?threadId=${post.threadId}${isReply ? '#' + post.id : ''}`;
                if (!displayTitle || displayTitle.startsWith("@")) displayTitle = 'Стена обсуждения';
                contentType = 'message';
            } else {
                pageUrl = `https://${wikiDomain}/f/p/${post.threadId}${isReply ? '/r/' + post.id : ''}`;
                if (!displayTitle) displayTitle = 'Обсуждение на форуме';
            }

            let summary = post.snippet || post.rawContent || post.body;
            
            if (!summary && post.jsonModel) {
                try {
                    let texts = [];
                    JSON.parse(post.jsonModel, (key, value) => {
                        if (key === 'text' && typeof value === 'string') texts.push(value);
                        return value;
                    });
                    summary = texts.join(' ').replace(/\s+/g, ' ').trim();
                } catch (e) {}
            }

            summary = summary || '(Вложение / Опрос)';
            if (summary.length > 85) summary = summary.substring(0, 85) + '...';

            let act = 'Новый';
            if (post.isDeleted) act = 'Удаление';
            else if (post.isLocked) act = 'Закрытие';

            let safeContentType = ['comment', 'message', 'blog', 'post'].includes(contentType) ? contentType : 'post';
            let actionTitle;
            
            if (act === 'Новый' && isReply) {
                const replyMap = { 'comment': 'Ответ на комментарий', 'message': 'Ответ на сообщение', 'blog': 'Ответ на блог', 'post': 'Ответ на пост' };
                actionTitle = replyMap[safeContentType];
            } else {
                actionTitle = CwaDicts.socialTitleMap[safeContentType === 'comment' ? 'talk' : safeContentType]?.[act] || 'Изменение';
            }

            return Object.freeze({
                id: 'disc-' + post.id,
                revid: null, rcid: null, old_revid: null, pageid: null,
                unpatrolled: false,
                type: 'discussion', logtype: '', logaction: '',
                ns: -5234, 
                title: displayTitle,
                actionTitle: actionTitle,
                user: post.createdBy?.name || 'Аноним',
                timestamp: date.toISOString(),
                time: date.toLocaleTimeString(navigator.language, { hour: '2-digit', minute: '2-digit' }),
                parsedComment: summary, sizeDiff: 0,
                flags: [], 
                wikiDomain: wikiDomain,
                wikiName: wikiName || wikiDomain,
                wikiFavicon: `https://${wikiDomain}/wiki/Special:FilePath/Site-favicon.ico`,
                pageUrl: pageUrl,
                userUrl: `https://${wikiDomain}/wiki/User:${encodeURIComponent(post.createdBy?.name || 'Аноним')}`,
                userTalkUrl: `https://${wikiDomain}/wiki/User_talk:${encodeURIComponent(post.createdBy?.name || 'Аноним')}`,
                userContribsUrl: `https://${wikiDomain}/wiki/Special:Contributions/${encodeURIComponent(post.createdBy?.name || 'Аноним')}`,
                userBlockUrl: `https://${wikiDomain}/wiki/Special:Block/${encodeURIComponent(post.createdBy?.name || 'Аноним')}`,
                category: 'social', groupWithID: 'disc-' + post.threadId,
                socialContext: { activityType: post.isDeleted ? 'delete' : 'create', contentType: contentType + (isReply ? '-reply' : '') },
                jsonModel: post.jsonModel,
                rawContent: post.rawContent
            });
        }
    };
