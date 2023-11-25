
from aiogram import Router, F
from aiogram.filters import Command
from aiogram import types
from aiogram.fsm.state import StatesGroup, State

from app.db.mongodb import engine
from app.functions.products import send_products
from app.markups.messages import start_message, rules_message, help_message
from app.markups.reply import main_menu, admin_menu
from aiogram.fsm.context import FSMContext
from app.models.user import User
router = Router()


@router.message(Command(commands=['start']))
async def start(msg: types.Message, state: FSMContext):
    await state.clear()
    user_data = await engine['users'].find_one({
        "id": msg.from_user.id
    })

    if not user_data:
        user = User(
            id=msg.from_user.id,
            name=msg.from_user.username,
            tg_data=msg.from_user
        )
    else:
        user_data['tg_data'] = msg.from_user
        user_data['name'] = msg.from_user.username
        user = User(**user_data)
    await user.save()

    # photo = FSInputFile("/files/greeting.jpg")
    await msg.answer(
        start_message,
        reply_markup=admin_menu if user.is_admin else main_menu
    )


class SearchState(StatesGroup):
    search = State()


@router.message(Command(commands='search'))
@router.message(F.text == "🔎 Поиск")
async def search(msg: types.Message, state: FSMContext):
    await state.set_state(SearchState.search)
    await msg.answer(
        "Введите поисковый запрос",
        reply_markup=types.ReplyKeyboardRemove()
    )


@router.message(Command(commands='catalog'))
@router.message(F.text == "📦 Товары")
@router.message(F.text, SearchState.search)
async def catalog(msg: types.Message):
    search_term = '' if msg.text in ['/catalog', '📦 Товары'] else msg.text
    await send_products(msg, search_term=search_term)


@router.callback_query(F.data.startswith("product_navigation"))
async def catalog_callback(msg: types.CallbackQuery):
    skip, search_term = msg.data.split(":")[1:]
    await msg.answer()
    await send_products(msg.message, skip=int(skip), search_term=search_term)


@router.callback_query(F.data == 'products:clear_search_term')
async def clear_search_term(msg: types.CallbackQuery, state: FSMContext, user: User):
    await state.clear()
    await msg.answer()
    answer = await msg.message.answer('Поиск очищен', reply_markup=main_menu if not user.is_admin else admin_menu)
    await send_products(msg.message)


@router.message(F.text == "🚦 Правила")
async def rules(msg: types.Message, state: FSMContext, user: User):
    await msg.answer(rules_message, reply_markup=main_menu if not user.is_admin else admin_menu)


@router.message(Command(commands='support'))
@router.message(Command(commands='help'))
@router.message(F.text == "🛟 Поддержка")
async def _help(msg: types.Message, state: FSMContext, user: User):
    await msg.answer(help_message, reply_markup=main_menu if not user.is_admin else admin_menu)


@router.message(F.text == "👤 Профиль")
async def profile(msg: types.Message, user: User):
    unknown = "Не указан"
    await msg.answer(
        "Ваш профиль\n\n"
        f"Вы заказали: {user.total_orders} раз за ${user.total_orders_amount}\n\n"
        f"Ваш адрес: {user.address or unknown}\n"
        f"Ваш номер телефона: {user.phone or unknown}\n\n"
    )
