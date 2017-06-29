import json
import requests
import time
from prettytable import PrettyTable as pt
import datetime
import sys
import os
import urllib
from dbhelper import DBHelper_sc232
from key import STATUSCHECK232_BOT_TOKEN


#https://www.codementor.io/garethdwyer/building-a-telegram-bot-using-python-part-1-goi5fncay

URL="https://api.telegram.org/bot{}/".format(STATUSCHECK232_BOT_TOKEN)
NO_RESPONSE_TASK="No Response"
db = DBHelper_sc232()

def wrong_input_response(chat_id):
	msg="Unsupported. Send /help or /menu"
	send_message(msg, chat_id)

def handle_updates(updates):
	for update in updates["result"]:
		try:
			add_command_to_history_boolean = True
			text = update["message"]["text"]
			chat_id = update["message"]["chat"]["id"]
			previous_msg = ""
			if (len(db.get_last_cmd(chat_id))>0):
				previous_msg = str(db.get_last_cmd(chat_id)[0])
			
			print "Chat_Id: {}\nText: {}\nPrevious Msg: {}".format(chat_id, text, previous_msg)
			all_tasks = db.get_active_task_names(chat_id)
			keyboard=build_keyboard(all_tasks)

			if text=='/start' or text=='/help':
				
				welcome_msg= "<b>Hi, Welcome to StatusCheckBot</b>\nI ask you each hour for what you have been doing, keeping a log of time and work. :)\n1. Add tasks - /add\n2. Update the status - /update\n3. Delete - /delete\n4. List all - /list\n5. Register for Alerts - /register\n6. Deregister - /deregister\n7. Menu - /menu"
				send_message(welcome_msg, chat_id, True)


			elif text =='/list':
				
				send_task_list_as_msg(chat_id)


			elif text =='/register':

				if not is_user_registered(chat_id):
					register_user(chat_id)
					send_message("User Registered for hourly updates", chat_id)
					send_menu_bar(chat_id)
				else:
					send_message("User already Registered", chat_id)
					send_menu_bar(chat_id)


			elif text =='/deregister':

				if is_user_registered(chat_id):
					deregister_user(chat_id)
					send_message("User Deregistered!", chat_id)
					send_menu_bar(chat_id)
				else:
					send_message("User Not Registered", chat_id)
					send_menu_bar(chat_id)

			elif text =='/menu':

				send_menu_bar(chat_id)

			elif text =='/delete' :
				
				send_keyboard_with_message("Select the Task to be deleted", chat_id, keyboard)

			elif text =='/cancel' :

				send_message("Cancelled.", chat_id)
				send_menu_bar(chat_id)

			elif text =='/update':

				if is_update_required(chat_id):
					send_keyboard_with_message("Select the Task from below", chat_id, keyboard)
				else:
					send_message("Task already updated for this hour.", chat_id)
					send_menu_bar(chat_id)

			elif text =='/add':
				
				add_msg_reply="Add your task below, or /cancel"
				send_message(add_msg_reply, chat_id, True)

			else:
				if text in all_tasks :

					if previous_msg =='/delete':
						print "Previous Msg is /delete, proceeding to delete task."
						print "Deleting {}".format(text)
						db.remove_task(text, chat_id)
						send_message("Deleting {}".format(text), chat_id)
						send_task_list_as_msg(chat_id)

					else:
						if is_update_required(chat_id):
							print "Updating task."
							db.update_task(text, chat_id)
							db.update_time_row(chat_id, get_current_time_code())
							send_message("Updated {}".format(text), chat_id)
							send_task_list_as_msg(chat_id)
						else:
							print "Update Not Required."
							send_message("Task already updated for this hour.", chat_id)
							send_menu_bar(chat_id)

				elif previous_msg =='/add':
					print "Previous Msg is /add, proceeding to add task."
					db.add_task(chat_id, text, 0)
					send_message("Added {}".format(text), chat_id)
					send_task_list_as_msg(chat_id)

				else:
					print "Previous command is : {}".format(previous_msg)
					print "Don't know what to do with this Message. Error!"
					add_command_to_history_boolean = False
					wrong_input_response(chat_id)
			
			if add_command_to_history_boolean == True:
				db.add_command_to_history(chat_id, text, int(time.time()))

		except Exception as e:
			print e


def GET_JSON(url):
	response = requests.get(url)
	content = response.content.decode("utf8")
	return json.loads(content)

