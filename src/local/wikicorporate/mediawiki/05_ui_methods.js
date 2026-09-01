const AppMethodsUi = {
        savePatrolledId(id) {
            if (!id) return;
            if (!this.patrolledIds.includes(id)) {
                this.patrolledIds.push(id);
                if (this.patrolledIds.length > 2000) {
                    this.patrolledIds = this.patrolledIds.slice(-2000);
                }
                try {
                    localStorage.setItem('cwa-patrolled-cache', JSON.stringify(this.patrolledIds));
                } catch (e) {}
            }
        },
        openInNewTab(url) { window.open(url, '_blank'); },
        pluralize(count, words) {
            const cases = [2, 0, 1, 1, 1, 2];
            return count + ' ' + words[(count % 100 > 4 && count % 100 < 20) ? 2 : cases[(count % 10 < 5) ? count % 10 : 5]];
        },
        getEditsByTab(tabId) { return this.edits.filter(edit => edit.category === tabId); },
        toggleGroup(key) { this.expandedGroups[key] = !this.expandedGroups[key]; },
        
        getGroupDiff(group) {
            const diffableEdits = group.items.filter(i => i.revid && i.old_revid);
            if (diffableEdits.length === 0) return null;
            return { from: diffableEdits[diffableEdits.length - 1].old_revid, to: diffableEdits[0].revid };
        },
        
        formatWikiUrl(inputUrl) {
            const urlToParse = inputUrl.startsWith('http') ? inputUrl : 'https://' + inputUrl;
            let parsed;
            try {
                parsed = new URL(urlToParse);
            } catch (e) {
                throw new Error('Security Error: Invalid URL format.');
            }

            const hostname = parsed.hostname;

            if (!hostname.endsWith('.fandom.com') && hostname !== 'fandom.com') {
                throw new Error('Security Error: Only fandom.com domains are allowed.');
            }

            let url = parsed.host + parsed.pathname;
            url = url.replace(/\/$/, '');

            const oldFormatMatch = url.match(/^([a-z\-]{2,3})\.([^\.]+)\.fandom\.com$/);
            if (oldFormatMatch) {
                let wikiName = oldFormatMatch[2];
                url = `${wikiName}.fandom.com/${oldFormatMatch[1]}`;
            }

            return url; 
        },
        
        setupAutoRefresh() {
            if (this.refreshInterval) {
                clearInterval(this.refreshInterval);
            }
            if (this.settings.autoRefresh && this.settings.autoRefresh > 0) {
                this.refreshInterval = setInterval(() => {
                    if (!this.isLoading && !this.isPatrolling) {
                        this.fetchData();
                    }
                }, this.settings.autoRefresh * 1000);
            }
        },
        
        getIconForType(edit) {
            if (edit.type === 'discussion' && edit.socialContext) {
                const act = edit.socialContext.activityType; 
                const ctx = edit.socialContext.contentType;  

                const socialMap = {
                    'create': {
                        'comment': 'fa-solid fa-comment-dots',      
                        'comment-reply': 'fa-solid fa-comments',    
                        'message': 'fa-solid fa-envelope',          
                        'message-reply': 'fa-solid fa-reply',       
                        'post': 'fa-solid fa-message',              
                        'post-reply': 'fa-solid fa-reply-all',
                        'blog': 'fa-solid fa-blog',
                        'blog-reply': 'fa-solid fa-comment-medical'
                    },
                    'update': {
                        'comment': 'fa-solid fa-pen-to-square',
                        'comment-reply': 'fa-solid fa-pen',
                        'message': 'fa-solid fa-envelope-open-text',
                        'message-reply': 'fa-solid fa-marker',
                        'post': 'fa-solid fa-pen-clip',
                        'post-reply': 'fa-solid fa-pencil',
                        'blog': 'fa-solid fa-pen-nib',
                        'blog-reply': 'fa-solid fa-pen-ruler'
                    },
                    'delete': {
                        'comment': 'fa-solid fa-trash-can',         
                        'comment-reply': 'fa-solid fa-eraser',      
                        'message': 'fa-solid fa-calendar-xmark',    
                        'message-reply': 'fa-solid fa-minus-square',
                        'post': 'fa-solid fa-ban',                  
                        'post-reply': 'fa-solid fa-trash',
                        'blog': 'fa-solid fa-trash-can',
                        'blog-reply': 'fa-solid fa-eraser'
                    },
                    'undelete': {
                        'comment': 'fa-solid fa-trash-arrow-up',    
                        'message': 'fa-solid fa-recycle',            
                        'post': 'fa-solid fa-trash-can-arrow-up',
                        'blog': 'fa-solid fa-trash-arrow-up'
                    },
                    'lock': {
                        'comment': 'fa-solid fa-lock',              
                        'message': 'fa-solid fa-user-lock',         
                        'post': 'fa-solid fa-clock',
                        'blog': 'fa-solid fa-lock'
                    },
                    'unlock': {
                        'comment': 'fa-solid fa-lock-open',         
                        'message': 'fa-solid fa-unlock',            
                        'post': 'fa-solid fa-key',
                        'blog': 'fa-solid fa-lock-open'
                    }
                };

                if (socialMap[act] && socialMap[act][ctx]) {
                    return socialMap[act][ctx];
                }
                return 'fa-solid fa-comment';
            }

            if (edit.type === 'log') {
                const map = {
                    'delete': 'fa-solid fa-trash',          
                    'block': 'fa-solid fa-user-lock',       
                    'protect': 'fa-solid fa-shield-halved', 
                    'upload': 'fa-solid fa-upload',         
                    'move': 'fa-solid fa-copy',             
                    'rights': 'fa-solid fa-user-shield',    
                    'contentmodel': 'fa-solid fa-file-code' 
                };
                return map[edit.logtype] || 'fa-solid fa-clipboard-list';
            }

            if (edit.type === 'new') return 'fa-solid fa-folder-plus';
            
            const nsIconMap = {
                '-1': 'fa-solid fa-code', '8': 'fa-solid fa-code', '828': 'fa-solid fa-code',
                '10': 'fa-solid fa-gears',
                '14': 'fa-solid fa-tags',
                '6': 'fa-solid fa-image',
                '4': 'fa-solid fa-flag',
                '2': 'fa-solid fa-user',
                '500': 'fa-solid fa-message', '502': 'fa-solid fa-message',
                '400': 'fa-solid fa-video', '1100': 'fa-solid fa-video',
                '420': 'fa-solid fa-map-location-dot'
            };
            
            return nsIconMap[edit.ns] || 'fa-solid fa-pen-to-square';
        },
        
        getSizeClass(diff) {
            if (diff > 500) return 'cwa-rc__size--large-plus';
            if (diff > 0) return 'cwa-rc__size--plus';
            if (diff < -500) return 'cwa-rc__size--large-minus';
            if (diff < 0) return 'cwa-rc__size--minus';
            return 'cwa-rc__size--zero';
        },

        async doPatrol(edit) {
            try {
                const api = new mw.ForeignApi(`https://${edit.wikiDomain}/api.php`);
                const params = { action: 'patrol', formatversion: 2 };
                
                if (edit.rcid) params.rcid = edit.rcid;
                else if (edit.revid) params.revid = edit.revid;
                else throw new Error('No ID');
                
                await api.postWithToken('patrol', params);
                mw.notify(`Правка на странице "${edit.title}" отпатрулирована.`, { type: 'success' });
                
                this.savePatrolledId(edit.rcid || edit.logid || edit.revid);

                const index = this.edits.findIndex(e => e.id === edit.id);
                if (index !== -1) {
                    this.edits[index] = Object.freeze({ ...this.edits[index], unpatrolled: false });
                }
            } catch (e) {
                mw.notify('Ошибка при патрулировании: ' + (e.info || 'Нет прав.'), { type: 'error' });
            }
        },

        async doPatrolGroup(group) {
            const unpatrolled = group.items.filter(i => i.unpatrolled);
            if (!unpatrolled.length) return;

            try {
                const api = new mw.ForeignApi(`https://${group.wikiDomain}/api.php`);
                for (const edit of unpatrolled) {
                    const params = { action: 'patrol', formatversion: 2 };
                    if (edit.rcid) params.rcid = edit.rcid;
                    else if (edit.revid) params.revid = edit.revid;
                    else continue;

                    await api.postWithToken('patrol', params);
                    
                    this.savePatrolledId(edit.rcid || edit.logid || edit.revid);

                    const index = this.edits.findIndex(e => e.id === edit.id);
                    if (index !== -1) {
                        this.edits[index] = Object.freeze({ ...this.edits[index], unpatrolled: false });
                    }
                }
                mw.notify('Группа правок отпатрулирована.', { type: 'success' });
            } catch (e) {
                mw.notify('Ошибка при патрулировании группы: ' + (e.info || 'Нет прав.'), { type: 'error' });
            }
        },
        
        async patrolAll() {
            const unpatrolled = this.edits.filter(e => e.unpatrolled && e.category === this.activeTab);
            if (!unpatrolled.length) return;
            
            if (!confirm(`Найдено действий для патрулирования на текущей вкладке: ${unpatrolled.length}. Начать процесс?`)) return;

            this.isPatrolling = true;
            let successCount = 0;
            let errorCount = 0;

            const byDomain = {};
            unpatrolled.forEach(edit => {
                if (!byDomain[edit.wikiDomain]) byDomain[edit.wikiDomain] = [];
                byDomain[edit.wikiDomain].push(edit);
            });

            for (const domain of Object.keys(byDomain)) {
                const api = new mw.ForeignApi(`https://${domain}/api.php`);
                const items = byDomain[domain];
                
                for (let i = 0; i < items.length; i += 4) {
                    const chunk = items.slice(i, i + 4);
                    const chunkPromises = chunk.map(async (edit) => {
                        try {
                            const params = { action: 'patrol', formatversion: 2 };
                            if (edit.rcid) params.rcid = edit.rcid;
                            else if (edit.revid) params.revid = edit.revid;
                            else return;

                            await api.postWithToken('patrol', params);
                            
                            this.savePatrolledId(edit.rcid || edit.logid || edit.revid);

                            const index = this.edits.findIndex(e => e.id === edit.id);
                            if (index !== -1) {
                                this.edits[index] = Object.freeze({ ...this.edits[index], unpatrolled: false });
                            }
                            successCount++;
                        } catch (e) {
                            errorCount++;
                        }
                    });

                    await Promise.all(chunkPromises);
                    await new Promise(r => setTimeout(r, 250));
                }
            }
            
            this.isPatrolling = false;
            mw.notify(`Готово! Успешно: ${successCount}` + (errorCount > 0 ? `, Ошибок: ${errorCount}` : ''), { type: errorCount > 0 ? 'warn' : 'success' });
        },

        async doRollback(edit) {
            if (!confirm(`Откатить правки участника ${edit.user} на странице "${edit.title}"?`)) return;
            try {
                const api = new mw.ForeignApi(`https://${edit.wikiDomain}/api.php`);
                await api.postWithToken('rollback', { action: 'rollback', title: edit.title, user: edit.user, formatversion: 2 });
                mw.notify(`Правки участника ${edit.user} успешно откачены.`, { type: 'success' });
                this.edits = this.edits.filter(e => e.id !== edit.id);
            } catch (e) {
                mw.notify('Ошибка при откате: ' + (e.info || 'Недостаточно прав или правка уже откачена.'), { type: 'error' });
            }
        },

        cleanUpRemoteResources() {
            ['cwa-remote-styles', 'cwa-remote-scripts', 'cwa-remote-inline', 'cwa-remote-styles-preload'].forEach(id => {
                const el = document.getElementById(id);
                if (el) el.remove();
            });
        },

        closeModal() {
            this.cleanUpRemoteResources();
            this.modal.isOpen = false;
            this.modal.content = '';
        },
        
        openDiffModal(wikiDomain, fromRev, toRev, title) {
            this.modal.isOpen = true; this.modal.isLoading = true;
            this.modal.title = `Сравнение версий: ${title}`;
            
            const siteStylesUrl = `https://${wikiDomain}/load.php?lang=ru&modules=mediawiki.diff.styles|site.styles&only=styles&skin=fandomdesktop`;
            const preloadLink = document.createElement('link');
            preloadLink.rel = 'preload';
            preloadLink.as = 'style';
            preloadLink.href = siteStylesUrl;
            preloadLink.id = 'cwa-remote-styles-preload';
            document.head.appendChild(preloadLink);
            
            const api = new mw.ForeignApi(`https://${wikiDomain}/api.php`, { anonymous: true });
            api.get({ action: 'compare', fromrev: fromRev, torev: toRev, prop: 'diff|ids|title|user|timestamp|parsedcomment', formatversion: 2 }).then(data => {
                if (data?.compare?.body) {
                    const c = data.compare;
                    const serverUrl = `https://${wikiDomain}`;
                    const articleUrl = `${serverUrl}/wiki/${encodeURIComponent(title.replace(/ /g, '_'))}`;
                    
                    const formatTime = (ts) => {
                        if (!ts) return '';
                        const d = new Date(ts);
                        const time = d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
                        const date = d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).replace(' г.', '');
                        return `${time}, ${date}`;
                    };

                    const fromTs = formatTime(c.fromtimestamp);
                    const toTs = formatTime(c.totimestamp);
                    const fromUser = mw.html.escape(c.fromuser || 'Аноним');
                    const toUser = mw.html.escape(c.touser || 'Аноним');
                    
                    const headerHtml = `
                        <tr class="diff-header" valign="top">
                            <td class="diff-otitle" colspan="2">
                                <div class="mw-diff-otitle1"><strong><a href="${articleUrl}?oldid=${c.fromrevid}" target="_blank" data-action="revision-link-before">Версия от ${fromTs}</a> <span class="mw-rev-head-action">(<a href="${articleUrl}?oldid=${c.fromrevid}&action=edit" target="_blank" data-action="edit-revision-before">править</a>)</span></strong></div>
                                <div class="mw-diff-otitle2"><span class="mw-usertoollinks"><a href="${serverUrl}/wiki/User:${encodeURIComponent(fromUser)}" target="_blank" data-username="${fromUser}">${fromUser}</a> (<a href="${serverUrl}/wiki/User_talk:${encodeURIComponent(fromUser)}" target="_blank">обсуждение</a> | <a href="${serverUrl}/wiki/Special:Contributions/${encodeURIComponent(fromUser)}" target="_blank">вклад</a>)</span></div>
                                <div class="mw-diff-otitle3 cwa-rc__summary">${c.fromparsedcomment || ''}</div>
                            </td>
                            <td class="diff-ntitle" colspan="2">
                                <div class="mw-diff-ntitle1"><strong><a href="${articleUrl}?oldid=${c.torevid}" target="_blank" data-action="revision-link-after">Версия от ${toTs}</a> <span class="mw-rev-head-action">(<a href="${articleUrl}?oldid=${c.torevid}&action=edit" target="_blank" data-action="edit-revision-after">править</a>)</span><span class="mw-rev-head-action">(<a href="${articleUrl}?action=edit&undoafter=${c.fromrevid}&undo=${c.torevid}" target="_blank" data-action="undo">отменить</a>)</span></strong></div>
                                <div class="mw-diff-ntitle2"><span class="mw-usertoollinks"><a href="${serverUrl}/wiki/User:${encodeURIComponent(toUser)}" target="_blank" data-username="${toUser}">${toUser}</a> (<a href="${serverUrl}/wiki/User_talk:${encodeURIComponent(toUser)}" target="_blank">обсуждение</a> | <a href="${serverUrl}/wiki/Special:Contributions/${encodeURIComponent(toUser)}" target="_blank">вклад</a>)</span></div>
                                <div class="mw-diff-ntitle3 cwa-rc__summary">${c.toparsedcomment || ''}</div>
                            </td>
                        </tr>
                    `;

                    const linkNode = document.createElement('link');
                    linkNode.id = 'cwa-remote-styles';
                    linkNode.rel = 'stylesheet';
                    linkNode.href = siteStylesUrl;

                    const finishLoading = () => {
                        this.modal.content = `
                            <div class="cwa-remote-container skin-fandomdesktop theme-fandomdesktop-dark sitedir-ltr">
                                <table class="diff"><colgroup><col class="diff-marker"><col class="diff-content"><col class="diff-marker"><col class="diff-content"></colgroup><tbody>${headerHtml}${data.compare.body}</tbody></table>
                            </div>
                        `;
                        this.modal.isLoading = false;
                    };

                    linkNode.onload = finishLoading;
                    linkNode.onerror = finishLoading;
                    document.body.appendChild(linkNode);

                } else { 
                    this.modal.content = '<em>Изменения скрыты или не найдены.</em>'; 
                    this.modal.isLoading = false; 
                }
            }).catch(() => {
                this.modal.content = '<em>Не удалось загрузить изменения.</em>';
                this.modal.isLoading = false;
            });
        },

        parseProseMirror(jsonString, fallbackText) {
            if (!jsonString) return fallbackText ? `<p>${mw.html.escape(fallbackText)}</p>` : '<em>Нет содержимого</em>';
            try {
                const doc = typeof jsonString === 'string' ? JSON.parse(jsonString) : jsonString;
                
                const renderMarks = (text, marks) => {
                    if (!marks || !marks.length) return mw.html.escape(text);
                    let res = mw.html.escape(text);
                    marks.forEach(m => {
                        if (m.type === 'strong') res = `<strong>${res}</strong>`;
                        else if (m.type === 'em') res = `<em>${res}</em>`;
                        else if (m.type === 'code') res = `<code>${res}</code>`;
                        else if (m.type === 'underline') res = `<u>${res}</u>`;
                        else if (m.type === 'strike') res = `<s>${res}</s>`;
                        else if (m.type === 'link') res = `<a href="${mw.html.escape(m.attrs?.href || '#')}" target="_blank">${res}</a>`;
                    });
                    return res;
                };

                const renderNode = (n) => {
                    if (n.type === 'text') return renderMarks(n.text, n.marks);
                    if (n.type === 'hardBreak') return '<br>';
                    
                    const innerHTML = (n.content || []).map(renderNode).join('');
                    
                    switch (n.type) {
                        case 'doc': return innerHTML;
                        case 'paragraph': return `<p>${innerHTML}</p>`;
                        case 'blockquote': return `<blockquote>${innerHTML}</blockquote>`;
                        case 'bulletList': return `<ul>${innerHTML}</ul>`;
                        case 'orderedList': return `<ol>${innerHTML}</ol>`;
                        case 'listItem': return `<li>${innerHTML}</li>`;
                        case 'heading': return `<h${n.attrs?.level || 2}>${innerHTML}</h${n.attrs?.level || 2}>`;
                        case 'code_block': return `<pre><code>${innerHTML}</code></pre>`;
                        case 'mention': return `<em>@${mw.html.escape(n.attrs?.text || 'User')}</em>`;
                        default: return innerHTML;
                    }
                };

                return renderNode(doc);
            } catch (e) {
                return fallbackText ? `<p>${mw.html.escape(fallbackText)}</p>` : '<em>Ошибка обработки содержимого</em>';
            }
        },

        openPreviewModal(edit) {
            this.cleanUpRemoteResources();

            this.modal.isOpen = true; this.modal.isLoading = true;
            this.modal.title = `Предпросмотр: ${edit.title}`;

            if (edit.type === 'discussion') {
                const parsedHtml = this.parseProseMirror(edit.jsonModel, edit.rawContent);
                
                const siteStylesUrl = `https://${edit.wikiDomain}/load.php?lang=ru&modules=site.styles&only=styles&skin=fandomdesktop`;
                const linkNode = document.createElement('link');
                linkNode.id = 'cwa-remote-styles';
                linkNode.rel = 'stylesheet';
                linkNode.href = siteStylesUrl;

                const finishLoading = () => {
                    this.modal.content = `
                        <div class="cwa-remote-container skin-fandomdesktop theme-fandomdesktop-dark sitedir-ltr">
                            <div class="mw-parser-output">
                                ${parsedHtml}
                            </div>
                        </div>
                    `;
                    this.modal.isLoading = false;
                };

                linkNode.onload = finishLoading;
                linkNode.onerror = finishLoading; 
                document.body.appendChild(linkNode);
                
                return;
            }
            
            if (edit.ns !== 6) {
                const siteStylesUrl = `https://${edit.wikiDomain}/load.php?lang=ru&modules=site.styles&only=styles&skin=fandomdesktop`;
                const preloadLink = document.createElement('link');
                preloadLink.rel = 'preload';
                preloadLink.as = 'style';
                preloadLink.href = siteStylesUrl;
                preloadLink.id = 'cwa-remote-styles-preload';
                document.head.appendChild(preloadLink);
            }

            if (edit.ns === 6) {
                const api = new mw.ForeignApi(`https://${edit.wikiDomain}/api.php`, { anonymous: true });
                api.get({ action: 'query', titles: edit.title, prop: 'imageinfo', iiprop: 'url', formatversion: 2 }).then(data => {
                    const pages = data?.query?.pages;
                    if (pages && pages[0] && pages[0].imageinfo && pages[0].imageinfo.length > 0) {
                        this.modal.content = `<div class="cwa-modal__img-wrap"><img src="${pages[0].imageinfo[0].url}" class="cwa-modal__img" /></div>`;
                    } else {
                        this.modal.content = '<em>Не удалось загрузить изображение. Возможно, файл удалён.</em>';
                    }
                    this.modal.isLoading = false;
                }).catch(() => {
                    this.modal.content = '<em>Ошибка при загрузке файла.</em>';
                    this.modal.isLoading = false;
                });
                return;
            }

            const api = new mw.ForeignApi(`https://${edit.wikiDomain}/api.php`, { anonymous: true });
            const parseParams = edit.pageid ? { pageid: edit.pageid } : { page: edit.title };
            
            api.get({ action: 'parse', ...parseParams, prop: 'text|modules|headhtml', useskin: 'fandomdesktop', disabletoc: true, formatversion: 2 }).then(data => {
                if (data?.parse?.text) {
                    let html = data.parse.text;
                    html = html.replace(/(href|src)="(\/(?!\/).*?)"/g, `$1="https://${edit.wikiDomain}$2"`);

                    let inlineStyles = '';
                    if (data.parse.headhtml) {
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = data.parse.headhtml;
                        tempDiv.querySelectorAll('style').forEach(st => {
                            inlineStyles += st.textContent + '\n';
                        });
                    }

                    if (inlineStyles) {
                        const styleNode = document.createElement('style');
                        styleNode.id = 'cwa-remote-inline';
                        styleNode.textContent = inlineStyles;
                        document.body.appendChild(styleNode);
                    }

                    const siteStylesUrl = `https://${edit.wikiDomain}/load.php?lang=ru&modules=site.styles&only=styles&skin=fandomdesktop`;
                    const siteScriptsUrl = `https://${edit.wikiDomain}/load.php?lang=ru&modules=site.scripts&only=scripts&skin=fandomdesktop`;

                    const linkNode = document.createElement('link');
                    linkNode.id = 'cwa-remote-styles';
                    linkNode.rel = 'stylesheet';
                    linkNode.href = siteStylesUrl;

                    const scriptNode = document.createElement('script');
                    scriptNode.id = 'cwa-remote-scripts';
                    scriptNode.src = siteScriptsUrl;

                    const finishLoading = () => {
                        this.modal.content = `
                            <div class="cwa-remote-container skin-fandomdesktop theme-fandomdesktop-dark sitedir-ltr">
                                <div class="mw-parser-output">
                                    ${html}
                                </div>
                            </div>
                        `;
                        this.modal.isLoading = false; 

                        this.$nextTick(() => {
                            const modules = [
                                ...(data.parse.modules || []),
                                ...(data.parse.modulestyles || [])
                            ];
                            const safeModules = modules.filter(m => m.startsWith('ext.') || m.startsWith('mediawiki.'));
                            if (safeModules.length > 0) {
                                mw.loader.load(safeModules);
                            }

                            document.body.appendChild(scriptNode);

                            setTimeout(() => {
                                const contentElement = document.querySelector('.cwa-remote-container .mw-parser-output');
                                if (contentElement && window.mw && window.mw.hook && window.$) {
                                    window.mw.hook('wikipage.content').fire(window.$(contentElement));
                                }
                            }, 100);
                        });
                    };

                    linkNode.onload = finishLoading;
                    linkNode.onerror = finishLoading; 
                    document.body.appendChild(linkNode);

                } else {
                    throw new Error('No content');
                }
            }).catch(() => {
                const authApi = new mw.ForeignApi(`https://${edit.wikiDomain}/api.php`);
                authApi.get({ action: 'query', prop: 'deletedrevisions', titles: edit.title, drvprop: 'content', drvlimit: 1, formatversion: 2 }).then(data => {
                    const pages = data?.query?.pages;
                    if (pages && pages[0] && pages[0].deletedrevisions && pages[0].deletedrevisions.length > 0) {
                        const content = pages[0].deletedrevisions[0].content;
                        authApi.post({ action: 'parse', text: content, contentmodel: 'wikitext', disabletoc: true, formatversion: 2 }).then(parseData => {
                            this.modal.content = `<div class="cwa-modal__alert">Внимание: Это содержимое удалённой страницы</div>` + 
                                (parseData?.parse?.text || '').replace(/href="\//g, `target="_blank" href="https://${edit.wikiDomain}/`);
                            this.modal.isLoading = false;
                        }).catch(() => {
                            this.modal.content = `<div class="cwa-modal__alert">Внимание: Это содержимое удалённой страницы</div><div class="cwa-modal__pre-wrap">${mw.html.escape(content)}</div>`;
                            this.modal.isLoading = false;
                        });
                    } else {
                        this.modal.content = '<em>Страница удалена или у вас нет прав для её просмотра.</em>';
                        this.modal.isLoading = false;
                    }
                }).catch(() => {
                    this.modal.content = '<em>Ошибка при загрузке. Страница не существует или удалена.</em>';
                    this.modal.isLoading = false;
                });
            });
        }
    };
