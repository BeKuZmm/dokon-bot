import logging
import os
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)
from database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# States
MAIN_MENU, CATALOG, PRODUCT_DETAIL, CART, CHECKOUT, ADMIN_MENU, \
ADMIN_ADD_NAME, ADMIN_ADD_DESC, ADMIN_ADD_PRICE, ADMIN_ADD_CATEGORY, \
ADMIN_ADD_IMAGE, WAITING_PHONE, WAITING_ADDRESS = range(13)

db = Database()

# ─── KEYBOARDS ───────────────────────────────────────────────

def main_menu_keyboard():
    return ReplyKeyboardMarkup([
        ["🛍 Katalog", "🛒 Savat"],
        ["📦 Buyurtmalarim", "📞 Aloqa"],
    ], resize_keyboard=True)

def admin_menu_keyboard():
    return ReplyKeyboardMarkup([
        ["➕ Mahsulot qo'shish", "📋 Mahsulotlar ro'yxati"],
        ["📦 Barcha buyurtmalar", "🏠 Bosh menyu"],
    ], resize_keyboard=True)

# ─── START ───────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username or "", user.full_name)
    
    is_admin = db.is_admin(user.id)
    keyboard = admin_menu_keyboard() if is_admin else main_menu_keyboard()
    
    await update.message.reply_text(
        f"👋 Assalomu alaykum, *{user.first_name}*!\n\n"
        "🏪 Do'konimizga xush kelibsiz!\n"
        "Pastdagi tugmalardan foydalaning 👇",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    return MAIN_MENU

# ─── SET ADMIN ───────────────────────────────────────────────

async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    secret = os.getenv("ADMIN_SECRET", "")

    if not secret:
        await update.message.reply_text("❌ ADMIN_SECRET sozlanmagan.")
        return MAIN_MENU

    if not context.args:
        await update.message.reply_text("❌ Foydalanish: /setadmin <parol>")
        return MAIN_MENU

    entered = context.args[0]

    if entered != secret:
        await update.message.reply_text("❌ Parol noto'g'ri!")
        return MAIN_MENU

    if db.is_admin(user.id):
        await update.message.reply_text("✅ Siz allaqachon adminsiz!")
        return ADMIN_MENU

    db.add_admin(user.id)
    await update.message.reply_text(
        f"✅ *{user.first_name}* admin qilindi!\n\n"
        "Endi /admin buyrug'i ishlaydi.",
        parse_mode="Markdown",
        reply_markup=admin_menu_keyboard()
    )
    return ADMIN_MENU

# ─── CATALOG ─────────────────────────────────────────────────

async def catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = db.get_categories()
    if not categories:
        await update.message.reply_text("😔 Hozircha mahsulotlar yo'q.")
        return MAIN_MENU

    buttons = [[InlineKeyboardButton(f"📂 {cat}", callback_data=f"cat_{cat}")] for cat in categories]
    await update.message.reply_text(
        "📂 *Kategoriyani tanlang:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CATALOG

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace("cat_", "")
    products = db.get_products_by_category(category)

    if not products:
        await query.edit_message_text("😔 Bu kategoriyada mahsulot yo'q.")
        return CATALOG

    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(
            f"🏷 {p['name']} — {p['price']:,} so'm",
            callback_data=f"prod_{p['id']}"
        )])
    buttons.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_catalog")])

    await query.edit_message_text(
        f"📂 *{category}* kategoriyasi:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CATALOG

async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = int(query.data.replace("prod_", ""))
    p = db.get_product(product_id)

    if not p:
        await query.edit_message_text("❌ Mahsulot topilmadi.")
        return CATALOG

    text = (
        f"🏷 *{p['name']}*\n\n"
        f"📝 {p['description']}\n\n"
        f"💰 Narx: *{p['price']:,} so'm*\n"
        f"📂 Kategoriya: {p['category']}"
    )
    buttons = [
        [InlineKeyboardButton("🛒 Savatga qo'shish", callback_data=f"addcart_{p['id']}")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data=f"cat_{p['category']}")]
    ]

    if p.get("image_url"):
        try:
            await query.message.reply_photo(
                photo=p["image_url"],
                caption=text,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            await query.delete_message()
        except:
            await query.edit_message_text(text, parse_mode="Markdown",
                                          reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(buttons))
    return PRODUCT_DETAIL

async def back_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    categories = db.get_categories()
    buttons = [[InlineKeyboardButton(f"📂 {cat}", callback_data=f"cat_{cat}")] for cat in categories]
    await query.edit_message_text(
        "📂 *Kategoriyani tanlang:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CATALOG

# ─── CART ────────────────────────────────────────────────────

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ Savatga qo'shildi!")
    product_id = int(query.data.replace("addcart_", ""))
    db.add_to_cart(query.from_user.id, product_id)
    return PRODUCT_DETAIL

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    items = db.get_cart(user_id)

    if not items:
        await update.message.reply_text(
            "🛒 Savatingiz bo'sh.\n\nMahsulotlarni katalogdan tanlang!",
            reply_markup=main_menu_keyboard()
        )
        return MAIN_MENU

    text = "🛒 *Savatingiz:*\n\n"
    total = 0
    buttons = []

    for item in items:
        subtotal = item['price'] * item['qty']
        total += subtotal
        text += f"• {item['name']} x{item['qty']} = {subtotal:,} so'm\n"
        buttons.append([
            InlineKeyboardButton(f"➕", callback_data=f"inc_{item['product_id']}"),
            InlineKeyboardButton(f"  {item['qty']}  ", callback_data="noop"),
            InlineKeyboardButton(f"➖", callback_data=f"dec_{item['product_id']}"),
            InlineKeyboardButton(f"🗑", callback_data=f"del_{item['product_id']}"),
        ])

    text += f"\n💰 *Jami: {total:,} so'm*"
    buttons.append([InlineKeyboardButton("✅ Buyurtma berish", callback_data="checkout")])
    buttons.append([InlineKeyboardButton("🗑 Savatni tozalash", callback_data="clear_cart")])

    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CART

async def cart_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("inc_"):
        db.update_cart_qty(user_id, int(data.replace("inc_", "")), 1)
    elif data.startswith("dec_"):
        db.update_cart_qty(user_id, int(data.replace("dec_", "")), -1)
    elif data.startswith("del_"):
        db.remove_from_cart(user_id, int(data.replace("del_", "")))
    elif data == "clear_cart":
        db.clear_cart(user_id)
        await query.edit_message_text("🗑 Savat tozalandi.")
        return MAIN_MENU
    elif data == "noop":
        return CART

    # Refresh cart
    items = db.get_cart(user_id)
    if not items:
        await query.edit_message_text("🛒 Savat bo'sh.")
        return MAIN_MENU

    text = "🛒 *Savatingiz:*\n\n"
    total = 0
    buttons = []
    for item in items:
        subtotal = item['price'] * item['qty']
        total += subtotal
        text += f"• {item['name']} x{item['qty']} = {subtotal:,} so'm\n"
        buttons.append([
            InlineKeyboardButton("➕", callback_data=f"inc_{item['product_id']}"),
            InlineKeyboardButton(f"  {item['qty']}  ", callback_data="noop"),
            InlineKeyboardButton("➖", callback_data=f"dec_{item['product_id']}"),
            InlineKeyboardButton("🗑", callback_data=f"del_{item['product_id']}"),
        ])
    text += f"\n💰 *Jami: {total:,} so'm*"
    buttons.append([InlineKeyboardButton("✅ Buyurtma berish", callback_data="checkout")])
    buttons.append([InlineKeyboardButton("🗑 Savatni tozalash", callback_data="clear_cart")])

    await query.edit_message_text(text, parse_mode="Markdown",
                                  reply_markup=InlineKeyboardMarkup(buttons))
    return CART

# ─── CHECKOUT ────────────────────────────────────────────────

async def checkout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📞 Telefon raqamingizni yuboring:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("📱 Raqamni ulashish", request_contact=True)]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return WAITING_PHONE

async def got_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data['phone'] = update.message.contact.phone_number
    else:
        context.user_data['phone'] = update.message.text

    await update.message.reply_text(
        "🏠 Manzilingizni kiriting\n_(ko'cha, uy raqami)_:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["🔙 Bekor qilish"]], resize_keyboard=True)
    )
    return WAITING_ADDRESS

async def got_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    phone = context.user_data.get('phone', 'Noma\'lum')
    address = update.message.text
    items = db.get_cart(user_id)

    if not items:
        await update.message.reply_text("❌ Savat bo'sh!", reply_markup=main_menu_keyboard())
        return MAIN_MENU

    total = sum(i['price'] * i['qty'] for i in items)
    order_id = db.create_order(user_id, phone, address, items, total)
    db.clear_cart(user_id)

    # Buyurtma xulosasi
    summary = f"📦 *Buyurtma #{order_id}*\n\n"
    for item in items:
        summary += f"• {item['name']} x{item['qty']} = {item['price']*item['qty']:,} so'm\n"
    summary += f"\n💰 Jami: *{total:,} so'm*\n"
    summary += f"📞 Tel: {phone}\n"
    summary += f"🏠 Manzil: {address}\n\n"
    summary += "✅ Buyurtmangiz qabul qilindi! Tez orada bog'lanamiz."

    await update.message.reply_text(summary, parse_mode="Markdown",
                                    reply_markup=main_menu_keyboard())

    # Admin ga xabar
    admin_ids = db.get_admin_ids()
    for admin_id in admin_ids:
        try:
            await context.bot.send_message(
                admin_id,
                f"🔔 *Yangi buyurtma #{order_id}!*\n\n{summary}",
                parse_mode="Markdown"
            )
        except:
            pass

    return MAIN_MENU

# ─── MY ORDERS ───────────────────────────────────────────────

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    orders = db.get_user_orders(user_id)
    if not orders:
        await update.message.reply_text("📦 Hali buyurtma yo'q.")
        return MAIN_MENU

    text = "📦 *Buyurtmalaringiz:*\n\n"
    for o in orders[-5:]:
        status_emoji = {"yangi": "🆕", "jarayonda": "⏳", "yetkazildi": "✅", "bekor": "❌"}.get(o['status'], "📦")
        text += f"{status_emoji} *#{o['id']}* — {o['total']:,} so'm\n"
        text += f"   📅 {o['created_at'][:10]}  |  {o['status'].upper()}\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")
    return MAIN_MENU

