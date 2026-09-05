const CwaDicts = {
        logActMap: {
            'delete': 'Удаление', 'restore': 'Восстановление', 'protect': 'Закрытие', 'unprotect': 'Открытие'
        },
        logMap: {
            'delete/delete': 'Страница удалена', 'delete/restore': 'Страница восстановлена',
            'block/block': 'Участник заблокирован', 'block/unblock': 'Участник разблокирован',
            'protect/protect': 'Страница защищена', 'protect/unprotect': 'Защита снята',
            'upload/upload': 'Загружен новый файл', 'upload/overwrite': 'Перезаписан файл',
            'move/move': 'Страница переименована', 'move/move_redir': 'Переименована поверх перенаправления',
            'rights/rights': 'Изменены права участника', 'contentmodel/change': 'Изменена модель контента'
        },
        logNamesMap: {
            'move': 'Журнал переименований', 'rights': 'Журнал прав участника', 'delete': 'Журнал удалений',
            'block': 'Журнал блокировок', 'protect': 'Журнал защиты', 'upload': 'Журнал загрузок',
            'contentmodel': 'Журнал изменения модели', 'newusers': 'Журнал регистрации', 'patrol': 'Журнал патрулирования',
            'import': 'Журнал импорта', 'merge': 'Журнал объединений', 'create': 'Журнал создания страниц'
        },
        icons: {
            social: {
                'create': { 'comment': 'fa-solid fa-comment-dots', 'comment-reply': 'fa-solid fa-comments', 'message': 'fa-solid fa-envelope', 'message-reply': 'fa-solid fa-reply', 'post': 'fa-solid fa-message', 'post-reply': 'fa-solid fa-reply-all', 'blog': 'fa-solid fa-blog', 'blog-reply': 'fa-solid fa-comment-medical' },
                'update': { 'comment': 'fa-solid fa-pen-to-square', 'comment-reply': 'fa-solid fa-pen', 'message': 'fa-solid fa-envelope-open-text', 'message-reply': 'fa-solid fa-marker', 'post': 'fa-solid fa-pen-clip', 'post-reply': 'fa-solid fa-pencil', 'blog': 'fa-solid fa-pen-nib', 'blog-reply': 'fa-solid fa-pen-ruler' },
                'delete': { 'comment': 'fa-solid fa-trash-can', 'comment-reply': 'fa-solid fa-eraser', 'message': 'fa-solid fa-calendar-xmark', 'message-reply': 'fa-solid fa-minus-square', 'post': 'fa-solid fa-ban', 'post-reply': 'fa-solid fa-trash', 'blog': 'fa-solid fa-trash-can', 'blog-reply': 'fa-solid fa-eraser' },
                'undelete': { 'comment': 'fa-solid fa-trash-arrow-up', 'message': 'fa-solid fa-recycle', 'post': 'fa-solid fa-trash-can-arrow-up', 'blog': 'fa-solid fa-trash-arrow-up' },
                'lock': { 'comment': 'fa-solid fa-lock', 'message': 'fa-solid fa-user-lock', 'post': 'fa-solid fa-clock', 'blog': 'fa-solid fa-lock' },
                'unlock': { 'comment': 'fa-solid fa-lock-open', 'message': 'fa-solid fa-unlock', 'post': 'fa-solid fa-key', 'blog': 'fa-solid fa-lock-open' }
            },
            log: {
                'delete': 'fa-solid fa-trash', 'block': 'fa-solid fa-user-lock', 'protect': 'fa-solid fa-shield-halved', 'upload': 'fa-solid fa-upload', 'move': 'fa-solid fa-copy', 'rights': 'fa-solid fa-user-shield', 'contentmodel': 'fa-solid fa-file-code'
            },
            ns: {
                '-1': 'fa-solid fa-code', '8': 'fa-solid fa-code', '828': 'fa-solid fa-code', '10': 'fa-solid fa-gears', '14': 'fa-solid fa-tags', '6': 'fa-solid fa-image', '4': 'fa-solid fa-flag', '2': 'fa-solid fa-user', '500': 'fa-solid fa-message', '502': 'fa-solid fa-message', '400': 'fa-solid fa-video', '1100': 'fa-solid fa-video', '420': 'fa-solid fa-map-location-dot'
            }
        }
    };
