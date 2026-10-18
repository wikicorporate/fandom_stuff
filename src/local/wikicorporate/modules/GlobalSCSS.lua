local p = {}

p.ScssCode = [=[

/* ==========================================================================
   FANDOM SCSS FRAMEWORK
   Мощный препроцессор со строгим и понятным синтаксисом
   ========================================================================== */

// --- 1. ПЕРЕМЕННЫЕ ---
$bg-base:        var(--theme-page-background-color);
$text-main:      var(--theme-page-text-color);
$accent-color:   var(--theme-accent-color);
$border-color:   var(--theme-border-color);

// --- 2. МИКСИНЫ ---

// Флекс-центрирование
@mixin flex-center {
    display: flex;
    justify-content: center;
    align-items: center;
}

// Кастомный скроллбар WDS
@mixin custom-scrollbar($thumb: $accent-color, $track: transparent) {
    &::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    &::-webkit-scrollbar-track {
        background: $track;
    }
    &::-webkit-scrollbar-thumb {
        background: $thumb;
        border-radius: 4px;
        
        &:hover {
            // Встроенная функция darken (затемнение цвета)
            background: darken(#00b073, 10%); 
        }
    }
}

// Умная обрезка текста (Line clamp)
@mixin line-clamp($lines: 3) {
    display: -webkit-box;
    -webkit-line-clamp: $lines;
    -webkit-box-orient: vertical;  
    overflow: hidden;
}

// --- 3. ИСПОЛЬЗОВАНИЕ (БЭМ) ---

.scss-custom-widget {
    background-color: $bg-base;
    color: $text-main;
    border: 1px solid $border-color;
    border-radius: 8px;
    padding: 1rem;
    
    // Вложенность элементов
    &__header {
        @include flex-center;
        justify-content: space-between;
        border-bottom: 2px solid $accent-color;
        padding-bottom: 10px;

        h2 {
            margin: 0;
            color: $accent-color;
        }
    }

    &__content {
        margin-top: 15px;
        max-height: 250px;
        overflow-y: auto;
        
        // Применяем миксин скроллбара
        @include custom-scrollbar();
    }

    &__desc {
        // Ограничиваем текст двумя строками
        @include line-clamp(2);
        color: rgba(#fff, 0.7); // Использование альфа-канала с HEX
    }
}

]=]

return p
