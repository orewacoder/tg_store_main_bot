from aiogram import Router, Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove
from app.db.mongodb import engine
from app.markups.reply import admin_menu, main_menu
from app.middlewares.Admin import AdminMiddleware
from app.models import User

router = Router()
router.message.middleware(AdminMiddleware())
router.callback_query.middleware(AdminMiddleware())


class Notify(StatesGroup):
    notification = State()


class MessageState(StatesGroup):
    user_id = State()
    message = State()


@router.message(F.text == "📢 Рассылка")
async def notify(msg: Message, state: FSMContext):
    await state.set_state(Notify.notification)
    await msg.answer("Напишите текс сообщения", reply_markup=ReplyKeyboardRemove())


@router.message(Notify.notification)
async def send(msg: Message, state: FSMContext, bot: Bot):
    usrs = await engine['users'].find({'is_banned': False}).to_list(length=1000)
    notified = []
    error = []
    for user in usrs:
        user_id = user['id']
        if user.get('is_admin', False):
            continue
        username = user.get('username', '---')
        name = user.get('first_name', '') + ' ' + user.get('last_name', '')
        lang = user.get('language_code', '-')
        u = {'id': user_id, 'name': name, 'lang': lang, 'username': username}
        try:
            await bot.send_chat_action(user_id, 'typing')
            await bot.send_message(user_id, msg.text, reply_markup=main_menu)
            notified.append(u)
        except Exception as e:
            print(e)
            error.append(u)
    await msg.answer(f"{len(error)} Пользователей не получили сообщение из за того что они заблокировали этого бота\n"
                     f"{len(notified)} Пользователей получили сообщение\n", reply_markup=admin_menu)


@router.message(F.text == "💬 Сообщение")
async def send_message(msg: Message, state: FSMContext):
    await state.set_state(MessageState.user_id)
    await msg.answer("Введите id пользователя", reply_markup=ReplyKeyboardRemove())


@router.message(MessageState.user_id)
async def message_user_id(msg: Message, state: FSMContext):
    await state.update_data(user_id=msg.text)
    await state.set_state(MessageState.message)

    await msg.answer("Введите сообщение", reply_markup=ReplyKeyboardRemove())


@router.message(MessageState.message)
async def send_message_to_user(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = data.get('user_id')
    try:
        await bot.send_chat_action(user_id, 'typing')
        await bot.send_message(user_id, msg.text, reply_markup=main_menu)
        await msg.answer("Сообщение отправлено", reply_markup=admin_menu)
    except Exception as e:
        await msg.answer("Пользователь не получил сообщение из за того что он заблокировал этого бота", reply_markup=admin_menu)
    await state.clear()

