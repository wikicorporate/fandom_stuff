local p = {}

p.LessCode = [=[

// ---
   FANDOM LESS FRAMEWORK (v4.x)
   Глобальные переменные и миксины для удобной разработки
    ---

// --- 1. ПЕРЕМЕННЫЕ (Связка с нативными токенами Fandom) ---
@bg-base:        var(--theme-page-background-color);
@bg-secondary:   var(--theme-page-background-color--secondary);
@text-main:      var(--theme-page-text-color);
@text-secondary: var(--theme-page-text-color--secondary);
@link-color:     var(--theme-link-color);
@accent-color:   var(--theme-accent-color);
@border-color:   var(--theme-border-color);
@shadow-base:    0 2px 4px rgba(0, 0, 0, 0.15);

// --- 2. БРЕЙКПОИНТЫ (Медиазапросы) ---
@mobile:  ~"screen and (max-width: 768px)";
@tablet:  ~"screen and (max-width: 1024px)";
@desktop: ~"screen and (min-width: 1025px)";

// --- 3. БАЗОВЫЕ МИКСИНЫ ---

// Идеальное центрирование (Flex)
.flex-center() {
    display: flex;
    justify-content: center;
    align-items: center;
}

// Абсолютное позиционирование на весь контейнер
.absolute-fill() {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
}

// Быстрое обрезание длинного текста троеточием
.text-truncate() {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

// Ограничение текста по количеству строк (Line clamp)
.line-clamp(@lines: 3) {
    display: -webkit-box;
    -webkit-line-clamp: @lines;
    -webkit-box-orient: vertical;  
    overflow: hidden;
}

// Скрытие элемента только визуально (остается для скринридеров)
.visually-hidden() {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
}

// --- 4. МИКСИНЫ ОФОРМЛЕНИЯ ---

// Красивый скроллбар WDS-стайла
.custom-scrollbar(@thumb: @accent-color, @track: rgba(0,0,0,0.1), @size: 8px) {
    &::-webkit-scrollbar {
        width: @size;
        height: @size;
    }
    &::-webkit-scrollbar-track {
        background: @track;
        border-radius: (@size / 2);
    }
    &::-webkit-scrollbar-thumb {
        background: @thumb;
        border-radius: (@size / 2);
        
        &:hover {
            background: darken(@thumb, 10%);
        }
    }
}

// Кнопки в стиле WDS
.wds-button-custom(@bg-color: @accent-color, @text-color: #fff) {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background-color: @bg-color;
    color: @text-color;
    border: none;
    border-radius: 3px;
    font-size: 12px;
    font-weight: 600;
    line-height: 1;
    padding: 7px 18px;
    text-transform: uppercase;
    cursor: pointer;
    transition: background-color 0.3s ease;

    &:hover {
        background-color: darken(@bg-color, 12%);
        text-decoration: none;
    }

    &:active {
        background-color: darken(@bg-color, 20%);
    }
}

// --- 5. МИКСИНЫ КАК ФУНКЦИИ (Продвинутый Less) ---

// Перевод пикселей в rem (База браузера обычно 16px)
.px-to-rem(@px) {
    @rem: (@px / 16);
    return: ~"@{rem}rem";
}

// Генерация сетки (Grid) с автозаполнением
.auto-grid(@min-width: 200px, @gap: 15px) {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(@min-width, 1fr));
    gap: @gap;
}

]=]

-- Возвращаем таблицу для возможного использования другими модулями
return p
