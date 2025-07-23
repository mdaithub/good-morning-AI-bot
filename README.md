# Good Morning AI BOT ☀️

[![Build](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://t.me/YourBotUsername)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

> **Good Morning AI BOT** is an intelligent, customizable Telegram bot built to deliver positive, scheduled Good Morning messages to groups or users in their preferred language and format. It supports text, images, and stickers, includes special messages for festivals, and automatically rotates fallback content when internet sources are unavailable. Designed for high reliability, it’s ideal for community management, student groups, corporate teams, or personal use.

---

![Preview](A_promotional_graphic_for_the_"Good_Morning_Bot,"_.png)

---

## ✅ Features

- Per-group scheduled messages (`/settime`)
- Multi-language support (`/language`)
- Modes: text, image, sticker, mixed (`/mode`)
- Admin-only control for critical commands
- Weekend sticker mode 🎉
- Auto-festive messages from `festivals.json`
- Fallback system: 100 messages + 100 images
- Daily rotating message/image system

## 📦 Files

- `bot.py`: Main bot script
- `group_times.json`: Stores group time schedules
- `group_modes.json`: Message types per group
- `group_languages.json`: Language preferences
- `skip_groups.json`: Skipped groups tracker
- `fallback_messages_and_images.json`: Offline content
- `fallback_index_tracker.json`: Daily message/image index tracker
- `festivals.json`: Special day messages

## 🚀 Getting Started

1. Install requirements:
   ```bash
   pip install python-telegram-bot apscheduler requests
   ```

2. Set your bot token in `bot.py`:
   ```python
   TOKEN = 'YOUR_BOT_TOKEN'
   ```

3. Run the bot:
   ```bash
   python bot.py
   ```

## 🧑‍💻 Deployment Options

- Local server or VPS
- Render.com (free worker service)
- Railway.app (free credits, always-on)

## 🔒 Admin Commands

- `/settime HH:MM` → Only admin
- `/mode text|image|sticker|mixed` → Only admin
- `/language xx` → Any user
- `/skip`, `/stop` → Available to all

## 🌐 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT)
