import requests, time, hmac, hashlib, secret
from colorama import Fore, Style, init
init()
import sys, time, threading, itertools
import telegram_sender

# Открываем файл и читаем его содержимое
with open("tokens.txt", "r") as file:
    tokens_data = file.read()
# Разделяем строки по запятой и удаляем лишние пробелы
top_tokens = [currency.strip()+"USDT" for currency in tokens_data.split(",")]

with open("blocked_tokens.txt", "r") as file:
    blocked_tokens_data = file.read()
blocked_top_tokens = [currency.strip()+"USDT" for currency in blocked_tokens_data.split(",")]



#Список отправленных токенов
sended_tokens = []



# Функция для спиннера (анимация)
def spinner(stop_event):
    spinner_cycle = itertools.cycle(['|', '/', '-', '\\'])
    while not stop_event.is_set():
        sys.stdout.write(next(spinner_cycle))  # выводим спиннер
        sys.stdout.flush()  # сбрасываем буфер вывода
        time.sleep(0.1)  # задержка для обновления
        sys.stdout.write('\b')  # удаляем последний символ



#Получение всех символов на используемых биржах
def get_all_symbols_htx():
    """Получаем все торговые пары с HTX (Huobi), торгуемые в USDT"""
    url = "https://api.huobi.pro/market/tickers"
    response = requests.get(url)
    data = response.json()
    symbols = {}

    for symbol in data['data']:
        symbol_name = symbol['symbol']
        price = float(symbol['close'])

        if symbol_name[-4:] == 'usdt':
            symbols[symbol_name.upper()] = price
            
    return symbols

def get_all_symbols_bybit():
    # Эндпоинт для получения данных о тикерах
    url = "https://api.bybit.com/v5/market/tickers"
    params = {
        "category": "spot"
    }
    response = requests.get(url, params=params)
    symbols = {}

    # Проверяем статус ответа
    if response.status_code == 200:
        data = response.json()

        # Выводим данные о всех тикерах
        for ticker in data['result']['list']:
            symbol_name = ticker['symbol']
            price = float(ticker['lastPrice'])

            if symbol_name[-4:] == 'USDT':
                symbols[symbol_name] = price
    return symbols

def get_all_symbols_mexc():
    url = "https://api.mexc.com/api/v3/ticker/price"
    # Выполняем GET-запрос к API
    response = requests.get(url)
    symbols = {}

    # Проверяем успешность запроса
    if response.status_code == 200:
        # Преобразуем ответ в JSON формат
        data = response.json()

        for ticker in data:
            symbol_name = ticker['symbol']
            price = float(ticker['price'])

            if symbol_name[-4:] == 'USDT':
                    symbols[symbol_name] = price
    return symbols


# Получение статусов вывода и депозита на всех биржах по всем монетам
def get_all_deposit_and_withdraw_status_htx():
    """Получаем информацию о возможности депозита и вывода на HTX (Huobi)"""
    url = "https://api.huobi.pro/v2/reference/currencies"
    response = requests.get(url)
    data = response.json()
    all_statuses = {}

    if "data" in data:
        for currency in data['data']:
            currencyName = currency['currency'] + "usdt"
            chains = currency["chains"]
            chainTypes = {}

            if len(chains) > 0:
                deposit_allowed_flag = False
                withdraw_allowed_flag = False
                for chain in chains:
                    depositStatus = chain['depositStatus']
                    withdrawStatus = chain['withdrawStatus']
                    if 'transactFeeWithdraw' in chain.keys():
                        fee = chain['transactFeeWithdraw']
                    else:
                        fee = None

                    if depositStatus == 'allowed':
                        deposit_allowed_flag = True
                    if withdrawStatus == 'allowed':
                        withdraw_allowed_flag = True
                    if deposit_allowed_flag or withdraw_allowed_flag:
                        chainTypes[chain['displayName']] = {"fee": fee}

                if deposit_allowed_flag:
                    depositStatus = True
                else:
                    depositStatus = False

                if withdraw_allowed_flag:
                    withdrawStatus = True
                else:
                    withdrawStatus = False

                all_statuses[currencyName] = {'depositStatus': depositStatus, 'withdrawStatus': withdrawStatus, 'chainTypes': chainTypes}
    return all_statuses

