local p = {}

p.ScssCode = [=[
/* ==========================================================================
   FANDOM SCSS FRAMEWORK
   Глобальные переменные, миксины и базовые компоненты
   ========================================================================== */

// --- 1. ТОКЕНЫ ТЕМЫ FANDOM DESKTOP ---
$bg-base:          var(--theme-page-background-color);
$bg-secondary:     var(--theme-page-background-color--secondary);
$text-main:        var(--theme-page-text-color);
$text-secondary:   var(--theme-page-text-color--secondary);
$link-color:       var(--theme-link-color);
$accent-color:     var(--theme-accent-color);
$border-color:     var(--theme-border-color);

$surface-glass:    color-mix(in srgb, var(--theme-page-background-color--secondary) 80%, transparent);
$accent-hover:     color-mix(in srgb, var(--theme-accent-color) 85%, #000);
$accent-subtle:    color-mix(in srgb, var(--theme-accent-color) 15%, transparent);

$radius-sm:        4px;
$radius-md:        8px;
$radius-lg:        12px;
$shadow-sm:        0 2px 4px rgba(0, 0, 0, 0.15);
$shadow-md:        0 4px 12px rgba(0, 0, 0, 0.25);
$transition-base:  0.25s cubic-bezier(0.4, 0, 0.2, 1);

// --- 2. МИКСИНЫ АДАПТИВНОСТИ ---
@mixin respond-to($breakpoint) {
    @if $breakpoint == mobile {
        @media screen and (max-width: 767px) { @content; }
    } @else if $breakpoint == tablet {
        @media screen and (max-width: 1023px) { @content; }
    } @else if $breakpoint == desktop {
        @media screen and (min-width: 1024px) { @content; }
    } @else if $breakpoint == wide {
        @media screen and (min-width: 1440px) { @content; }
    }
}

// --- 3. МИКСИНЫ РАСКЛАДКИ И ТИПОГРАФИКИ ---
@mixin flex-center {
    display: flex;
    justify-content: center;
    align-items: center;
}

@mixin flex-between {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

@mixin absolute-fill {
    position: absolute;
    inset: 0;
}

@mixin auto-grid($min-width: 200px, $gap: 16px) {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax($min-width, 1fr));
    gap: $gap;
}

@mixin text-truncate {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

@mixin line-clamp($lines: 3) {
    display: -webkit-box;
    -webkit-line-clamp: $lines;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

// --- 4. МИКСИНЫ ОФОРМЛЕНИЯ ---
@mixin custom-scrollbar($thumb: $accent-color, $track: transparent, $size: 8px) {
    scrollbar-width: thin;
    scrollbar-color: $thumb $track;

    &::-webkit-scrollbar {
        width: $size;
        height: $size;
    }
    &::-webkit-scrollbar-track {
        background: $track;
    }
    &::-webkit-scrollbar-thumb {
        background: $thumb;
        border-radius: 4px;

        &:hover {
            background: $accent-hover;
        }
    }
}

@mixin glass-panel($blur: 10px) {
    background: $surface-glass;
    backdrop-filter: blur($blur);
    -webkit-backdrop-filter: blur($blur);
    border: 1px solid $border-color;
}

@mixin wiki-card($padding: 1rem, $radius: $radius-md) {
    background-color: $bg-secondary;
    color: $text-main;
    border: 1px solid $border-color;
    border-radius: $radius;
    padding: $padding;
    box-shadow: $shadow-sm;
    transition: transform $transition-base, box-shadow $transition-base, border-color $transition-base;

    &:hover {
        border-color: $accent-color;
        box-shadow: $shadow-md;
    }
}

// --- 5. БАЗОВЫЕ БЭМ-КОМПОНЕНТЫ ---
.scss-custom-widget {
    @include wiki-card(1rem, $radius-md);

    &__header {
        @include flex-between;
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
        @include custom-scrollbar();
    }

    &__desc {
        @include line-clamp(2);
        color: $text-secondary;
    }
}
]=]

return p
