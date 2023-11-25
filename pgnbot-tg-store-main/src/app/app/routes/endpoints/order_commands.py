import os
from typing import Union
import requests
from aiogram import Router, Bot, F
from aiogram import types
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton as button, InlineKeyboardMarkup, KeyboardButton, \
    ReplyKeyboardRemove
from aiogram.utils.keyboard import KeyboardBuilder
from app.core.config import settings
from app.db.mongodb import engine
from aiogram.fsm.context import FSMContext
from app.markups.reply import main_menu
from app.models.order import SelectedProducts, Cart, Order
from app.models.product import Product

router = Router()


class CheckoutState(StatesGroup):
    cart_id = State()
    address = State()
    phone = State()
    payment_method = State()
    comments = State()


class ProductAddToCartState(StatesGroup):
    count = State()
    product_id = State()


async def add_product_to_cart(product_id: int, user_id: int, count: int = 1):
    product_data = await engine['products'].find_one({
        "id": product_id
    })
    product = Product(**product_data)

    cart_data = await engine['carts'].find_one({
        "user_id": user_id,
        "closed": False
    })
    selected_product = SelectedProducts(
        name=product.name,
        product_id=product_id,
        quantity=count,
        total_price=product.price * count
    )
    if not cart_data:

        cart = Cart(
            user_id=user_id,
            products=[selected_product],
            total_amount=selected_product.total_price,
        )
        await cart.save()
    else:
        cart = Cart(**cart_data)
        product_in_cart = False
        for p in cart.products:
            if int(p.product_id) == int(product_id):
                p.quantity += count
                p.total_price = product.price * p.quantity
                product_in_cart = True
                break

        if not product_in_cart:
            cart.products.append(selected_product)
        cart.total_amount = sum([p.total_price for p in cart.products])

        await cart.save()
    return cart


async def build_cart_data(cart: Cart, message: types.Message):
    builder = KeyboardBuilder(button_type=button)
    builder.add(
        *[button(text=f"❌ {p.name}", callback_data=f"product:remove_from_cart:{p.product_id}:{cart.id}") for p in
          cart.products])
    builder.row(button(text="Оформить заказ", callback_data="cart:checkout"))
    builder.row(button(text="Очистить корзину", callback_data="cart:clear"))
    markup = InlineKeyboardMarkup(inline_keyboard=builder.export())
    await message.answer(
        f"В вашей корзине {sum([p.quantity for p in cart.products])} товаров на сумму ${cart.total_amount}",
        reply_markup=markup
    )


@router.callback_query(F.data.startswith("product:add_to_cart_count"))
@router.message(F.text.isdigit(), ProductAddToCartState.count)
async def add_to_cart_count(query: Union[types.CallbackQuery, types.Message], state: FSMContext):
    if isinstance(query, types.CallbackQuery):
        message = query.message
        count = int(query.data.split(":")[2])
        user_id = query.from_user.id
    else:
        message = query
        count = int(query.text)
        user_id = query.from_user.id

    data = await state.get_data()
    cart = await add_product_to_cart(product_id=data['product_id'], user_id=user_id, count=count)
    await state.clear()
    await query.answer("Товар добавлен в корзину")
    await build_cart_data(cart, message)

    if isinstance(query, types.Message):
        await query.delete()
    else:
        await query.message.delete()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: types.Message):
    cart_data = await engine['carts'].find_one({
        "user_id": message.from_user.id,
        "closed": False
    })
    if not cart_data:
        return await message.answer("Ваша корзина пуста")

    cart = Cart(**cart_data)
    await build_cart_data(cart, message)


