import telebot
from telebot import types
from random import randrange
import json
import re

commands = []
forms = {}
user_data = {}

#читаем конфиг файл
print("Начинаю читать конфиг")
file = open("config.json", mode="r", encoding="utf-8")
config = json.load(file)
file.close()

for command in config["commands"]:
	commands.append(command)

for form in config["forms"]:
	forms[form["name"]] = form.copy()
print("Закончил читать конфиг")



print("Подключаемся с помощью api ключа...")
bot = telebot.TeleBot(config["api_key"])
print("Подключение завершено.")

def handle_form_field(message, form_name, form_field):
	field_type = forms[form_name]["fields"][form_field]["field_data"]["type"]
	if field_type == "string":
		user_data[message.from_user.id][form_name][form_field] = message.text
		pattern = forms[form_name]["fields"][form_field]["field_data"]["validation"]
		if re.match(pattern, message.text):
			pass
		else:
			answer = forms[form_name]["fields"][form_field]["validation_error"]
			bot.send_message(message.from_user.id, answer)
			return
	else:
		user_data[message.from_user.id][form_name][form_field] = message.text
	

	if forms[form_name]["fields"][form_field]["next_field"] == "":
		function_name = forms[form_name]["end_handler"]
		globals()[function_name](message)
		return

	new_field = forms[form_name]["fields"][form_field]["next_field"]
	answer = forms[form_name]["fields"][new_field]["message"]
	bot.send_message(message.from_user.id, answer)
	bot.register_next_step_handler_by_chat_id(message.from_user.id, handle_form_field, form_name, new_field )




def start_form(message, form_name):
	user_data[message.from_user.id] = {}
	user_data[message.from_user.id][form_name] = {}

	field = forms[form_name]["first_field"]
	answer = forms[form_name]["fields"][field]["message"]
	bot.send_message(message.from_user.id, answer)

	bot.register_next_step_handler_by_chat_id(message.from_user.id, handle_form_field, form_name, field )

@bot.message_handler(commands=['start'])
def bot_start(message):
	answer = ""
	keyboard = types.ReplyKeyboardMarkup()
	for command in commands:
		answer += command + " - " + config["commands"][command]["description"] + "\n"
		keyboard.row( types.KeyboardButton(text=command) )

	bot.send_message(message.from_user.id, text = answer, reply_markup=keyboard)

def show_all_commands(message):
	keyboard = types.ReplyKeyboardMarkup()
	for command in commands:
		keyboard.row( types.KeyboardButton(text=command) )

	bot.send_message(message.from_user.id, text = "Меню", reply_markup=keyboard)

@bot.message_handler(commands=['status'])
def order_status(message):
	args = message.text.split()
	if len(args) < 2:
		bot.send_message(message.from_user.id, "Получаю твой список товаров...")
		keyboard = types.ReplyKeyboardMarkup()
		for i in range(5):
			keyboard.row( types.KeyboardButton(text="/status " + str( randrange(9999) ) ) )
		bot.send_message(message.from_user.id, text = "Выберите из списка заказов:", reply_markup=keyboard)
	else:
		answer = "Информация по заказу {0}\nДа я без понятия, меня ещё не интегрировали в CRM.".format(args[1])
		bot.send_message(message.from_user.id, answer)

	

@bot.message_handler(commands=['order'])
def new_order(message):
	bot.send_message(message.from_user.id, "Начало заказа")
	start_form(message, "new_order_form")

def new_order_complete(message):
	bot.send_message(message.from_user.id, "Спасибо, ваш заказ размещён!")
	bot.send_message(message.from_user.id, str(user_data))


print("Бот запущен!")
bot.polling(none_stop=True, interval=0)