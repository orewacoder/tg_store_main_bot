import os

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from app.bot import bot, dp, setup
from aiogram.types import Update
from app.db.mongodb import engine
from app.models import User
from app.models.order import Order, Cart
from app.models.payment import Payment
from app.models.payment_callback import PaymentCallback
from app.utils.verify_callback import callback_handler

app = FastAPI(openapi_url="/api/v1/openapi.json")


@app.on_event('startup')
async def on_startup():
    await setup(bot)


@app.on_event('shutdown')
async def shutdown():
    await bot.session.close()


@app.post("/api/events/telegram-webhook")
async def handle_webhook(update: dict):
    u = Update(**update)
    return await dp.feed_update(bot=bot, update=u)


async def handle_payment(order, data):
    payment_cb = PaymentCallback(**data)
    order_data = await engine['orders'].find_one({'id': order})

    if not order_data:
        await bot.send_message(os.getenv('SUPER_ADMIN_ID'), f'Получили оплату за не найденный заказ {order}')
        return '*ok*'

    order = Order(**order_data)
    cart_data = await engine['carts'].find_one({'id': order.cart_id})
    if not cart_data:
        await bot.send_message(os.getenv('SUPER_ADMIN_ID'),
                               f'Получили оплату за заказ {order.id}, но не найдена корзина {order.cart_id}')
        return '*ok*'

    cart = Cart(**cart_data)

    payment = Payment(
        user_id=order.user_id,
        order_id=order.id,
        amount=float(payment_cb.value_coin_convert.get('USD', 0.0)),
        coin_amount=payment_cb.value_coin,
        status='confirmed',
        data=data,
    )
    await payment.save()
    order.paid_amount += payment.amount
    order.paid_coin_amount += payment_cb.value_coin

    user_data = await engine['users'].find_one({'id': order.user_id})
    user = User(**user_data)
    user.total_orders += 1
    user.total_orders_amount += payment.amount
    await user.save()

    if order.paid_coin_amount < cart.total_coin_amount:
        order.payment_status = False
        order.status = 'paid_partially'
        amount_less = (f'Получили оплату за заказ {order.id}, но сумма меньше чем стоимость заказа\n\n'
                       f'Полученная сумма: {payment_cb.value_coin}, стоимость заказа: {cart.total_coin_amount}')
        await bot.send_message(os.getenv('SUPER_ADMIN_ID'), f"{amount_less}\n\nID пользователя: {order.user_id}")
        await bot.send_message(order.user_id, amount_less)
    else:
        order.payment_status = True
        order.status = 'paid'

        ordered_products = '\n'.join([f'<b>{p.name}</b> - {p.quantity} шт.' for p in cart.products])
        # product_ids = [p.product_id for p in cart.products]

        await bot.send_message(
            os.getenv('SUPER_ADMIN_ID'),
            f'Получили оплату за заказ <code>{order.id}</code>\n\n'
            f'ID пользователя: <code>{order.user_id}</code>\n'
            f'Сумма: {payment_cb.value_coin} {payment_cb.coin.upper()}\n'
            f'Аддрес доставки: {user.address}\n'
            f'Телефон: {user.phone}\n\n'
            f'Товары:\n{ordered_products}\n\n'
            f'Комментарии к заказу:\n<i>{order.user_comments}</i>\n\n'
            f'Общая сумма: ${cart.total_amount}\n'
            f'Сумма после конвертации: ${payment.amount}\n'
        )

        values = ""
        for product in cart.products:
            values += f"{product.name} - {product.quantity} шт.\n"
            inventories = await engine['inventory'].find({'product_id': product.product_id, "sold_at": None}).to_list(product.quantity)
            if not inventories:
                await bot.send_message(os.getenv('SUPER_ADMIN_ID'), f'Не найдено товара {product.name} в количестве {product.quantity}\n\n'
                                                                    f'ID пользователя: {order.user_id}, ID заказа: {order.id}')
                continue

            for idx, inventory in enumerate(inventories):
                inventory['sold_at'] = order.date
                inventory['buyer'] = user.id
                await engine['inventory'].update_one({'id': inventory['id']}, {'$set': inventory})
                values += f"{idx+1}. <code>{inventory['value']}</code>\n"
        await bot.send_message(order.user_id, f'Ваш заказ {order.id} оплачен. Вот ваши заказы.\n\n'
                                              f'{values}\n\n'
                                              f'Спасибо за покупку!')

    await order.save()


@app.post('/api/events/telegram-payment')
async def handle_payment_confirmation(order: str, request: Request, background_tasks: BackgroundTasks):
    fake_payment = {
        "uuid": "f9b0b0f0-5b1a-11eb-9c3a-0242ac110002",
        "value_coin_convert": {
            "USD": 1000
        },
        "value_coin": 1,
        "coin": "BTC",
    }
    background_tasks.add_task(handle_payment, order, fake_payment)


@app.post("/api/events/payment")
@app.post("//api/events/payment")
async def handle_payment_confirmation(order: str, request: Request, background_tasks: BackgroundTasks):
    data_bytes = await request.body()
    signature = request.headers.get('x-ca-signature')
    if not signature:
        raise HTTPException(status_code=400, detail='Missing signature')
    valid = callback_handler(signature, data_bytes)
    if not valid:
        raise HTTPException(status_code=400, detail='Invalid signature')

    data = dict(await request.form())

    background_tasks.add_task(handle_payment, order, data)
    return '*ok*'
