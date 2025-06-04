# 🌐 Как запустить бота 24/7 на сервере

Простое руководство для размещения вашего персонального бота в интернете.

## 💰 **Варианты по цене (от дешевого к дорогому)**

### 🆓 **Бесплатные варианты (с ограничениями)**

#### ⭐ **Render.com - РЕКОМЕНДУЮ для редкого использования**
```
✅ Плюсы:
- Полностью бесплатный план
- Простая настройка через GitHub
- Автоматические обновления
- Работает 24/7

❌ Минусы:
- "Засыпает" через 15 минут без активности
- Первый ответ после сна: 20-30 секунд
```

**🚀 Пошаговая инструкция Render.com:**

**Шаг 1: Подготовка GitHub репозитория**
```bash
# Убедитесь что все файлы в репозитории:
# ✅ main.py (точка входа)
# ✅ requirements.txt (зависимости)
# ✅ render.yaml (конфигурация Render)
# ✅ runtime.txt (версия Python)

git add .
git commit -m "Готов к деплою на Render"
git push
```

**Шаг 2: Создание приложения на Render**
```
1. Идете на render.com
2. Sign Up через GitHub
3. New → Web Service
4. Connect Repository → выбираете ваш репозиторий
5. Name: telegram-bot-adviser
6. Environment: Python
7. Build Command: pip install -r requirements.txt
8. Start Command: python main.py
```

**Шаг 3: Настройка переменных окружения**
```
В разделе Environment Variables добавляете:

TELEGRAM_BOT_TOKEN = ваш_токен_бота
GEMINI_API_KEY = ваш_ключ_gemini

Остальные переменные уже настроены в render.yaml
```

**Шаг 4: Деплой**
```
1. Create Web Service
2. Ждете 3-5 минут (первая сборка)
3. Смотрите логи - должно быть "🔥 Запускаю бота-советника..."
4. Готово! Бот работает 24/7
```

**🔧 Как работает "засыпание":**
```
⏰ Через 15 минут без сообщений → сервер засыпает
📱 Ваше сообщение → сервер просыпается (20-30 сек)
⚡ Дальше работает мгновенно до следующего сна
```

#### 1. **GitHub Codespaces** - РЕКОМЕНДУЮ для начала
```
✅ Плюсы:
- Бесплатно 60 часов/месяц
- Готовая среда разработки
- Docker уже установлен
- Простой запуск

❌ Минусы:
- Ограничение по времени
- Может "засыпать"
```

#### 2. **Railway.app**
```
✅ Плюсы:
- $5 бесплатных кредитов
- Простой деплой из GitHub
- Автоматические обновления

❌ Минусы:
- Ограничение по трафику
```

#### 3. **Render.com**
```
✅ Плюсы:
- Бесплатный план
- Простой интерфейс

❌ Минусы:
- "Засыпает" без активности
- Медленный запуск
```

### 💳 **Платные VPS (рекомендуемое решение)**

#### 1. **DigitalOcean Droplets** - МОЙ ВЫБОР
```
💰 Цена: $4-6/месяц
🖥️ Характеристики: 1GB RAM, 1 CPU, 25GB SSD
🌍 Дата-центры: по всему миру
📖 Документация: отличная
```

#### 2. **Vultr**
```
💰 Цена: $2.50-5/месяц  
🖥️ Характеристики: 512MB-1GB RAM
🌍 Локации: много вариантов
⚡ Особенность: очень дешево
```

#### 3. **Hetzner**
```
💰 Цена: €3.79/месяц (~$4)
🖥️ Характеристики: 1GB RAM, 20GB SSD
🌍 Локация: Германия/Финляндия
💪 Особенность: отличное соотношение цена/качество
```

#### 4. **Linode (Akamai)**
```
💰 Цена: $5/месяц
🖥️ Характеристики: 1GB RAM, 1 CPU, 25GB SSD
🏢 Особенность: корпоративный уровень
```

---

## 🚀 **Пошаговая инструкция развертывания**

### 📋 **Что нужно подготовить:**
1. Файл `.env` с токенами
2. Ваш код на GitHub
3. 30 минут времени

### 🎯 **Вариант 1: DigitalOcean (рекомендую)**

#### Шаг 1: Создание сервера
```bash
1. Регистрируемся на digitalocean.com
2. Create Droplet → Ubuntu 22.04 → Basic Plan → $4/month
3. Добавляем SSH ключ (или используем пароль)
4. Create Droplet
```

#### Шаг 2: Подключение к серверу
```bash
# Подключение через SSH (замените IP на ваш)
ssh root@your-server-ip

# Первое подключение - обновляем систему
apt update && apt upgrade -y
```

#### Шаг 3: Установка Docker
```bash
# Установка Docker одной командой
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Установка docker-compose
apt install docker-compose -y

# Проверка
docker --version
docker-compose --version
```

