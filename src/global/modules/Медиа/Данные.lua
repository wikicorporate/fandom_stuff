local data = {
    ['YOUTUBE'] = {
        [2] = { pattern = "[https://www.youtube.com/watch?v=$1 $2]" },
        [3] = { pattern = "[https://www.youtube.com/watch?v=$1&t=$2 $3]" }
    },
    ['YOUTUBE-CHANNEL'] = {
        [2] = { pattern = "[https://www.youtube.com/channel/$1 $2]" }
    },
    ['YOUTUBE-HANDLE'] = {
        [2] = { pattern = "[https://www.youtube.com/$1 $2]" }
    },
    ['YOUTUBE-PLAYLIST'] = {
        [2] = { pattern = "[https://www.youtube.com/playlist?list=$1 $2]" }
    },
    ['YT-MUSIC'] = {
        [2] = { pattern = "[https://music.youtube.com/watch?v=$1 $2]" }
    },
    ['APPLE-MUSIC'] = {
        [1] = { pattern = "[https://music.apple.com/search/$url1 $1 (поиск)]" },
        [2] = { pattern = "[https://music.apple.com/$1 $2]" },
        [3] = { pattern = "[https://music.apple.com/$1?i=$2 $3]" }
    },
    ['SPOTIFY'] = {
        [1] = { pattern = "[https://open.spotify.com/search/$url1 $1 (поиск)]" },
        [2] = { pattern = "[https://open.spotify.com/$1 $2]" }
    },
    ['TWITTER'] = {
        [2] = { pattern = "[https://x.com/$1 $2]" }
    },
    ['FACEBOOK'] = {
        [2] = { pattern = "[https://facebook.com/$1 $2]" }
    },
    ['INSTAGRAM'] = {
        [2] = { pattern = "[https://instagram.com/$1 $2]" }
    },
    ['TELEGRAM'] = {
        [2] = { pattern = "[https://t.me/$1 $2]" }
    },
    ['TIKTOK'] = {
        [2] = { pattern = "[https://www.tiktok.com/$1 $2]" }
    },
    ['TUMBLR'] = {
        [2] = { pattern = "[https://$1.tumblr.com $2]" },
        [3] = { pattern = "[https://$1.tumblr.com/post/$2 $3]" }
    },
    ['DEVIANTART'] = {
        [2] = { pattern = "[https://www.deviantart.com/$url1 $2]" }
    },
    ['PATREON'] = {
        [2] = { pattern = "[https://www.patreon.com/$1 $2]" }
    },
    ['SOUNDCLOUD'] = {
        [2] = { pattern = "[https://soundcloud.com/$url1 $2]" }
    },
    ['REDDIT'] = {
        [2] = { pattern = "[https://www.reddit.com/$1 $2]" }
    },
    ['IMDB'] = {
        [2] = { pattern = "[https://www.imdb.com/name/$1 $2]" }
    },
    ['IMGUR'] = {
        [2] = { pattern = "[https://imgur.com/$1 $2]" }
    },
    ['BLUESKY'] = {
        [2] = { pattern = "[https://bsky.app/profile/$1 $2]" }
    },
    ['G-DOCS'] = {
        [2] = { pattern = "[https://docs.google.com/document/d/$1 $2]" }
    },
    ['G-TABLES'] = {
        [2] = { pattern = "[https://docs.google.com/spreadsheets/u/0/d/$1 $2]" }
    },
    ['STEAM-STORE'] = {
        [1] = { pattern = "[https://store.steampowered.com/$1 $1]" },
        [2] = { pattern = "[https://store.steampowered.com/$1 $2]" }
    },
    ['STEAM-COMMUNITY'] = {
        [1] = { pattern = "[https://steamcommunity.com/$1 $1]" },
        [2] = { pattern = "[https://steamcommunity.com/$1 $2]" }
    },
    ['GOOGLE'] = {
        [1] = { pattern = "[https://www.google.com/search?q=$url1 $1]" },
        [2] = { pattern = "[https://www.google.com/search?q=$url1 $2]" }
    },
    ['WEB-ARCHIVE'] = {
        [2] = { pattern = "[https://web.archive.org/web/$1 $2] (архивировано)" }
    },
    ['WEB-ARCHIVE-VIDEO'] = {
        [2] = { pattern = "[https://web.archive.org/web/https://www.youtube.com/watch?v=$1 $2] (архивировано)" }
    },
    ['FANDOM'] = {
        [3] = { pattern = "[https://$1.fandom.com/$2/wiki/$3 $3]" },
        [4] = { pattern = "[https://$1.fandom.com/$2/wiki/$3 $4]" }
    },
    ['WIKI'] = {
        [2] = { pattern = "[[Wikipedia:$1:$2|$2]]" },
        [3] = { pattern = "[[Wikipedia:$1:$2|$3]]" }
    },
    ['WIKTIONARY'] = {
        [2] = { pattern = "[[Wiktionary:$1:$2|$2]]" },
        [3] = { pattern = "[[Wiktionary:$1:$2|$3]]" }
    },
    
    -- Блок обратной совместимости
    ['V'] = 'YOUTUBE', ['P'] = 'YOUTUBE-PLAYLIST', 
    ['C'] = 'YOUTUBE-CHANNEL',
    ['T'] = 'TWITTER', ['F'] = 'FACEBOOK', ['I'] = 'INSTAGRAM', 
    ['S'] = 'SPOTIFY', ['AM'] = 'APPLE-MUSIC', ['APPLEMUSIC'] = 'APPLE-MUSIC', 
    ['W'] = 'WEB-ARCHIVE', ['WV'] = 'WEB-ARCHIVE-VIDEO', 
    ['GD'] = 'G-DOCS', ['GOOGLEDOCS'] = 'G-DOCS', 
    ['GDT'] = 'G-TABLES', ['GOOGLEDOCSTABLE'] = 'G-TABLES', 
    ['PTRN'] = 'PATREON', ['IB'] = 'IMDB', 
    ['TR'] = 'TUMBLR', ['TUMBLER'] = 'TUMBLR', 
    ['TT'] = 'TIKTOK', ['TIKTOK'] = 'TIKTOK', 
    ['YM'] = 'YT-MUSIC', ['BS'] = 'BLUESKY', 
    ['DART'] = 'DEVIANTART', ['SCLOUD'] = 'SOUNDCLOUD', 
    ['TG'] = 'TELEGRAM', ['STEAMCOM'] = 'STEAM-COMMUNITY', 
    ['STEAMSTORE'] = 'STEAM-STORE'
}

return data
