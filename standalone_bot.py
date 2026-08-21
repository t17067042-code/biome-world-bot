"""Standalone settlement bot + static game server for Railway."""
import asyncio, logging, os, sys, time, urllib.request
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stdout)
log = logging.getLogger("bot")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PORT = int(os.environ.get("PORT", "8080"))
PUBLIC = os.environ.get("MP_PUBLIC_URL", "").rstrip("/")
DB_PATH = os.environ.get("DATABASE_PATH", "data/game.db")
GAME_URL = os.environ.get("GAME_HTML_URL", "")

def ensure_game():
    sp = Path(__file__).parent / "static_game.html"
    if sp.exists() and sp.stat().st_size > 1000:
        return sp
    if not GAME_URL:
        return None
    try:
        log.info("Downloading game from %s", GAME_URL)
        urllib.request.urlretrieve(GAME_URL, sp)
        log.info("Game saved %s bytes", sp.stat().st_size)
        return sp
    except Exception as e:
        log.exception("game download failed: %s", e)
        return None

async def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN required")
    Path("data").mkdir(exist_ok=True)
    game_path = ensure_game()

    import aiosqlite
    from aiohttp import web
    from aiogram import Bot, Dispatcher, F, Router
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from aiogram.filters import CommandStart, Command
    from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.fsm.storage.memory import MemoryStorage

    async def db_init():
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
                food REAL DEFAULT 100, wood REAL DEFAULT 50, stone REAL DEFAULT 30, gold REAL DEFAULT 20,
                population INTEGER DEFAULT 5, max_population INTEGER DEFAULT 10, army INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1, exp INTEGER DEFAULT 0, last_active REAL
            )""")
            await db.commit()

    async def get_player(uid):
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM players WHERE user_id=?", (uid,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def create_player(uid, username, first_name):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR IGNORE INTO players (user_id, username, first_name, last_active) VALUES (?,?,?,?)",
                (uid, username, first_name, time.time()))
            await db.commit()
        return await get_player(uid)

    def kb_main():
        rows = [[InlineKeyboardButton(text="📊 Статус", callback_data="status")]]
        if PUBLIC:
            rows.append([InlineKeyboardButton(text="🎮 Biome World", url=f"{PUBLIC}/sp")])
        return InlineKeyboardMarkup(inline_keyboard=rows)

    def fmt(p):
        return (f"🏕 <b>Поселение</b>\n⭐ Ур.{p['level']}\n"
                f"👥 {p['population']}/{p['max_population']}  ⚔ {p['army']}\n"
                f"🍖 {int(p['food'])} 🪵 {int(p['wood'])} 🪨 {int(p['stone'])} 💰 {int(p['gold'])}")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    r = Router()

    @r.message(CommandStart())
    async def start(m: Message):
        p = await get_player(m.from_user.id)
        if not p:
            await create_player(m.from_user.id, m.from_user.username, m.from_user.first_name)
            await m.answer("🏕 Добро пожаловать в Поселение: Граница!\n/game — RTS Biome World", reply_markup=kb_main())
        else:
            await m.answer(fmt(p), reply_markup=kb_main())

    @r.message(Command("game", "rts", "play"))
    async def game(m: Message):
        if not PUBLIC:
            await m.answer("Поставь MP_PUBLIC_URL в Railway Variables"); return
        url = f"{PUBLIC}/sp"
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎮 Открыть Biome World", url=url)]])
        await m.answer("🌍 Biome World — одиночная RTS", reply_markup=kb)

    @r.callback_query(F.data == "status")
    async def st(c: CallbackQuery):
        p = await get_player(c.from_user.id)
        if not p:
            await c.answer("Сначала /start", show_alert=True); return
        try: await c.message.edit_text(fmt(p), reply_markup=kb_main())
        except Exception: pass
        try: await c.answer()
        except Exception: pass

    @r.callback_query()
    async def any_cb(c: CallbackQuery):
        try: await c.answer()
        except Exception: pass

    dp.include_router(r)
    await db_init()

    async def health(_):
        return web.json_response({"ok": True, "game": bool(game_path and Path(game_path).exists())})

    app = web.Application()
    app.router.add_get("/health", health)
    sp = Path(__file__).parent / "static_game.html"
    if sp.exists():
        app.router.add_get("/sp", lambda r: web.FileResponse(sp))
        app.router.add_get("/", lambda r: web.FileResponse(sp))
    else:
        async def no_game(_):
            return web.Response(text="Game file missing. Upload static_game.html to the repo or set GAME_HTML_URL.", status=404)
        app.router.add_get("/sp", no_game)

    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", PORT).start()
    log.info("HTTP :%s game=%s", PORT, bool(sp.exists()))

    me = await bot.get_me()
    log.info("Bot @%s public=%s", me.username, PUBLIC)
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
