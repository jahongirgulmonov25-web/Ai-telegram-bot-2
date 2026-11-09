import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import google.generativeai as genai

# --- SOZLAMALAR ---
TELEGRAM_BOT_TOKEN = "9187404099:AAEfNwUMeFrobFNLAw-C238_d7PyKbUcwB4"
GEMINI_API_KEY = "AQ.Ab8RN6KQfDoGanOPoKlR8plFZNJVkp7KIdne09gQKis-kiRs0A"

# Gemini API ni sozlash
genai.configure(api_key=GEMINI_API_KEY)

# Modelni sozlash
generation_config = {
    "temperature": 0.3,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 1500,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
}

gemini_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction=(
        "Sen oliy toifali matematika ustozi va imtihon ekspertisan. "
        "Sening asosiy vazifang foydalanuvchi tashlagan murakkab matematika masalalariga "
        "faqat uzun va zerikarli klassik usullarni emas, balki imtihonlarda vaqtni tejaydigan "
        "ENG TEZKOR, QISQA USULLAR (short-cuts) va mantiqiy yechimlarni topib berish. "
        "Javoblarni o'zbek tilida, aniq, tushunarli va formula ko'rinishida chiroyli formatda taqdim et."
    )
)

# --- FSM HOLATLARI ---
class MathStates(StatesGroup):
    waiting_for_problem = State()

# Vaqtinchalik baza
user_balances = {}  
user_subscriptions = {} 

router = Router()

# --- KLAVIATURALAR ---
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧮 Masala yechish (Tezkor usul)", callback_data="solve_math")],
        [InlineKeyboardButton(text="💎 Premium obuna sotib olish", callback_data="buy_sub")],
        [InlineKeyboardButton(text="👤 Profil va Balans", callback_data="profile")]
    ])

def back_to_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Asosiy menyuga qaytish", callback_data="main_menu")]
    ])

# --- HANDLERLAR ---
@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 3  # Yangi foydalanuvchiga 3 ta bepul imkoniyat
        user_subscriptions[user_id] = False

    welcome_text = (
        f"Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
        "Men — <b>MathPro AI</b> botiman. Murakkab matematika masalalarini "
        "klassik usulda emas, imtihonlarda vaqtni tejaydigan <b>eng tezkor va oson yo'llar</b> bilan yechib beraman.\n\n"
        "Quyidagi tugmalar yordamida o'zingizga kerakli bo'limni tanlang:"
    )
    await message.answer(welcome_text, reply_markup=main_menu_kb(), parse_html=True)

@router.callback_query(F.data == "main_menu")
async def process_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Asosiy menyu. Kerakli bo'limni tanlang:",
        reply_markup=main_menu_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "profile")
async def process_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    balance = user_balances.get(user_id, 0)
    is_sub = user_subscriptions.get(user_id, False)
    sub_status = "Faol 💎 (Cheksiz)" if is_sub else "Faol emas (Bepul rejim)"

    text = (
        f"<b>👤 Profil ma'lumotlari:</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"🎁 Qolgan bepul urinishlar: <b>{balance} ta</b>\n"
        f"💎 Premium obuna: <b>{sub_status}</b>"
    )
    await callback.message.edit_text(text, reply_markup=back_to_menu_kb(), parse_html=True)
    await callback.answer()

@router.callback_query(F.data == "buy_sub")
async def process_buy_sub(callback: CallbackQuery):
    text = (
        "<b>💎 Premium Obuna xaridi</b>\n\n"
        "Premium obuna orqali siz quyidagilarga ega bo'lasiz:\n"
        "• Cheksiz miqdorda matematika masalalarini tezkor yechish\n"
        "• Har bir masalaning qadam-baqadam tushuntirishi\n"
        "• Eng qisqa formula va tezyurar usullar\n\n"
        "💳 <i>Oylik to'lov: 25,000 so'm (Click / Payme orqali)</i>\n\n"
        "To'lov qilish uchun quyidagi tugmani bosing (Test rejimida simulyatsiya):"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Hozir 25,000 so'm to'lash", callback_data="pay_confirm")],
        [InlineKeyboardButton(text="« Orqaga", callback_data="main_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_html=True)
    await callback.answer()

@router.callback_query(F.data == "pay_confirm")
async def process_pay_confirm(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_subscriptions[user_id] = True
    await callback.message.edit_text(
        "✅ <b>Tabriklaymiz! To'lov muvaffaqiyatli amalga oshirildi.</b>\n\n"
        "Sizga Premium obuna faollashtirildi. Endi cheksiz masalalar yechishingiz mumkin!",
        reply_markup=back_to_menu_kb(),
        parse_html=True
    )
    await callback.answer("Obuna faollashdi!", show_alert=True)

@router.callback_query(F.data == "solve_math")
async def process_solve_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    is_sub = user_subscriptions.get(user_id, False)
    balance = user_balances.get(user_id, 0)

    if not is_sub and balance <= 0:
        await callback.message.edit_text(
            "⚠️ <b>Bepul urinishlar tugadi!</b>\n\n"
            "Kunlik limit tugagan yoki obunangiz yo'q. Davom etish uchun Premium obuna sotib oling.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💎 Obuna sotib olish", callback_data="buy_sub")],
                [InlineKeyboardButton(text="« Orqaga", callback_data="main_menu")]
            ]),
            parse_html=True
        )
        await callback.answer()
        return

    await state.set_state(MathStates.waiting_for_problem)
    await callback.message.edit_text(
        "✍️ <b>Matematika masalasini yuboring:</b>\n\n"
        "Masala shartini matn ko'rinishida yuboring (masalan: <i>log2(x+3) = 3 tenglamani tezkor usulda yeching</i>).\n\n"
        "Men sizga eng qisqa va tushunarli yo'lini chiqarib beraman.",
        reply_markup=back_to_menu_kb(),
        parse_html=True
    )
    await callback.answer()

@router.message(MathStates.waiting_for_problem, F.text)
async def process_math_solution(message: Message, state: FSMContext):
    user_id = message.from_user.id
    problem_text = message.text

    is_sub = user_subscriptions.get(user_id, False)
    if not is_sub:
        user_balances[user_id] -= 1

    waiting_msg = await message.answer("⏳ <b>Sun'iy intellekt masalani tahlil qilmoqda va eng qisqa yechimni qidirmoqda...</b>", parse_html=True)

    try:
        chat = gemini_model.start_chat(history=[])
        response = await asyncio.to_thread(
            chat.send_message, 
            f"Quyidagi matematika masalasini eng tezkor, qisqa va tushunarli usulda yechib ber:\n\n{problem_text}"
        )
        
        ai_answer = response.text

        result_text = (
            f"🎯 <b>Tezkor yechim va tahlil:</b>\n\n"
            f"{ai_answer}\n\n"
            f"──────────────────\n"
            f"💡 <i>Yana boshqa masala yuborishingiz mumkin.</i>"
        )
        
        await waiting_msg.edit_text(result_text, reply_markup=main_menu_kb(), parse_html=True)
        await state.clear()

    except Exception as e:
        logging.error(f"Gemini API xatoligi: {e}")
        await waiting_msg.edit_text(
            "❌ <b>Xatolik yuz berdi!</b>\n\n"
            "Serverda vaqtinchalik muammo bo'ldi yoki so'rov noto'g'ri. Iltimos, birozdan keyin qayta urinib ko'ring.",
            reply_markup=main_menu_kb(),
            parse_html=True
        )
        await state.clear()

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.include_router(router)
    
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
