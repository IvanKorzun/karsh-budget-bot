import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReactionTypeEmoji
import database as db

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 1893245583  # Твой ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище в оперативной памяти
poll_results = {}  # {user_id: {"name": "First Name", "username": "username"}}
current_crew = {}  # {admin_id: ["Имя1", "Имя2"]}


def is_admin(user_id: int):
    return user_id == ADMIN_ID


async def set_reaction(message: types.Message, emoji: str):
    try:
        await message.react([ReactionTypeEmoji(emoji=emoji)])
    except:
        pass


def clean_uname(uname: str):
    if not uname: return ""
    return uname.replace("@", "").strip().lower()


# --- СТАТУС ---
@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    await set_reaction(message, "🔥")
    users = db.get_all_users()
    text = "БУХАЛ ТЕР ПАБЛИКА \"КАРШУЮДЛЯДУШИ\" 🟢\n📊 <b>Балансы:</b>\n───────────────────\n"
    for name, tg, bal in users:
        emoji = "🟢" if bal >= 0 else "🔴" if bal <= -2.6 else "⚪"
        text += f"{emoji} <b>{name}</b>: {bal:.2f} BYN" + (" (до 2.6 можно не платить)" if emoji == "⚪" else "") + "\n"
    await message.answer(text, parse_mode="HTML")


# --- ОПРОС ---
def get_poll_text():
    going = [v["name"] for v in poll_results.values()]
    return f"🚗 <b>Сборы на катку!</b>\n\n✅ <b>Едут:</b> " + (", ".join(going) if going else "...")


@dp.message(Command("poll"))
async def cmd_poll(message: types.Message):
    if not is_admin(message.from_user.id):
        await set_reaction(message, "🤡");
        return
    poll_results.clear()
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Еду", callback_data="poll_going")
    builder.button(text="❌ Не еду", callback_data="poll_not_going")
    await message.answer(get_poll_text(), reply_markup=builder.as_markup(), parse_mode="HTML")


@dp.callback_query(F.data.startswith("poll_"))
async def handle_poll(callback: types.CallbackQuery):
    u_id, u_un, u_n = callback.from_user.id, clean_uname(callback.from_user.username), callback.from_user.first_name
    if u_id == ADMIN_ID and callback.data == "poll_going":
        return await callback.answer("Ты водитель!", show_alert=True)
    if callback.data == "poll_not_going":
        poll_results.pop(u_id, None)
        await callback.answer("Ты лошпедиус! 🤡", show_alert=True)
    else:
        poll_results[u_id] = {"name": u_n, "username": u_un}
        await callback.answer("Записал!")
    try:
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Еду", callback_data="poll_going")
        builder.button(text="❌ Не еду", callback_data="poll_not_going")
        await callback.message.edit_text(get_poll_text(), reply_markup=builder.as_markup(), parse_mode="HTML")
    except:
        pass


# --- ЭКИПАЖ ---
def get_crew_keyboard(selected_names):
    builder = InlineKeyboardBuilder()
    db_users = db.get_all_users()
    db_names = [u[0] for u in db_users]
    db_unames_map = {clean_uname(u[1]): u[0] for u in db_users if u[1]}
    for name, uname, bal in db_users:
        prefix = "✅ " if name in selected_names else "⬜ "
        builder.button(text=f"{prefix}{name}", callback_data=f"crew_{name}")
    for val in poll_results.values():
        v_un, v_n = clean_uname(val["username"]), val["name"]
        if v_un not in db_unames_map and v_n not in db_names:
            builder.button(text=f"➕ Регнуть {v_n}", callback_data=f"hreg_{v_n}")
    builder.button(text="🔄 Обновить", callback_data="refresh_crew")
    builder.button(text="🚀 ПОЕХАЛИ!", callback_data="start_drive")
    builder.button(text="❌ ОТМЕНА", callback_data="cancel_trip")
    builder.adjust(2)
    return builder.as_markup()


@dp.message(Command("start_trip"))
async def cmd_start_trip(message: types.Message):
    if not is_admin(message.from_user.id):
        await set_reaction(message, "🤡");
        return
    db_users = db.get_all_users()
    db_unames_map = {clean_uname(u[1]): u[0] for u in db_users if u[1]}
    db_names = [u[0] for u in db_users]
    auto_selected = []
    for val in poll_results.values():
        v_un, v_n = clean_uname(val["username"]), val["name"]
        if v_un in db_unames_map:
            auto_selected.append(db_unames_map[v_un])
        elif v_n in db_names:
            auto_selected.append(v_n)
    current_crew[message.from_user.id] = list(set(auto_selected))
    await message.answer("🛠 <b>Сбор экипажа:</b>", reply_markup=get_crew_keyboard(auto_selected), parse_mode="HTML")


