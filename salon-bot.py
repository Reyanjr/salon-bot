import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Config
TOKEN = os.environ.get("TOKEN", "8525862815:AAF4isHo4QOFXiYN0-j09gBKMyuMrRZa3ZI")
OWNER_ID = 1209419167
SPREADSHEET_ID = "1dEHuvkLVBRjYcKsiX2Y1xOSH8nXTaVhdzrPTDubzN_4"

# Google Sheets setup
def get_sheet():
    import json, base64
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = base64.b64decode(os.environ.get("GOOGLE_CREDENTIALS_B64")).decode("utf-8")
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).sheet1

# Conversation states
NAME, PHONE, SERVICE, DATE, TIME = range(5)

# Services
SERVICES = {
    "✂️ Стрижка": "1500 руб — 45 мин",
    "🎨 Окрашивание": "3500 руб — 2 часа",
    "💅 Маникюр": "1200 руб — 1 час",
    "💆 Уход за лицом": "2000 руб — 1 час",
    "💇 Укладка": "1000 руб — 30 мин",
}

TIMES = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]

def main_menu():
    keyboard = [
        [KeyboardButton("📅 Записаться"), KeyboardButton("💼 Услуги и цены")],
        [KeyboardButton("📍 Контакты"), KeyboardButton("❌ Отменить запись")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def services_keyboard():
    keyboard = [[KeyboardButton(s)] for s in SERVICES.keys()]
    keyboard.append([KeyboardButton("🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def times_keyboard():
    keyboard = [[KeyboardButton(t) for t in TIMES[i:i+3]] for i in range(0, len(TIMES), 3)]
    keyboard.append([KeyboardButton("🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.from_user.first_name
    await update.message.reply_text(
        f"👋 Привет, {name}!\n\n"
        "Добро пожаловать в салон красоты *Bella* 💄\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "💼 *Наши услуги:*\n\n"
    for service, details in SERVICES.items():
        text += f"{service}\n💰 {details}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu())

async def show_contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📍 *Контакты салона Bella*\n\n"
        "📌 Адрес: ул. Арбат, 25, Москва\n"
        "📞 Телефон: +7 (495) 123-45-67\n"
        "🕐 Часы работы: Пн-Сб 10:00 — 20:00\n"
        "📱 Instagram: @bella_salon_msk",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

# Booking conversation
async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 *Запись на приём*\n\nКак вас зовут?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Назад")]], resize_keyboard=True)
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Назад":
        await start(update, context)
        return ConversationHandler.END
    context.user_data["name"] = update.message.text
    await update.message.reply_text("📞 Ваш номер телефона?")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Назад":
        await start(update, context)
        return ConversationHandler.END
    context.user_data["phone"] = update.message.text
    await update.message.reply_text(
        "💼 Выберите услугу:",
        reply_markup=services_keyboard()
    )
    return SERVICE

async def get_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Назад":
        await start(update, context)
        return ConversationHandler.END
    if update.message.text not in SERVICES:
        await update.message.reply_text("Пожалуйста выберите услугу из списка 👇")
        return SERVICE
    context.user_data["service"] = update.message.text
    await update.message.reply_text(
        "📅 Введите дату (например: 28.05.2026):",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🔙 Назад")]], resize_keyboard=True)
    )
    return DATE

async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Назад":
        await start(update, context)
        return ConversationHandler.END
    context.user_data["date"] = update.message.text
    await update.message.reply_text(
        "🕐 Выберите время:",
        reply_markup=times_keyboard()
    )
    return TIME

async def get_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Назад":
        await start(update, context)
        return ConversationHandler.END
    if update.message.text not in TIMES:
        await update.message.reply_text("Пожалуйста выберите время из списка 👇")
        return TIME

    context.user_data["time"] = update.message.text
    data = context.user_data

    # Save to Google Sheets
    try:
        sheet = get_sheet()
        sheet.append_row([data["name"], data["phone"], data["service"], data["date"], data["time"], "Новая"])
    except Exception as e:
        print(f"Sheets error: {e}")

    # Notify owner
    owner_msg = (
        f"🔔 *Новая запись!*\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"💼 Услуга: {data['service']}\n"
        f"📅 Дата: {data['date']}\n"
        f"🕐 Время: {data['time']}"
    )
    try:
        await context.bot.send_message(chat_id=OWNER_ID, text=owner_msg, parse_mode="Markdown")
    except Exception as e:
        print(f"Owner notify error: {e}")

    # Confirm to user
    await update.message.reply_text(
        f"✅ *Вы записаны!*\n\n"
        f"👤 Имя: {data['name']}\n"
        f"💼 Услуга: {data['service']}\n"
        f"📅 Дата: {data['date']}\n"
        f"🕐 Время: {data['time']}\n\n"
        f"Ждём вас! Если нужно отменить — нажмите ❌ Отменить запись",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    return ConversationHandler.END

async def cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ *Отмена записи*\n\n"
        "Для отмены позвоните нам:\n"
        "📞 +7 (495) 123-45-67\n\n"
        "Или напишите в Instagram: @bella_salon_msk",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "💼 Услуги и цены":
        await show_services(update, context)
    elif text == "📍 Контакты":
        await show_contacts(update, context)
    elif text == "❌ Отменить запись":
        await cancel_booking(update, context)
    else:
        await start(update, context)

# App setup
app = ApplicationBuilder().token(TOKEN).build()

booking_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^📅 Записаться$"), start_booking)],
    states={
        NAME: [MessageHandler(filters.TEXT, get_name)],
        PHONE: [MessageHandler(filters.TEXT, get_phone)],
        SERVICE: [MessageHandler(filters.TEXT, get_service)],
        DATE: [MessageHandler(filters.TEXT, get_date)],
        TIME: [MessageHandler(filters.TEXT, get_time)],
    },
    fallbacks=[CommandHandler("start", start)]
)

app.add_handler(CommandHandler("start", start))
app.add_handler(booking_handler)
app.add_handler(MessageHandler(filters.TEXT, handle_message))

print("Salon bot is running...")
app.run_polling()