# ─── CONTACT ─────────────────────────────────────────────────

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 *Biz bilan bog'laning:*\n\n"
        "📱 Tel: +998 90 123 45 67\n"
        "💬 Telegram: @dokon_admin\n"
        "🕐 Ish vaqti: 9:00 - 21:00",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard()
    )
    return MAIN_MENU

# ─── ADMIN ───────────────────────────────────────────────────

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not db.is_admin(user_id):
        await update.message.reply_text("❌ Ruxsat yo'q.")
        return MAIN_MENU
    await update.message.reply_text("👨‍💼 *Admin panel*", parse_mode="Markdown",
                                    reply_markup=admin_menu_keyboard())
    return ADMIN_MENU

async def admin_products_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = db.get_all_products()
    if not products:
        await update.message.reply_text("😔 Mahsulotlar yo'q.")
        return ADMIN_MENU

    text = "📋 *Mahsulotlar ro'yxati:*\n\n"
    for p in products:
        text += f"#{p['id']} *{p['name']}* — {p['price']:,} so'm [{p['category']}]\n"

    await update.message.reply_text(text, parse_mode="Markdown")
    return ADMIN_MENU

async def admin_all_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    orders = db.get_all_orders()
    if not orders:
        await update.message.reply_text("📦 Buyurtmalar yo'q.")
        return ADMIN_MENU

    text = "📦 *Barcha buyurtmalar:*\n\n"
    for o in orders[-10:]:
        status_emoji = {"yangi": "🆕", "jarayonda": "⏳", "yetkazildi": "✅", "bekor": "❌"}.get(o['status'], "📦")
        text += f"{status_emoji} *#{o['id']}* | {o['total']:,} so'm\n"
        text += f"   👤 User: {o['user_id']} | 📞 {o['phone']}\n"
        text += f"   🏠 {o['address']}\n"
        text += f"   📅 {o['created_at'][:16]}\n\n"

    buttons = []
    for o in orders[-5:]:
        if o['status'] == 'yangi':
            buttons.append([InlineKeyboardButton(
                f"✅ #{o['id']} ni tasdiqlash",
                callback_data=f"confirm_order_{o['id']}"
            )])

    markup = InlineKeyboardMarkup(buttons) if buttons else None
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=markup)
    return ADMIN_MENU

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    order_id = int(query.data.replace("confirm_order_", ""))
    db.update_order_status(order_id, "jarayonda")
    await query.edit_message_text(f"✅ Buyurtma #{order_id} tasdiqlandi — *Jarayonda*", parse_mode="Markdown")
    return ADMIN_MENU

