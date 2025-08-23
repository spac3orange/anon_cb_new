from aiogram import Router
from aiogram.filters import Command
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, FSInputFile, CallbackQuery, InputMediaPhoto
from app.keyboards import main_kb
from app.utils import with_session
from app.database import crud
from app.states import user_states

router = Router()


@router.message(Command(commands='start'))
@with_session
async def start(message: Message, session):
    uid = message.from_user.id
    username = message.from_user.username
    await crud.add_user(session, user_id=uid, username=username)
    await message.answer('Добро пожаловать!',
                         reply_markup=main_kb.main_menu())


# Поиск собеседника
@router.callback_query(F.text == '🔍 Поиск собеседника')
@with_session
async def search_companion(call: CallbackQuery, state, session):
    uid = call.from_user.id
    uname = call.from_user.username

    # Обновляем или добавляем пользователя
    user = await crud.add_user(session, uid, uname)

    # Ставим пользователя в состояние поиска
    await crud.set_user_state(session, uid, "Searching")

    # Ищем свободного пользователя
    partner = await crud.find_searching_user(session, exclude_user_id=uid)

    if partner:
        # Создаём диалог
        dialog = await crud.create_dialog(session, user, partner)

        # Сообщаем обоим
        await call.message.answer("🎉 Собеседник найден! Можете начинать общение.")
        await call.bot.send_message(partner.user_id, "🎉 Вам найден собеседник! Можете начинать общение.")

    else:
        await call.message.answer("⏳ Собеседник не найден, ждём подключения...")

    # FSM для кнопок
    await state.set_state(user_states.StartDialog.dialog_data)


# Переписка через БД
@router.message(F.text)
@with_session
async def relay_message(message: Message, state, session):
    uid = message.from_user.id

    # Узнаем, есть ли у пользователя активный диалог
    companion_id = await crud.get_companion_id(session, uid)

    if not companion_id:
        await message.answer("❗ Сейчас вы не находитесь в диалоге. Нажмите «🔍 Поиск собеседника».")
        return

    try:
        await message.bot.send_message(
            chat_id=companion_id,
            text=message.text
        )
    except Exception as e:
        await message.answer("⚠ Не удалось отправить сообщение собеседнику.")
        print(f"Ошибка отправки: {e}")



@router.callback_query(F.text == "❌ Завершить диалог")
@with_session
async def finish_dialog(call: CallbackQuery, session):
    uid = call.from_user.id

    companion_id = await crud.get_companion_id(session, uid)
    if not companion_id:
        await call.message.answer("❗ У вас нет активного диалога.")
        return

    success = await crud.end_dialog(session, uid)
    if success:
        # Уведомляем обоих участников
        await call.message.answer("✅ Диалог завершён.")
        try:
            await call.bot.send_message(companion_id, "✅ Ваш собеседник завершил диалог.")
        except Exception:
            pass
    else:
        await call.message.answer("⚠ Не удалось завершить диалог.")
