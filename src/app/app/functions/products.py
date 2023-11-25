from typing import Union

from aiogram import types
from aiogram.types import FSInputFile, InlineKeyboardButton as button, InlineKeyboardMarkup
from aiogram.utils.keyboard import KeyboardBuilder

from app.db.mongodb import engine
from app.models.product import Product


async def send_products(msg: Union[types.Message, types.CallbackQuery], skip=0, limit=5, search_term=''):
    products = await engine['products'].find({
            'is_active': True, '$or': [
                {'name': {'$regex': search_term, '$options': 'si'}},
                {'description': {'$regex': search_term, '$options': 'si'}}
            ]
        }, skip=skip, limit=limit).to_list(limit)
    if not products:
        return await msg.answer("Товаров не найдено")
    else:
        product_count = await engine['products'].count_documents({'is_active': True}, skip=skip)

    for product in products:
        model = Product(**product)
        message_text = f"<b>{model.name}</b>\n\n{model.description}\n\nЦена: ${model.price}"

        # order button
        builder = KeyboardBuilder(button_type=button)
        builder.add(button(text='Добавить в корзинку', callback_data=f"product:add_to_cart:{model.id}"))
        markup = InlineKeyboardMarkup(inline_keyboard=builder.export())
        try:
            if not model.file or not model.file.file_id:
                raise Exception("No file")
            await msg.answer_photo(
                photo=model.file.file_id,
                caption=message_text,
                reply_markup=markup
            )
        except Exception as e:
            print(e)
            await msg.answer_photo(
                photo=FSInputFile(model.photo),
                caption=message_text,
                reply_markup=markup
            )

    builder = KeyboardBuilder(button_type=button)

    nav_buttons = []
    if search_term:
        nav_buttons.append(button(text=f"❌ {search_term}", callback_data=f"products:clear_search_term"))
    if skip > 0:
        nav_buttons.append(button(test="<<", callback_data=f"products:prev:{skip - limit}:{search_term}"))
    if skip + limit < product_count:
        nav_buttons.append(button(text=">>", callback_data=f"products:next:{skip + limit}:{search_term}"))
    if nav_buttons:
        builder.add(*nav_buttons)
        markup = InlineKeyboardMarkup(inline_keyboard=builder.export())
        await msg.answer(
            "Выберите действие",
            reply_markup=markup
        )