@router.callback_query(F.data.startswith("product:add_to_cart"))
async def add_to_cart(query: types.CallbackQuery, state: FSMContext):
    product_id = query.data.split(":")[2]
    await state.update_data(product_id=product_id)
    await state.set_state(ProductAddToCartState.count)

    builder = KeyboardBuilder(button_type=button)
    builder.add(*[
        button(text=str(number), callback_data=f"product:add_to_cart_count:{number}")
        for number in range(1, 11)
    ], button(text="Отмена", callback_data="product:cart_cancel"))
    builder.adjust(3, 3, 3, 2)
    markup = InlineKeyboardMarkup(inline_keyboard=builder.export())

    await query.message.answer("Введите количество товара", reply_markup=markup)
    await query.answer()


@router.callback_query(F.data.startswith("product:cart_cancel"))
async def add_to_cart_cancel(query: Union[types.CallbackQuery, types.Message], state: FSMContext):
    await state.clear()
    await query.answer("Выбор отменен", reply_markup=main_menu)
    await query.message.delete()


@router.callback_query(F.data.startswith("product:remove_from_cart"))
async def remove_from_cart(query: types.CallbackQuery):
    product_id, cart_id = query.data.split(":")[2:]
    cart_data = await engine['carts'].find_one({
        "id": str(cart_id)
    })
    cart = Cart(**cart_data)
    for i, p in enumerate(cart.products):
        if int(p.product_id) == int(product_id):
            del cart.products[i]
            break

    cart.total_amount = sum([p.total_price for p in cart.products])
    if not cart.products:
        cart.closed = True
        await query.message.answer("Ваша корзина пуста")
    else:
        await build_cart_data(cart, query.message)

    await cart.save()
    await query.answer("Товар удален из корзины")
    await query.message.delete()


@router.callback_query(F.data == "cart:clear")
async def clear_cart(query: types.CallbackQuery):
    cart_data = await engine['carts'].find_one({
        "user_id": query.from_user.id,
        "closed": False
    })
    if not cart_data:
        await query.answer("Ваша корзина пуста")
    else:
        await engine['carts'].delete_one({
            "id": cart_data['id']
        })
    await query.answer("Корзина очищена")
    await query.message.delete()


@router.callback_query(F.data == "cart:checkout")
async def checkout_cart(query: types.CallbackQuery, state: FSMContext):
    cart_data = await engine['carts'].find_one({
        "user_id": query.from_user.id,
        "closed": False
    })
    if not cart_data:
        return await query.answer("Ваша корзина пуста")

    await state.update_data(cart_id=cart_data['id'])
    await query.message.answer("Оставьте комментарии к заказу", reply_markup=ReplyKeyboardRemove())
    await query.answer()
    await state.set_state(CheckoutState.comments)


# @router.message(F.text, CheckoutState.address)
# async def checkout_address(message: types.Message, state: FSMContext):
#     await state.update_data(address=message.text)
#     await engine['users'].update_one({
#         "id": message.from_user.id
#     }, {
#         "$set": {
#             "address": message.text
#         }
#     })
#
#     builder = KeyboardBuilder(button_type=KeyboardButton)
#     builder.add(KeyboardButton(text="Отправить номер телефона", request_contact=True))
#
#     await message.answer("Введите номер телефона", reply_markup=builder.as_markup(resize_keyboard=True))
#     await state.set_state(CheckoutState.phone)


# @router.message(F.contact, CheckoutState.phone)
# @router.message(F.text, CheckoutState.phone)
# async def checkout_phone(message: types.Message, state: FSMContext):
#     phone = message.text
#     if message.contact:
#         phone = message.contact.phone_number
#     await state.update_data(phone=phone)
#     await state.set_state(CheckoutState.comments)
#     await engine['users'].update_one({
#         "id": message.from_user.id
#     }, {
#         "$set": {
#             "phone": phone
#         }
#     })
#     await message.answer("Оставьте комментарии к заказу", reply_markup=ReplyKeyboardRemove())


@router.message(F.text, CheckoutState.comments)
async def checkout_comments(message: types.Message, state: FSMContext):
    await state.update_data(comments=message.text)
    await state.set_state(CheckoutState.payment_method)

    builder = KeyboardBuilder(button_type=KeyboardButton)
    builder.add(KeyboardButton(text="Bitcoin"))
    builder.add(KeyboardButton(text="Litecoin"))

    await message.answer("Выберите способ оплаты", reply_markup=builder.as_markup(resize_keyboard=True))


