import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# --- الإعدادات الأساسية ---
BOT_TOKEN = ""
OWNERS = [] 

# التوقيع الثابت
FOOTER = "\n\nBen 10 🍀"

logging.basicConfig(level=logging.INFO)

keys_store: dict[str, str] = {}
SET_PHRASE, SET_KEY, WAITING_GUESS = range(3)

# ── وظائف الأونر (ADMINS ONLY) ──────────────────────────────

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS:
        return 

    admin_text = (
        "🛠 **Admin Control Panel | لوحة التحكم**\n\n"
        "مرحباً بك في قائمة المطورين. إليك الأوامر المتاحة:\n"
        "• `/setkey` : إضافة كلمة سر وجائزة جديدة.\n"
        "• `/listkeys` : عرض جميع الكلمات المتاحة.\n"
        "• `/removekey` : حذف كلمة سر معينة.\n"
        "• `/addowner ID` : إضافة مطور جديد للبوت.\n"
        "• `/cancel` : إلغاء العملية الحالية."
    )
    await update.message.reply_text(admin_text + FOOTER, parse_mode="Markdown")

async def cmd_addowner(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS:
        await update.message.reply_text("⛔️ Access denied." + FOOTER)
        return

    if not ctx.args:
        await update.message.reply_text("Usage: `/addowner 12345678`" + FOOTER, parse_mode="Markdown")
        return

    try:
        new_id = int(ctx.args[0])
        if new_id not in OWNERS:
            OWNERS.append(new_id)
            await update.message.reply_text(f"✅ User `{new_id}` added to Owners list." + FOOTER, parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ This ID is already an owner." + FOOTER)
    except ValueError:
        await update.message.reply_text("❌ Please provide a valid numeric ID." + FOOTER)

async def cmd_setkey(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS:
        await update.message.reply_text("⛔️ Access denied." + FOOTER)
        return ConversationHandler.END

    await update.message.reply_text(
        "🔐 **Step 1/2**\n\n"
        "Send the *winning phrase* users must type.\n"
        "أرسل الآن *كلمة السر* التي يجب على المستخدم كتابتها." + FOOTER,
        parse_mode="Markdown"
    )
    return SET_PHRASE

async def owner_receive_phrase(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["pending_phrase"] = update.message.text.strip()
    await update.message.reply_text(
        "🔐 **Step 2/2**\n\n"
        "✅ Phrase saved! Now send the *prize/key*.\n"
        "تم حفظ الكلمة! أرسل الآن *الجائزة أو المفتاح*." + FOOTER,
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
        f"🎁 Key: `{key}`" + FOOTER,
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def cmd_listkeys(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS:
        return

    if not keys_store:
        await update.message.reply_text("📭 No keys available." + FOOTER)
        return

    lines = ["📋 Active Keys:\n"]
    for i, (phrase, key) in enumerate(keys_store.items(), 1):
        lines.append(f"{i}. 🗝 `{phrase}` → `{key}`")
    
    await update.message.reply_text("\n".join(lines) + FOOTER, parse_mode="Markdown")

async def cmd_removekey(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS:
        return

    if not ctx.args:
        await update.message.reply_text("Usage: `/removekey <phrase>`" + FOOTER)
        return

    phrase = " ".join(ctx.args).lower()
    if phrase in keys_store:
        del keys_store[phrase]
        await update.message.reply_text(f"🗑 Key for `{phrase}` removed." + FOOTER, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Phrase not found." + FOOTER)

# ── وظائف المستخدمين (USER SIDE) ─────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_text = (
        f"👋 **Welcome | أهلاً بك {user.first_name}**\n\n"
        "🎯 **English:**\n"
        "Do you have a secret phrase? Type it below to claim your prize!\n\n"
        "🎯 **عربي:**\n"
        "هل تمتلك كلمة السر؟ أرسلها هنا للحصول على جائزتك فوراً!\n\n"
        "🍀 *Good luck! | حظاً موفقاً!*"
    )
    await update.message.reply_text(welcome_text + FOOTER, parse_mode="Markdown")
    return WAITING_GUESS

async def user_guess(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    guess = update.message.text.strip().lower()
    user  = update.effective_user

    if guess in keys_store:
        prize_key = keys_store.pop(guess)
        await update.message.reply_text(
            f"🏆 **Winner! | مبروك يا بطل!**\n\n"
            f"🎁 Your Prize: `{prize_key}`\n\n"
            "_Enjoy your reward!_" + FOOTER,
            parse_mode="Markdown"
        )
        
        # إشعار الأونرز
        for admin_id in OWNERS:
            try:
                await ctx.bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 **Key Claimed!**\n👤 User: {user.full_name}\n🗝 Phrase: `{guess}`" + FOOTER,
                    parse_mode="Markdown"
                )
            except: continue
    else:
        await update.message.reply_text("❌ **Wrong! | كلمة خاطئة**\nTry again! | حاول مجدداً!" + FOOTER)
    
    return WAITING_GUESS

# ── تشغيل البوت ──────────────────────────────────────────────

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Cancelled / تم الإلغاء" + FOOTER)
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
    app.add_handler(CommandHandler("listkeys", cmd_listkeys))
    app.add_handler(CommandHandler("removekey", cmd_removekey))
    
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