def get_all_deposit_and_withdraw_status_bybit():
    # Твой API Key и API Secret
    api_key = secret.api_key_bybit
    api_secret = secret.api_secret_bybit
    all_statuses = {}

    # Параметры для запроса
    params = {
        'api_key': api_key,
        'timestamp': str(int(time.time() * 1000)),
        'recv_window': '5000',
    }

    # Генерация подписи
    param_str = "&".join([f"{key}={params[key]}" for key in sorted(params)])
    signature = hmac.new(api_secret.encode('utf-8'), param_str.encode('utf-8'), hashlib.sha256).hexdigest()

    # Добавляем подпись в параметры
    params['sign'] = signature

    # Выполнение запроса
    url = "https://api.bybit.com/v5/asset/coin/query-info"
    response = requests.get(url, params=params)
    data = response.json()
    
    # Проверка успешности запроса и вывод данных
    if data.get('retCode') == 0:
        for coin in data['result']['rows']:
            currencyName = coin['coin'].lower() + 'usdt'
            deposit_allowed_flag = False
            withdraw_allowed_flag = False
            chainTypes = {}

            for chain in coin['chains']:
                deposit_status = True if chain['chainDeposit'] == '1' else False
                withdraw_status = True if chain['chainWithdraw'] == '1' else False
                if 'withdrawFee' in chain.keys():
                    fee = chain['withdrawFee']
                else:
                    fee = None

                if deposit_status:
                    deposit_allowed_flag = True
                
                if withdraw_status:
                    withdraw_allowed_flag = True

                if deposit_allowed_flag or withdraw_allowed_flag:
                    chainTypes[chain['chainType']] = {"fee": fee}
            
            if deposit_allowed_flag:
                depositStatus = True
            else:
                depositStatus = False

            if withdraw_allowed_flag:
                withdrawStatus = True
            else:
                withdrawStatus = False

            all_statuses[currencyName] = {'depositStatus': depositStatus, 'withdrawStatus': withdrawStatus, 'chainTypes': chainTypes}
    return all_statuses

def get_all_deposit_and_withdraw_status_mexc():
    # Твой API Key и API Secret
    api_key = secret.api_key_mexc
    api_secret = secret.api_secret_mexc
    all_statuses = {}

    # Эндпоинт для получения доступных сетей для вывода
    url = "https://api.mexc.com/api/v3/capital/config/getall"
    timestamp = int(time.time() * 1000)
    query_string = f'timestamp={timestamp}'
    signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    query_string += f'&signature={signature}'

    # Заголовки с вашим API-ключом
    headers = {
        'X-MEXC-APIKEY': api_key
    }

    response = requests.get(f'{url}?{query_string}', headers=headers)

    # Проверяем успешность запроса
    if response.status_code == 200:
        # Преобразуем ответ в JSON формат
        data = response.json()

        # Выводим список криптовалют и доступных сетей для вывода
        for coin in data:
            currencyName = coin['coin'].lower() + 'usdt'
            deposit_allowed_flag = False
            withdraw_allowed_flag = False
            chainTypes = {}

            for chain in coin['networkList']:
                deposit_status = True if chain['depositEnable'] else False
                withdraw_status = True if chain['withdrawEnable'] else False
                if 'withdrawFee' in chain.keys():
                    fee = chain['withdrawFee']
                else:
                    fee = None
                
                if deposit_status:
                    deposit_allowed_flag = True
                
                if withdraw_status:
                    withdraw_allowed_flag = True

                if deposit_allowed_flag or withdraw_allowed_flag:
                    chainTypes[chain['network']] = {"fee": fee}

            if deposit_allowed_flag:
                depositStatus = True
            else:
                depositStatus = False

            if withdraw_allowed_flag:
                withdrawStatus = True
            else:
                withdrawStatus = False

            all_statuses[currencyName] = {'depositStatus': depositStatus, 'withdrawStatus': withdrawStatus, 'chainTypes': chainTypes}
    return all_statuses



# Общая функция получения статусов и сетей
def get_all_statuses_and_chains(all_statuses, symbol, price, market):
    if symbol.lower() in all_statuses.keys():
        deposit_status = all_statuses[symbol.lower()]['depositStatus']
        withdraw_status = all_statuses[symbol.lower()]['withdrawStatus']
        chainTypes = ""

        for chainType in all_statuses[symbol.lower()]['chainTypes'].keys():
            # Комиссия за вывод
            fee = all_statuses[symbol.lower()]['chainTypes'][chainType]['fee'] 
            try:
                fee = float(fee) * price
                fee = f"{fee:.2f}"
            except:
                pass

            #Собираем (сеть + комиссия за нее)
            chainTypes += str(chainType).upper() + f'(fee: {fee}💲), '  
        chainTypes = chainTypes.rstrip(", ")

        #Проверка на пустоту сетей вывода
        if len(chainTypes.strip(' ')) == 0:
            chainTypes = "⛔"
            
    else:
        return False
        
    
    return {'deposit_status': deposit_status, 'withdraw_status': withdraw_status, 'chainTypes': chainTypes, 'price': price, 'market': market}



