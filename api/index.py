from flask import Flask, request, jsonify
import requests
import json
import os
import random
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# ==================== تحميل الحسابات من ملف accounts.json ====================
ACCOUNTS_FILE = os.path.join(os.path.dirname(__file__), 'accounts.json')

def load_accounts():
    """تحميل جميع الحسابات من ملف accounts.json"""
    try:
        if os.path.exists(ACCOUNTS_FILE):
            with open(ACCOUNTS_FILE, 'r') as f:
                data = json.load(f)
                return data.get('accounts', [])
        else:
            print(f"[⚠️] ملف {ACCOUNTS_FILE} غير موجود!")
            return []
    except Exception as e:
        print(f"[❌] خطأ في تحميل الحسابات: {e}")
        return []

# ==================== اختيار حساب عشوائي ====================
def get_random_account():
    """اختيار حساب عشوائي من القائمة"""
    accounts = load_accounts()
    if not accounts:
        return None
    return random.choice(accounts)

# ==================== الحصول على توكن لحساب محدد ====================
def get_token_for_account(account):
    """الحصول على توكن لحساب معين - نفس منطق بوت التلغرام"""
    try:
        uid = account['uid']
        password = account['password']
        
        print(f"[ℹ️] محاولة الحصول على توكن للحساب: {uid}")

        # الخطوة 1: طلب guest token من جارينا
        url = "https://100067.connect.garena.com/oauth/guest/token/grant"
        headers = {
            "Host": "100067.connect.garena.com",
            "User-Agent": "GarenaMSDK/4.0.19P4",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "uid": uid,
            "password": password,
            "response_type": "token",
            "client_type": "2",
            "client_id": "100067",
            "client_secret": ""
        }

        r = requests.post(url, headers=headers, data=data)
        
        if r.status_code != 200:
            print(f"[❌] فشل الاتصال بـ Garena للحساب {uid}: {r.status_code}")
            return None

        d = r.json()
        NEW_ACCESS_TOKEN = d.get("access_token")
        NEW_OPEN_ID = d.get("open_id")

        if not NEW_ACCESS_TOKEN or not NEW_OPEN_ID:
            print(f"[❌] لم يتم استلام التوكن من Garena للحساب {uid}")
            return None

        print(f"[✅] تم الحصول على التوكن من Garena للحساب {uid}")

        # البيانات القديمة (ثابتة)
        OLD_ACCESS_TOKEN = "c69ae208fad72738b674b2847b50a3a1dfa25d1a19fae745fc76ac4a0e414c94"
        OLD_OPEN_ID = "4306245793de86da425a52caadf21eed"

        # الخطوة 2: إنشاء التوكن النهائي باستخدام TOKEN_MAKER
        token = TOKEN_MAKER(
            OLD_ACCESS_TOKEN,
            NEW_ACCESS_TOKEN,
            OLD_OPEN_ID,
            NEW_OPEN_ID,
            uid
        )

        if token:
            print(f"[✅] تم إنشاء التوكن للحساب {uid}")
            return token
        else:
            print(f"[❌] فشل إنشاء التوكن للحساب {uid}")
            return None

    except Exception as e:
        print(f"[❌] خطأ في الحصول على توكن للحساب {account.get('uid')}: {e}")
        return None

