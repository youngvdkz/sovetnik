# 🚀 Деплой на Render.com

## 📋 **Подготовка (уже готово!)**

✅ Все файлы подготовлены:
- `render.yaml` - конфигурация для Render
- `app.py` - Flask wrapper для health checks
- `requirements.txt` - обновлен с Flask
- Ваш бот готов к деплою!

## 🎯 **Пошаговая инструкция:**

### Шаг 1: Загрузка на GitHub
```bash
# Если еще не загружено в GitHub:
git add .
git commit -m "Add Render.com deployment config"
git push origin main
```

### Шаг 2: Регистрация на Render
1. Идите на https://render.com
2. Нажмите "Get Started" 
3. Авторизуйтесь через GitHub

### Шаг 3: Создание сервиса
1. В dashboard нажмите "New +"
2. Выберите "Web Service"
3. Подключите ваш GitHub репозиторий
4. Render автоматически найдет `render.yaml`

### Шаг 4: Настройка переменных
В разделе Environment добавьте:
```
TELEGRAM_BOT_TOKEN = ваш_токен_бота
GEMINI_API_KEY = ваш_ключ_gemini
```

### Шаг 5: Деплой
1. Нажмите "Deploy Web Service"
2. Ждите 3-5 минут сборки
3. Ваш бот будет доступен по ссылке вида: `https://telegram-bot-adviser-xxx.onrender.com`

## 🎉 **Готово!**

### ✅ **Проверка работы:**
- Откройте ссылку вашего сервиса - увидите статус
- Напишите боту в Telegram - должен ответить
- При первом обращении может быть задержка 20-30 сек

### 📊 **Мониторинг:**
- Logs: в dashboard Render → ваш сервис → Logs
- Статус: откройте ссылку сервиса в браузере
- Детальный статус: добавьте `/status` к ссылке

### 🔄 **Автообновления:**
При каждом `git push` в GitHub - автоматический редеплой!

## 💡 **Полезные ссылки:**
- Ваш сервис: будет показан после деплоя
- Render Dashboard: https://dashboard.render.com
- Документация: https://render.com/docs

---
**Примечание:** Первый ответ бота после "сна" может занять 20-30 секунд - это нормально для бесплатного плана! 