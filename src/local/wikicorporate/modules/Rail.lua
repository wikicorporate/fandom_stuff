local p = {}

local CommunityRail = [==[
<h2 class="t-header"><i class="fa-solid fa-star"></i>Уголок сообщества</h2>
<div class="t-rail">
<div class="t-rail__item" data-title="Discord">[https://discord.gg/hhwiki <i class="fa-brands fa-discord"></i>]</div>
<div class="t-rail__item" data-title="ВКонтакте">[https://vk.com/hazbin_hotel <i class="fa-brands fa-vk"></i>]</div>
<div class="t-rail__item" data-title="Правила">[[{{ns:4}}:Правила|<i class="fa-solid fa-scale-balanced"></i>]]</div>
<div class="t-rail__item" data-title="Шаблоны">[[{{ns:4}}:Шаблоны|<i class="fa-solid fa-gears"></i>]]</div>
<div class="t-rail__item" data-title="Персонал">[[Шаблон:Персонал|<i class="fa-solid fa-user"></i>]]</div>
<div class="t-rail__item" data-title="Перевод">[[{{ns:4}}:Перевод|<i class="fa-solid fa-language"></i>]]</div>
<div class="t-rail__item" data-title="Статусы">[[{{ns:4}}:Кандидаты на должности|<i class="fa-solid fa-graduation-cap"></i>]]</div>
<div class="t-rail__item" data-title="Вопросы">[[{{ns:4}}:Вопросы и ответы|<i class="fa-solid fa-question"></i>]]</div>
<div class="t-rail__item" data-title="Доска почёта">[[{{ns:4}}:Доска почёта|<i class="fa-solid fa-medal"></i>]]</div>
</div>
]==]

local LinksRail = [==[
<h2 class="t-header"><i class="fa-solid fa-code"></i>Ссылки и статистика</h2>
<div class="t-rail">
<div class="t-rail__item" data-title="Личный CSS">[[Служебная:Моя страница/common.css|<i class="fa-brands fa-css3-alt"></i>]]</div>
<div class="t-rail__item" data-title="Глобальный CSS">[[w:Special:MyPage/global.css|<i class="fa-brands fa-css3"></i>]]</div>
<div class="t-rail__item" data-title="Личный JS">[[Служебная:Моя страница/common.js|<i class="fa-brands fa-square-js"></i>]]</div>
<div class="t-rail__item" data-title="Глобальный JS">[[w:Special:MyPage/global.js|<i class="fa-brands fa-node-js"></i>]]</div>
<div class="t-rail__item" data-title="Общий CSS">[[MediaWiki:Common.css|<i class="fa-solid fa-laptop-code"></i>]]</div>
<div class="t-rail__item" data-title="Мобильный CS">[[MediaWiki:FandomMobile.css|<i class="fa-solid fa-mobile-screen-button"></i>]]</div>
<div class="t-rail__item" data-title="Общий JS">[[MediaWiki:Common.js|<i class="fa-brands fa-react"></i>]]</div>
<div class="t-rail__item" data-title="ImportJS">[[MediaWiki:ImportJS|<i class="fa-brands fa-vuejs"></i>]]</div>
<div class="t-rail__item" data-title="Страницы JS">[[Служебная:JSPages|<i class="fa-solid fa-terminal"></i>]]</div>
<div class="t-rail__item" data-title="{{NUMBEROFEDITS}} {{PLURAL:{{NUMBEROFEDITS}}|правка|правки|правок}}">[[Служебная:Свежие правки|<i class="fa-solid fa-pen-to-square"></i>]]</div>
<div class="t-rail__item" data-title="{{NUMBEROFARTICLES}} {{PLURAL:{{NUMBEROFARTICLES}}|статья|статьи|статей}}">[[Служебная:NewPages|<i class="fa-solid fa-newspaper"></i>]]</div>
<div class="t-rail__item" data-title="{{NUMBEROFPAGES}} {{PLURAL:{{NUMBEROFPAGES}}|страница|страницы|страниц}}">[[Служебная:AllPages|<i class="fa-solid fa-file"></i>]]</div>
<div class="t-rail__item" data-title="{{NUMBEROFFILES}} {{PLURAL:{{NUMBEROFFILES}}|файл|файла|файлов}}">[[Служебная:NewFiles|<i class="fa-solid fa-image"></i>]]</div>
</div>
]==]

function p.main(frame)
	return frame:preprocess(LinksRail..CommunityRail)
end

return p
