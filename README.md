# 🏪 Do'kon Telegram Bot

O'zbek tilida to'liq do'kon boti — katalog, savat, buyurtma va admin panel.

## 📁 Fayllar

| Fayl | Vazifasi |
|------|---------|
| `bot.py` | Asosiy bot kodi |
| `database.py` | SQLite ma'lumotlar bazasi |
| `setup.py` | Admin va namunaviy mahsulotlar qo'shish |
| `requirements.txt` | Kerakli kutubxonalar |

## 🚀 Ishga tushirish

### 1. Bot token olish
[@BotFather](https://t.me/BotFather) da yangi bot yarating va tokenini oling.

### 2. O'rnatish
```bash
pip install -r requirements.txt
```

### 3. Token sozlash
```bash
# Windows:
set BOT_TOKEN=your_token_here

# Linux/Mac:
export BOT_TOKEN=your_token_here
```

### 4. Admin va mahsulotlar qo'shish
```bash
python setup.py
```
> Telegram ID ni bilish uchun [@userinfobot](https://t.me/userinfobot) ga /start yuboring.

### 5. Botni ishga tushirish
```bash
python bot.py
```

## ✨ Funksiyalar

### 👤 Foydalanuvchi uchun
- **🛍 Katalog** — Kategoriya bo'yicha mahsulotlarni ko'rish
- **🛒 Savat** — Mahsulot qo'shish, miqdorni o'zgartirish, o'chirish
- **✅ Buyurtma** — Telefon raqam va manzil orqali buyurtma
- **📦 Buyurtmalarim** — Oxirgi buyurtmalarni ko'rish
- **📞 Aloqa** — Do'kon ma'lumotlari

### 👨‍💼 Admin uchun (`/admin` buyrug'i)
- **➕ Mahsulot qo'shish** — Nom, tavsif, narx, kategoriya, rasm
- **📋 Mahsulotlar ro'yxati** — Barcha mahsulotlarni ko'rish
- **📦 Barcha buyurtmalar** — Buyurtmalarni ko'rish va tasdiqlash
- **🔔 Bildirishnoma** — Yangi buyurtma kelganda avtomatik xabar

## 📦 Buyurtma holatlari
- 🆕 **Yangi** — Yangi buyurtma
- ⏳ **Jarayonda** — Tasdiqlanib, yetkazilmoqda
- ✅ **Yetkazildi** — Muvaffaqiyatli
- ❌ **Bekor** — Bekor qilindi

## ☁️ Hosting (bepul)

**Koyeb** yoki **Render** da deploy qilish:
1. GitHub ga yuklang
2. `BOT_TOKEN` environment variable qo'shing
3. Start command: `python bot.py`
