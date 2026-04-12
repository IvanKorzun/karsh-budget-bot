import database as db

users_to_import = [
    ("Полина", "@No_polyaa", 0.00),
    ("Санек", "@SashaKorotkevich", 19.39),
    ("Стас", "@kawun", -14.98),
    ("Кирилл", "@XLordPlay", 6.39),
    ("Тимофей", "@Makkensie671games3", -1.51)
]

def run_import():
    db.init_db()
    for name, tg, bal in users_to_import:
        db.add_or_update_user(name, tg, bal)
    print("✅ Все пользователи успешно внесены в базу!")

if __name__ == "__main__":
    run_import()