#### Шаг 4: Загрузка вашего бота
```bash
# Клонирование репозитория
git clone https://github.com/your-username/your-bot-repo.git
cd your-bot-repo

# Создание папки для данных
mkdir -p data

# Создание .env файла
nano .env
```

#### Шаг 5: Настройка .env
```env
# Вставьте ваши настройки:
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_key_here
GEMINI_MODEL=gemini-2.5-flash-preview-05-20
```

#### Шаг 6: Запуск бота
```bash
# Запуск простой версии
docker-compose -f docker-compose.simple.yml up -d

# Проверка что работает
docker ps
docker logs my_telegram_bot
```

### 🎯 **Вариант 2: GitHub Codespaces (бесплатно)**

#### Шаг 1: Открытие Codespace
```
1. Идете в ваш GitHub репозиторий
2. Code → Codespaces → Create codespace
3. Ждете 1-2 минуты загрузки
```

#### Шаг 2: Настройка и запуск
```bash
# В терминале Codespace:
cp config.env.example .env
nano .env  # вставляете ваши токены

# Запуск
docker-compose -f docker-compose.simple.yml up
```

---

## 🔧 **Полезные команды для управления**

### 📊 **Мониторинг бота**
```bash
# Посмотреть логи
docker logs my_telegram_bot -f

# Посмотреть статус
docker ps

# Перезапуск
docker-compose -f docker-compose.simple.yml restart

# Остановка
docker-compose -f docker-compose.simple.yml down
```

### 🔄 **Обновление бота**
```bash
# Скачать обновления
git pull

# Пересобрать и запустить
docker-compose -f docker-compose.simple.yml up --build -d
```

### 💾 **Бэкапы**
```bash
# Бэкап данных
tar -czf bot-backup-$(date +%Y%m%d).tar.gz data/

# Восстановление
tar -xzf bot-backup-20241204.tar.gz
```

---

## 🛡️ **Безопасность и настройки**

### 🔒 **Базовая безопасность VPS**
```bash
# Создание пользователя (не root)
adduser botuser
usermod -aG sudo botuser
usermod -aG docker botuser

# Настройка брандмауэра
ufw allow ssh
ufw allow 22
ufw enable

# Отключение входа root по SSH (опционально)
nano /etc/ssh/sshd_config
# PermitRootLogin no
systemctl restart ssh
```

### 📧 **Автоматическое обновление системы**
```bash
# Установка автообновлений
apt install unattended-upgrades -y
dpkg-reconfigure -plow unattended-upgrades
```

---

## 💰 **Реальные затраты**

### 🆓 **Бесплатные варианты**
- GitHub Codespaces: 60 часов/месяц бесплатно
- Railway: $5 кредитов
- Render: ограниченный бесплатный план

### 💳 **VPS серверы (в месяц)**
- Vultr: от $2.50
- DigitalOcean: от $4
- Hetzner: от €3.79 (~$4)
- Linode: от $5

### 📊 **Дополнительные расходы**
- Домен (опционально): $8-12/год
- Резервное копирование: $1-2/месяц
- Мониторинг (опционально): бесплатно

---

## 🎯 **Мои рекомендации**

### 🥇 **Для начинающих:**
1. **GitHub Codespaces** - попробовать бесплатно
2. Если понравится → **DigitalOcean** $4/месяц

### 🥈 **Для экономных:**
1. **Vultr** $2.50/месяц - самый дешевый
2. **Hetzner** €3.79/месяц - лучшее качество за деньги

### 🥉 **Для ленивых:**
1. **Railway** или **Render** - деплой одной кнопкой
2. Ничего настраивать не нужно

---

## 🚨 **Важные моменты**

### ✅ **Что нужно помнить:**
- Регулярно делайте бэкапы папки `data/`
- Следите за обновлениями системы
- Проверяйте логи раз в неделю
- Настройте уведомления о проблемах

### ⚠️ **Частые проблемы:**
- Забыли создать папку `data/` → ошибка SQLite
- Неправильные токены в `.env` → бот не запускается
- Закончилось место на диске → бот падает
- Забыли продлить VPS → бот пропадает

### 🎯 **Мониторинг здоровья:**
```bash
# Добавьте в crontab для проверки каждые 5 минут
*/5 * * * * docker ps | grep my_telegram_bot || docker-compose -f /path/to/docker-compose.simple.yml up -d
```

---

## 🎉 **Итог**

### 🆓 **Сегодня (бесплатно):**
```bash
# GitHub Codespaces
1. Открыть репозиторий на GitHub
2. Code → Codespaces → Create
3. docker-compose -f docker-compose.simple.yml up
```

### 💳 **На выходных ($4/месяц):**
```bash
# DigitalOcean VPS
1. Создать Droplet
2. Установить Docker
3. Загрузить код
4. Запустить бота
```

**Результат:** Ваш бот работает 24/7! 🚀 