const AppState = {
        data() {
            const uGroups = mw.config.get('wgUserGroups') || [];
            const hasRollback = uGroups.some(g => ['sysop', 'content-moderator', 'rollback', 'staff', 'wiki-representative', 'soap'].includes(g));
            const hasPatrol = uGroups.some(g => ['sysop', 'content-moderator', 'staff', 'wiki-representative', 'soap', 'wiki-specialist'].includes(g));
            const hasBlock = uGroups.some(g => ['sysop', 'staff', 'wiki-representative', 'soap'].includes(g));

            let cachedPatrolled = [];
            try {
                const stored = localStorage.getItem('cwa-patrolled-cache');
                if (stored) cachedPatrolled = JSON.parse(stored);
            } catch(e) {}

            return {
                canRollback: hasRollback,
                canPatrol: hasPatrol,
                canBlock: hasBlock,
                isLoading: false,
                isPatrolling: false,
                activeTab: 'content',
                settings: { limit: 4000, days: 3, showBots: false, showMinor: true, autoRefresh: 60 },
                refreshInterval: null, 
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
                const groups = [];
                
                filtered.forEach(edit => {
                    const dateKey = new Date(edit.timestamp).toDateString();
                    const groupKey = `${edit.wikiDomain}-${edit.groupWithID}-${dateKey}`;
                    
                    let existingGroup = groups.find(g => g.key === groupKey);
                    if (existingGroup) {
                        existingGroup.items.push(edit);
                        existingGroup.totalSizeDiff += edit.sizeDiff;
                    } else {
                        groups.push({
                            key: groupKey, 
                            wikiDomain: edit.wikiDomain, 
                            wikiName: edit.wikiName, 
                            wikiFavicon: edit.wikiFavicon,
                            title: edit.title, 
                            totalSizeDiff: edit.sizeDiff, 
                            items: [edit]
                        });
                    }
                });

                const result = [];
                groups.forEach(g => {
                    const d = new Date(g.items[0].timestamp);
                    const dateStr = d.toLocaleString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' }).replace(' г.', '');
                    
                    let lastDateGroup = result[result.length - 1];
                    if (lastDateGroup && lastDateGroup.date === dateStr) {
                        lastDateGroup.groups.push(g);
                    } else {
                        result.push({ date: dateStr, groups: [g] });
                    }
                });
                return result;
            }
        }
    };