# Рабочая часть
def compare_prices_for_all(all_symbols, all_statuses):
    global top_tokens, blocked_top_tokens, sended_tokens
    
    #Сравниваем цены для всех криптовалют на обеих биржах последовательно
    all_symbols_htx = list(all_symbols['htx'].keys())
    all_symbols_bybit = list(all_symbols['bybit'].keys())
    all_symbols_mexc = list(all_symbols['mexc'].keys())

    # Пересечение символов
    common_symbols = sorted(set(all_symbols_htx) | set(all_symbols_bybit) | set(all_symbols_mexc)) 


    for symbol in common_symbols:
        if (symbol in top_tokens) and not (symbol in blocked_top_tokens):
            # Объединенная информация по монете со всех бирж
            united_symbol_info = []
            flag_passed_diff = False


            # Статусы и сети для HTX
            price_htx = all_symbols['htx'][symbol] if symbol in all_symbols['htx'].keys() else None
            all_symbol_info_htx = get_all_statuses_and_chains(all_statuses['htx'], symbol, price_htx, market="HTX")
            if all_symbol_info_htx and price_htx:
                #Проверка, что депозит и вывод работают:
                if all_symbol_info_htx['deposit_status'] and all_symbol_info_htx['withdraw_status']:
                    united_symbol_info.append(all_symbol_info_htx)
            
            # Статусы и сети для ByBit
            price_bybit = all_symbols['bybit'][symbol] if symbol in all_symbols['bybit'].keys() else None
            all_symbol_info_bybit = get_all_statuses_and_chains(all_statuses['bybit'], symbol, price_bybit, market='ByBit')
            if all_symbol_info_bybit and price_bybit:
                #Проверка, что депозит и вывод работают:
                if all_symbol_info_bybit['deposit_status'] and all_symbol_info_bybit['withdraw_status']:
                    united_symbol_info.append(all_symbol_info_bybit)

            # Статусы и сети для MEXC
            price_mexc = all_symbols['mexc'][symbol] if symbol in all_symbols['mexc'].keys() else None
            all_symbol_info_mexc = get_all_statuses_and_chains(all_statuses['mexc'], symbol, price_mexc, market='MEXC')
            if all_symbol_info_mexc and price_mexc:
                #Проверка, что депозит и вывод работают:
                if all_symbol_info_mexc['deposit_status'] and all_symbol_info_mexc['withdraw_status']:
                    united_symbol_info.append(all_symbol_info_mexc)


            # Сравниваем все биржи, на которых есть выбранная монета
            united_symbol_info = sorted(united_symbol_info, key=lambda x: x['price'])
            for i in range(len(united_symbol_info)):
                for j in range(i+1, len(united_symbol_info)):
                    market1 = united_symbol_info[i]
                    market2 = united_symbol_info[j]

                    diff_percent = abs((market1['price'] - market2['price']) / ((market1['price'] + market2['price']) / 2)) * 100

                    if 0 <= diff_percent <= 2:
                        flag_passed_diff = True
                        #Проверка, был ли отправлен этот токен
                        if symbol not in sended_tokens:

                            text = f"""🔥 Спред {symbol}: {diff_percent:.2f}%\n\n 
{market1['market']}: {market1['price']}💲   🛜  Сети: {market1['chainTypes']}\n
⏬ ⏬ ⏬\n
{market2['market']}: {market2['price']}💲   🛜  Сети: {market2['chainTypes']}\n"""
                            
                            print(text)
                            #Отправляем связку в TG бота
                            coin_map_url = f"https://www.google.com/search?q={symbol.lower()[:-4]}+site:coinmarketcap.com"
                            telegram_sender.send_message(text, coin_map_url)
            
            if flag_passed_diff:
                if symbol not in sended_tokens:
                    sended_tokens.append(symbol)
            else:
                if symbol in sended_tokens:
                    sended_tokens.remove(symbol)
            


                        



# Run
if __name__ == "__main__":
    print(Fore.CYAN + "💸 CryptoChecker Started!\n\n" + Style.RESET_ALL)

    while True:
        # Получаем список всех торговых пар на обеих биржах
        all_symbols_htx = get_all_symbols_htx()
        all_symbols_bybit = get_all_symbols_bybit()
        all_symbols_mexc = get_all_symbols_mexc()

        # Получаем статусы вывода и депозита всех торговых пар
        all_statuses_htx = get_all_deposit_and_withdraw_status_htx()
        all_statuses_bybit = get_all_deposit_and_withdraw_status_bybit()
        all_statuses_mexc = get_all_deposit_and_withdraw_status_mexc()

        #Собираем под один словарь
        all_symbols = {'htx': all_symbols_htx, 'bybit': all_symbols_bybit, 'mexc': all_symbols_mexc}
        all_statuses = {'htx': all_statuses_htx, 'bybit': all_statuses_bybit, 'mexc': all_statuses_mexc}

        # Run
        compare_prices_for_all(all_symbols, all_statuses)
        
        # Вывод текста с цветом
        print(Fore.GREEN + "✅ Все связки просмотрены!" + Style.RESET_ALL) 

        time.sleep(5)
