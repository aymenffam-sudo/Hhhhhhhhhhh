import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

# --- الإعدادات الصحيحة (بياناتك الخاصة) ---
BOT_TOKEN = "8593915208:AAHTLNiwLsN8uonzRRoP4CJsWgjYvC8IEPY"
OWNERS = [6676819684] 
FOOTER = "\n\n**Ben 10 🍀**" 
USERS_FILE = "users_db.json"

logging.basicConfig(level=logging.INFO)
keys_store: dict[str, str] = {}

# حالات المحادثة
SET_PHRASE, SET_KEY, BROADCAST_STATE = range(3)

# ── وظائف البيانات ──
def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f: return set(json.load(f))
        except: return set()
    return set()

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        with open(USERS_FILE, "w") as f: json.dump(list(users), f)

# ── لوحة التحكم بالأزرار (كل الأوامر هنا) ──
async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS: return
    
    keyboard = [
        [
            InlineKeyboardButton("🔐 إضافة مفتاح", callback_data='add_key'),
            InlineKeyboardButton("📋 عرض المفاتيح", callback_data='list_keys')
        ],
        [
            InlineKeyboardButton("📊 الإحصائيات", callback_data='show_stats'),
            InlineKeyboardButton("📢 إذاعة (Broadcast)", callback_data='start_bc')
        ],
        [
            InlineKeyboardButton("👤 إضافة مطور", callback_data='add_owner_hint'),
            InlineKeyboardButton("🗑 حذف مطور", callback_data='rem_owner_hint')
        ],
        [
            InlineKeyboardButton("❌ مسح كل المفاتيح", callback_data='clear_all')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    admin_text = (
        "🛠 **— لوحة تحكم المطورين —**\n\n"
        "مرحباً بك! استخدم **الأزرار** أدناه للتحكم السريع في البوت:\n\n"
        "🔹 **لإضافة مطور:** أرسل `/addowner` متبوعاً بالأيدي.\n"
        "🔹 **لحذف مطور:** أرسل `/removeowner` متبوعاً بالأيدي."
    )
    await update.message.reply_text(admin_text + FOOTER, reply_markup=reply_markup, parse_mode="Markdown")

# ── إدارة الأونرات (أوامر مباشرة) ──
async def cmd_addowner(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS: return
    if not ctx.args:
        await update.message.reply_text("⚠️ **تنبيه:** أرسل الأيدي مع الأمر، مثال:\n`/addowner 12345`" + FOOTER, parse_mode="Markdown")
        return
    new_id = int(ctx.args[0])
    if new_id not in OWNERS:
        OWNERS.append(new_id)
        await update.message.reply_text(f"✅ **تمت الإضافة:** `{new_id}` أصبح مطوراً." + FOOTER, parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ **تنبيه:** هذا الحساب مطور بالفعل." + FOOTER, parse_mode="Markdown")

async def cmd_removeowner(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS: return
    if not ctx.args:
        await update.message.reply_text("⚠️ **تنبيه:** أرسل الأيدي مع الأمر، مثال:\n`/removeowner 12345`" + FOOTER, parse_mode="Markdown")
        return
    target_id = int(ctx.args[0])
    if target_id == 6676819684:
        await update.message.reply_text("❌ **فشل:** لا يمكنك حذف الأونر الأساسي!" + FOOTER, parse_mode="Markdown")
        return
    if target_id in OWNERS:
        OWNERS.remove(target_id)
        await update.message.reply_text(f"🗑 **تم الحذف:** الحساب `{target_id}` تم إزالته." + FOOTER, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ **خطأ:** الحساب غير موجود بالإدارة." + FOOTER, parse_mode="Markdown")

# ── معالج ضغط الأزرار ──
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'list_keys':
        msg = "**📋 قائمة المفاتيح النشطة:**\n\n" + "\n".join([f"• `{p}` ⬅️ `{k}`" for p, k in keys_store.items()]) if keys_store else "📭 **لا توجد مفاتيح حالياً.**"
        await query.edit_message_text(msg + FOOTER, parse_mode="Markdown")
    
    elif query.data == 'show_stats':
        await query.edit_message_text(f"📊 **إحصائيات البوت:**\n\n👤 **المستخدمين:** `{len(load_users())}`\n🗝 **المفاتيح:** `{len(keys_store)}`" + FOOTER, parse_mode="Markdown")
    
    elif query.data == 'clear_all':
        keys_store.clear()
        await query.edit_message_text("🗑 **تم التصفير:** تم مسح جميع المفاتيح بنجاح." + FOOTER, parse_mode="Markdown")
    
    elif query.data == 'add_owner_hint':
        await query.edit_message_text("👤 **لإضافة مطور جديد:**\nاكتب الأمر التالي: `/addowner` متبوعاً بالرقم التعريفي (ID)." + FOOTER, parse_mode="Markdown")
    
    elif query.data == 'rem_owner_hint':
        await query.edit_message_text("🗑 **لحذف مطور:**\nاكتب الأمر التالي: `/removeowner` متبوعاً بالرقم التعريفي (ID)." + FOOTER, parse_mode="Markdown")

# ── أنظمة الإضافة والإذاعة (Conversations) ──
async def start_add_key_conv(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # نستخدم هذا لبدء المحادثة من زر
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔐 **خطوة 1:** أرسل الآن كلمة السر (Phrase):" + FOOTER, parse_mode="Markdown")
    return SET_PHRASE

async def start_bc_conv(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📢 **الإذاعة:** أرسل النص الذي تريد نشره للجميع الآن:" + FOOTER, parse_mode="Markdown")
    return BROADCAST_STATE

async def get_phrase(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['p'] = update.message.text.strip().lower()
    await update.message.reply_text("✅ **تم الحفظ!** أرسل الآن الجائزة (Key):" + FOOTER, parse_mode="Markdown")
    return SET_KEY

async def get_key(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    p, k = ctx.user_data.get('p'), update.message.text.strip()
    keys_store[p] = k
    await update.message.reply_text(f"✨ **تمت الإضافة!**\n\n🔑 الكلمة: `{p}`\n🎁 الجائزة: `{k}`" + FOOTER, parse_mode="Markdown")
    return ConversationHandler.END

async def send_bc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sent = 0
    for u in load_users():
        try:
            await ctx.bot.send_message(u, f"📢 **رسالة إدارية:**\n\n{update.message.text}" + FOOTER, parse_mode="Markdown")
            sent += 1
        except: continue
    await update.message.reply_text(f"✅ **اكتملت الإذاعة!** وصلت لـ `{sent}` مستخدم." + FOOTER, parse_mode="Markdown")
    return ConversationHandler.END

# ── المستخدم ──
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    await update.message.reply_text(f"👋 **مرحباً بك {update.effective_user.first_name}!**\nأرسل كلمة السر للحصول على جائزتك! 🎁" + FOOTER, parse_mode="Markdown")

async def handle_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip().lower()
    if msg in keys_store:
        prize = keys_store.pop(msg)
        await update.message.reply_text(f"🏆 **مبروك يا بطل!**\nلقد وجدت الجائزة:\n\n`{prize}`" + FOOTER, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ **كلمة خاطئة!** حاول مجدداً." + FOOTER, parse_mode="Markdown")

# ── التشغيل النهائي ──
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # أوامر الأونر المباشرة
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("addowner", cmd_addowner))
    app.add_handler(CommandHandler("removeowner", cmd_removeowner))
    app.add_handler(CommandHandler("start", cmd_start))

    # محادثة إضافة مفتاح (تبدأ من زر add_key)
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_key_conv, pattern='^add_key$')],
        states={
            SET_PHRASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phrase)],
            SET_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_key)],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)]
    ))

    # محادثة الإذاعة (تبدأ من زر start_bc)
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_bc_conv, pattern='^start_bc$')],
        states={BROADCAST_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_bc)]},
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)]
    ))

    # معالجات الأزرار العامة
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # معالج الرسائل العادية
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))

    print("🤖 Bot is Online with ALL Features & Buttons!")
    app.run_polling()

if __name__ == "__main__":
    main()
