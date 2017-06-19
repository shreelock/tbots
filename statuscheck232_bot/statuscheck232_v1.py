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
db = DBHelper_sc232()

def wrong_input_response(chat_id):
	msg="Unsupported. Send /help or /start or /menu"
	send_message(msg, chat_id)

def handle_updates(updates):
	for update in updates["result"]:
		try:
			text = update["message"]["text"]
			chat_id = update["message"]["chat"]["id"]
			previous_msg = ""
			if (len(db.get_last_cmd(chat_id))>0):
				previous_msg = str(db.get_last_cmd(chat_id)[0])
			
			print "Chat_Id: {}\nText: {}\nPrevious Msg: {}".format(chat_id, text, previous_msg)
			all_tasks = db.get_active_task_names(chat_id)
			keyboard=build_keyboard(all_tasks)

			items=text.split(',')
			[i.strip() for i in items]
			print "Splitted : ",items

			if len(items)==1:
				print "Got Single Length Message."
				if text=='/start' or text=='/help':
					
					welcome_msg= "<b>Hi, Welcome to StatusCheckBot</b>\n1. Add tasks - /add\n2. Update - /update\n3. Delete - /delete\n4. List all - /list\n5. Menu - /menu"
					send_message(welcome_msg, chat_id, True)

				elif text =='/list':
					
					send_task_list_as_msg(chat_id)

				elif text =='/menu':

					send_menu_bar(chat_id)

				elif text =='/delete' or text == '/update':
					send_keyboard_with_message("Select from the Task List below", chat_id, keyboard)

				elif text =='/add':
					
					add_msg_reply="Add your task below"
					send_message(add_msg_reply, chat_id, True)

				else:
					if text in all_tasks :

						if previous_msg =='/delete':
							print "Previous Msg is /delete, proceeding to delete task."
							print "Deleting {}".format(text)
							db.remove_task(text, chat_id)
							send_message("Deleting {}".format(text), chat_id, False)
							send_task_list_as_msg(chat_id)

						elif is_update_required():
							print "Updating task."
							db.update_task(text, chat_id)
							send_message("Updated {}".format(text), chat_id, False)
							send_task_list_as_msg(chat_id)

					elif previous_msg =='/add':
						print "Previous Msg is /add, proceeding to add task."
						db.add_task(chat_id, text, 0)
						send_message("Added {}".format(text), chat_id, False)
						send_task_list_as_msg(chat_id)

					else:
						print "Previous command is : {}, Boolean comparison : {}".format(previous_msg, '/add' is previous_msg)
						print "Don't know what to do with this Message. Error!"
						wrong_input_response(chat_id)

			elif len(items)==2:
				print "Got 2 items"
				if previous_msg=='/add':
					[task_name, req_hrs] = text.split(',')
					
					task_name=str(task_name).strip()
					req_hrs=str(req_hrs).strip()

					if task_name in all_tasks:
						already_added_task_msg = "Task Already Added! Cannot Add."
						send_message(already_added_task_msg, chat_id, False)
					else:
						db.add_task(chat_id, task_name, req_hrs)
						send_message("Added {}".format(text), chat_id, False)
						send_task_list_as_msg(chat_id)
				else:
					wrong_input_response(chat_id)

			else:
				wrong_input_response(chat_id)
			
			db.add_command_to_history(chat_id, text, int(time.time()))
		except Exception as e:
			print e


def GET_JSON(url):
	response = requests.get(url)
	content = response.content.decode("utf8")
	return json.loads(content)

def get_updates(offset=None):
	print "Getting updates"
	url = URL + "getUpdates?timeout=10000"
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
	menu_bar="( /add | /update | /delete | /list )"
	send_message(menu_bar, chat_id)


def is_update_required():
	return True




def build_keyboard(all_tasks):
    keyboard = [[item] for item in all_tasks]
    reply_markup = {"keyboard":keyboard, "one_time_keyboard": True}
    return json.dumps(reply_markup)



def main():
	# db.purge()
	db.setup()
	last_updated_id=None
	while True:
		upds = get_updates(last_updated_id)
		if len(upds["result"])>0:
			handle_updates(upds)
			last_updated_id = get_max_update_id(upds)+1
		time.sleep(0.15)

if __name__ == '__main__':
	main()