@router.message(F.text, CheckoutState.payment_method)
async def checkout_payment_method(message: types.Message, state: FSMContext, bot: Bot):
    if message.text not in ["Bitcoin", "Litecoin"]:
        return await message.answer("Пожалуйста выберите поддерживаемый способ оплаты")

    await state.update_data(payment_method=message.text)
    data = await state.get_data()
    cart_data = await engine['carts'].find_one({
        "id": data['cart_id']
    })
    if not cart_data:
        return await message.answer("Ваша корзина пуста", reply_markup=main_menu)

    wait_message = await message.answer("Класс! Ваш заказ принят в обработку. Через несколько секунд вы получите "
                                        "аддрес для оплаты.\n\nПожалуйста ждите....")

    # Creating order
    cart = Cart(**cart_data)
    order = Order(
        cart_id=cart.id,
        user_id=cart.user_id,
        user_comments=data['comments'],
    )
    await order.save()

    ticker = "btc" if message.text == "Bitcoin" else "ltc"
    cart.coin = ticker.upper()
    try:
        # generating unique address for payment.
        address_in = generate_payment_address(ticker, order.id)
    except Exception as e:
        await bot.send_message(os.getenv('SUPER_ADMIN_ID'),
                               f"Error while generating address for order {order.id}\n\n{e}")
        return await wait_message.edit_text("Произошла ошибка при создании адреса для оплаты. Мы уведомлены об этом "
                                            "и в скором времени исправим")

    # converting to crypto
    try:
        amount = convert_to_crypto(ticker, cart.total_amount)
        cart.total_coin_amount = amount
        await cart.save()
    except Exception as e:
        await bot.send_message(os.getenv('SUPER_ADMIN_ID'),
                               f"Error while converting to crypto for order {order.id}\n\n{e}")
        return await wait_message.edit_text("Произошла ошибка при конвертации в криптовалюту. Мы уведомлены об этом "
                                            "и в скором времени исправим")

    await wait_message.delete()
    await message.answer(f"Номер вашего заказа: <code>{order.id}</code>\n\n"
                         f"Пожалуйста отправьте <code>{amount}</code> {cart.coin} (${cart.total_amount}) на этот аддрес\n\n"
                         f"<code>{address_in}</code>\n\n"
                         f"После успешной оплаты, вы получите уведомление и мы отправим ваш заказ.\n"
                         f"Спасибо за покупку!",
                         reply_markup=main_menu)
    cart.closed = True
    await cart.save()


def convert_to_crypto(ticker, amount):

    url = "https://api.blockbee.io/" + ticker + "/convert/"

    query = {
        "apikey": os.getenv('BLOCKBEE_API_KEY'),
        "value": amount,
        "from": "usd"
    }

    response = requests.get(url, params=query)

    if response.status_code != 200:
        raise ValueError(response.text)

    response = response.json()

    return response['value_coin']


def generate_payment_address(ticker, order_id):
    url = "https://api.blockbee.io/" + ticker + "/create/"

    query = {
        "apikey": os.getenv('BLOCKBEE_API_KEY'),
        "callback": f"{settings.SERVER_HOST}api/events/payment?order={order_id}",
        "post": "1",
        "convert": "1"
    }

    # Example response {'status': 'success', 'address_in': GENERATED_ADDRESS',
    # 'address_out': 'YOUR_BTC_ADDRESS', 'callback_url':f"{settings.SERVER_HOST}/api/events/payment?order",
    # 'minimum_transaction_coin': '0.00008000', 'priority': 'default'}
    response = requests.get(url, params=query)

    if response.status_code != 200:
        raise ValueError(response.text)

    address_response = response.json()
    return address_response['address_in']
