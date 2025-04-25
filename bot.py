from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegramcalendar import create_calendar, process_calendar_selection
import datetime

user_data = {}

# Стартовое меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📤 Расход", callback_data='expense')],
        [InlineKeyboardButton("📥 Приход", callback_data='income')],
    ]
    await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

# Обработка callback-кнопок
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data in ['expense', 'income']:
        user_data[user_id] = {'type': 'расход' if data == 'expense' else 'приход'}
        calendar, step = create_calendar()
        await query.edit_message_text("Выберите дату:", reply_markup=calendar)

    elif data.startswith("CALENDAR"):
        selected, date = process_calendar_selection(update, context)
        if selected:
            user_data[user_id]['date'] = date.strftime("%Y-%m-%d")

            # Переход к юрлицам
            keyboard = [
                [InlineKeyboardButton("ИП Волынин", callback_data='org_волынин')],
                [InlineKeyboardButton("ИП Морозова", callback_data='org_морозова')],
            ]
            text = "На какое ИП пришли деньги?" if user_data[user_id]['type'] == 'приход' else "Выберите юрлицо:"
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            # Календарь еще в процессе — не меняем
            pass

    elif data.startswith('org_'):
        org = data.split('_')[1]
        user_data[user_id]['org'] = org

        if user_data[user_id]['type'] == 'расход':
            keyboard = [
                [InlineKeyboardButton("Логистика", callback_data='cat_логистика')],
                [InlineKeyboardButton("ЗП", callback_data='cat_зп')],
                [InlineKeyboardButton("Упаковка", callback_data='cat_упаковка')],
            ]
            await query.edit_message_text("Категория расхода:", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("От кого пришли деньги?")
            context.user_data['awaiting_from'] = True

    elif data.startswith('cat_'):
        cat = data.split('_')[1]
        user_data[user_id]['category'] = cat
        await query.edit_message_text("Введите сумму расхода:")
        context.user_data['awaiting_sum'] = True

    elif data == 'confirm':
        summary = user_data.get(user_id, {})
        message = f"✅ Подтверждено:\nТип: {summary.get('type')}\nДата: {summary.get('date')}\nЮрлицо: {summary.get('org')}\n"

        if summary['type'] == 'расход':
            message += f"Категория: {summary.get('category')}\n"
        if summary.get('from'):
            message += f"От кого: {summary.get('from')}\n"

        message += f"Сумма: {summary.get('sum')} ₽"
        await query.edit_message_text(message)

# Обработка текстов (от кого и сумма)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if context.user_data.get('awaiting_from'):
        user_data[user_id]['from'] = text
        context.user_data['awaiting_from'] = False
        await update.message.reply_text("Введите сумму прихода:")
        context.user_data['awaiting_sum'] = True
        return

    if context.user_data.get('awaiting_sum'):
        user_data[user_id]['sum'] = text
        context.user_data['awaiting_sum'] = False

        summary = user_data[user_id]
        msg = f"Проверьте данные:\nТип: {summary['type']}\nДата: {summary['date']}\nЮрлицо: {summary['org']}\n"

        if summary['type'] == 'расход':
            msg += f"Категория: {summary['category']}\n"
        if summary.get('from'):
            msg += f"От кого: {summary.get('from')}\n"

        msg += f"Сумма: {summary['sum']} ₽"

        keyboard = [[InlineKeyboardButton("✅ Подтвердить", callback_data='confirm')]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

# Запуск бота
app = ApplicationBuilder().token("7425395840:AAFp9rUpWu-EQqLi-vryGH7y5cjLbvTmb4E").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

app.run_polling()