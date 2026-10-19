const AppState = {
        data() {
            const uGroupsSet = new Set(mw.config.get('wgUserGroups') ?? []);
            const rollbackGroups = new Set(['sysop', 'content-moderator', 'rollback', 'staff', 'wiki-representative', 'soap']);
            const patrolGroups = new Set(['sysop', 'content-moderator', 'staff', 'wiki-representative', 'soap', 'wiki-specialist']);
            const blockGroups = new Set(['sysop', 'staff', 'wiki-representative', 'soap']);

            // ES2025/ES2026 Set.prototype.isDisjointFrom (O(1) проверка пересечения множеств групп)
            const hasRollback = !uGroupsSet.isDisjointFrom(rollbackGroups);
            const hasPatrol = !uGroupsSet.isDisjointFrom(patrolGroups);
            const hasBlock = !uGroupsSet.isDisjointFrom(blockGroups);

            let cachedPatrolled = [];
            try {
                const parsed = JSON.parse(localStorage.getItem('cwa-patrolled-cache') ?? '[]');
                if (Array.isArray(parsed)) cachedPatrolled = parsed;
            } catch {}

            return {
                canRollback: hasRollback,
                canPatrol: hasPatrol,
                canBlock: hasBlock,
                isLoading: false,
                isPatrolling: false,
                activeTab: 'content',
                settings: { limit: 4000, days: 3, showBots: false, showMinor: true, autoRefresh: 60 },
                refreshInterval: null,
                apiCache: {},
                wikis: [],
                edits: [],
                failedWikis: [],
                expandedGroups: {},
                patrolledIds: cachedPatrolled,
                tabs: [
                    { id: 'content', name: 'Статьи и Шаблоны', icon: 'fa-solid fa-file-lines' },
                    { id: 'social', name: 'Общение', icon: 'fa-solid fa-comments' },
                    { id: 'media', name: 'Медиа', icon: 'fa-solid fa-image' },
                    { id: 'system', name: 'Служебное и Боты', icon: 'fa-solid fa-robot' }
                ],
                modal: { isOpen: false, isLoading: false, title: '', content: '' }
            };
        },
        computed: {
            hasUnpatrolled() {
                return this.edits.some(e => e.unpatrolled && e.category === this.activeTab);
            },
            editsByDate() {
                const filtered = this.getEditsByTab(this.activeTab);
                const groupMap = new Map();

                for (const edit of filtered) {
                    const dateKey = new Date(edit.timestamp).toDateString();
                    const groupKey = `${edit.wikiDomain}-${edit.groupWithID}-${dateKey}`;
                    const existing = groupMap.get(groupKey);

                    if (existing) {
                        existing.items.push(edit);
                        existing.totalSizeDiff += edit.sizeDiff;
                    } else {
                        groupMap.set(groupKey, {
                            key: groupKey,
                            wikiDomain: edit.wikiDomain,
                            wikiName: edit.wikiName,
                            wikiFavicon: edit.wikiFavicon,
                            title: edit.title,
                            totalSizeDiff: edit.sizeDiff,
                            items: [edit]
                        });
                    }
                }

                const result = [];
                for (const g of groupMap.values()) {
                    const d = new Date(g.items[0].timestamp);
                    const dateStr = d.toLocaleString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).replace(' г.', '');

                    const lastDateGroup = result.at(-1);
                    if (lastDateGroup?.date === dateStr) {
                        lastDateGroup.groups.push(g);
                    } else {
                        result.push({ date: dateStr, groups: [g] });
                    }
                }
                return result;
            }
        }
    };
