import asyncio
import logging
import os
from aiogram.types import Update

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from config import TOKEN, PRICES  # TOKEN va PRICES ni Railway ENV orqali uzatish tavsiya qilinadi


# --- FSM States ---
class Form(StatesGroup):
    contract = State()
    consulting = State()
    consulting_price = State()
    program = State()
    region = State()
    bank_shot = State()
    parents_income = State()

# --- Keyboards ---
def yes_no_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Ha"), KeyboardButton(text="❌ Yo'q")], [KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True
    )

def program_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🎓 Bakalavr"), KeyboardButton(text="🎓 Magistratura")],
                  [KeyboardButton(text="🌐 Til kursi")],
                  [KeyboardButton(text="🔙 Orqaga")]], resize_keyboard=True
    )

def region_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🏢 Seul ichida"), KeyboardButton(text="🏠 Seul tashqarisida")],
                  [KeyboardButton(text="🔙 Orqaga")]], resize_keyboard=True
    )

def restart_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="♻️ Boshqatdan hisoblash")]], resize_keyboard=True
    )

contact_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📞 +998 99 658 22 72", url="https://wa.me/998996582272")],
    [InlineKeyboardButton(text="📞 +998 90 810 22 72", url="https://wa.me/998998102272")],
    [InlineKeyboardButton(text="📷 Instagram (@eduexpress_uz)", url="https://instagram.com/eduexpress_uz")],
    [InlineKeyboardButton(text="🎵 TikTok (@eduexpress_uz)", url="https://tiktok.com/@eduexpress_uz")]
])


# --- Bot setup ---
TOKEN = os.getenv("BOT_TOKEN", TOKEN)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "supersecret123")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{os.getenv('RAILWAY_STATIC_URL')}{WEBHOOK_PATH}"

