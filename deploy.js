const { mwn } = require('mwn');
const fs = require('fs');
const config = require('./config.json');

// Получаем пароли из секретов GitHub (передаются при запуске)
const username = process.env.FANDOM_USERNAME;
const password = process.env.FANDOM_PASSWORD;

async function deployToWiki(wikiUrl, fileConfig) {
    try {
        // Подключаемся к API конкретной Вики
        const bot = await mwn.init({
            apiUrl: `${wikiUrl}/api.php`,
            username: username,
            password: password,
            silent: true // Не спамить в консоль
        });

        // Читаем локальный файл
        const content = fs.readFileSync(fileConfig.localPath, 'utf8');

        // Отправляем код на Вики
        await bot.save(fileConfig.wikiPage, content, fileConfig.summary);
        console.log(`✅ [Успех] ${fileConfig.localPath} ➔ ${wikiUrl} (${fileConfig.wikiPage})`);
        
    } catch (error) {
        console.error(`❌ [Ошибка] Вики: ${wikiUrl} | Файл: ${fileConfig.localPath}`);
        console.error(error.message);
    }
}

// Запускаем цикл по всем Вики и всем файлам
async function run() {
    console.log('🚀 Начинаем деплой на Фэндом...');
    for (const wiki of config.wikis) {
        for (const file of config.files) {
            await deployToWiki(wiki, file);
        }
    }
    console.log('🎉 Деплой завершен!');
}

run();