def get_updates(offset=None):
	print "Getting updates"
	url = URL + "getUpdates?timeout=60"
	if offset:
		url += "&offset={}".format(offset)
	return GET_JSON(url)



def send_keyboard_with_message(text, chat_id, reply_markup=None):
	url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
	if reply_markup:
		url += "&reply_markup={}".format(reply_markup)
	GET_JSON(url)


def send_message(text, chat_id, markdown=None):
	url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
	if markdown==True:
		url=url+"&parse_mode=HTML"
	GET_JSON(url)

def get_max_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def send_task_list_as_msg(chat_id):
	listall = db.get_active_tasks(chat_id)
	if len(listall)>0:
		table=pt(["Count","Task"])
		table.align="l"
		table.left_padding_width=5
		table.border=False
		for l in listall:
			table.add_row([l[2],l[1]])
		send_message(table,chat_id)
		send_menu_bar(chat_id)
		
	else:
		send_message("No Tasks yet!", chat_id)

def send_menu_bar(chat_id):
	menu_bar="/add\t|\t/update\t|\t/delete\t|\t/list\n/register\t|\t/deregister\t|\t/help"
	send_message(menu_bar, chat_id)



def build_keyboard(all_tasks):
    keyboard = [[item] for item in all_tasks]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)


def is_user_registered(chat_id):
	users_list = db.get_all_users()
	print "All users - ", users_list
	return chat_id in users_list

def register_user(chat_id):
	db.add_user(chat_id)

def deregister_user(chat_id):
	db.remove_user(chat_id)

def get_current_time_code():
	return time.localtime().tm_hour + 100*time.localtime().tm_mday + 10000*time.localtime().tm_mon + 1000000*time.localtime().tm_year

def is_update_required(chat_id):
	current_time_code = get_current_time_code()
	#found_timerow_for_current_time_code = ftfctc
	ftfctc = db.get_time_row(chat_id, current_time_code)
	print "time-row : ",ftfctc
	if len(ftfctc) == 0:
		db.add_time_row(chat_id, current_time_code)
		return True
	
	else:
		if db.get_time_row(chat_id, current_time_code)[0][2] == 0:
			return True

	return False

def check_if_updated_last_hour(chat_id):
	print "Got in If UPDATED"
	last_2_hour_rows=db.get_last_2_hour_time_row(chat_id)
	print "last hour row", last_2_hour_rows[0], last_2_hour_rows[1]
	if last_2_hour_rows[1][2]==0:
		print "Didnt respond Last hour."
		if not db.has_task(NO_RESPONSE_TASK, chat_id) :
			print "DB doesn't have NO_RESPONSE task added."
			db.add_task(chat_id, NO_RESPONSE_TASK)
		
		print "DB has NO_RESPONSE task already added."
		db.update_task(NO_RESPONSE_TASK, chat_id)
		db.update_time_row(chat_id, last_2_hour_rows[1][1])
		send_message("Marking No Response for last hour", chat_id)
		send_task_list_as_msg(chat_id)


def send_push_msgs():
	print time.localtime().tm_mon, time.localtime().tm_mday, time.localtime().tm_hour, time.localtime().tm_min, time.localtime().tm_sec
	current_time_min = time.localtime().tm_min
	#To Create a time row in beginning of the hour itself.
	if current_time_min < 5 :
		users_list = db.get_all_users()
		for chat_id in users_list:
			is_update_required(chat_id)
			try:
				check_if_updated_last_hour(chat_id)
			except Exception as e:
				print e
			

	#To check status in later half of the hour, and not each minute
	if current_time_min > 30 and current_time_min%5 == 0:
		users_list = db.get_all_users()
		for chat_id in users_list:
			if is_update_required(chat_id):
				print "Update is required at sending automated push msg."
				all_tasks = db.get_active_task_names(chat_id)
				keyboard=build_keyboard(all_tasks)
				send_keyboard_with_message("Select what are you doing this hour!", chat_id, keyboard)


def main():
	# db.purge()
	db.setup()
	last_updated_id=None
	while True:
		send_push_msgs()
		try:
			upds = get_updates(last_updated_id)
			if len(upds["result"])>0:
				handle_updates(upds)
				last_updated_id = get_max_update_id(upds)+1
			# time.sleep(0.15) //Dont Need to sleep, We are using Long polling
		except Exception as e:
			print e

if __name__ == '__main__':
	main()