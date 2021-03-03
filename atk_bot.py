#!/usr/bin/python
 
from configparser import ConfigParser
from bs4 import BeautifulSoup
import requests
import telebot
import sys
import os
import logging
import time
import mysql.connector
#import streets

#config init
config = ConfigParser()
config.read('config.ini')
bot_id = config.get('id', 'bot')
login = config.get('id', 'login')
password = config.get('id', 'password')
valid_chat = config.get('id', 'valid_chat')
valid_chat2 = config.get('id', 'valid_chat2')
save_dir = config.get('vars', 'save_dir')
user_agent_val = config.get('vars', 'user_agent_val')
wait_time = int(config.get('vars', 'wait_time'))

#setup logging
logging.basicConfig(filename=os.path.basename(sys.argv[0])+'.log', level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

#create bot instance
try:
    bot = telebot.TeleBot(bot_id)
except Exception as e:
    print (e)
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    logging.error(exc_type, fname, exc_tb.tb_lineno)
    
#getting other stuff from config
url = {
    'root_url' : config.get('url', 'root_url'),
    'ref_url_ref' : config.get('url', 'ref_url_ref'),
    'cookie' : config.get('url', 'cookie'),
    'host' : config.get('url', 'host'),
    'auth_page' : config.get('url', 'auth_page'),
    'search_url' : config.get('url', 'search_url')
}

netdb_vars = {
    'host' : config.get('mysql_netdb', 'host'),
    'user' : config.get('mysql_netdb', 'login'),
    'password' : config.get('mysql_netdb', 'password'),
    'database' : config.get('mysql_netdb', 'database')
}

#global vars
request_num = {}
request_str = {}
request = {}

def check_comm_aviability(ip):
    netdb = mysql.connector.connect(
    host = netdb_vars.get('host'),
    user = netdb_vars.get('user'),
    password = netdb_vars.get('password'),
    database = netdb_vars.get('database')
    )
    #Получаем id коммутатора
    comm_cur = netdb.cursor()
    comm_cur.execute("select id from commutators where ip = '" + ip + "'")
    comm_res = comm_cur.fetchall()
    return len(comm_res)


def check_IPV4(ip):
    def isIPv4(s):
        try: return str(int(s)) == s and 0 <= int(s) <= 255
        except: return False
    if ip.count(".") == 3 and all(isIPv4(i) for i in ip.split(".")):
        return ip
    elif ip.count(".") == 1 and all(isIPv4(i) for i in ip.split(".")):
        return "10.254." + ip
    else:
        return ""

def extract_arg(arg):
    return arg.split(maxsplit=1)[1:]
    
def get_command(arg):
    return arg.split(' ', 1)[0]
    
def start_session():
    _s = requests.Session()
    _r = _s.get(url.get('root_url'), headers = {'User-Agent': user_agent_val})
    _cookie = _s.cookies.get(url.get('cookie'), domain=url.get('host'))
    _s.headers.update({'Referer':url.get('ref_url_ref')})
    _s.headers.update({'User-Agent':user_agent_val})
    _r = _s.get(url.get('auth_page'), headers = {'User-Agent': user_agent_val})
    _p = _s.post(url.get('auth_page'), {
    'sectok' : '', 
    'id' : 'start',
    'do' : 'login',
    'u' : login,
    'p' : password,
    'r' : 1
    })
    return _s
    
def search_pages(_arg):
    _s = start_session()
    _r = _s.get(url.get('search_url') + _arg, headers = {'User-Agent': user_agent_val})
    _c = _r.content
    return _c
    
def search_files(_src):
    _s = _s = start_session()
    _r = _s.get(url.get('root_url') + _src, headers = {'User-Agent': user_agent_val})
    _c = _r.content
    
    return _c
    
def get_file(_url):
    _s = start_session()
    _r = _s.get(url.get('root_url') + _url, headers = {'User-Agent': user_agent_val})
    return _r
    
def write_file(_n, _h):
    f = open(_n, "wb")
    r = get_file(_h)
    f.write(r.content)
    f.close()
    
def parse_pdf(_c):
    _files = []
    soup = BeautifulSoup(_c,'lxml')
    for var in soup.findAll('a', class_="media mediafile mf_pdf"):
        _n = var["title"]
        _h = var['href']
        _n = ('.pdf'.join(_n.split('.pdf')[:-1]) + '.pdf')
        _n = _n.replace('_', ' ').replace('corp', '').replace('pld', '')
        _path = save_dir + _n
        write_file(_path, _h)
        _files.append(_path)
    return _files

@bot.message_handler(content_types=['text'])
def pld(message):
    global request_num
    global request_str
    global request
    _chat_id = message.chat.id
    _command = get_command(message.text).lower()
    
    try:
        _args = extract_arg(message.text)[0]
    except:
        _args = ''
        pass
        
    try:
        if (str(_chat_id) == str(valid_chat) or str(_chat_id) == str(valid_chat2)):
            #FREE PORT
            if ((_command == 'порт') and (_args != "")):
                if (check_IPV4(message.text.split(' ')[1])!= "") :
                    _ip = check_IPV4(message.text.split(' ')[1])
                    if check_comm_aviability(_ip) > 0 :
                        msg = "Свободные порты на коммутаторе " + _ip + ":\n"
                        netdb = mysql.connector.connect(
                        host = netdb_vars.get('host'),
                        user = netdb_vars.get('user'),
                        password = netdb_vars.get('password'),
                        database = netdb_vars.get('database')
                        )
                        comm_cur = netdb.cursor()
                        comm_cur = netdb.cursor()
                        comm_cur.execute("select id from commutators where ip = '" + _ip + "'")
                        comm_res = comm_cur.fetchone()
                        comm_id = comm_res[0]
                        comm_cur.execute("select p.number from net.ports p left outer join UTM5.ip_groups g on p.commutator_id = g.switch_id and p.number = g.port_id where p.commutator_id = " + str(comm_id)+" and p.type = 'empty' and g.account_id is null and p.number < 24 and (p.comment = '' or p.comment is null) order by p.number")
                        port_res = comm_cur.fetchall()
                        for port in port_res :
                            msg = msg + str(port[0]) + ", "
                        bot.reply_to(message, msg)
                    else :
                        bot.reply_to(message, "Коммутатор " + _ip + " недоступен или не существует")
            #WIKI SEARCH
            elif ((_command == 'плд') and (_args != "")):
            
                msg = 'pld search: "' + 'плд ' + _args + '" from: ' + str(_chat_id)
                logging.warning(msg)
                c = search_pages(_args)
                soup = BeautifulSoup(c,'lxml')
                svars = {}
                
                for var in soup.findAll('a', class_="wikilink1"):
                    svars[var['title']] = var['href']
                    
                num = 0
                msg = ""
                for key in svars:
                    num += 1
                    msg += "➡️ " + str(num) + " " + key.replace('corp:pld:', '').replace('_', ' ').replace('corp:','').replace('pld1:', '').replace('it:', '').replace('tp:', '') + "\n"
                
                if (len(msg) > 1023):
                    msg = msg[:1023]
                    msg = '➡️'.join(msg.split('➡️')[:-1])
                    msg = "Нашлось совпадений: " + str(num) + "\nПревышена максимальная длина сообщения!\n\n" + msg
                else:
                    msg =  "Нашлось совпадений: " + str(num) + "\n\n" + msg
                
                if (num == 1):
                    bot.reply_to(message, msg)
                    keys = list(svars.keys())
                    src = svars.get(keys[num-1])
                    c = search_files(src)
                    _files = parse_pdf(c)
                    request = {_chat_id : False}
                    
                    if (len(_files) == 0):
                        bot.reply_to(message, "Нет файлов")
                    else:
                        _count = len(_files) // 10
                        bot.reply_to(message, "Файлов нашлось: " + str(len(_files)))
                        
                        for x in range(_count + 1):
                            bot.send_media_group(_chat_id, [telebot.types.InputMediaDocument(open(doc, 'rb')) for doc in _files[x*10:x*10+10]])
                            time.sleep(wait_time)

                elif (num > 1):
                    msg += "\nКакой номер интересует?"
                    bot.reply_to(message, msg)
                    request = {_chat_id : True}
                    request_str = {_chat_id : svars}
                    request_num = {_chat_id : num}
                else:
                    bot.send_message(_chat_id, msg)
                
            elif (_command.isdigit() and request.get(_chat_id) and (int(_command)-1 <= request_num.get(_chat_id)) and (int(_command)-1 >= 0)):
                request = {_chat_id : False}
                keys = list(request_str.get(_chat_id).keys())
                src = request_str.get(_chat_id).get(keys[int(_command)-1])
                c = search_files(src)
                _files = parse_pdf(c)
                request = {_chat_id : False}
                
                if (len(_files) == 0):
                    bot.reply_to(message, "Нет файлов")
                else:
                    _count = len(_files) // 10
                    bot.reply_to(message, "Файлов нашлось: " + str(len(_files)))
                    
                    for x in range(_count + 1):
                        bot.send_media_group(_chat_id, [telebot.types.InputMediaDocument(open(doc, 'rb')) for doc in _files[x*10:x*10+10]])
                        time.sleep(wait_time)
                
            else:
                pass
        else:
            msg = 'UNAUTORIZED ACCESS ATTEMP from '+str(_chat_id)
            logging.warning(msg)
            
    except Exception as e:
        print (e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        logging.error(exc_type, fname, exc_tb.tb_lineno)
        try:
            bot.reply_to(message, e)
        except:
            pass
        pass

bot.polling(none_stop = True)
