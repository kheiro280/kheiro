import telebot
import requests
import time
import json

# توكن بوت
bot = telebot.TeleBot('7912176694:AAGUfy5AcHhJneFAJFzXyAs6i6dC3r46YoQ')

# ملف لحفظ توكن الوصول
TOKEN_FILE = 'tokens999.json'

CHANNEL_ID = '@https://t.me/xreqx'  # استبدلها بمعرف القناة الفعلي

def load_access_token(phone_number):
    try:
        with open(TOKEN_FILE, 'r') as f:
            tokens = json.load(f)
            return tokens.get(phone_number)
    except FileNotFoundError:
        return None

def save_access_token(phone_number, access_token):
    try:
        with open(TOKEN_FILE, 'r') as f:
            tokens = json.load(f)
    except FileNotFoundError:
        tokens = {}
    
    tokens[phone_number] = access_token
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.chat.id, 'مرحباً! من فضلك أرسل رقم هاتفك 📱:')
    bot.register_next_step_handler(message, get_phone_number)

def get_phone_number(message):
    num = message.text

    if not num.startswith('05'):
        bot.send_message(message.chat.id, '⚠️ رقم الهاتف يجب أن يبدأ بـ 05.')
        return

    access_token = load_access_token(num)
    if access_token:
        bot.send_message(message.chat.id, 'تم العثور على توكن محفوظ. جاري إرسال الإنترنت...')
        send_internet(message, access_token)
    else:
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'ibiza.ooredoo.dz',
            'Connection': 'Keep-Alive',
            'User-Agent': 'okhttp/4.9.3',
        }

        data = {
            'client_id': 'ibiza-app',
            'grant_type': 'password',
            'mobile-number': num,
            'language': 'AR',
        }

        response = requests.post('https://ibiza.ooredoo.dz/auth/realms/ibiza/protocol/openid-connect/token', headers=headers, data=data)

        if 'ROOGY' in response.text:
            bot.send_message(message.chat.id, 'لإكمال العملية، أرسل رمز التحقق الذي وصلك 💌:')
            bot.register_next_step_handler(message, get_otp, num)
        else:
            bot.send_message(message.chat.id, '❌ فشل إرسال رمز التحقق. يرجى المحاولة لاحقاً.')

def get_otp(message, num):
    otp = message.text
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'ibiza.ooredoo.dz',
        'Connection': 'Keep-Alive',
        'User-Agent': 'okhttp/4.9.3',
    }

    data = {
        'client_id': 'ibiza-app',
        'otp': otp,
        'grant_type': 'password',
        'mobile-number': num,
        'language': 'AR',
    }

    response = requests.post('https://ibiza.ooredoo.dz/auth/realms/ibiza/protocol/openid-connect/token', headers=headers, data=data)
    
    access_token = response.json().get('access_token')
    if access_token:
        save_access_token(num, access_token)
        send_internet(message, access_token)
    else:
        bot.send_message(message.chat.id, '❌ خطأ في التحقق من OTP. حاول مرة أخرى.')

def send_internet(message, access_token):
    url = 'https://ibiza.ooredoo.dz/api/v1/mobile-bff/users/mgm/info/apply'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'language': 'AR',
        'request-id': 'ef69f4c6-2ead-4b93-95df-106ef37feefd',
        'flavour-type': 'gms',
        'Content-Type': 'application/json'
    }

    payload = {
        "mgmValue": "ABC"  
    }

    count_reference = 0
    m = 0
    start_time = time.time()

    while m < 12:
        response = requests.post(url, headers=headers, json=payload)
        
        if 'EU1002' in response.text:
            count_reference += 1

        m += 1
        if time.time() - start_time > 10:
            break

    balance_response = requests.get('https://ibiza.ooredoo.dz/api/v1/mobile-bff/users/balance', headers=headers)
    balance_data = balance_response.json()

    if 'accounts' in balance_data and len(balance_data['accounts']) > 1:
        balance_value = balance_data['accounts'][1]['value']
        user_name = message.from_user.first_name
        user_username = message.from_user.username or "غير معروف"
        
        bot.send_message(message.chat.id, f'''        📢 **تحديث رصيد الإنترنت!**
        
        🗣️ **الاسم:** {user_name}
        🏷️ **اسم المستخدم:** @{user_username}
        💼 **رقم الرسالة:** {message.message_id}
        📈 **رصيد البداية:** {balance_data['accounts'][0]['value']}
        📉 **رصيد النهاية:** {balance_value}''', parse_mode='html')

        bot.send_message(CHANNEL_ID, channel_message, parse_mode='markdown')
    else:
        bot.send_message(message.chat.id, '⚠️ حدث خطأ أثناء جلب الرصيد. يرجى المحاولة لاحقاً.')

# Ignore all other messages
@bot.message_handler(func=lambda message: True)
def handle_all_other_messages(message):
    pass

bot.polling(none_stop=True)