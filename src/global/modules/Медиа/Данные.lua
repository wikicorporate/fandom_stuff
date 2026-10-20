local data = {
    -- === ВИДЕО И СТРИМИНГ ===
    ['YOUTUBE'] = {
        [2] = { pattern = "[https://www.youtube.com/watch?v=$1 $2]" },
        [3] = { pattern = "[https://www.youtube.com/watch?v=$1&t=$2 $3]" }
    },
    ['YOUTUBE-SHORTS'] = {
        [2] = { pattern = "[https://www.youtube.com/shorts/$1 $2]" }
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
    ['TWITCH'] = {
        [2] = { pattern = "[https://www.twitch.tv/$1 $2]" }
    },
    ['TWITCH-VIDEO'] = {
        [2] = { pattern = "[https://www.twitch.tv/videos/$1 $2]" }
    },
    ['VIMEO'] = {
        [2] = { pattern = "[https://vimeo.com/$1 $2]" }
    },
    ['PRIME-VIDEO'] = {
        [2] = { pattern = "[https://www.primevideo.com/detail/$1 $2]" }
    },

    -- === МУЗЫКА И ТЕКСТЫ ПЕСЕН ===
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
    ['SOUNDCLOUD'] = {
        [2] = { pattern = "[https://soundcloud.com/$url1 $2]" }
    },
    ['BANDCAMP'] = {
        [2] = { pattern = "[https://$1.bandcamp.com $2]" },
        [3] = { pattern = "[https://$1.bandcamp.com/$2 $3]" }
    },
    ['DEEZER'] = {
        [2] = { pattern = "[https://www.deezer.com/$1 $2]" }
    },
    ['YANDEX-MUSIC'] = {
        [2] = { pattern = "[https://music.yandex.ru/$1 $2]" }
    },
    ['GENIUS'] = {
        [2] = { pattern = "[https://genius.com/$1 $2]" }
    },

    -- === СОЦСЕТИ, МЕССЕНДЖЕРЫ И ВИЗИТКИ ===
    ['TWITTER'] = {
        [2] = { pattern = "[https://x.com/$1 $2]" }
    },
    ['BLUESKY'] = {
        [2] = { pattern = "[https://bsky.app/profile/$1 $2]" }
    },
    ['THREADS'] = {
        [2] = { pattern = "[https://www.threads.net/$1 $2]" }
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
    ['VK'] = {
        [2] = { pattern = "[https://vk.com/$1 $2]" }
    },
    ['DISCORD'] = {
        [2] = { pattern = "[https://discord.gg/$1 $2]" }
    },
    ['TIKTOK'] = {
        [2] = { pattern = "[https://www.tiktok.com/$1 $2]" }
    },
    ['TUMBLR'] = {
        [2] = { pattern = "[https://$1.tumblr.com $2]" },
        [3] = { pattern = "[https://$1.tumblr.com/post/$2 $3]" }
    },
    ['REDDIT'] = {
        [2] = { pattern = "[https://www.reddit.com/$1 $2]" }
    },
    ['LINKTREE'] = {
        [2] = { pattern = "[https://linktr.ee/$1 $2]" }
    },
    ['CARRD'] = {
        [2] = { pattern = "[https://$1.carrd.co $2]" }
    },

    -- === АРТ, КРАУДФАНДИНГ И МЕРЧ ===
    ['ARTSTATION'] = {
        [2] = { pattern = "[https://www.artstation.com/$1 $2]" }
    },
    ['DEVIANTART'] = {
        [2] = { pattern = "[https://www.deviantart.com/$url1 $2]" }
    },
    ['NEWGROUNDS'] = {
        [2] = { pattern = "[https://www.newgrounds.com/$1 $2]" },
        [3] = { pattern = "[https://$1.newgrounds.com/$2 $3]" }
    },
    ['PIXIV'] = {
        [2] = { pattern = "[https://www.pixiv.net/$1 $2]" }
    },
    ['PINTEREST'] = {
        [2] = { pattern = "[https://www.pinterest.com/$1 $2]" }
    },
    ['IMGUR'] = {
        [2] = { pattern = "[https://imgur.com/$1 $2]" }
    },
    ['PATREON'] = {
        [2] = { pattern = "[https://www.patreon.com/$1 $2]" }
    },
    ['KO-FI'] = {
        [2] = { pattern = "[https://ko-fi.com/$1 $2]" }
    },
    ['BOOSTY'] = {
        [2] = { pattern = "[https://boosty.to/$1 $2]" }
    },
    ['KICKSTARTER'] = {
        [2] = { pattern = "[https://www.kickstarter.com/projects/$1 $2]" }
    },
    ['SHARKROBOT'] = {
        [2] = { pattern = "[https://sharkrobot.com/$1 $2]" }
    },
    ['A24-SHOP'] = {
        [2] = { pattern = "[https://shop.a24films.com/$1 $2]" }
    },

    -- === КИНОБАЗЫ И АГРЕГАТОРЫ ===
    ['IMDB'] = {
        [2] = { pattern = "[https://www.imdb.com/name/$1 $2]" }
    },
    ['IMDB-TITLE'] = {
        [2] = { pattern = "[https://www.imdb.com/title/$1 $2]" }
    },
    ['ROTTEN-TOMATOES'] = {
        [2] = { pattern = "[https://www.rottentomatoes.com/$1 $2]" }
    },
    ['METACRITIC'] = {
        [2] = { pattern = "[https://www.metacritic.com/$1 $2]" }
    },

    -- === ИГРОВЫЕ ПЛАТФОРМЫ И МАГАЗИНЫ ===
    ['STEAM-STORE'] = {
        [1] = { pattern = "[https://store.steampowered.com/$1 $1]" },
        [2] = { pattern = "[https://store.steampowered.com/$1 $2]" }
    },
    ['STEAM-COMMUNITY'] = {
        [1] = { pattern = "[https://steamcommunity.com/$1 $1]" },
        [2] = { pattern = "[https://steamcommunity.com/$1 $2]" }
    },
    ['STEAMDB'] = {
        [2] = { pattern = "[https://steamdb.info/$1 $2]" }
    },
    ['ITCH-IO'] = {
        [2] = { pattern = "[https://$1.itch.io $2]" },
        [3] = { pattern = "[https://$1.itch.io/$2 $3]" }
    },
    ['PLAYSTATION'] = {
        [2] = { pattern = "[https://store.playstation.com/$1 $2]" }
    },
    ['EPIC-GAMES'] = {
        [2] = { pattern = "[https://store.epicgames.com/$1 $2]" }
    },
    ['GOG'] = {
        [2] = { pattern = "[https://www.gog.com/$1 $2]" }
    },
    ['NINTENDO'] = {
        [2] = { pattern = "[https://www.nintendo.com/$1 $2]" }
    },
    ['XBOX'] = {
        [2] = { pattern = "[https://www.xbox.com/$1 $2]" }
    },

    -- === ДОКУМЕНТЫ, КОД И ПОИСК ===
    ['G-DOCS'] = {
        [2] = { pattern = "[https://docs.google.com/document/d/$1 $2]" }
    },
    ['G-TABLES'] = {
        [2] = { pattern = "[https://docs.google.com/spreadsheets/u/0/d/$1 $2]" }
    },
    ['G-DRIVE'] = {
        [2] = { pattern = "[https://drive.google.com/$1 $2]" }
    },
    ['GITHUB'] = {
        [2] = { pattern = "[https://github.com/$1 $2]" }
    },
    ['GOOGLE'] = {
        [1] = { pattern = "[https://www.google.com/search?q=$url1 $1]" },
        [2] = { pattern = "[https://www.google.com/search?q=$url1 $2]" }
    },

    -- === АРХИВЫ ===
    ['WEB-ARCHIVE'] = {
        [2] = { pattern = "[https://web.archive.org/web/$1 $2] (архивировано)" }
    },
    ['WEB-ARCHIVE-VIDEO'] = {
        [2] = { pattern = "[https://web.archive.org/web/https://www.youtube.com/watch?v=$1 $2] (архивировано)" },
        [3] = { pattern = "[https://web.archive.org/web/$1/https://www.youtube.com/watch?v=$2 $3] (архивировано)" }
    },
    ['ARCHIVE-TODAY'] = {
        [2] = { pattern = "[https://archive.ph/$1 $2] (архивировано)" }
    },

    -- === МЕЖВИКИ И ЭНЦИКЛОПЕДИИ ===
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
    }
}

return data
