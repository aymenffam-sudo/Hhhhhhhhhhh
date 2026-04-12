import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

BOT_TOKEN = "8593915208:AAHTLNiwLsN8uonzRRoP4CJsWgjYvC8IEPY"
OWNER_ID  = 6676819684  # het lid tlgrm dialk hna

logging.basicConfig(level=logging.INFO)

keys_store: dict[str, str] = {}

SET_PHRASE, SET_KEY, WAITING_GUESS = range(3)


# ── OWNER ──────────────────────────────────────────────────

async def cmd_setkey(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔️ Access denied.")
        return ConversationHandler.END

    await update.message.reply_text(
        "🔐 Add New Key — Step 1/2\n\n"
        "Send the *winning phrase* users must type to claim the key.",
        parse_mode="Markdown"
    )
    return SET_PHRASE


async def owner_receive_phrase(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["pending_phrase"] = update.message.text.strip()
    await update.message.reply_text(
        "🔐 Add New Key — Step 2/2\n\n"
        f"✅ Phrase saved: `{ctx.user_data['pending_phrase']}`\n\n"
        "Now send the *prize key* the winner will receive.",
        parse_mode="Markdown"
    )
    return SET_KEY


async def owner_receive_key(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    phrase = ctx.user_data.pop("pending_phrase")
    key    = update.message.text.strip()
    keys_store[phrase.lower()] = key

    await update.message.reply_text(
        "✅ Key saved successfully!\n\n"
        f"🗝 Phrase : `{phrase}`\n"
        f"🎁 Key    : `{key}`\n\n"
        "_The key will be deleted automatically once someone claims it._",
        parse_mode="Markdown"
    )
    return ConversationHandler.END


async def cmd_listkeys(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔️ Access denied.")
        return

    if not keys_store:
        await update.message.reply_text("📭 No keys available right now.")
        return

    lines = ["📋 Active Keys:\n"]
    for i, (phrase, key) in enumerate(keys_store.items(), 1):
        lines.append(f"{i}. 🗝 `{phrase}` → `{key}`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def cmd_removekey(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔️ Access denied.")
        return

    if not ctx.args:
        await update.message.reply_text("Usage: /removekey <phrase>")
        return

    phrase = " ".join(ctx.args).lower()
    if phrase in keys_store:
        del keys_store[phrase]
        await update.message.reply_text(f"🗑 Key for `{phrase}` removed.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Phrase not found.")


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END


# ── USER ───────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Welcome, *{user.first_name}*!\n\n"
        f"🎯 Do you know the secret phrase?\n\n"
        f"Type it below and you could win a prize! 🎁\n\n"
        f"_Good luck!_ 🍀",
        parse_mode="Markdown"
    )
    return WAITING_GUESS


async def user_guess(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    guess = update.message.text.strip().lower()
    user  = update.effective_user

    if guess in keys_store:
        prize_key = keys_store.pop(guess)

        await update.message.reply_text(
            f"🏆 Congratulations, *{user.first_name}*!\n\n"
            f"🎉 You found the correct phrase!\n\n"
            f"🎁 Your Prize Key:\n`{prize_key}`\n\n"
            f"_Enjoy your reward! You deserve it_ 🌟",
            parse_mode="Markdown"
        )

        username = f"@{user.username}" if user.username else "No username"
        try:
            await ctx.bot.send_message(
                chat_id=OWNER_ID,
                text=(
                    "🔔 Key Claimed!\n\n"
                    f"👤 Name     : {user.full_name}\n"
                    f"🆔 User ID  : `{user.id}`\n"
                    f"📎 Username : {username}\n\n"
                    f"🗝 Phrase   : `{guess}`\n"
                    f"🎁 Key Sent : `{prize_key}`\n\n"
                    "✅ The key has been automatically deleted from the bot."
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.warning(f"Could not notify owner: {e}")

    else:
        await update.message.reply_text(
            "❌ Wrong phrase!\n\n"
            "That's not the right answer. 😔\n\n"
            "Think carefully and try again! 💪🍀"
        )

    return WAITING_GUESS


# ── MAIN ───────────────────────────────────────────────────

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
    app.add_handler(CommandHandler("listkeys",  cmd_listkeys))
    app.add_handler(CommandHandler("removekey", cmd_removekey))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
