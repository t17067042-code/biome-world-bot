from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from db.database import db
from game.engine import apply_offline_progress, format_main_status
from keyboards.inline import main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    player = await db.get_player(user.id)

    if not player:
        player = await db.create_player(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
        )
        text = (
            "🏕 <b>Добро пожаловать в Поселение: Граница!</b>\n\n"
            "Вы основали небольшое поселение на краю неизведанных земель.\n"
            "Собирайте ресурсы, стройте здания, нанимайте жителей и воинов.\n\n"
            "Удачи, вождь!"
        )
    else:
        progress = await apply_offline_progress(user.id)
        player = await db.get_player(user.id)
        buildings = await db.get_buildings(user.id)
        text = format_main_status(player, buildings)
        if progress.get("hours", 0) > 0.05:
            gained = progress.get("gained", {})
            if gained:
                gains = ", ".join(f"+{v} {k}" for k, v in gained.items() if v != 0)
                text += f"\n\n⏱ За {progress['hours']} ч: {gains}"

    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.message(Command("status"))
async def cmd_status(message: Message):
    user_id = message.from_user.id
    await apply_offline_progress(user_id)
    player = await db.get_player(user_id)
    if not player:
        await message.answer("Сначала нажмите /start")
        return
    buildings = await db.get_buildings(user_id)
    text = format_main_status(player, buildings)
    await message.answer(text, reply_markup=main_menu_kb(), parse_mode="HTML")
