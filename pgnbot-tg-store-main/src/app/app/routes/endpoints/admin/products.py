from aiogram import Router, Bot, F
from aiogram import types
from aiogram.fsm.state import StatesGroup, State

from app.db.mongodb import engine
from app.markups.reply import main_menu, admin_menu
from aiogram.fsm.context import FSMContext

from app.models import User
from app.models.inventory import Inventory
from app.models.product import Product
from app.middlewares import AdminMiddleware

router = Router()
router.message.middleware(AdminMiddleware())
router.callback_query.middleware(AdminMiddleware())


class AddProduct(StatesGroup):
    start = State()
    name = State()
    price = State()
    description = State()
    photo = State()
    complete = State()
    quantity = State()


class AddInventory(StatesGroup):
    start = State()
    product_id = State()
    value = State()
    complete = State()


@router.message(F.text == '➕ Добавить инвентарь')
async def add_inventory(msg: types.Message, state: FSMContext):
    await state.set_state(AddInventory.start)
    await msg.answer('Выберите ID продукта', reply_markup=types.ReplyKeyboardRemove())
    products = await engine['products'].find({'is_active': True}).to_list(length=1000)

    if not products:
        await msg.answer('Нет активных продуктов')
        return

    product_list = ""
    for product in products:
        product_list += f"{product['name']} - `{product['id']}`\n"

    await msg.answer(product_list)


@router.message(AddInventory.start)
async def add_inventory_product_id(msg: types.Message, state: FSMContext):
    await state.update_data(product_id=msg.text)
    await state.set_state(AddInventory.value)
    await msg.answer('Введите значение инвентаря каждое с новой строки')


@router.message(AddInventory.value)
async def add_inventory_value(msg: types.Message, state: FSMContext):
    await state.update_data(value=msg.text)
    data = await state.get_data()
    product = await engine['products'].find_one({'id': data['product_id']})
    inventories = []
    for idx, inv in enumerate(data['value'].split('\n')):
        inventory = Inventory(product_id=product['id'], value=inv).model_dump()
        inventories.append(inventory)

    await engine['inventory'].insert_many(inventories)
    await state.clear()
    await msg.answer(f'Инвентарь успешно добавлен {len(inventories)} шт.',
                     reply_markup=admin_menu)


@router.message(F.text == '➕ Добавить товар')
async def add_product(msg: types.Message, state: FSMContext):
    await state.set_state(AddProduct.start)
    await msg.answer('Введите название товара', reply_markup=types.ReplyKeyboardRemove())


@router.message(AddProduct.start)
async def add_product_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await state.set_state(AddProduct.price)
    await msg.answer('Введите цену товара')


@router.message(AddProduct.price)
async def add_product_name(msg: types.Message, state: FSMContext):
    await state.update_data(price=msg.text)
    await state.set_state(AddProduct.quantity)
    await msg.answer('Введите количество товара')


@router.message(AddProduct.quantity)
async def add_product_price(msg: types.Message, state: FSMContext):
    await state.update_data(quantity=msg.text)
    await state.set_state(AddProduct.description)
    await msg.answer('Введите описание товара')


@router.message(AddProduct.description)
async def add_product_description(msg: types.Message, state: FSMContext):
    await state.update_data(description=msg.text)
    await state.set_state(AddProduct.photo)
    await msg.answer('Отправьте фото товара')


@router.message(AddProduct.photo, F.photo)
async def add_product_photo(msg: types.Message, state: FSMContext, bot: Bot, user: User):
    data = await state.get_data()
    try:
        product = Product(**data)
        product.file = await bot.get_file(msg.photo[0].file_id)
        product.photo = f'/files/products/{product.id}' + '-' + product.file.file_path.split('/')[-1]

        await product.save()
        await bot.download_file(product.file.file_path, destination=product.photo)
        await state.clear()
        await msg.answer(f'Товар успешно добавлен ID={product.id}', reply_markup=admin_menu)
    except Exception as e:
        await msg.answer(f'Ошибка: {e}')
