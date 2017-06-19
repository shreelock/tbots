import sqlite3


class DBHelper_sc232:
	def __init__(self, dbname="statuscheck232_bot.sqlite"):
		self.dbname = dbname
		self.conn = sqlite3.connect(dbname)

	def setup(self):
		stmt = "CREATE TABLE IF NOT EXISTS tasks_table (chat_id integer, task_name text, count integer, req_count integer, id integer primary key)"
		self.conn.execute(stmt)
		self.conn.commit()
		print "Created tasks_table"

		stmt = "CREATE TABLE IF NOT EXISTS cmds_table (chat_id integer, cmd text, sent_at integer)"
		self.conn.execute(stmt)
		self.conn.commit()
		print "Created cmds_table"

		print "Setup done"

	def purge(self):
		stmt = "DROP TABLE tasks_table"
		self.conn.execute(stmt)
		self.conn.execute("VACUUM")
		self.conn.commit()
		print "Purged the table"

	def add_task(self, chat_id, task_name, req_count):
		stmt = "INSERT INTO tasks_table (chat_id, task_name, count, req_count) VALUES (?,?,?,?)"
		vals = (chat_id, task_name, '0', req_count)
		self.conn.execute(stmt, vals)
		self.conn.commit()
		print "Added {} into db ".format(task_name)


	def get_active_tasks(self, chat_id):
		 stmt = "SELECT * FROM tasks_table WHERE chat_id = {}".format(chat_id)
		 return [x for x in self.conn.execute(stmt)]

	def get_active_task_names(self, chat_id):
		 stmt = "SELECT * FROM tasks_table WHERE chat_id = {}".format(chat_id)
		 return [x[1] for x in self.conn.execute(stmt)]

	def get_active_task_ids(self, chat_id):
		 stmt = "SELECT * FROM tasks_table WHERE chat_id = {}".format(chat_id)
		 return [x[4] for x in self.conn.execute(stmt)]


	def remove_task(self, task_name, chat_id):
		stmt = "DELETE FROM tasks_table WHERE task_name = (?) AND chat_id =(?)"
		args = (task_name, chat_id)
		self.conn.execute(stmt, args)
		self.conn.commit()


	def update_task(self, task_name, chat_id):
		stmt = "UPDATE tasks_table SET count=count+1 WHERE task_name = (?) AND chat_id=(?)"
		vals = (task_name, chat_id)
		self.conn.execute(stmt,vals)


	def add_command_to_history(self, chat_id, cmd, sent_at):
		stmt = "INSERT INTO cmds_table (chat_id, cmd, sent_at) VALUES (?,?,?)"
		vals = (chat_id, cmd, sent_at)
		self.conn.execute(stmt, vals)
		self.conn.commit()
		print "Added {} into commands history table".format(cmd)

	def get_last_cmd(self, chat_id):
		stmt = "SELECT * from cmds_table WHERE chat_id = {} ORDER BY sent_at desc limit 1".format(chat_id)
		return [x[1] for x in self.conn.execute(stmt)]
