import logging
import json
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# --- الإعدادات الأساسية ---
BOT_TOKEN = "8593915208:AAHTLNiwLsN8uonzRRoP4CJsWgjYvC8IEPY"
OWNERS = [6676819684] 
FOOTER = "\n\nBen 10 🍀"

# ملف حفظ المستخدمين للإذاعة
USERS_FILE = "users_db.json"

logging.basicConfig(level=logging.INFO)

keys_store: dict[str, str] = {}
SET_PHRASE, SET_KEY, WAITING_GUESS, BROADCAST_STATE = range(4)

# ── وظائف إدارة المستخدمين ──────────────────────────────

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return set(json.load(f))
        except: return set()
    return set()

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(list(users), f)

# ── وظائف الأونر (ADMINS ONLY) ──────────────────────────────

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS: return
    admin_text = (
        "🛠 **لوحة تحكم المطورين**\n\n"
        "• `/setkey` : إضافة مفتاح جديد\n"
        "• `/listkeys` : عرض المفاتيح النشطة\n"
        "• `/removekey` : حذف مفتاح محدد\n"
        "• `/clear_keys` : مسح كل المفاتيح\n"
        "• `/stats` : إحصائيات البوت\n"
        "• `/broadcast` : إذاعة رسالة للجميع\n"
        "• `/addowner ID` : إضافة مطور جديد"
    )
    await update.message.reply_text(admin_text + FOOTER, parse_mode="Markdown")

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS: return
    users_count = len(load_users())
    keys_count = len(keys_store)
    stats_text = (
        "📊 **إحصائيات البوت:**\n\n"
        f"👤 عدد المستخدمين الكلي: `{users_count}`\n"
        f"🗝 عدد المفاتيح المتاحة حالياً: `{keys_count}`"
    )
    await update.message.reply_text(stats_text + FOOTER, parse_mode="Markdown")

async def cmd_clear_keys(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS: return
    keys_store.clear()
    await update.message.reply_text("🗑 تم مسح جميع المفاتيح بنجاح." + FOOTER)

# ── نظام الإذاعة (Broadcast) ──────────────────────────────

async def start_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS: return
    await update.message.reply_text("📢 أرسل الرسالة التي تريد إذاعتها للجميع (نص فقط):" + FOOTER)
    return BROADCAST_STATE

async def do_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    broadcast_msg = update.message.text
    users = load_users()
    count = 0
    for user_id in users:
        try:
            await ctx.bot.send_message(chat_id=user_id, text=broadcast_msg + FOOTER)
            count += 1
        except: continue
    await update.message.reply_text(f"✅ تم إرسال الإذاعة إلى {count} مستخدم." + FOOTER)
    return ConversationHandler.END

# ── استكمال الأوامر الإدارية ──────────────────────────────

async def cmd_addowner(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS: return
    if not ctx.args: return
    try:
        new_id = int(ctx.args[0])
        if new_id not in OWNERS:
            OWNERS.append(new_id)
            await update.message.reply_text(f"✅ تم إضافة `{new_id}` كأونر." + FOOTER)
    except: pass

async def cmd_setkey(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS: return ConversationHandler.END
    await update.message.reply_text("🔐 خطوة 1/2: أرسل كلمة السر:" + FOOTER)
    return SET_PHRASE

async def owner_receive_phrase(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["pending_phrase"] = update.message.text.strip().lower()
    await update.message.reply_text("✅ خطوة 2/2: أرسل الجائزة الآن:" + FOOTER)
    return SET_KEY

async def owner_receive_key(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    phrase = ctx.user_data.pop("pending_phrase")
    key = update.message.text.strip()
    keys_store[phrase] = key
    await update.message.reply_text(f"✅ تم الحفظ بنجاح!\nالكلمة: `{phrase}`" + FOOTER, parse_mode="Markdown")
    return ConversationHandler.END

# ── وظائف المستخدمين (User Side) ───────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user.id) # حفظ اليوزر للإذاعة
    user = update.effective_user
    welcome_text = (
        f"👋 **أهلاً بك {user.first_name}**\n\n"
        "🎯 **عربي:**\n"
        "هل تمتلك كلمة السر؟ أرسلها هنا للحصول على جائزتك فوراً!\n\n"
        "🎯 **English:**\n"
        "Do you have a secret phrase? Type it below to claim your prize!"
    )
    await update.message.reply_text(welcome_text + FOOTER, parse_mode="Markdown")
    return WAITING_GUESS

async def user_guess(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    guess = update.message.text.strip().lower()
    if guess in keys_store:
        prize = keys_store.pop(guess)
        await update.message.reply_text(f"🏆 مبروك يا بطل! جائزتك هي:\n`{prize}`" + FOOTER, parse_mode="Markdown")
        # إشعار الأونرز
        for admin_id in OWNERS:
            try: await ctx.bot.send_message(admin_id, f"🔔 تم حصد مفتاح!\nالكلمة: `{guess}`\nالمستخدم: {update.effective_user.full_name}")
            except: pass
    else:
        await update.message.reply_text("❌ كلمة خاطئة، حاول مجدداً!" + FOOTER)
    return WAITING_GUESS

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية." + FOOTER)
    return ConversationHandler.END

# ── تشغيل البوت ───────────────────────────────

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # محادثة إضافة مفتاح
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("setkey", cmd_setkey)],
        states={
            SET_PHRASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_receive_phrase)],
            SET_KEY:    [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_receive_key)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    # محادثة الإذاعة
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("broadcast", start_broadcast)],
        states={
            BROADCAST_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, do_broadcast)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    # محادثة المستخدم (التخمين)
    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            WAITING_GUESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_guess)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    ))

    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("addowner", cmd_addowner))
    app.add_handler(CommandHandler("clear_keys", cmd_clear_keys))
    
    # أمر عرض المفاتيح
    async def list_keys(update, context):
        if update.effective_user.id in OWNERS:
            if not keys_store:
                await update.message.reply_text("📭 لا توجد مفاتيح نشطة حالياً." + FOOTER)
                return
            msg = "📋 قائمة المفاتيح النشطة:\n" + "\n".join([f"• `{p}` -> `{k}`" for p, k in keys_store.items()])
            await update.message.reply_text(msg + FOOTER, parse_mode="Markdown")
    app.add_handler(CommandHandler("listkeys", list_keys))

    print("🤖 Bot is running... Signature: Ben 10 🍀")
    app.run_polling()

if __name__ == "__main__":
    main()
