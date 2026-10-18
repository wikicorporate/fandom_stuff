local p = {}

p.StylusCode = [=[

/* ==========================================================================
   FANDOM STYLUS FRAMEWORK
   Синтаксис Stylus: минимум лишних символов (отступы решают всё)
   ========================================================================== */

// Переменные объявляются просто через знак равно
bg-base = var(--theme-page-background-color)
text-main = var(--theme-page-text-color)
accent-color = var(--theme-accent-color)

// Миксин в Stylus (прозрачное примешивание)
// Даже не нужно писать "mixin", просто имя функции
flex-center()
  display flex
  justify-content center
  align-items center

// Кастомный скроллбар (проброс аргументов)
custom-scrollbar(thumb = accent-color, track = transparent)
  &::-webkit-scrollbar
    width 8px
    height 8px
  &::-webkit-scrollbar-track
    background track
  &::-webkit-scrollbar-thumb
    background thumb
    border-radius 4px

// --- Использование ---

.stylus-custom-widget
  background bg-base
  color text-main
  border 1px solid accent-color
  padding 20px
  border-radius 8px
  
  // Вложенность работает так же, как в Less/SCSS
  &__header
    flex-center()
    justify-content space-between
    border-bottom 2px solid accent-color
    padding-bottom 10px

    h2
      margin 0
      color accent-color

  &__content
    margin-top 15px
    max-height 200px
    overflow-y auto
    custom-scrollbar() // Вызов миксина

]=]

return p
