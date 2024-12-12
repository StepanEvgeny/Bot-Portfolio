from logic import DB_Manager  
from config import *  
from telebot import TeleBot  
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types  # Дополнительные типы, используемые в Telebot

bot = TeleBot(TOKEN)  
hideBoard = types.ReplyKeyboardRemove()  # Скрыть клавиатуру

cancel_button = "Отмена 🚫"

# Функция отмены действия
def cansel(message):
    bot.send_message(message.chat.id, "Чтобы посмотреть команды, используй - /info", reply_markup=hideBoard)

# Немаш проекта
def no_projects(message):
    bot.send_message(message.chat.id, 'У тебя пока нет проектов!\nМожешь добавить их с помощью команды /new_project')

# Генерация inline-клавиатуры
def gen_inline_markup(rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(row, callback_data=row))
    return markup

# обычная клава
def gen_markup(rows):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup

# Атрибуты проекта
attributes_of_projects = {
    'Имя проекта': ["Введите новое имя проекта", "project_name"],
    "Описание": ["Введите новое описание проекта", "description"],
    "Ссылка": ["Введите новую ссылку на проект", "url"],
    "Статус": ["Выберите новый статус задачи", "status_id"]
}

# информации о проекте
def info_project(message, user_id, project_name):
    info = manager.get_project_info(user_id, project_name)[0]
    skills = manager.get_project_skills(project_name)
    if not skills:
        skills = 'Навыки пока не добавлены'
    bot.send_message(message.chat.id, f"""Project name: {info[0]}
Description: {info[1]}
Link: {info[2]}
Status: {info[3]}
Skills: {skills}
""")

# запуск бота
@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id,
"""
🎉 **Привет! Я твой бот-менеджер проектов!**
Помогу организовать и отслеживать твои проекты. Вот, что я умею:
- Сохранять проекты.
- Добавлять навыки и обновлять информацию.
- Удалять и показывать проекты.

⚡ Используй команду `/info`, чтобы узнать больше обо всех моих функциях!
""", parse_mode="Markdown")

# какие комманды есть
@bot.message_handler(commands=['info'])
def info(message):
    bot.send_message(message.chat.id,
"""
👋 **Добро пожаловать в меню справки!**

Вот команды, которые тебе помогут:

📌 **Добавление проекта**:
  `/new_project` — добавь новый проект с описанием, ссылкой и статусом.

📌 **Удаление проекта**:
  `/delete` — удаляй проекты, которые больше не нужны.

📌 **Просмотр проектов**:
  `/projects` — получи список всех проектов с их краткой информацией.

📌 **Обновление информации**:
  `/update_projects` — измени детали уже существующего проекта.

📌 **Добавление навыков**:
  `/skills` — добавь навыки для своих проектов.

📌 **Информация о проекте**:
  Просто введи название проекта, чтобы увидеть его подробности!

💡 Удачи с идеями!
""", parse_mode="Markdown")

# Комманд для нового проекта
@bot.message_handler(commands=['new_project'])
def addtask_command(message):
    bot.send_message(message.chat.id, "Введите название проекта:")
    bot.register_next_step_handler(message, name_project)

# имя проекта
def name_project(message):
    name = message.text
    user_id = message.from_user.id
    data = [user_id, name]
    bot.send_message(message.chat.id, "Введите ссылку на проект")
    bot.register_next_step_handler(message, link_project, data=data)

# ссылки на проект
def link_project(message, data):
    data.append(message.text)
    statuses = [x[0] for x in manager.get_statuses()]  # Получение статусов из базы данных
    bot.send_message(message.chat.id, "Введите текущий статус проекта", reply_markup=gen_markup(statuses))
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)