bot = Bot(TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# --- Handlers ---
@dp.message(F.text == "/start")
@dp.message(F.text == "♻️ Boshqatdan hisoblash")
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("👋 *Eduexpress hisobchi botiga xush kelibsiz!*\n\n"
                         "Davom etish uchun 🎓Universitet kontrakt summasini kiriting (USD💲):",
                         parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.contract)

@dp.message(Form.contract)
async def get_contract(message: Message, state: FSMContext):
    try:
        contract = float(message.text)
        await state.update_data(contract_amount=contract)
        await message.answer("🤝 *Konsulting yoki visa xizmatidan foydalanyapsizmi?*", parse_mode="Markdown", reply_markup=yes_no_keyboard())
        await state.set_state(Form.consulting)
    except ValueError:
        await message.answer("❗ Iltimos, faqat raqam kiriting.")

@dp.message(Form.consulting)
async def consulting(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await start(message, state)
        return

    if "Ha" in message.text:
        await message.answer("💰 Konsulting xizmatining summasini kiriting (USD💲):", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.consulting_price)
    else:
        await state.update_data(consulting_price=0)
        await ask_program(message, state)

@dp.message(Form.consulting_price)
async def consulting_price(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(Form.consulting)
        await message.answer("🤝 *Konsulting yoki visa xizmatidan foydalanyapsizmi?*", parse_mode="Markdown", reply_markup=yes_no_keyboard())
        return

    try:
        price = float(message.text)
        await state.update_data(consulting_price=price)
        await ask_program(message, state)
    except ValueError:
        await message.answer("❗ Iltimos, faqat raqam kiriting.")

async def ask_program(message: Message, state: FSMContext):
    await message.answer("🌟 *Qaysi dasturga topshirasiz?*", parse_mode="Markdown", reply_markup=program_keyboard())
    await state.set_state(Form.program)

@dp.message(Form.program)
async def program_choice(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(Form.consulting_price)
        await message.answer("💰 Konsulting xizmatining summasini kiriting (USD💲):")
        return

    if "Til kursi" in message.text:
        program = "Til kursi"
    elif "Bakalavr" in message.text:
        program = "Bakalavr"
    elif "Magistratura" in message.text:
        program = "Magistratura"
    else:
        await message.answer("❗ Iltimos, ro‘yxatdan birini tanlang.")
        return

    await state.update_data(program=program)

    if program == "Til kursi":
        await message.answer(
            "📅 *Bank shot ma'lumotlari:*\n"
            "💵 Seul ichida: 8,000 USD\n"
            "💵 Seul tashqarisida: 7,000 USD\n\n"
            "🌆 Iltimos lokatsiyani tanlang:",
            parse_mode="Markdown",
            reply_markup=region_keyboard()
        )
    else:
        await message.answer(
            "📅 *Bank shot ma'lumotlari:*\n"
            "💵 Seul ichida: 15,000 USD\n"
            "💵 Seul tashqarisida: 13,000 USD\n\n"
            "🌆 Iltimos lokatsiyani tanlang:",
            parse_mode="Markdown",
            reply_markup=region_keyboard()
        )

    await state.set_state(Form.region)

@dp.message(Form.region)
async def region_choice(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await ask_program(message, state)
        return

    if "Seul ichida" in message.text:
        region = "Seul ichida"
    elif "Seul tashqarisida" in message.text:
        region = "Seul tashqarisida"
    else:
        await message.answer("❗ Iltimos, ro‘yxatdan birini tanlang.")
        return

    await state.update_data(region=region)
    await message.answer("🏦 Bank shot qo‘yib berish xizmatidan foydalanasizmi?", reply_markup=yes_no_keyboard())
    await state.set_state(Form.bank_shot)

@dp.message(Form.bank_shot)
async def bank_shot(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(Form.region)
        await message.answer("🌆 Iltimos lokatsiyani tanlang:", reply_markup=region_keyboard())
        return

    await state.update_data(bank_shot=message.text)
    await message.answer("👥 Ota-ona yillik daromadi xizmati kerakmi? (+600 USD)", reply_markup=yes_no_keyboard())
    await state.set_state(Form.parents_income)

@dp.message(Form.parents_income)
async def summary(message: Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await state.set_state(Form.bank_shot)
        await message.answer("🏦 Bank shot qo‘yib berish xizmatidan foydalanasizmi?", reply_markup=yes_no_keyboard())
        return

    await state.update_data(parents_income=message.text)
    data = await state.get_data()

    contract = data.get("contract_amount", 0)
    consulting = data.get("consulting_price", 0)
    total = contract + consulting

    msg = (
        f"\U0001F4C8 *Umumiy hisob:*\n\n"
        f"📚 Universitet kontrakti: {contract} USD\n"
        f"💼 Konsulting: {consulting} USD\n"
    )

    if data["program"] == "Til kursi":
        if "Ha" in data["bank_shot"]:
            amount = PRICES["bank_shot_lang_service_seoul"] if data["region"] == "Seul ichida" else PRICES["bank_shot_lang_service_other"]
            total += amount
            msg += f"🛠️ Bank shot xizmati: {amount} USD\n"
        else:
            course_fee = 8000 if data["region"] == "Seul ichida" else 7000
            total += course_fee
            msg += f"📘 Bank shot: {course_fee} USD\n"
    else:
        if "Yo'q" in data["bank_shot"]:
            amount = PRICES["bank_shot_seoul"] if data["region"] == "Seul ichida" else PRICES["bank_shot_other"]
        else:
            amount = PRICES["bank_shot_service_seoul"] if data["region"] == "Seul ichida" else PRICES["bank_shot_service_other"]
        total += amount
        is_no = "Yo'q" in data["bank_shot"]
        msg += f"{'🏦' if is_no else '🛠️'} Bank shot {'summasi' if is_no else 'xizmati'}: {amount} USD\n"

    if "Ha" in data["parents_income"]:
        total += PRICES["parents_income_service"]
        msg += f"🧱 Ota-ona daromadi xizmati: {PRICES['parents_income_service']} USD\n"

    msg += f"\n💰 *Jami:* {total} USD\n"
    msg += "\n⚠️ Diqqat! Bu taxminiy hisob. O‘zgarishi mumkin."

    await message.answer(msg, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    await message.answer(
        "🏢 *Eduexpress* — bu Janubiy Koreyada o‘qish uchun to‘liq hujjatlar to‘plami, "
        "professional maslahat va ishonchli hamkorlikni taklif qiluvchi kompaniya.\n\n"
        "✅ 1000+ muvaffaqiyatli talabalar\n"
        "✅ Rasmiy universitetlar bilan hamkorlik\n"
        "✅ Visa, bank shot, ota-ona daromadi va boshqa hujjatlar — barchasi bir joyda!\n\n"
        "Siz ham bizga qo‘shiling va o‘qishingizni biz bilan boshlang!",
        parse_mode="Markdown")
    await message.answer("Quyidagi tugmalar orqali biz bilan bog‘laning 👇", reply_markup=contact_buttons)
    await message.answer("♻️ Hisobni boshqatdan boshlash uchun tugmani bosing:", reply_markup=restart_keyboard())
    await state.clear()


# --- Webhook Server (aiohttp) ---
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
    logging.info("Webhook set successfully")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

async def handle_webhook(request: web.Request):
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != WEBHOOK_SECRET:
        return web.Response(status=403)
    data = await request.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return web.Response()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle_webhook)

async def main():
    logging.basicConfig(level=logging.INFO)
    await on_startup(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", 8080)))
    await site.start()
    logging.info(f"Bot listening via webhook on {WEBHOOK_URL}")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
