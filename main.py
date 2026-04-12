import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# --- الإعدادات الأساسية ---
BOT_TOKEN = "8593915208:AAHTLNiwLsN8uonzRRoP4CJsWgjYvC8IEPY"
# وضعنا المعرفات في قائمة للسماح بأكثر من أونر
OWNERS = [6676819684] 

logging.basicConfig(level=logging.INFO)

keys_store: dict[str, str] = {}
SET_PHRASE, SET_KEY, WAITING_GUESS = range(3)

# ── وظائف الأونر (ADMINS ONLY) ──────────────────────────────

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """رسالة خاصة بالأونرز فقط"""
    if update.effective_user.id not in OWNERS:
        return # تجاهل إذا لم يكن أونر

    admin_text = (
        "🛠 **Admin Control Panel | لوحة التحكم**\n\n"
        "مرحباً بك في قائمة المطورين. إليك الأوامر المتاحة:\n"
        "• `/setkey` : إضافة كلمة سر وجائزة جديدة.\n"
        "• `/listkeys` : عرض جميع الكلمات المتاحة.\n"
        "• `/removekey` : حذف كلمة سر معينة.\n"
        "• `/addowner ID` : إضافة مطور جديد للبوت.\n"
        "• `/cancel` : إلغاء العملية الحالية."
    )
    await update.message.reply_text(admin_text, parse_mode="Markdown")

async def cmd_addowner(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """إضافة أونر جديد للبوت"""
    if update.effective_user.id not in OWNERS:
        await update.message.reply_text("⛔️ Access denied.")
        return

    if not ctx.args:
        await update.message.reply_text("Usage: `/addowner 12345678`", parse_mode="Markdown")
        return

    try:
        new_id = int(ctx.args[0])
        if new_id not in OWNERS:
            OWNERS.append(new_id)
            await update.message.reply_text(f"✅ User `{new_id}` added to Owners list.", parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ This ID is already an owner.")
    except ValueError:
        await update.message.reply_text("❌ Please provide a valid numeric ID.")

async def cmd_setkey(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS:
        await update.message.reply_text("⛔️ Access denied.")
        return ConversationHandler.END

    await update.message.reply_text(
        "🔐 **Step 1/2**\n\n"
        "Send the *winning phrase* users must type.\n"
        "أرسل الآن *كلمة السر* التي يجب على المستخدم كتابتها.",
        parse_mode="Markdown"
    )
    return SET_PHRASE

async def owner_receive_phrase(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["pending_phrase"] = update.message.text.strip()
    await update.message.reply_text(
        "🔐 **Step 2/2**\n\n"
        "✅ Phrase saved! Now send the *prize/key*.\n"
        "تم حفظ الكلمة! أرسل الآن *الجائزة أو المفتاح*.",
        parse_mode="Markdown"
    )
    return SET_KEY

async def owner_receive_key(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    phrase = ctx.user_data.pop("pending_phrase")
    key    = update.message.text.strip()
    keys_store[phrase.lower()] = key

    await update.message.reply_text(
        "✅ **Done | تم الحفظ**\n\n"
        f"🗝 Phrase: `{phrase}`\n"
        f"🎁 Key: `{key}`",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ── وظائف المستخدمين (USER SIDE) ─────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"👋 **Welcome | أهلاً بك {user.first_name}**\n\n"
        "🎯 **English:**\n"
        "Do you have a secret phrase? Type it below to claim your prize! "
        "Each phrase can be used only once.\n\n"
        "🎯 **عربي:**\n"
        "هل تمتلك كلمة السر؟ أرسلها هنا للحصول على جائزتك فوراً! "
        "كل كلمة سر تعمل لمرة واحدة فقط لشخص واحد.\n\n"
        "🍀 *Good luck! | حظاً موفقاً!*"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")
    return WAITING_GUESS

async def user_guess(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    guess = update.message.text.strip().lower()
    user  = update.effective_user

    if guess in keys_store:
        prize_key = keys_store.pop(guess)
        await update.message.reply_text(
            f"🏆 **Winner! | مبروك يا بطل!**\n\n"
            f"🎁 Your Prize: `{prize_key}`\n\n"
            "_Enjoy your reward!_",
            parse_mode="Markdown"
        )
        
        # إشعار الأونرز
        for admin_id in OWNERS:
            try:
                await ctx.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 **Key Claimed!**\n👤 User: {user.full_name}\n🗝 Phrase: `{guess}`"
                )
            except: continue
    else:
        await update.message.reply_text("❌ **Wrong! | كلمة خاطئة**\nTry again! | حاول مجدداً!")
    
    return WAITING_GUESS

# ── تشغيل البوت ──────────────────────────────────────────────

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Cancelled / تم الإلغاء")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    set_key_conv = ConversationHandler(
        entry_points=[CommandHandler("setkey", cmd_setkey)],
        states={
            SET_PHRASE: [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_receive_phrase)],
            SET_KEY:    [MessageHandler(filters.TEXT & ~filters.COMMAND, owner_receive_key)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    user_conv = ConversationHandler(
        entry_points=[CommandHandler("start", cmd_start)],
        states={
            WAITING_GUESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, user_guess)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(set_key_conv)
    app.add_handler(user_conv)
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CommandHandler("addowner", cmd_addowner))
    app.add_handler(CommandHandler("listkeys", lambda u, c: cmd_listkeys(u, c) if u.effective_user.id in OWNERS else None))
    
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
