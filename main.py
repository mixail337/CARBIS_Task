import sqlite3
from dadata import Dadata


# Класс, который реализует приложение
class MainApp:
    # Функция для создания локальной базы данных на движке sqlite3
    def db_set(self):
        conn = sqlite3.connect('settings.db')
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS settings")
        cur.execute("""CREATE TABLE settings(
            id INT PRIMARY KEY,
            base_url TEXT,
            api_key TEXT,
            lang TEXT,
            secret TEXT);
        """)
        conn.commit()
        cur.execute("""INSERT OR REPLACE INTO settings(id,base_url,api_key,lang,secret)
            VALUES (1,'https://suggestions.dadata.ru/suggestions/api/4_1/rs','f4519aef4a7ae0eb404ebe3fdd7302390060a3b9'
            ,'ru','e40cca88cd34e8ff0948b2859d3c3e81686cf943')""")
        conn.commit()

        # Создание виртуальной таблицы для хранения настроек по умолчанию
        cur.execute("DROP TABLE IF EXISTS settings_default")
        cur.execute("CREATE VIRTUAL TABLE settings_default USING fts5(id,base_url,api_key,lang)")
        cur.execute("INSERT INTO settings_default (id,base_url,api_key,lang) VALUES(1,(SELECT base_url FROM settings),"
                    "(SELECT api_key FROM settings),(SELECT lang FROM settings))")
        conn.commit()
        conn.close()

    # Функция для загрузки параметров приложения из локальной базы данных
    def db_get(self):
        conn = sqlite3.connect('settings.db')
        cur = conn.cursor()
        try:
            cur.execute("SELECT api_key,base_url,lang,secret FROM settings")
            tok = cur.fetchall()
            token = tok[0][0]
            url = tok[0][1]
            language = tok[0][2]
            secret = tok[0][3]
            conn.close()
            return token ,url, language, secret
        except Exception as e:
            print(e)

    # Функция, реализующая интерфейс приложения
    def ui(self):
        self.db_set()
        while True:
            print("1. Начать\n2. Настройки\n3. Выход")
            state = input()
            if state == '1':
                self.state1()
            if state == '2':
                self.state2()
            if state == '3':
                break

    # Функция работы API Dadata для поиска координат адреса
    def state1(self):
        data = self.db_get()
        # Подключение API Dadata
        dadata = Dadata(token=data[0], secret=data[3])
        dadata.api_url = data[1]
        while True:
            print("Введите искомый адрес (например Новосибирск Ленина 6):")
            addr = input()
            try:
                # Использование подсказок из API Dadata для вывода вариантов поиска
                res = dadata.suggest("address", addr, 20, language=data[2])
                lst = []
                for r in res:
                    lst.append(r['value'])
            except Exception as e:
                print(e)
                self.state2()
                return
            print("Выберите номер искомого адреса из списка:")
            for i, val in enumerate(lst):
                print("{0}. {1}".format(i + 1, val))
            num = input()
            # Использование поиска координат искомого адреса
            result = dadata.clean(name="address", source=res[int(num) - 1]['value'])
            print("Координаты искомого адреса:", result['geo_lat'], result['geo_lon'])
            print("1. Продолжить поиск\n2. Выйти в меню")
            st = input()
            if st == '2':
                dadata.close()
                break

    # Функция, которая реализует раздел настроек приложения
    def state2(self):
        conn = sqlite3.connect('settings.db')
        cur = conn.cursor()
        while True:
            cur.execute("SELECT base_url,api_key,lang FROM settings")
            sets = cur.fetchall()
            print("Параметры приложения:\n1.Базовый URL:{0}\n2.API-ключ:{1}\n3.Язык ответа на запрос:{2}\n4.Изменить\n"
                  "5.Вернуть настройки по умолчанию\n6.Выход в меню".format(sets[0][0], sets[0][1], sets[0][2]))
            state = input()
            if state == '4':
                print("Введите номер параметра, который хотите изменить")
                par = input()
                if par == '1':
                    print("Базовый URL:{0}\nВведите новый базовый URL:".format(sets[0][0]))
                    url = input()
                    try:
                        cur.execute("UPDATE settings SET base_url = ? WHERE id = ?", (url, 1))
                        conn.commit()
                    except Exception as e:
                        print(e)
                        conn.rollback()
                if par == '2':
                    print("API-ключ:{0}\nВведите новый API-ключ:".format(sets[0][1]))
                    key = input()
                    try:
                        cur.execute("UPDATE settings SET api_key = ? WHERE id = ?", (key, 1))
                        conn.commit()
                    except Exception as e:
                        print(e)
                        conn.rollback()
                if par == '3':
                    print("Язык ответа на запрос:{0}\nВведите номер языка ответа на запрос\n1.ru\n2.en".format(
                        sets[0][2]))
                    lang = input()
                    if lang == '1':
                        lang = 'ru'
                    if lang == '2':
                        lang = 'en'
                    try:
                        cur.execute("UPDATE settings SET lang = ? WHERE id = ?", (lang, 1))
                        conn.commit()
                    except Exception as e:
                        print(e)
                        conn.rollback()
            if state == '5':
                try:
                    cur.execute("UPDATE settings SET base_url = settings_default.base_url, "
                                "api_key = settings_default.api_key,"
                                "lang = settings_default.lang FROM settings_default")
                    conn.commit()
                except Exception as e:
                    print(e)
                    conn.rollback()
            if state == '6':
                conn.close()
                return

# Запуск приложения
if __name__ == '__main__':
    App = MainApp()
    App.ui()
