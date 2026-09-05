const AppTemplate = `
            <div class="cwa-rc">
                <header class="cwa-rc__header">
                    <div class="cwa-rc__title">
                        <h2><i class="fa-solid fa-globe"></i> Вся активность с любимых Вики в одном месте</h2>
                        <div class="cwa-rc__title-actions">
                            <button v-if="canPatrol && hasUnpatrolled" class="wds-button wds-is-secondary cwa-rc__refresh" @click="patrolAll" :disabled="isPatrolling || isLoading">
                                <i class="fa-solid cwa-rc__btn-icon" :class="isPatrolling ? 'fa-spinner fa-spin' : 'fa-check-double'"></i> {{ isPatrolling ? 'Патрулирование...' : 'Отпатрулировать видимые' }}
                            </button>
                            <button class="wds-button wds-is-secondary cwa-rc__refresh" @click="fetchData" :disabled="isLoading || isPatrolling">
                                <i class="fa-solid fa-rotate-right cwa-rc__btn-icon" :class="{'fa-spin': isLoading}"></i> Обновить
                            </button>
                        </div>
                    </div>
                    <nav class="cwa-rc__tabs">
                        <div v-for="tab in tabs" :key="tab.id" 
                             class="cwa-rc__tab" 
                             :class="{'cwa-rc__tab--active': activeTab === tab.id}"
                             @click="activeTab = tab.id">
                             <i :class="tab.icon"></i> {{ tab.name }}
                             <span class="cwa-rc__badge" v-if="getEditsByTab(tab.id).length">{{ getEditsByTab(tab.id).length }}</span>
                        </div>
                    </nav>
                </header>
                <main class="cwa-rc__content">
                    
                    <div v-if="failedWikis.length > 0" class="cwa-rc__error-box">
                        <strong><i class="fa-solid fa-triangle-exclamation"></i> Ошибка загрузки с этих Вики. Возможно, неправильно указаны ссылки в Модуле или данные проекты внесены в реестр запрещённых ресурсов РКН:</strong>
                        <ul><li v-for="w in failedWikis" :key="w">{{ w }}</li></ul>
                    </div>
                    
                    <div v-if="isLoading && edits.length === 0" class="cwa-rc__loader">
                        <i class="fa-solid fa-spinner fa-spin-pulse"></i> Сбор данных с Википроектов...
                    </div>
                    
                    <div v-else-if="editsByDate.length === 0" class="cwa-rc__empty">
                        В этой категории пока нет новых изменений.
                    </div>
                    
                    <ul v-else class="cwa-rc__list">
                        <!-- РАЗБИВКА ПО ДНЯМ -->
                        <template v-for="dateGroup in editsByDate" :key="dateGroup.date">
                            <li class="cwa-rc__date-header">
                                {{ dateGroup.date }}
                            </li>
                            
                            <li v-for="group in dateGroup.groups" :key="group.key" class="cwa-rc__group-container">
                                
                                <!-- ОДИНОЧНАЯ ПРАВКА -->
                                <div v-if="group.items.length === 1" 
                                     class="cwa-rc__item"
                                     :data-type="group.items[0].type"
                                     :data-ns="group.items[0].ns"
                                     :data-logtype="group.items[0].logtype"
                                     :data-activity-type="group.items[0].socialContext ? group.items[0].socialContext.activityType : null"
                                     :data-content-type="group.items[0].socialContext ? group.items[0].socialContext.contentType : null">
                                     
                                    <div class="cwa-rc__favicon-wrap">
                                        <img :src="group.items[0].wikiFavicon" class="cwa-rc__favicon" :title="group.items[0].wikiName">
                                    </div>
                                    <div class="cwa-rc__main-info">
                                        <div class="cwa-rc__meta">
                                            <i :class="getIconForType(group.items[0])" class="cwa-rc__type-icon" :title="group.items[0].actionTitle || group.items[0].logaction || group.items[0].type"></i>
                                            <span v-if="group.items[0].unpatrolled" class="cwa-rc__unpatrolled" title="Неотпатрулированная правка">!</span>
                                            <span class="cwa-rc__time">{{ group.items[0].time }}</span>
                                            <a :href="group.items[0].pageUrl" class="cwa-rc__page-title" target="_blank">{{ group.items[0].title }}</a>
                                            <span v-if="group.items[0].actionText" class="cwa-rc__action-text">({{ group.items[0].actionText }})</span>
                                            <span v-if="group.items[0].type !== 'log' && group.items[0].type !== 'discussion'" class="cwa-rc__size" :class="getSizeClass(group.items[0].sizeDiff)">
                                                ({{ group.items[0].sizeDiff > 0 ? '+' : '' }}{{ group.items[0].sizeDiff }})
                                            </span>
                                            <span v-if="group.items[0].flags && group.items[0].flags.length" class="cwa-rc__flags">
                                                ( <template v-for="(flag, index) in group.items[0].flags" :key="index">
                                                    <abbr class="cwa-rc__flag-abbr" :title="flag.title">{{ flag.text }}</abbr><span v-if="index < group.items[0].flags.length - 1"> | </span>
                                                </template> )
                                            </span>
                                        </div>
                                        <div class="cwa-rc__details">
                                            <span class="cwa-rc__user-wrap">
                                                <a :href="group.items[0].userUrl" class="cwa-rc__user" target="_blank">{{ group.items[0].user }}</a>
                                                <span class="cwa-rc__user-actions">
                                                    <button class="cwa-rc__action-btn" title="Стена обсуждения" @click.stop="openInNewTab(group.items[0].userTalkUrl)"><i class="fa-solid fa-comment-dots"></i></button>
                                                    <button class="cwa-rc__action-btn" title="Вклад" @click.stop="openInNewTab(group.items[0].userContribsUrl)"><i class="fa-solid fa-list-ul"></i></button>
                                                    <button v-if="canBlock" class="cwa-rc__action-btn" title="Заблокировать" @click.stop="openInNewTab(group.items[0].userBlockUrl)"><i class="fa-solid fa-user-slash"></i></button>
                                                </span>
                                            </span>
                                            <span class="cwa-rc__summary" v-html="group.items[0].parsedComment"></span>
                                        </div>
                                    </div>
                                    <div class="cwa-rc__actions">
                                        <button v-if="canPatrol && group.items[0].unpatrolled" class="cwa-rc__action-btn cwa-rc__action-btn--success" title="Отпатрулировать" @click="doPatrol(group.items[0])">
                                            <i class="fa-solid fa-check"></i>
                                        </button>
                                        <button v-if="group.items[0].pageid || group.items[0].type === 'discussion'" class="cwa-rc__action-btn" title="Предпросмотр" @click="openPreviewModal(group.items[0])">
                                            <i class="fa-solid fa-eye"></i>
                                        </button>
                                        <button v-if="group.items[0].old_revid" class="cwa-rc__action-btn" title="Показать изменения" @click="openDiffModal(group.items[0].wikiDomain, group.items[0].old_revid, group.items[0].revid, group.items[0].title)">
                                            <i class="fa-solid fa-code-compare"></i>
                                        </button>
                                        <button v-if="group.items[0].undoUrl" class="cwa-rc__action-btn cwa-rc__action-btn--warn" title="Отменить" @click.stop="openInNewTab(group.items[0].undoUrl)">
                                            <i class="fa-solid fa-rotate-left"></i>
                                        </button>
                                        <button v-if="canRollback && group.items[0].type !== 'log' && group.items[0].type !== 'discussion'" class="cwa-rc__action-btn cwa-rc__action-btn--danger" title="Быстрый откат" @click="doRollback(group.items[0])">
                                            <i class="fa-solid fa-clock-rotate-left"></i>
                                        </button>
                                    </div>
                                </div>
                                
                                <!-- СГРУППИРОВАННЫЕ ПРАВКИ -->
                                <div v-else class="cwa-rc__group">
                                    <div class="cwa-rc__item cwa-rc__item--group-header" 
                                         @click="toggleGroup(group.key)"
                                         :data-type="group.items[0].type"
                                         :data-ns="group.items[0].ns"
                                         :data-logtype="group.items[0].logtype"
                                         :data-activity-type="group.items[0].socialContext ? group.items[0].socialContext.activityType : null"
                                         :data-content-type="group.items[0].socialContext ? group.items[0].socialContext.contentType : null">
                                         
                                        <div class="cwa-rc__favicon-wrap">
                                            <img :src="group.wikiFavicon" class="cwa-rc__favicon" :title="group.wikiName">
                                        </div>
                                        <div class="cwa-rc__main-info">
                                            <div class="cwa-rc__meta">
                                                <i :class="getIconForType(group.items[0])" class="cwa-rc__type-icon" :title="group.items[0].actionTitle || group.items[0].logaction || group.items[0].type"></i>
                                                <i class="fa-solid fa-chevron-right cwa-rc__toggle-icon" :class="{'cwa-rc__toggle-icon--expanded': expandedGroups[group.key]}"></i>
                                                <span v-if="group.items.some(i => i.unpatrolled)" class="cwa-rc__unpatrolled" title="Есть неотпатрулированные правки">!</span>
                                                <span class="cwa-rc__time">{{ group.items[0].time }}</span>
                                                <a :href="group.items[0].pageUrl" class="cwa-rc__page-title" target="_blank" @click.stop>{{ group.title }}</a>
                                                <span v-if="group.items[0].actionText" class="cwa-rc__action-text">({{ group.items[0].actionText }})</span>
                                                <span class="cwa-rc__group-count">{{ pluralize(group.items.length, ['изменение', 'изменения', 'изменений']) }}</span>
                                                <span v-if="group.items[0].type !== 'log' && group.items[0].type !== 'discussion'" class="cwa-rc__size" :class="getSizeClass(group.totalSizeDiff)">
                                                    ({{ group.totalSizeDiff > 0 ? '+' : '' }}{{ group.totalSizeDiff }})
                                                </span>
                                            </div>
                                            <div class="cwa-rc__details">
                                                <span class="cwa-rc__summary">Авторы: {{ Array.from(new Set(group.items.map(i => i.user))).join(', ') }}</span>
                                            </div>
                                        </div>
                                        <div class="cwa-rc__actions">
                                            <button v-if="canPatrol && group.items.some(i => i.unpatrolled)" class="cwa-rc__action-btn cwa-rc__action-btn--success" title="Отпатрулировать группу" @click.stop="doPatrolGroup(group)">
                                                <i class="fa-solid fa-check-double"></i>
                                            </button>
                                            <button v-if="group.items[0].pageid || group.items[0].type === 'discussion'" class="cwa-rc__action-btn" title="Предпросмотр" @click.stop="openPreviewModal(group.items[0])">
                                                <i class="fa-solid fa-eye"></i>
                                            </button>
                                            <button v-if="getGroupDiff(group)" class="cwa-rc__action-btn" title="Все изменения" @click.stop="openDiffModal(group.wikiDomain, getGroupDiff(group).from, getGroupDiff(group).to, group.title)">
                                                <i class="fa-solid fa-code-compare"></i>
                                            </button>
                                        </div>
                                    </div>
                                    
                                    <ul v-if="expandedGroups[group.key]" class="cwa-rc__sublist">
                                        <li v-for="subEdit in group.items" :key="subEdit.id" 
                                            class="cwa-rc__item cwa-rc__item--sub"
                                            :data-type="subEdit.type"
                                            :data-ns="subEdit.ns"
                                            :data-logtype="subEdit.logtype"
                                            :data-activity-type="subEdit.socialContext ? subEdit.socialContext.activityType : null"
                                            :data-content-type="subEdit.socialContext ? subEdit.socialContext.contentType : null">
                                            
                                            <div class="cwa-rc__main-info">
                                                <div class="cwa-rc__meta">
                                                    <i :class="getIconForType(subEdit)" class="cwa-rc__type-icon cwa-rc__sub-icon" :title="subEdit.actionTitle || subEdit.logaction || subEdit.type"></i>
                                                    <span v-if="subEdit.unpatrolled" class="cwa-rc__unpatrolled" title="Неотпатрулированная правка">!</span>
                                                    <span class="cwa-rc__time">{{ subEdit.time }}</span>
                                                    <span v-if="subEdit.type !== 'log' && subEdit.type !== 'discussion'" class="cwa-rc__size" :class="getSizeClass(subEdit.sizeDiff)">
                                                        ({{ subEdit.sizeDiff > 0 ? '+' : '' }}{{ subEdit.sizeDiff }})
                                                    </span>
                                                    <span v-if="subEdit.actionText" class="cwa-rc__action-text">({{ subEdit.actionText }})</span>
                                                    <span v-if="subEdit.flags && subEdit.flags.length" class="cwa-rc__flags">
                                                        ( <template v-for="(flag, index) in subEdit.flags" :key="index">
                                                            <abbr class="cwa-rc__flag-abbr" :title="flag.title">{{ flag.text }}</abbr><span v-if="index < subEdit.flags.length - 1"> | </span>
                                                        </template> )
                                                    </span>
                                                </div>
                                                <div class="cwa-rc__details">
                                                    <span class="cwa-rc__user-wrap">
                                                        <a :href="subEdit.userUrl" class="cwa-rc__user" target="_blank">{{ subEdit.user }}</a>
                                                        <span class="cwa-rc__user-actions">
                                                            <button class="cwa-rc__action-btn" title="Стена обсуждения" @click.stop="openInNewTab(subEdit.userTalkUrl)"><i class="fa-solid fa-comment-dots"></i></button>
                                                            <button class="cwa-rc__action-btn" title="Вклад" @click.stop="openInNewTab(subEdit.userContribsUrl)"><i class="fa-solid fa-list-ul"></i></button>
                                                            <button v-if="canBlock" class="cwa-rc__action-btn" title="Заблокировать" @click.stop="openInNewTab(subEdit.userBlockUrl)"><i class="fa-solid fa-user-slash"></i></button>
                                                        </span>
                                                    </span>
                                                    <span class="cwa-rc__summary" v-html="subEdit.parsedComment"></span>
                                                </div>
                                            </div>
                                            <div class="cwa-rc__actions">
                                                <button v-if="canPatrol && subEdit.unpatrolled" class="cwa-rc__action-btn cwa-rc__action-btn--success" title="Отпатрулировать" @click="doPatrol(subEdit)">
                                                    <i class="fa-solid fa-check"></i>
                                                </button>
                                                <button v-if="subEdit.old_revid" class="cwa-rc__action-btn" title="Показать изменения" @click="openDiffModal(subEdit.wikiDomain, subEdit.old_revid, subEdit.revid, subEdit.title)">
                                                    <i class="fa-solid fa-code-compare"></i>
                                                </button>
                                                <button v-if="subEdit.undoUrl" class="cwa-rc__action-btn cwa-rc__action-btn--warn" title="Отменить" @click.stop="openInNewTab(subEdit.undoUrl)">
                                                    <i class="fa-solid fa-rotate-left"></i>
                                                </button>
                                                <button v-if="canRollback && subEdit.type !== 'log' && subEdit.type !== 'discussion'" class="cwa-rc__action-btn cwa-rc__action-btn--danger" title="Быстрый откат" @click="doRollback(subEdit)">
                                                    <i class="fa-solid fa-clock-rotate-left"></i>
                                                </button>
                                            </div>
                                        </li>
                                    </ul>
                                </div>
                            </li>
                        </template>
                    </ul>
                </main>
                <!-- МОДАЛЬНОЕ ОКНО -->
                <div v-if="modal.isOpen" class="cwa-modal-overlay" @click.self="closeModal">
                    <div class="cwa-modal">
                        <header class="cwa-modal__header">
                            <h3>{{ modal.title }}</h3>
                            <button class="cwa-modal__close" @click="closeModal"><i class="fa-solid fa-xmark"></i></button>
                        </header>
                        <div class="cwa-modal__body">
                            <div v-if="modal.isLoading" class="cwa-modal__loader">
                                <i class="fa-solid fa-spinner fa-spin-pulse"></i> Загрузка...
                            </div>
                            <div v-else class="cwa-modal__content" id="mw-content-text">
                                <div class="mw-parser-output" v-html="modal.content"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
    `;