@dp.callback_query(F.data == "refresh_crew")
async def refresh_crew(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    selected = current_crew.get(callback.from_user.id, [])
    await callback.message.edit_reply_markup(reply_markup=get_crew_keyboard(selected))
    await callback.answer("Список обновлен!")


@dp.callback_query(F.data.startswith("crew_"))
async def handle_toggle(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return await callback.answer("Только для водителя!", show_alert=True)
    name, sel = callback.data.replace("crew_", ""), current_crew.get(callback.from_user.id, [])
    if name in sel:
        sel.remove(name)
    else:
        sel.append(name)
    current_crew[callback.from_user.id] = sel
    await callback.message.edit_reply_markup(reply_markup=get_crew_keyboard(sel))
    await callback.answer()


@dp.callback_query(F.data == "start_drive")
async def handle_drive(callback: types.CallbackQuery):
    sel = current_crew.get(callback.from_user.id, [])
    if not sel: return await callback.answer("Выбери людей!", show_alert=True)
    await callback.message.edit_text(f"🛣 <b>Поехали!</b>\nЭкипаж: {', '.join(sel)}\n\nЖду /end [сумма]",
                                     parse_mode="HTML")


# --- КОНЕЦ ПОЕЗДКИ ---
@dp.message(Command("end"))
async def cmd_end(message: types.Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        await set_reaction(message, "🤡");
        return

    sel = current_crew.get(message.from_user.id)
    if not sel:
        await message.reply("⚠️ <b>Нет активной поездки!</b>\nНажми 'ПОЕХАЛИ' в меню /start_trip", parse_mode="HTML")
        return

    # Получаем аргументы команды /end сумма
    if not command.args:
        await message.reply("⚠️ <b>Введи сумму!</b>\nПример: <code>/end 4.45</code>", parse_mode="HTML")
        return

    try:
        # Убираем пробелы, меняем запятую на точку
        raw_sum = command.args.strip().replace(',', '.')
        total = float(raw_sum)

        # Считаем на всех (водитель + пассажиры)
        count = len(sel) + 1
        share = round(total / count, 2)

        for name in sel:
            db.update_balance(name, -share)

        await message.answer(f"💰 Сумма: {total:.2f} BYN\n💳 С каждого (на {count} чел.): <b>{share:.2f} BYN</b>",
                             parse_mode="HTML")

        # Очистка памяти
        current_crew.pop(message.from_user.id, None)
        poll_results.clear()

    except ValueError:
        await message.reply("❌ <b>Ошибка!</b>\nСумма должна быть числом (например, 4.45)", parse_mode="HTML")


# --- ОСТАЛЬНЫЕ КОМАНДЫ ---
@dp.message(Command("reg"))
async def cmd_reg(message: types.Message):
    if not is_admin(message.from_user.id):
        await set_reaction(message, "🤡");
        return
    args = message.text.split()
    if len(args) < 2: return
    new_n, ref_u = args[1], clean_uname(args[2]) if len(args) > 2 else clean_uname(args[1])
    db.add_or_update_user(new_n, ref_u)
    if message.from_user.id in current_crew:
        if new_n not in current_crew[message.from_user.id]: current_crew[message.from_user.id].append(new_n)
    await message.answer(f"✅ {new_n} готов!")


@dp.message(Command("pay"))
async def cmd_pay(message: types.Message):
    if not is_admin(message.from_user.id):
        await set_reaction(message, "🤡");
        return
    try:
        args = message.text.split()
        val = float(args[2].replace(',', '.'))
        db.update_balance(args[1], val)
        await message.answer(f"✅ {args[1]}: +{val:.2f} BYN")
    except:
        await message.reply("Формат: /pay Имя 10.5")


@dp.message(Command("db"))
async def cmd_db(message: types.Message):
    if not is_admin(message.from_user.id):
        await set_reaction(message, "🤡");
        return
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Добавить", callback_data="db_add");
    builder.button(text="➖ Удалить типа", callback_data="db_del");
    builder.button(text="📋 Список", callback_data="db_list")
    builder.adjust(1);
    await message.answer("🛠 <b>База данных</b>", reply_markup=builder.as_markup())


@dp.callback_query(F.data == "db_list")
async def db_list(callback: types.CallbackQuery):
    u = db.get_all_users()
    await callback.message.answer("📋 <b>В базе:</b>\n" + "\n".join([f"• {x[0]}" for x in u]));
    await callback.answer()


@dp.callback_query(F.data == "db_del")
async def db_del(callback: types.CallbackQuery):
    u = db.get_all_users()
    builder = InlineKeyboardBuilder()
    for n, un, b in u: builder.button(text=f"❌ {n}", callback_data=f"db_confirm_{n}")
    builder.button(text="⬅ Назад", callback_data="db_back")
    builder.adjust(2);
    await callback.message.edit_text("Кого удалить?", reply_markup=builder.as_markup())


@dp.callback_query(F.data.startswith("db_confirm_"))
async def db_confirm(callback: types.CallbackQuery):
    n = callback.data.replace("db_confirm_", "")
    db.delete_user(n);
    await callback.answer(f"Удален: {n}", show_alert=True);
    await db_del(callback)


@dp.callback_query(F.data == "db_back")
async def db_back(callback: types.CallbackQuery):
    await cmd_db(callback.message);
    await callback.answer()


@dp.callback_query(F.data == "cancel_trip")
async def cancel_trip(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id): return
    current_crew.pop(callback.from_user.id, None);
    await callback.message.edit_text("🚫 Отменено.");
    await callback.answer()


async def main():
    db.init_db();
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())