# Сохранение проекта бз
def callback_project(message, data, statuses):
    status = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if status not in statuses:
        bot.send_message(message.chat.id, "Ты выбрал статус не из списка, попробуй еще раз!)", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return
    status_id = manager.get_status_id(status)
    data.append(status_id)
    manager.insert_project([tuple(data)])  # Вставка данных проекта в базу
    bot.send_message(message.chat.id, "Проект сохранен")


# добавления навыков к проекту
@bot.message_handler(commands=['skills'])
def skill_handler(message):    
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)  # Получение списка проектов пользователя
    if projects:
        projects = [x[2] for x in projects]  # Извлекаем названия проектов
        bot.send_message(message.chat.id, 'Выбери проект, для которого нужно выбрать навык', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        no_projects(message)  # Если проектов нет, отправляем сообщение

# Шаг 2: Выбор проекта для добавления навыка
def skill_project(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй еще раз!) Выбери проект, для которого нужно выбрать навык', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        skills = [x[1] for x in manager.get_skills()]  # Получение списка навыков из базы данных
        bot.send_message(message.chat.id, 'Выбери навык', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)

# Шаг 3: Привязка навыка к проекту
def set_skill(message, project_name, skills):
    skill = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cansel(message)
        return
    if skill not in skills:
        bot.send_message(message.chat.id, '❌ Кажется, ты выбрал неверный навык. Попробуй еще раз!', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    manager.insert_skill(user_id, project_name, skill)  # Добавление навыка в базу
    bot.send_message(message.chat.id, f"✅ Навык **{skill}** добавлен проекту **{project_name}**!", parse_mode="Markdown")

# Хэндлер для получения списка проектов
@bot.message_handler(commands=['projects'])
def get_projects(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)  # Получение списка проектов из базы данных
    if projects:
        text = "\n\n".join([
            f"📝 **{x[2]}**\n🔗 Ссылка: {x[4]}\n📌 Статус: {x[3]}"
            for x in projects
        ])
        bot.send_message(message.chat.id, f"Вот твои проекты:\n\n{text}", reply_markup=gen_inline_markup([x[2] for x in projects]), parse_mode="Markdown")
    else:
        no_projects(message)

# Callback-хэндлер для обработки нажатий на inline-кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    project_name = call.data  # Получение имени проекта из callback_data
    info_project(call.message, call.from_user.id, project_name)  # Отправка информации о проекте

# Хэндлер для удаления проекта
@bot.message_handler(commands=['delete'])
def delete_handler(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name:{x[2]} \nLink:{x[4]}\n" for x in projects])
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, text, reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
    else:
        no_projects(message)

# Удаление проекта из базы данных
def delete_project(message, projects):
    project = message.text
    user_id = message.from_user.id
    if message.text == cancel_button:
        cansel(message)
        return
    if project not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй выбрать еще раз!', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
        return
    project_id = manager.get_project_id(project, user_id)
    manager.delete_project(user_id, project_id)  # Удаление проекта из базы данных
    bot.send_message(message.chat.id, f'Проект {project} удален!')

# Хэндлер для обновления данных проекта
@bot.message_handler(commands=['update_projects'])
def update_project(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "Выбери проект, который хочешь изменить", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
    else:
        no_projects(message)

# Шаг 2: Выбор проекта для обновления
def update_project_step_2(message, projects):
    project_name = message.text
    if message.text == cancel_button:
        cansel(message)
        return
    if project_name not in projects:
        bot.send_message(message.chat.id, "Что-то пошло не так!) Выбери проект, который хочешь изменить еще раз:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects)
        return
    bot.send_message(message.chat.id, "Выбери, что требуется изменить в проекте", reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)

# Шаг 3: Выбор атрибута для обновления
def update_project_step_3(message, project_name):
    attribute = message.text
    reply_markup = None
    if message.text == cancel_button:
        cansel(message)
        return
    if attribute not in attributes_of_projects.keys():
        bot.send_message(message.chat.id, "Кажется, ты ошибся, попробуй еще раз!)", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return
    elif attribute == "Статус":
        rows = manager.get_statuses()
        reply_markup = gen_markup([x[0] for x in rows])
    bot.send_message(message.chat.id, attributes_of_projects[attribute][0], reply_markup=reply_markup)
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attributes_of_projects[attribute][1])

# Шаг 4: Сохранение обновленных данных проекта
def update_project_step_4(message, project_name, attribute):
    update_info = message.text
    if attribute == "status_id":
        rows = manager.get_statuses()
        if update_info in [x[0] for x in rows]:
            update_info = manager.get_status_id(update_info)
        elif update_info == cancel_button:
            cansel(message)
        else:
            bot.send_message(message.chat.id, "Был выбран неверный статус, попробуй еще раз!)", reply_markup=gen_markup([x[0] for x in rows]))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return
    user_id = message.from_user.id
    data = (update_info, project_name, user_id)
    manager.update_projects(attribute, data)  # Обновление данных проекта в базе
    bot.send_message(message.chat.id, "Готово! Обновления внесены!)")

# Обработка текста, который не является командой
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    projects = [x[2] for x in manager.get_projects(user_id)]  # Список проектов пользователя
    project = message.text
    if project in projects:
        info_project(message, user_id, project)  # Отправка информации о проекте
        return
    bot.reply_to(message, "Тебе нужна помощь?")
    info(message)

# Основная точка входа
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)  # Инициализация менеджера базы данных
    bot.infinity_polling()  # Бесконечный цикл обработки сообщений
