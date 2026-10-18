const AppMethodsUi = {
        sanitizeUrl(rawUrl) {
            if (!rawUrl || typeof rawUrl !== 'string') return '#';
            const trimmed = rawUrl.trim();
            if (trimmed.startsWith('/') && !trimmed.startsWith('//')) {
                return mw.html.escape(trimmed);
            }
            try {
                const parsed = new URL(trimmed);
                if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
                    return mw.html.escape(parsed.href);
                }
            } catch {}
            return '#';
        },

        savePatrolledId(id) {
            if (!id || this.patrolledIds.includes(id)) return;
            this.patrolledIds.push(id);
            if (this.patrolledIds.length > 2000) {
                this.patrolledIds = this.patrolledIds.slice(-2000);
            }
            try {
                localStorage.setItem('cwa-patrolled-cache', JSON.stringify(this.patrolledIds));
            } catch {}
        },

        openInNewTab(url) {
            if (url) window.open(url, '_blank', 'noopener,noreferrer');
        },

        pluralize(count, words) {
            const cases = [2, 0, 1, 1, 1, 2];
            return `${count} ${words[(count % 100 > 4 && count % 100 < 20) ? 2 : cases[Math.min(count % 10, 5)]]}`;
        },

        getEditsByTab(tabId) {
            return this.edits.filter(edit => edit.category === tabId);
        },

        toggleGroup(key) {
            this.expandedGroups[key] = !this.expandedGroups[key];
        },

        getGroupDiff(group) {
            const diffableEdits = group.items.filter(i => i.revid && i.old_revid);
            if (diffableEdits.length === 0) return null;
            return { from: diffableEdits.at(-1).old_revid, to: diffableEdits[0].revid };
        },

        formatWikiUrl(inputUrl) {
            const urlToParse = inputUrl.startsWith('http') ? inputUrl : `https://${inputUrl}`;
            const parsed = new URL(urlToParse);
            const hostname = parsed.hostname.toLowerCase();

            if (!hostname.endsWith('.fandom.com') && hostname !== 'fandom.com') {
                throw new Error('Security Error: Only fandom.com domains are allowed.');
            }

            let url = `${hostname}${parsed.pathname}`.replace(/\/$/, '');
            const oldFormatMatch = url.match(/^([a-z]{2,3}(?:-[a-z]{2,4})?)\.([^.]+)\.fandom\.com$/);
            if (oldFormatMatch) {
                url = `${oldFormatMatch[2]}.fandom.com/${oldFormatMatch[1]}`;
            }
            return url;
        },

        setupAutoRefresh() {
            if (this.refreshInterval) clearInterval(this.refreshInterval);
            if (this.settings.autoRefresh > 0) {
                this.refreshInterval = setInterval(() => {
                    if (!this.isLoading && !this.isPatrolling) this.fetchData();
                }, this.settings.autoRefresh * 1000);
            }
        },

        getIconForType(edit) {
            if (edit.socialContext) {
                const { activityType, contentType } = edit.socialContext;
                const socialIcon = CwaDicts.icons.social[activityType]?.[contentType];
                if (socialIcon) return socialIcon;
                if (edit.type === 'discussion') return 'fa-solid fa-comment';
            }
            if (edit.type === 'log') {
                return CwaDicts.icons.log[edit.logtype] ?? 'fa-solid fa-clipboard-list';
            }
            if (edit.type === 'new') return 'fa-solid fa-folder-plus';
            return CwaDicts.icons.ns[edit.ns] ?? 'fa-solid fa-pen-to-square';
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
                const api = this.getForeignApi(edit.wikiDomain, false);
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
                mw.notify(`Ошибка при патрулировании: ${e.info || 'Нет прав.'}`, { type: 'error' });
            }
        },

        async doPatrolGroup(group) {
            const unpatrolled = group.items.filter(i => i.unpatrolled);
            if (!unpatrolled.length) return;

            try {
                const api = this.getForeignApi(group.wikiDomain, false);
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
                mw.notify(`Ошибка при патрулировании группы: ${e.info || 'Нет прав.'}`, { type: 'error' });
            }
        },

        async patrolAll() {
            const unpatrolled = this.edits.filter(e => e.unpatrolled && e.category === this.activeTab);
            if (!unpatrolled.length) return;
            if (!confirm(`Найдено действий для патрулирования на текущей вкладке: ${unpatrolled.length}. Начать процесс?`)) return;

            this.isPatrolling = true;
            let successCount = 0;
            let errorCount = 0;

            // ES2024 Object.groupBy
            const byDomain = Object.groupBy(unpatrolled, edit => edit.wikiDomain);

            for (const [domain, items] of Object.entries(byDomain)) {
                const api = this.getForeignApi(domain, false);

                for (let i = 0; i < items.length; i += 4) {
                    const chunk = items.slice(i, i + 4);
                    await Promise.all(chunk.map(async (edit) => {
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
                        } catch {
                            errorCount++;
                        }
                    }));
                    await new Promise(r => setTimeout(r, 250));
                }
            }

            this.isPatrolling = false;
            mw.notify(
                `Готово! Успешно: ${successCount}${errorCount > 0 ? `, Ошибок: ${errorCount}` : ''}`,
                { type: errorCount > 0 ? 'warn' : 'success' }
            );
        },

        async doRollback(edit) {
            if (!confirm(`Откатить правки участника ${edit.user} на странице "${edit.title}"?`)) return;
            try {
                const api = this.getForeignApi(edit.wikiDomain, false);
                await api.postWithToken('rollback', {
                    action: 'rollback',
                    title: edit.title,
                    user: edit.user,
                    formatversion: 2
                });
                mw.notify(`Правки участника ${edit.user} успешно откачены.`, { type: 'success' });
                this.edits = this.edits.filter(e => e.id !== edit.id);
            } catch (e) {
                mw.notify(`Ошибка при откате: ${e.info || 'Недостаточно прав или правка уже откачена.'}`, { type: 'error' });
            }
        },

        cleanUpRemoteResources() {
            for (const id of ['cwa-remote-styles', 'cwa-remote-inline', 'cwa-remote-styles-preload']) {
                document.getElementById(id)?.remove();
            }
        },

        closeModal() {
            this.cleanUpRemoteResources();
            this.modal.isOpen = false;
            this.modal.content = '';
        },

        openDiffModal(wikiDomain, fromRev, toRev, title) {
            this.cleanUpRemoteResources();
            this.modal.isOpen = true;
            this.modal.isLoading = true;
            this.modal.title = `Сравнение версий: ${title}`;

            const siteStylesUrl = `https://${wikiDomain}/load.php?lang=ru&modules=mediawiki.diff.styles|site.styles&only=styles&skin=fandomdesktop`;
            const preloadLink = document.createElement('link');
            preloadLink.rel = 'preload';
            preloadLink.as = 'style';
            preloadLink.href = siteStylesUrl;
            preloadLink.id = 'cwa-remote-styles-preload';
            document.head.appendChild(preloadLink);

            const api = this.getForeignApi(wikiDomain, true);
            api.get({
                action: 'compare',
                fromrev: fromRev,
                torev: toRev,
                prop: 'diff|ids|title|user|timestamp|parsedcomment',
                formatversion: 2
            }).then(data => {
                if (data?.compare?.body) {
                    const c = data.compare;
                    const serverUrl = `https://${wikiDomain}`;
                    const articleUrl = mw.html.escape(`${serverUrl}/wiki/${encodeURIComponent(title.replaceAll(' ', '_'))}`);

                    const formatTime = (ts) => {
                        if (!ts) return '';
                        const d = new Date(ts);
                        const time = d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
                        const date = d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).replace(' г.', '');
                        return mw.html.escape(`${time}, ${date}`);
                    };

                    const fromTs = formatTime(c.fromtimestamp);
                    const toTs = formatTime(c.totimestamp);
                    const rawFromUser = c.fromuser || 'Аноним';
                    const rawToUser = c.touser || 'Аноним';
                    const fromUser = mw.html.escape(rawFromUser);
                    const toUser = mw.html.escape(rawToUser);
                    const fromRevId = Number(c.fromrevid) || 0;
                    const toRevId = Number(c.torevid) || 0;

                    const headerHtml = `
                        <tr class="diff-header" valign="top">
                            <td class="diff-otitle" colspan="2">
                                <div class="mw-diff-otitle1"><strong><a href="${articleUrl}?oldid=${fromRevId}" target="_blank" rel="noopener noreferrer" data-action="revision-link-before">Версия от ${fromTs}</a> <span class="mw-rev-head-action">(<a href="${articleUrl}?oldid=${fromRevId}&action=edit" target="_blank" rel="noopener noreferrer" data-action="edit-revision-before">править</a>)</span></strong></div>
                                <div class="mw-diff-otitle2"><span class="mw-usertoollinks"><a href="${serverUrl}/wiki/User:${encodeURIComponent(rawFromUser)}" target="_blank" rel="noopener noreferrer" data-username="${fromUser}">${fromUser}</a> (<a href="${serverUrl}/wiki/User_talk:${encodeURIComponent(rawFromUser)}" target="_blank" rel="noopener noreferrer">обсуждение</a> | <a href="${serverUrl}/wiki/Special:Contributions/${encodeURIComponent(rawFromUser)}" target="_blank" rel="noopener noreferrer">вклад</a>)</span></div>
                                <div class="mw-diff-otitle3 cwa-rc__summary">${c.fromparsedcomment || ''}</div>
                            </td>
                            <td class="diff-ntitle" colspan="2">
                                <div class="mw-diff-ntitle1"><strong><a href="${articleUrl}?oldid=${toRevId}" target="_blank" rel="noopener noreferrer" data-action="revision-link-after">Версия от ${toTs}</a> <span class="mw-rev-head-action">(<a href="${articleUrl}?oldid=${toRevId}&action=edit" target="_blank" rel="noopener noreferrer" data-action="edit-revision-after">править</a>)</span><span class="mw-rev-head-action">(<a href="${articleUrl}?action=edit&undoafter=${fromRevId}&undo=${toRevId}" target="_blank" rel="noopener noreferrer" data-action="undo">отменить</a>)</span></strong></div>
                                <div class="mw-diff-ntitle2"><span class="mw-usertoollinks"><a href="${serverUrl}/wiki/User:${encodeURIComponent(rawToUser)}" target="_blank" rel="noopener noreferrer" data-username="${toUser}">${toUser}</a> (<a href="${serverUrl}/wiki/User_talk:${encodeURIComponent(rawToUser)}" target="_blank" rel="noopener noreferrer">обсуждение</a> | <a href="${serverUrl}/wiki/Special:Contributions/${encodeURIComponent(rawToUser)}" target="_blank" rel="noopener noreferrer">вклад</a>)</span></div>
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
            if (!jsonString) {
                return fallbackText ? `<p>${mw.html.escape(fallbackText)}</p>` : '<em>Нет содержимого</em>';
            }
            try {
                const doc = typeof jsonString === 'string' ? JSON.parse(jsonString) : jsonString;

                const renderMarks = (text, marks) => {
                    let res = mw.html.escape(text ?? '');
                    if (!marks?.length) return res;
                    for (const m of marks) {
                        if (m.type === 'strong') res = `<strong>${res}</strong>`;
                        else if (m.type === 'em') res = `<em>${res}</em>`;
                        else if (m.type === 'code') res = `<code>${res}</code>`;
                        else if (m.type === 'underline') res = `<u>${res}</u>`;
                        else if (m.type === 'strike') res = `<s>${res}</s>`;
                        else if (m.type === 'link') {
                            res = `<a href="${this.sanitizeUrl(m.attrs?.href)}" target="_blank" rel="noopener noreferrer">${res}</a>`;
                        }
                    }
                    return res;
                };

                const renderNode = (n) => {
                    if (!n || typeof n !== 'object') return '';
                    if (n.type === 'text') return renderMarks(n.text, n.marks);
                    if (n.type === 'hardBreak') return '<br>';

                    const innerHTML = Array.isArray(n.content) ? n.content.map(renderNode).join('') : '';

                    switch (n.type) {
                        case 'doc': return innerHTML;
                        case 'paragraph': return `<p>${innerHTML}</p>`;
                        case 'blockquote': return `<blockquote>${innerHTML}</blockquote>`;
                        case 'bulletList': return `<ul>${innerHTML}</ul>`;
                        case 'orderedList': return `<ol>${innerHTML}</ol>`;
                        case 'listItem': return `<li>${innerHTML}</li>`;
                        case 'heading': {
                            const lvl = Math.min(Math.max(parseInt(n.attrs?.level, 10) || 2, 1), 6);
                            return `<h${lvl}>${innerHTML}</h${lvl}>`;
                        }
                        case 'code_block': return `<pre><code>${innerHTML}</code></pre>`;
                        case 'mention': return `<em>@${mw.html.escape(n.attrs?.text ?? 'User')}</em>`;
                        default: return innerHTML;
                    }
                };

                return renderNode(doc);
            } catch {
                return fallbackText ? `<p>${mw.html.escape(fallbackText)}</p>` : '<em>Ошибка обработки содержимого</em>';
            }
        },

        openPreviewModal(edit) {
            this.cleanUpRemoteResources();
            this.modal.isOpen = true;
            this.modal.isLoading = true;
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
                            <div class="mw-parser-output">${parsedHtml}</div>
                        </div>
                    `;
                    this.modal.isLoading = false;
                };

                linkNode.onload = finishLoading;
                linkNode.onerror = finishLoading;
                document.body.appendChild(linkNode);
                return;
            }

            if (edit.ns === 6) {
                const api = this.getForeignApi(edit.wikiDomain, true);
                api.get({
                    action: 'query',
                    titles: edit.title,
                    prop: 'imageinfo',
                    iiprop: 'url',
                    formatversion: 2
                }).then(data => {
                    const imgUrl = data?.query?.pages?.[0]?.imageinfo?.[0]?.url;
                    if (imgUrl) {
                        this.modal.content = `<div class="cwa-modal__img-wrap"><img src="${this.sanitizeUrl(imgUrl)}" class="cwa-modal__img" loading="lazy" /></div>`;
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

            const siteStylesUrl = `https://${edit.wikiDomain}/load.php?lang=ru&modules=site.styles&only=styles&skin=fandomdesktop`;
            const preloadLink = document.createElement('link');
            preloadLink.rel = 'preload';
            preloadLink.as = 'style';
            preloadLink.href = siteStylesUrl;
            preloadLink.id = 'cwa-remote-styles-preload';
            document.head.appendChild(preloadLink);

            const api = this.getForeignApi(edit.wikiDomain, true);
            const parseParams = edit.pageid ? { pageid: edit.pageid } : { page: edit.title };

            api.get({
                action: 'parse',
                ...parseParams,
                prop: 'text|modules|headhtml',
                useskin: 'fandomdesktop',
                disabletoc: true,
                formatversion: 2
            }).then(data => {
                if (!data?.parse?.text) throw new Error('No content');

                const html = data.parse.text.replace(/(href|src)="(\/(?!\/).*?)"/g, `$1="https://${edit.wikiDomain}$2"`);

                if (data.parse.headhtml) {
                    const doc = new DOMParser().parseFromString(data.parse.headhtml, 'text/html');
                    const inlineStyles = Array.from(doc.querySelectorAll('style'), st => st.textContent).join('\n');
                    if (inlineStyles) {
                        const styleNode = document.createElement('style');
                        styleNode.id = 'cwa-remote-inline';
                        styleNode.textContent = inlineStyles;
                        document.body.appendChild(styleNode);
                    }
                }

                const linkNode = document.createElement('link');
                linkNode.id = 'cwa-remote-styles';
                linkNode.rel = 'stylesheet';
                linkNode.href = siteStylesUrl;

                const finishLoading = () => {
                    this.modal.content = `
                        <div class="cwa-remote-container skin-fandomdesktop theme-fandomdesktop-dark sitedir-ltr">
                            <div class="mw-parser-output">${html}</div>
                        </div>
                    `;
                    this.modal.isLoading = false;

                    this.$nextTick(() => {
                        const safeModules = [
                            ...(data.parse.modules ?? []),
                            ...(data.parse.modulestyles ?? [])
                        ].filter(m => m.startsWith('ext.') || m.startsWith('mediawiki.'));

                        if (safeModules.length > 0) mw.loader.load(safeModules);

                        setTimeout(() => {
                            const contentElement = document.querySelector('.cwa-remote-container .mw-parser-output');
                            if (contentElement && window.mw?.hook && window.$) {
                                window.mw.hook('wikipage.content').fire(window.$(contentElement));
                            }
                        }, 100);
                    });
                };

                linkNode.onload = finishLoading;
                linkNode.onerror = finishLoading;
                document.body.appendChild(linkNode);
            }).catch(() => {
                const authApi = this.getForeignApi(edit.wikiDomain, false);
                authApi.get({
                    action: 'query',
                    prop: 'deletedrevisions',
                    titles: edit.title,
                    drvprop: 'content',
                    drvlimit: 1,
                    formatversion: 2
                }).then(data => {
                    const content = data?.query?.pages?.[0]?.deletedrevisions?.[0]?.content;
                    if (content) {
                        authApi.post({
                            action: 'parse',
                            text: content,
                            contentmodel: 'wikitext',
                            disabletoc: true,
                            formatversion: 2
                        }).then(parseData => {
                            this.modal.content = `<div class="cwa-modal__alert">Внимание: Это содержимое удалённой страницы</div>` +
                                (parseData?.parse?.text ?? '').replaceAll('href="/', `target="_blank" rel="noopener noreferrer" href="https://${edit.wikiDomain}/`);
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
