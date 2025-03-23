from datetime import datetime

def calculate_time_left(deadline_str):
    deadline = datetime.strptime(deadline_str, '%d-%m-%Y')
    time_left = deadline - datetime.now()
    days = time_left.days
    hours, remainder = divmod(time_left.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return days, hours, minutes, seconds

def format_time_left(days, hours, minutes, seconds):
    return f"{days} дней, {hours} часов, {minutes} минут, {seconds} секунд"


# def calculate_to_left(deadline):
#     deadline_date = datetime.strptime(deadline, '%d-%m-%Y')
#     today = datetime.now()
#     time_difference = deadline_date - today
#     return time_difference

# deadline = '20.03.2025 22:00:00'
# deadline_date = datetime.strptime(deadline, '%d.%m.%Y %H:%M:%S')
# today = datetime.now()
# time_difference = deadline_date - today
# print(time_difference)