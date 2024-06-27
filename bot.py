from gpytranslate import Translator

from os import getenv
from tiktoken import encoding_for_model

from db import DataBase
from openaitools import OpenAiTools
from stablediffusion import StableDiffusion
from cryptopay import CryptoPay

from dotenv import load_dotenv
from aiofiles.os import remove

import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types.input_file import FSInputFile
from aiogram import F

class States(StatesGroup):
    ENTRY_STATE = State()
    CHATGPT_STATE = State()
    DALL_E_STATE = State()
    STABLE_STATE = State()
    INFO_STATE = State()
    PURCHASE_STATE = State()
    PURCHASE_CHATGPT_STATE = State()
    PURCHASE_DALL_E_STATE = State()
    PURCHASE_STABLE_STATE = State()

dp = Dispatcher()

# Starts a conversation
@dp.message(Command('start'))
@dp.message(States.ENTRY_STATE, F.text.regexp(r'^🔙Ortga$'))
@dp.message(States.CHATGPT_STATE, F.text.regexp(r'^🔙Ortga$'))
@dp.message(States.DALL_E_STATE, F.text.regexp(r'^🔙Ortga$'))
@dp.message(States.STABLE_STATE, F.text.regexp(r'^🔙Ortga$'))
@dp.message(States.INFO_STATE, F.text.regexp(r'^🔙Ortga$'))
async def start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    result = await DataBase.is_user(user_id)

    button = [[KeyboardButton(text="💭Suhbat — ChatGPT")],
              [KeyboardButton(text="🌄Rasm yaratish — DALL·E")],
              [KeyboardButton(text="🌅Rasm yaratish — Stable Diffusion")],
              [KeyboardButton(text="👤Menning hisobim | 💰To\'ldirish")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard = button, resize_keyboard=True
    )

    if not result:
        await DataBase.insert_user(user_id, username)
        await message.answer(
            text = "👋Sizga sovg'a: \n💭3000 ChatGPT token \n🌄3 DALL·E rasm generatsiyasi \n🌅3 Stable Diffusion rasm generatsiyasi\n Tanlang va ishlating: 👇 \n Agar muammo bo'lsa, /start buyrug'ini kiriting",
            reply_markup=reply_markup,
        )
    else:
        await message.answer(
            text = "Menudan foydalaning: 👇🏻 \n Agar tugmalar ishlamasa,  /start buyrug'ini kiriting",
            reply_markup=reply_markup,
        )
    await state.set_state(States.ENTRY_STATE)

# Question Handling
@dp.message(States.ENTRY_STATE, F.text.regexp(r'^💭Suhbat — ChatGPT$'))
@dp.message(States.ENTRY_STATE, F.text.regexp(r'^🌄Rasm yaratish — DALL·E$'))
@dp.message(States.ENTRY_STATE, F.text.regexp(r'^🌅Rasm yaratish — Stable Diffusion$'))
async def question_handler(message: types.Message, state: FSMContext):
    button = [[KeyboardButton(text="🔙Ortga")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard = button, resize_keyboard=True
    )
    await message.answer(
        text = "Qani boshladik: 👇🏻",
        reply_markup=reply_markup,
    )
    option = message.text
    if option == "💭Suhbat — ChatGPT":
        await state.set_state(States.CHATGPT_STATE)
    elif option == "🌄Rasm yaratish — DALL·E":
        await state.set_state(States.DALL_E_STATE)
    elif option == "🌅Rasm yaratish — Stable Diffusion":
        await state.set_state(States.STABLE_STATE)

# Answer Handling
@dp.message(States.CHATGPT_STATE, F.text)
async def chatgpt_answer_handler(message: types.Message, state: FSMContext):
    button = [[KeyboardButton(text="🔙Ortga")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard = button, resize_keyboard=True
    )

    user_id = message.from_user.id
    result = await DataBase.get_chatgpt(user_id)

    if result > 0:
        question = message.text

        answer = await OpenAiTools.get_chatgpt(question)

        if answer:
            await message.answer(
                text = answer,
                reply_markup=reply_markup,
            )
            result -= len(await asyncio.get_running_loop().run_in_executor(None, encoding.encode,question + answer))
            if result > 0:
                await DataBase.set_chatgpt(user_id, result)
            else:
                await DataBase.set_chatgpt(user_id, 0)
        else:
            await message.answer(
                text = "❌Your request activated the API's safety filters and could not be processed. Please modify the prompt and try again.",
                reply_markup=reply_markup,
            )

    else:
        await message.answer(
            text = "❎You have 0 ChatGPT tokens. You need to buy them to use ChatGPT.",
            reply_markup=reply_markup,
        )
    await state.set_state(States.CHATGPT_STATE)


# Answer Handling
@dp.message(States.DALL_E_STATE, F.text)
async def dall_e_answer_handler(message: types.Message, state: FSMContext):
    button = [[KeyboardButton(text="🔙Ortga")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard = button, resize_keyboard=True
    )

    user_id = message.from_user.id
    result = await DataBase.get_dalle(user_id)

    if result > 0:
        question = message.text

        prompt = await translator.translate(question, targetlang='en')

        answer = await OpenAiTools.get_dalle(prompt.text)

        if answer:
            await message.answer_photo(
                photo=answer,
                reply_markup=reply_markup,
                caption=question,
            )
            result -= 1
            await DataBase.set_dalle(user_id, result)
        else:
            await message.answer(
                text = "❌Your request activated the API's safety filters and could not be processed. Please modify the prompt and try again.",
                reply_markup=reply_markup,
            )
    else:
        await message.answer(
            text = "❎You have 0 DALL·E image generations. You need to buy them to use DALL·E.",
            reply_markup=reply_markup,
        )
    await state.set_state(States.DALL_E_STATE)


# Answer Handling
@dp.message(States.STABLE_STATE, F.text)
async def stable_answer_handler(message: types, state: FSMContext):
    button = [[KeyboardButton(text="🔙Ortga")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard = button, resize_keyboard=True
    )

    user_id = message.from_user.id
    result = await DataBase.get_stable(user_id)

    if result > 0:

        question = message.text

        prompt = await translator.translate(question, targetlang='en')

        path = await asyncio.get_running_loop().run_in_executor(None, StableDiffusion.get_stable,prompt.text)

        if path:
            await message.answer_photo(
                photo=FSInputFile(path),
                reply_markup=reply_markup,
                caption=question,
            )
            await remove(path)
            result -= 1
            await DataBase.set_stable(user_id, result)
        else:
            await message.answer(
                text = "❌Your request activated the API's safety filters and could not be processed. Please modify the prompt and try again.",
                reply_markup=reply_markup,
            )
    else:
        await message.answer(
            text = "❎You have 0 Stable Diffusion image generations. You need to buy them to use Stable Diffusion.",
            reply_markup=reply_markup,
        )
    await state.set_state(States.STABLE_STATE)


# Displays information about user
@dp.message(States.ENTRY_STATE, F.text.regexp(r'^👤Menning hisobim | 💰To\'ldirish$'))
@dp.message(States.PURCHASE_STATE, F.text.regexp(r'^🔙Ortga$'))
async def display_info(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    result = await DataBase.get_userinfo(user_id)

    button = [[KeyboardButton(text="💰Token va generatsiya sotib olish")], [KeyboardButton(text="🔙Ortga")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard = button, resize_keyboard=True
    )
    await message.answer(
        text = f"Sizda hozirda bor: \n 💭{result[2]} ChatGPT tokenlar \n 🌄{result[3]} DALL·E rasm generatsiyalari \n 🌅{result[4]} Stable Diffusion rasm generatsiyalari \n 💸 Siz yana sotib olishingiz mumkin",
        reply_markup=reply_markup,
    )
    await state.set_state(States.INFO_STATE)


# Displays goods
@dp.message(States.INFO_STATE, F.text.regexp(r'^💰Token va generatsiya sotib olish$'))
@dp.message(States.PURCHASE_CHATGPT_STATE, F.text.regexp(r'^🔙Ortga$'))
@dp.message(States.PURCHASE_DALL_E_STATE, F.text.regexp(r'^🔙Ortga$'))
@dp.message(States.PURCHASE_STABLE_STATE, F.text.regexp(r'^🔙Ortga$'))
async def purchase(message: types.Message, state: FSMContext):
    button = [[KeyboardButton(text="100K ChatGPT tokenlari - 5 USD💵")],
              [KeyboardButton(text="100 DALL·E rasm generatsiyalari - 5 USD💵")],
              [KeyboardButton(text="100 Stable Diffusion rasm generatsiyalari - 5 USD💵")],
              [KeyboardButton(text="🔙Ortga")]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard = button, resize_keyboard=True
    )
    await message.answer(
        text = "Nima sotib olmoqchisiz: 👇",
        reply_markup=reply_markup,
    )
    await state.set_state(States.PURCHASE_STATE)


# Displays cryptocurrencies
@dp.message(States.PURCHASE_STATE, F.text.regexp(r'^100K ChatGPT tokenlari - 5 USD💵$'))
@dp.message(States.PURCHASE_STATE, F.text.regexp(r'^100 DALL·E rasm generatsiyalari - 5 USD💵$'))
@dp.message(States.PURCHASE_STATE, F.text.regexp(r'^100 Stable Diffusion rasm generatsiyalari - 5 USD💵$'))
async def currencies(message: types.Message, state: FSMContext):
    buttons = [
        [KeyboardButton(text="💲USDT"),
        KeyboardButton(text="💲TON")],
        [KeyboardButton(text="💲BTC"),
        KeyboardButton(text="💲ETH")],
        [KeyboardButton(text="🔙Ortga")]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard = buttons,
        resize_keyboard=True
    )
    await message.answer(
        text = "Valyutani tanlang: 👇",
        reply_markup=keyboard,
    )
    product = message.text
    if product == "100K ChatGPT tokenlari - 5 USD💵":
        await state.set_state(States.PURCHASE_CHATGPT_STATE)
    elif product == "100 DALL·E rasm generatsiyalari - 5 USD💵":
        await state.set_state(States.PURCHASE_DALL_E_STATE)
    elif product == "100 Stable Diffusion rasm generatsiyalari - 5 USD💵":
        await state.set_state(States.PURCHASE_STABLE_STATE)

# Makes invoice and displays it
@dp.message(States.PURCHASE_CHATGPT_STATE, F.text.regexp(r'^💲USDT$'))
@dp.message(States.PURCHASE_CHATGPT_STATE, F.text.regexp(r'^💲TON$'))
@dp.message(States.PURCHASE_CHATGPT_STATE, F.text.regexp(r'^💲BTC$'))
@dp.message(States.PURCHASE_CHATGPT_STATE, F.text.regexp(r'^💲ETH$'))
@dp.message(States.PURCHASE_DALL_E_STATE, F.text.regexp(r'^💲USDT$'))
@dp.message(States.PURCHASE_DALL_E_STATE, F.text.regexp(r'^💲TON$'))
@dp.message(States.PURCHASE_DALL_E_STATE, F.text.regexp(r'^💲BTC$'))
@dp.message(States.PURCHASE_DALL_E_STATE, F.text.regexp(r'^💲ETH$'))
@dp.message(States.PURCHASE_STABLE_STATE, F.text.regexp(r'^💲USDT$'))
@dp.message(States.PURCHASE_STABLE_STATE, F.text.regexp(r'^💲TON$'))
@dp.message(States.PURCHASE_STABLE_STATE, F.text.regexp(r'^💲BTC$'))
@dp.message(States.PURCHASE_STABLE_STATE, F.text.regexp(r'^💲ETH$'))
async def buy(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    currency = message.text
    invoice_url, invoice_id = await CryptoPay.create_invoice(5, currency[1:])
    current_state = await state.get_state()
    product = ''
    if current_state == States.PURCHASE_CHATGPT_STATE:
        product = '100K ChatGPT tokenlari - 5 USD💵'
        await DataBase.new_order(invoice_id, user_id, 'chatgpt')
    elif current_state == States.PURCHASE_DALL_E_STATE:
        product = '100 DALL·E rasm generatsiyalari - 5 USD💵'
        await DataBase.new_order(invoice_id, user_id, 'dall_e')
    elif current_state == States.PURCHASE_STABLE_STATE:
        product = '100 Stable Diffusion rasm generatsiyalari - 5 USD💵'
        await DataBase.new_order(invoice_id, user_id, 'stable')
    keyboard = InlineKeyboardMarkup(
        inline_keyboard = [
            [InlineKeyboardButton(text="💰Sotib olish", url=invoice_url),
             InlineKeyboardButton(text="☑️Tekshirish", callback_data=str(invoice_id))],
        ]
    )
    await message.answer(
        text = f"🪙Harid qilmoqchisiz: {product} \n 💳Agar to'lamoqchi bo'lsangiz 'Sotib olish' tugmasini bosing, Crypto Botda 'Start' tugmasini bosing va ko'rsatmalarga amal qilgan holda to'lovni amalga oshiring \n ❗ Tarmoq komissiyasini ham hisobga oling \n ☑️To'lovni amalga oshirgandan so'ng 'Tekshirish' tugmasini bosing \n Agar hozir sotib olishni istamasangiz 'Ortga' tugmasini bosing: 👇",
        reply_markup=keyboard,
    )

# Checks payment
@dp.callback_query()
async def keyboard_callback(callback_query: types.CallbackQuery):
    query = callback_query
    invoice_id = int(query.data)
    result = await DataBase.get_orderdata(invoice_id)
    if result:
        status = await CryptoPay.get_status(invoice_id)
        if status == "active":
            await query.answer("⌚️Iltimos kutib turing!")
        elif status == "paid":
            if result[1] == 'chatgpt':
                await DataBase.update_chatgpt(result[0], invoice_id)
                await query.answer("✅To'lov amalga oshdi, tokenlar sizning hisobingizga qo'shildi")
            elif result[1] == 'dall_e':
                await DataBase.update_dalle(result[0], invoice_id)
                await query.answer("✅To'lov amalga oshdi, Dall-E rasm generatsiyalari sizning hisobingizga qo'shildi")
            elif result[1] == 'stable':
                await DataBase.update_stable(result[0], invoice_id)
                await query.answer("✅To'lov amalga oshdi, Stable Diffusion rasm generatsiyalari sizning hisobingizga qo'shildi")
        elif status == "expired":
            await query.answer("❎To'lov cheki amal qilish muddati tugadi, iltimos yangi to'lov yarating")
    else:
        await query.answer("✅Siz haridingizni qabul qilib olgansiz allaqachon!")

async def main():
    await DataBase.open_pool()
    await dp.start_polling(bot)

if __name__ == '__main__':
    load_dotenv()
    translator = Translator()
    bot = Bot(token=getenv("TELEGRAM_BOT_TOKEN"))
    encoding = encoding_for_model("gpt-3.5-turbo")
    asyncio.run(main())