# Admin - mahsulot qo'shish
async def admin_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product'] = {}
    await update.message.reply_text("📝 Mahsulot *nomini* kiriting:", parse_mode="Markdown")
    return ADMIN_ADD_NAME

async def admin_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product']['name'] = update.message.text
    await update.message.reply_text("📝 *Tavsifini* kiriting:", parse_mode="Markdown")
    return ADMIN_ADD_DESC

async def admin_add_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product']['description'] = update.message.text
    await update.message.reply_text("💰 *Narxini* kiriting (so'mda, faqat raqam):", parse_mode="Markdown")
    return ADMIN_ADD_PRICE

async def admin_add_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(" ", "").replace(",", ""))
        context.user_data['new_product']['price'] = price
        await update.message.reply_text("📂 *Kategoriyasini* kiriting (masalan: Kiyim, Oziq-ovqat):", parse_mode="Markdown")
        return ADMIN_ADD_CATEGORY
    except ValueError:
        await update.message.reply_text("❌ Faqat raqam kiriting!")
        return ADMIN_ADD_PRICE

async def admin_add_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product']['category'] = update.message.text
    await update.message.reply_text(
        "🖼 Rasmini yuboring yoki o'tkazib yuborish uchun /skip yozing:",
        parse_mode="Markdown"
    )
    return ADMIN_ADD_IMAGE