# ==================== TOKEN MAKER (من بوت التلغرام) ====================
def TOKEN_MAKER(OLD_ACCESS_TOKEN, NEW_ACCESS_TOKEN, OLD_OPEN_ID, NEW_OPEN_ID, uid):
    """صانع التوكن - نفس الموجود في بوت التلغرام"""
    now = datetime.now()
    now = str(now)[:len(str(now)) - 7]

    data = bytes.fromhex(
        '1a13323032352d31312d32362030313a35313a3238220966726565206669726528013a07312e3132302e314232416e64726f6964204f532039202f204150492d3238202850492f72656c2e636a772e32303232303531382e313134313333294a0848616e6468656c64520c4d544e2f537061636574656c5a045749464960800a68d00572033234307a2d7838362d3634205353453320535345342e3120535345342e32204156582041565832207c2032343030207c20348001e61e8a010f416472656e6f2028544d292036343092010d4f70656e474c20455320332e329a012b476f6f676c657c36323566373136662d393161372d343935622d396631362d303866653964336336353333a2010e3137362e32382e3133392e313835aa01026172b201203433303632343537393364653836646134323561353263616164663231656564ba010134c2010848616e6468656c64ca010d4f6e65506c7573204135303130ea014063363961653230386661643732373338623637346232383437623530613361316466613235643161313966616537343566633736616334613065343134633934f00101ca020c4d544e2f537061636574656cd2020457494649ca03203161633462383065636630343738613434323033626638666163363132306635e003b5ee02e8039a8002f003af13f80384078004a78f028804b5ee029004a78f029804b5ee02b00404c80401d2043d2f646174612f6170702f636f6d2e6474732e667265656669726574682d66705843537068495636644b43376a4c2d574f7952413d3d2f6c69622f61726de00401ea045f65363261623933353464386662356662303831646233333861636233333439317c2f646174612f6170702f636f6d2e6474732e667265656669726574682d66705843537068495636644b43376a4c2d574f7952413d3d2f626173652e61706bf00406f804018a050233329a050a32303139313139303236a80503b205094f70656e474c455332b805ff01c00504e005be7eea05093372645f7061727479f205704b717348543857393347646347335a6f7a454e6646775648746d377171316552554e6149444e67526f626f7a4942744c4f695943633459367a767670634943787a514632734f453463627974774c7334785a62526e70524d706d5752514b6d654f35766373386e51594268777148374bf805e7e4068806019006019a060134a2060134b2062213521146500e590349510e460900115843395f005b510f685b560a6107576d0f0366'
    )

    data = data.replace(OLD_OPEN_ID.encode(), NEW_OPEN_ID.encode())
    data = data.replace(OLD_ACCESS_TOKEN.encode(), NEW_ACCESS_TOKEN.encode())

    encrypted = encrypt_api(data.hex())
    Final_Payload = bytes.fromhex(encrypted)

    headers = {
        'X-Unity-Version': '2018.4.11f1',
        'ReleaseVersion': 'ob52',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-GA': 'v1 1',
        'Authorization': 'Bearer ...',
        'Content-Length': '928',
        'User-Agent': 'Dalvik/2.1.0',
        'Host': 'loginbp.ggpolarbear.com',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }

    url = "https://loginbp.ggpolarbear.com/MajorLogin"
    response = requests.post(url, headers=headers, data=Final_Payload, verify=False)

    if response.status_code == 200:
        if len(response.text) < 10:
            return False

        base = response.text[
            response.text.find("eyJhbGciOiJIUzI1NiIsInN2ciI6IjEiLCJ0eXAiOiJKV1QifQ"):
            -1
        ]

        second_dot = base.find(".", base.find(".") + 1)
        base = base[:second_dot + 44]
        return base
    return False

# ==================== دوال التشفير من byte.py ====================
def encrypt_api(plain_text):
    plain_text = bytes.fromhex(plain_text)
    key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
    return cipher_text.hex()

def Encrypt_ID(number):
    number = int(number)
    encoded_bytes = []
    while True:
        byte = number & 0x7F
        number >>= 7
        if number:
            byte |= 0x80
        encoded_bytes.append(byte)
        if not number:
            break
    return bytes(encoded_bytes).hex()

# ==================== إرسال طلب إضافة صديق ====================
def send_friend_request(token, target_uid, from_account):
    """إرسال طلب إضافة صديق باستخدام حساب محدد"""
    try:
        encrypted_id = Encrypt_ID(target_uid)
        payload = f"08a7c4839f1e10{encrypted_id}1801"
        payload_bytes = bytes.fromhex(encrypt_api(payload))

        url = "https://clientbp.ggpolarbear.com/RequestAddingFriend"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Unity-Version": "2018.4.11f1",
            "X-GA": "v1 1",
            "ReleaseVersion": "OB52",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(payload_bytes)),
            "User-Agent": "Dalvik/2.1.0 (Linux; Android 9)",
            "Connection": "close",
        }
        
        response = requests.post(url, headers=headers, data=payload_bytes, timeout=10)
        
        if response.status_code == 200:
            return True, f"تمت الإضافة من الحساب {from_account}"
        else:
            return False, f"خطأ {response.status_code} من الحساب {from_account}"
            
    except Exception as e:
        return False, str(e)

# ==================== نقاط النهاية ====================

@app.route('/', methods=['GET'])
def home():
    accounts = load_accounts()
    return jsonify({
        'name': 'Free Fire API - Multi Account',
        'version': '2.0.0',
        'developer': 'ZAKARIA',
        'total_accounts': len(accounts),
        'accounts': [acc['uid'] for acc in accounts],
        'endpoints': {
            '/add': 'إضافة صديق من حساب عشوائي - /add?uid=123456789',
            '/add_all': 'إضافة صديق من جميع الحسابات - /add_all?uid=123456789',
            '/add_specific': 'إضافة من حساب محدد - /add_specific?uid=123456789&account=4378068850',
            '/accounts': 'عرض جميع الحسابات',
            '/test_account': 'اختبار حساب محدد - /test_account?uid=4378068850'
        }
    })

