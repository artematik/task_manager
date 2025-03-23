from pymongo import MongoClient
import uuid
from bson import ObjectId

class Database:
    def __init__(self,url: str,db_name='task_db', collections_name='tasks'):
        self.client = MongoClient(url)
        self.db = self.client[db_name]
        self.collection = self.db[collections_name]

    def add_task(self,task_text, deadline):
        task = {
            'id': str(uuid.uuid4()),
            'task_text': task_text,
            'deadline': deadline
        }
        self.collection.insert_one(task)

    def get_all_task(self):
        tasks = list(self.collection.find())
        for task in tasks:
            task['_id'] = str(task['_id'])
        return tasks
    
    def delete_tasks_by_date(self, date):
        query = {'deadline': date}
        self.collection.delete_many(query)

    def edit_task(self, task_id, new_text=None, new_deadline=None):
        query = {'id': task_id}
        update = {}
        if new_text:
            update['task_text'] = new_text
        if new_deadline:
            update['deadline'] = new_deadline

        if update:
            self.collection.update_one(query,{'$set':update})

    def delete_all_tasks(self):
        self.collection.delete_many({})

    def check_connection(self):
        try:
            client = MongoClient("mongodb://127.0.0.1:27017/?directConnection=true", 
                            serverSelectionTimeoutMS=5000)
            self.client.admin.command("ping")
            print("✅ Успешное подключение к MongoDB!")
        except Exception as e:
            print(f"❌ Ошибка подключения к MongoDB: {e}")
            exit(1)