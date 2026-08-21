from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import os

router = Router()

def game_url():
    base = os.environ.get("MP_PUBLIC_URL", "").rstrip("/")
    if not base and os.path.exists("/tmp/bw_public_url.txt"):
        try:
            base = open("/tmp/bw_public_url.txt").read().strip()
        except Exception:
            base = ""
    return f"{base}/sp" if base else ""

@router.message(Command("game", "rts", "play"))
async def cmd_game(message: Message):
    url = game_url()
    if not url:
        await message.answer("Игра временно недоступна. Попробуй /start")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Открыть Biome World", url=url)]
    ])
    await message.answer(
        "🌍 <b>Biome World</b> — RTS\n\nНажми кнопку ниже.",
        reply_markup=kb,
        parse_mode="HTML",
    )