async def admin_add_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    image_url = None
    if update.message.photo:
        # file_id saqlash — doimiy va ishonchli (file_path vaqtinchalik bo'ladi)
        image_url = update.message.photo[-1].file_id
    context.user_data['new_product']['image_url'] = image_url
    return await _save_product(update, context)

async def admin_skip_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product']['image_url'] = None
    return await _save_product(update, context)

async def _save_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p = context.user_data['new_product']
    product_id = db.add_product(p['name'], p['description'], p['price'], p['category'], p.get('image_url'))
    await update.message.reply_text(
        f"✅ *{p['name']}* muvaffaqiyatli qo'shildi!\n"
        f"ID: #{product_id} | Narx: {p['price']:,} so'm",
        parse_mode="Markdown",
        reply_markup=admin_menu_keyboard()
    )
    return ADMIN_MENU

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏠 Bosh menyu", reply_markup=main_menu_keyboard())
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Bekor qilindi.", reply_markup=main_menu_keyboard())
    return MAIN_MENU

# ─── MAIN ────────────────────────────────────────────────────

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable not set!")

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("setadmin", set_admin),
        ],
        states={
            MAIN_MENU: [
                MessageHandler(filters.Regex("^🛍 Katalog$"), catalog),
                MessageHandler(filters.Regex("^🛒 Savat$"), show_cart),
                MessageHandler(filters.Regex("^📦 Buyurtmalarim$"), my_orders),
                MessageHandler(filters.Regex("^📞 Aloqa$"), contact),
                CommandHandler("admin", admin_panel),
                CommandHandler("setadmin", set_admin),
            ],
            CATALOG: [
                CallbackQueryHandler(show_category, pattern="^cat_"),
                CallbackQueryHandler(show_product, pattern="^prod_"),
                CallbackQueryHandler(back_catalog, pattern="^back_catalog$"),
            ],
            PRODUCT_DETAIL: [
                CallbackQueryHandler(add_to_cart, pattern="^addcart_"),
                CallbackQueryHandler(show_category, pattern="^cat_"),
            ],
            CART: [
                CallbackQueryHandler(checkout_start, pattern="^checkout$"),
                CallbackQueryHandler(cart_action, pattern="^(inc_|dec_|del_|clear_cart|noop)"),
            ],
            ADMIN_MENU: [
                MessageHandler(filters.Regex("^➕ Mahsulot qo'shish$"), admin_add_start),
                MessageHandler(filters.Regex("^📋 Mahsulotlar ro'yxati$"), admin_products_list),
                MessageHandler(filters.Regex("^📦 Barcha buyurtmalar$"), admin_all_orders),
                MessageHandler(filters.Regex("^🏠 Bosh menyu$"), back_to_main),
                CallbackQueryHandler(confirm_order, pattern="^confirm_order_"),
            ],
            ADMIN_ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_name)],
            ADMIN_ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_desc)],
            ADMIN_ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_price)],
            ADMIN_ADD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_category)],
            ADMIN_ADD_IMAGE: [
                MessageHandler(filters.PHOTO, admin_add_image),
                CommandHandler("skip", admin_skip_image),
            ],
            WAITING_PHONE: [
                MessageHandler(filters.CONTACT | filters.TEXT, got_phone),
            ],
            WAITING_ADDRESS: [
                MessageHandler(filters.Regex("^🔙 Bekor qilish$"), cancel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_address),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("setadmin", set_admin),
            CommandHandler("admin", admin_panel),
            MessageHandler(filters.Regex("^🛍 Katalog$"), catalog),
            MessageHandler(filters.Regex("^🛒 Savat$"), show_cart),
            MessageHandler(filters.Regex("^📦 Buyurtmalarim$"), my_orders),
            MessageHandler(filters.Regex("^📞 Aloqa$"), contact),
            MessageHandler(filters.Regex("^🏠 Bosh menyu$"), back_to_main),
            MessageHandler(filters.Regex("^🔙 Bekor qilish$"), cancel),
        ],
    )

    app.add_handler(conv_handler)
    logger.info("Bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