@app.route('/add', methods=['GET'])
def add_friend_random():
    """إضافة صديق من حساب عشوائي"""
    target_uid = request.args.get('uid')
    
    if not target_uid or not target_uid.isdigit():
        return jsonify({'success': False, 'error': 'uid غير صالح'}), 400
    
    # اختيار حساب عشوائي
    account = get_random_account()
    if not account:
        return jsonify({'success': False, 'error': 'لا توجد حسابات متاحة'}), 503
    
    # الحصول على توكن للحساب
    token = get_token_for_account(account)
    if not token:
        return jsonify({'success': False, 'error': f'فشل الحصول على توكن للحساب {account["uid"]}'}), 503
    
    # إرسال طلب الإضافة
    success, message = send_friend_request(token, target_uid, account['uid'])
    
    return jsonify({
        'success': success,
        'message': message,
        'target_uid': target_uid,
        'from_account': account['uid']
    })

@app.route('/add_all', methods=['GET'])
def add_friend_all():
    """إضافة صديق من جميع الحسابات (واحد تلو الآخر)"""
    target_uid = request.args.get('uid')
    
    if not target_uid or not target_uid.isdigit():
        return jsonify({'success': False, 'error': 'uid غير صالح'}), 400
    
    accounts = load_accounts()
    if not accounts:
        return jsonify({'success': False, 'error': 'لا توجد حسابات متاحة'}), 503
    
    results = []
    success_count = 0
    
    for account in accounts:
        token = get_token_for_account(account)
        if token:
            success, message = send_friend_request(token, target_uid, account['uid'])
            if success:
                success_count += 1
            results.append({
                'account': account['uid'],
                'success': success,
                'message': message
            })
        else:
            results.append({
                'account': account['uid'],
                'success': False,
                'message': 'فشل الحصول على توكن'
            })
    
    return jsonify({
        'success': success_count > 0,
        'total_accounts': len(accounts),
        'success_count': success_count,
        'target_uid': target_uid,
        'results': results
    })

@app.route('/add_specific', methods=['GET'])
def add_friend_specific():
    """إضافة صديق من حساب محدد"""
    target_uid = request.args.get('uid')
    account_uid = request.args.get('account')
    
    if not target_uid or not target_uid.isdigit():
        return jsonify({'success': False, 'error': 'uid غير صالح'}), 400
    
    if not account_uid:
        return jsonify({'success': False, 'error': 'يجب تحديد الحساب'}), 400
    
    # البحث عن الحساب
    accounts = load_accounts()
    account = next((acc for acc in accounts if acc['uid'] == account_uid), None)
    
    if not account:
        return jsonify({'success': False, 'error': f'الحساب {account_uid} غير موجود'}), 404
    
    # الحصول على توكن للحساب
    token = get_token_for_account(account)
    if not token:
        return jsonify({'success': False, 'error': f'فشل الحصول على توكن للحساب {account_uid}'}), 503
    
    # إرسال طلب الإضافة
    success, message = send_friend_request(token, target_uid, account_uid)
    
    return jsonify({
        'success': success,
        'message': message,
        'target_uid': target_uid,
        'from_account': account_uid
    })

@app.route('/accounts', methods=['GET'])
def list_accounts():
    """عرض جميع الحسابات المتاحة"""
    accounts = load_accounts()
    return jsonify({
        'success': True,
        'total': len(accounts),
        'accounts': [{'uid': acc['uid']} for acc in accounts]
    })

@app.route('/test_account', methods=['GET'])
def test_single_account():
    """اختبار حساب محدد"""
    account_uid = request.args.get('uid')
    
    if not account_uid:
        return jsonify({'success': False, 'error': 'يجب تحديد الحساب'}), 400
    
    accounts = load_accounts()
    account = next((acc for acc in accounts if acc['uid'] == account_uid), None)
    
    if not account:
        return jsonify({'success': False, 'error': f'الحساب {account_uid} غير موجود'}), 404
    
    token = get_token_for_account(account)
    
    return jsonify({
        'success': token is not None,
        'account': account_uid,
        'token_status': '✅ صالح' if token else '❌ غير صالح'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)