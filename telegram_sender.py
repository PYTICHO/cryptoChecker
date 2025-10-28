import requests
import secret

# Ваш токен бота и ID чата
TOKEN = secret.TOKEN

def get_chat_ids():
    # Открываем файл и читаем его содержимое
    with open("Users.txt", "r") as file:
        data = file.read()

    # Разделяем строки по запятой и удаляем лишние пробелы
    CHAT_IDS = [user.strip() for user in data.split(",")]

    return CHAT_IDS

# Функция отправки сообщения
def send_message(text: str, coin_map_url: str):
    CHAT_IDS = get_chat_ids()
    
    for ID in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {
            'chat_id': ID,
            'text': text,
            'reply_markup': {
                'inline_keyboard': [
                    [
                        {'text': 'CoinMarketCap', 'url': coin_map_url}
                    ]
                ]
            }
        }
        response = requests.post(url, json=data)
    
    if response.status_code != 200:
        print("Ошибка при отправке сообщения:", response.text)
        

