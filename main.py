import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

# --- الإعدادات الصحيحة ---
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

# ── لوحة التحكم ──
async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS: return
    
    keyboard = [
        [InlineKeyboardButton("🔐 إضافة مفتاح", callback_data='add_key'),
         InlineKeyboardButton("📋 عرض المفاتيح", callback_data='list_keys')],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data='show_stats'),
         InlineKeyboardButton("📢 إذاعة (Broadcast)", callback_data='start_bc')],
        [InlineKeyboardButton("👤 إضافة مطور", callback_data='add_owner_hint'),
         InlineKeyboardButton("🗑 حذف مطور", callback_data='rem_owner_hint')],
        [InlineKeyboardButton("❌ مسح كل المفاتيح", callback_data='clear_all')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    admin_text = (
        "🛠 **— لوحة تحكم المطورين —**\n\n"
        "استخدم **الأزرار** أدناه أو الأوامر المباشرة:\n\n"
        "🔹 **إضافة مطور:** `/addowner ID`\n"
        "🔹 **حذف مطور:** `/removeowner ID`"
    )
    await update.message.reply_text(admin_text + FOOTER, reply_markup=reply_markup, parse_mode="Markdown")

# ── إدارة الأونرات ──
async def cmd_addowner(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS: return
    if not ctx.args: return
    try:
        new_id = int(ctx.args[0])
        if new_id not in OWNERS:
            OWNERS.append(new_id)
            await update.message.reply_text(f"✅ **تمت الإضافة:** `{new_id}`" + FOOTER, parse_mode="Markdown")
    except: pass

async def cmd_removeowner(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS: return
    if not ctx.args: return
    target_id = int(ctx.args[0])
    if target_id == 6676819684: return
    if target_id in OWNERS:
        OWNERS.remove(target_id)
        await update.message.reply_text(f"🗑 **تم الحذف:** `{target_id}`" + FOOTER, parse_mode="Markdown")

# ── معالجات المحادثات (إضافة مفتاح وإذاعة) ──
async def start_add_key_conv(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🔐 **خطوة 1:** أرسل الآن كلمة السر (Phrase):" + FOOTER, parse_mode="Markdown")
    return SET_PHRASE

async def get_phrase(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['p'] = update.message.text.strip().lower()
    await update.message.reply_text("✅ **تم الحفظ!** أرسل الآن الجائزة (Key):" + FOOTER, parse_mode="Markdown")
    return SET_KEY

async def get_key(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    p, k = ctx.user_data.get('p'), update.message.text.strip()
    keys_store[p] = k
    await update.message.reply_text(f"✨ **تمت الإضافة!**\n🔑 `{p}` ➡️ `{k}`" + FOOTER, parse_mode="Markdown")
    return ConversationHandler.END

async def start_bc_conv(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📢 **الإذاعة:** أرسل النص الآن:" + FOOTER, parse_mode="Markdown")
    return BROADCAST_STATE

async def send_bc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    sent = 0
    for u in load_users():
        try:
            await ctx.bot.send_message(u, f"📢 **رسالة إدارية:**\n\n{update.message.text}" + FOOTER, parse_mode="Markdown")
            sent += 1
        except: continue
    await update.message.reply_text(f"✅ **اكتملت!** وصلت لـ `{sent}` مستخدم." + FOOTER, parse_mode="Markdown")
    return ConversationHandler.END

# ── معالج الأزرار العامة ──
async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'list_keys':
        msg = "**📋 القائمة:**\n\n" + "\n".join([f"• `{p}` ⬅️ `{k}`" for p, k in keys_store.items()]) if keys_store else "📭 لا توجد مفاتيح."
        await query.message.reply_text(msg + FOOTER, parse_mode="Markdown")
    elif query.data == 'show_stats':
        await query.message.reply_text(f"📊 **الإحصائيات:**\n👤 يوزر: `{len(load_users())}`\n🗝 مفاتيح: `{len(keys_store)}`" + FOOTER, parse_mode="Markdown")
    elif query.data == 'clear_all':
        keys_store.clear()
        await query.message.reply_text("🗑 **تم التصفير بنجاح.**" + FOOTER, parse_mode="Markdown")
    elif query.data in ['add_owner_hint', 'rem_owner_hint']:
        await query.message.reply_text("👤 استخدم الأوامر المباشرة:\n`/addowner ID` أو `/removeowner ID`" + FOOTER, parse_mode="Markdown")

# ── المستخدم ──
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id)
    await update.message.reply_text(f"👋 **أهلاً بك {update.effective_user.first_name}!**\nأرسل كلمة السر للحصول على جائزتك!" + FOOTER, parse_mode="Markdown")

async def handle_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip().lower()
    if msg in keys_store:
        prize = keys_store.pop(msg)
        await update.message.reply_text(f"🏆 **مبروك!** وجدت الجائزة:\n\n`{prize}`" + FOOTER, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ **كلمة خاطئة!**" + FOOTER, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # 1. الترتيب مهم جداً: الـ ConversationHandlers أولاً
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_key_conv, pattern='^add_key$')],
        states={
            SET_PHRASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phrase)],
            SET_KEY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_key)],
        },
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
        allow_reentry=True
    ))

    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(start_bc_conv, pattern='^start_bc$')],
        states={BROADCAST_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_bc)]},
        fallbacks=[CommandHandler("cancel", lambda u,c: ConversationHandler.END)],
        allow_reentry=True
    ))

    # 2. أوامر المطورين
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("addowner", cmd_addowner))
    app.add_handler(CommandHandler("removeowner", cmd_removeowner))
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # 3. معالج الرسائل العادية (يجب أن يكون الأخير)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))

    print("🤖 Bot is fixed and running!")
    app.run_polling()

if __name__ == "__main__":
    main()
