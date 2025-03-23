from environs import Env

class Config:
    BOT_TOKEN: str
    DATABASE_URL: str
    DATABASE_NAME: str
    DATABASE_COLLECTION: str
    
    def __init__(self):
        env = Env()
        env.read_env()
        
        try:
            self.BOT_TOKEN = env('BOT_TOKEN')
            self.DATABASE_URL = env('DATABASE_URL', 'mongodb://127.0.0.1:27017/?directConnection=true')
            self.DATABASE_NAME = env('DATABASE_NAME', default='tasks_db')
            self.DATABASE_COLLECTION = env('DATABASE_COLLECTION', default='tasks')
        except Exception as e:
            print(f"Ошибка чтения переменных окружения: {e}")
            exit(1)
