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
save_dir = config.get('vars', 'save_dir')
user_agent_val = config.get('vars', 'user_agent_val')
wait_time = int(config.get('vars', 'wait_time'))
access_list = dict(config.items('access_list'))

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

bazadb_vars = {
    'host' : config.get('mysql_baza', 'host'),
    'user' : config.get('mysql_baza', 'login'),
    'password' : config.get('mysql_baza', 'password'),
    'database' : config.get('mysql_baza', 'database')
}

#global vars
request_num = {}
request_str = {}
request = {}
# request_drs = {}
# links = {}

def netdb_connect():
    netdb = mysql.connector.connect(
        host = netdb_vars.get('host'),
        user = netdb_vars.get('user'),
        password = netdb_vars.get('password'),
        database = netdb_vars.get('database')
        )
    return netdb
    
def bazadb_connect():
    bazadb = mysql.connector.connect(
        host = bazadb_vars.get('host'),
        user = bazadb_vars.get('user'),
        password = bazadb_vars.get('password'),
        database = bazadb_vars.get('database')
        )
    return bazadb

def check_comm_aviability(ip):
    netdb = netdb_connect()
    #Получаем id коммутатора
    comm_cur = netdb.cursor(buffered=True)
    comm_cur.execute("select id from commutators where ip = '" + ip + "'")
    comm_res = comm_cur.fetchall()
    comm_cur.close()
    netdb.close()
    return len(comm_res)
    
def free_ports(ip):
    netdb = netdb_connect()
    comm_cur = netdb.cursor(buffered=True)
    _sql =("""select id from commutators 
            where ip = %s""")
    comm_cur.execute(_sql, (ip, ))
    comm_res = comm_cur.fetchone()
    comm_id = comm_res[0]
    _sql =("""select p.number from net.ports p left outer join UTM5.ip_groups g on p.commutator_id = g.switch_id and p.number = g.port_id 
        where p.commutator_id = %s
        and p.type = 'empty' and g.account_id is null and p.number < 24 and (p.comment = '' or p.comment is null) order by p.number""")
    comm_cur.execute(_sql, (str(comm_id), ))
    comm_cur.close()
    netdb.close()
    return comm_cur.fetchall()
    
# def get_street_id(street, house):
    # bazadb = bazadb_connect()
    # cur = bazadb.cursor(buffered=True)
    # _sql = """select b.id from buildings b join streets s on s.id = b.street_id 
                # where s.name = %s 
                # and b.number = %s;"""
    # cur.execute(_sql, (street, house))
    # res = cur.fetchone()
    # if res is not None:
        # street_id = res[0]
        # _sql = """select s.name, b.number, i.title, i.type, CONCAT('https://atk.is/schemes/', i.building_id, '/', i.date_upd, '.', i.fext) as link 
                    # from buildings b join building_image i on b.id = i.building_id join streets s on s.id = b.street_id 
                    # where b.id = %s;"""
        # cur.execute(_sql, (street_id,))
        # res = cur.fetchall()
    # else:
        # res = ''
    # return res
    
def get_drs(street, house):
    bazadb = bazadb_connect()
    cur = bazadb.cursor(buffered=True)
    _sql = """select b.id from buildings b join streets s on s.id = b.street_id 
                where s.name = %s 
                and b.number = %s;"""
    cur.execute(_sql, (street, house))
    res = cur.fetchone()
    if res is not None:
        street_id = res[0]
        _sql = """select CONCAT('https://atk.is/schemes/', i.building_id, '/', i.date_upd, '.', i.fext) as link 
                    from buildings b join building_image i on b.id = i.building_id join streets s on s.id = b.street_id 
                    where b.id = %s and i.type = 'drs';"""
        cur.execute(_sql, (street_id,))
        res1 = cur.fetchall()
         
        _sql = """select i.title
                    from buildings b join building_image i on b.id = i.building_id join streets s on s.id = b.street_id 
                    where b.id = %s and i.type = 'drs';"""
        cur.execute(_sql, (street_id,))
        res2 = cur.fetchall()
    else:
        res1 = ''
        res2 = ''
    cur.close()
    bazadb.close()
    return res1, res2
    
def get_link(street, house):
    bazadb = bazadb_connect()
    cur = bazadb.cursor(buffered=True)
    _sql = """select b.id from buildings b join streets s on s.id = b.street_id 
                where s.name = %s 
                and b.number = %s;"""
    cur.execute(_sql, (street, house))
    res = cur.fetchone()
    if res is not None:
        street_id = res[0]
        _sql = """select CONCAT('https://atk.is/schemes/', i.building_id, '/', i.date_upd, '.', i.fext) as link 
                    from buildings b join building_image i on b.id = i.building_id join streets s on s.id = b.street_id 
                    where b.id = %s;"""
        cur.execute(_sql, (street_id,))
        res = cur.fetchall()
    else:
        res = ''
    cur.close()
    bazadb.close()
    return res
    
def get_schemes_name(street, house):
    bazadb = bazadb_connect()
    cur = bazadb.cursor(buffered=True)
    _sql = """select b.id from buildings b join streets s on s.id = b.street_id 
                where s.name = %s 
                and b.number = %s;"""
    cur.execute(_sql, (street, house))
    res = cur.fetchone()
    if res is not None:
        street_id = res[0]
        _sql = """select i.title 
                    from buildings b join building_image i on b.id = i.building_id join streets s on s.id = b.street_id 
                    where b.id = %s;"""
        cur.execute(_sql, (street_id,))
        res = cur.fetchall()
    else:
        res = ''
    cur.close()
    bazadb.close()
    return res

def check_command_allow(chat_id, command):
    for key in access_list: 
        access = access_list.get(key).split()
        if (str(chat_id) == key) and command in access:
            return True

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
    s = requests.Session()
    r = s.get(url.get('root_url'), headers = {'User-Agent': user_agent_val})
    cookie = s.cookies.get(url.get('cookie'), domain=url.get('host'))
    s.headers.update({'Referer':url.get('ref_url_ref')})
    s.headers.update({'User-Agent':user_agent_val})
    r = s.get(url.get('auth_page'), headers = {'User-Agent': user_agent_val})
    p = s.post(url.get('auth_page'), {
    'sectok' : '', 
    'id' : 'start',
    'do' : 'login',
    'u' : login,
    'p' : password,
    'r' : 1
    })
    return s
    
def search_pages(arg):
    s = start_session()
    r = s.get(url.get('search_url') + arg, headers = {'User-Agent': user_agent_val})
    c = r.content
    
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
    
    r.close()
    return msg, num, svars
    
def search_files(arg):
    s = s = start_session()
    r = s.get(url.get('root_url') + arg, headers = {'User-Agent': user_agent_val})
    c = r.content
    r.close()
    return c
    
def get_file(arg):
    s = start_session()
    r = s.get(url.get('root_url') + arg, headers = {'User-Agent': user_agent_val})
    r.close()
    return r
    
def write_file(n, h):
    f = open(n, "wb")
    r = get_file(h)
    f.write(r.content)
    f.close()
    
def write_scheme(n, h):
    s = requests.Session()
    r = s.get('https://atk.is/', headers = {'User-Agent': user_agent_val})
    f = open(n, "wb")
    r = s.get(h, headers = {'User-Agent': user_agent_val})
    f.write(r.content)
    f.close()
    r.close()
    
def parse_pdf(arg):
    files = []
    soup = BeautifulSoup(arg,'lxml')
    for var in soup.findAll('a', class_="media mediafile mf_pdf"):
        n = var["title"]
        h = var['href']
        n = ('.pdf'.join(n.split('.pdf')[:-1]) + '.pdf')
        n = n.replace('corp', '').replace('pld', '')
        path = (save_dir) + n.replace('corp:pld:', '').replace('_', ' ').replace('corp:','').replace('pld1:', '').replace('it:', '').replace('tp:', '').replace('/', '').replace('\\', '').replace(':', '')
        write_file(path, h)
        files.append(path)
    return files

@bot.message_handler(content_types=['text'])
def pld(message):
    global links
    global request_num
    global request_str
    global request
    global request_drs
    chat_id = message.chat.id
    command = get_command(message.text).lower()
    
    try:
        args = extract_arg(message.text)[0]
    except:
        args = ''
        pass
        
    try:
        #FREE PORT
        if ((command == 'порт') and (args != "")):
            if check_command_allow(chat_id, command):
                if (check_IPV4(message.text.split(' ')[1])!= "") :
                    ip = check_IPV4(message.text.split(' ')[1])
                    if check_comm_aviability(ip) > 0 :
                        msg = "Свободные порты на коммутаторе " + ip + ":\n"
                        port_res = free_ports(ip)
                        for port in port_res :
                            msg = msg + str(port[0]) + ", "
                        bot.reply_to(message, msg[:-2])
                    else :
                        bot.reply_to(message, "Коммутатор " + ip + " недоступен или не существует")
            else:
                msg = 'UNAUTORIZED ACCESS ATTEMP from '+str(chat_id)
                logging.warning(msg)
        if ((command == 'схема') and (args != "")):
            if check_command_allow(chat_id, command):
                try:
                    house = ' '.join(args.split(' ')[-1:])
                    street = ' '.join(args.split(' ')[:-1])
                                       
                    #msg = get_street_id(street, house)
                    name = get_schemes_name(street, house)
                    link = get_link(street, house)
                    
                    _name = []
                    _link = []
                    
                    for key in range(len(name)):
                        _name.append(str(name[key]).replace('\'','')[1:-2])

                    for key in range(len(link)):
                        _link.append(str(link[key]).replace('\'','')[1:-2])

                    _sum = [list(tup) for tup in zip(_name, _link)]
                    
                    if name == '':
                        msg = "Неправильный адрес"
                        bot.reply_to(message, msg)
                    else:
                        
                        files = []
 
                        for key in _sum:
                            if (key[1][-3:]) != 'vsd':
                                n = key[0] + key[1][-4:]
                                write_scheme(save_dir + n, key[1])
                                files.append(save_dir + n)
                                print (key)
                                
                        if (len(files) == 0):
                            bot.reply_to(message, "Нет файлов")
                        else:
                            count = len(files) // 10
                            bot.reply_to(message, "Файлов нашлось: " + str(len(files)))
                        
                            for x in range(count + 1):
                                bot.send_media_group(chat_id, [telebot.types.InputMediaDocument(open(doc, 'rb')) for doc in files[x*10:x*10+10]])
                                time.sleep(wait_time)
                    
                except Exception as e:
                    print (e)
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    logging.error(exc_type, fname, exc_tb.tb_lineno)
                    pass
                
        #WIKI SEARCH
        elif ((command == 'плд') and (args != "")):
            if check_command_allow(chat_id, command):
            
                msg = 'pld search: "' + 'плд ' + args + '" from: ' + str(chat_id)
                logging.warning(msg)
                
                msg, num, svars = search_pages(args)
                
                if (num == 1):
                    bot.reply_to(message, msg)
                    keys = list(svars.keys())
                    src = svars.get(keys[num-1])
                    c = search_files(src)
                    files = parse_pdf(c)
                    request = {chat_id : False}
                    
                    if (len(files) == 0):
                        bot.reply_to(message, "Нет файлов")
                    else:
                        count = len(files) // 10
                        bot.reply_to(message, "Файлов нашлось: " + str(len(files)))
                        
                        for x in range(count + 1):
                            bot.send_media_group(chat_id, [telebot.types.InputMediaDocument(open(doc, 'rb')) for doc in files[x*10:x*10+10]])
                            time.sleep(wait_time)

                elif (num > 1):
                    msg += "\nКакой номер интересует?"
                    bot.reply_to(message, msg)
                    request = {chat_id : True}
                    request_str = {chat_id : svars}
                    request_num = {chat_id : num}
                else:
                    bot.send_message(chat_id, msg)
            else:
                msg = 'UNAUTORIZED ACCESS ATTEMP from '+str(chat_id)
                logging.warning(msg)
                
        elif ((command == 'дрс') and (args != "")):
            if check_command_allow(chat_id, command):
                try:
                    house = ' '.join(args.split(' ')[-1:])
                    street = ' '.join(args.split(' ')[:-1])
                                       
                    link, name = get_drs(street, house)
                    
                    _name = []
                    _link = []
                    
                    for key in range(len(name)):
                        _name.append(str(name[key]).replace('\'','')[1:-2])

                    for key in range(len(link)):
                        _link.append(str(link[key]).replace('\'','')[1:-2])
                    
                    _sum = [list(tup) for tup in zip(_name, _link)]
                    
                    print(str(_sum))
                    
                    if name == '':
                        msg = "Неправильный адрес"
                        bot.reply_to(message, msg)
                    else:
                        
                        files = []
 
                        for key in _sum:
                            if (key[1][-3:]) != 'vsd':
                                n = key[0] + key[1][-4:]
                                print(n)
                                print(key[1])
                                write_scheme(save_dir + n, key[1])
                                files.append(save_dir + n)
                                print (key)
                                
                        if (len(files) == 0):
                            bot.reply_to(message, "Нет файлов")
                        else:
                            count = len(files) // 10
                            bot.reply_to(message, "Файлов нашлось: " + str(len(files)))
                        
                            for x in range(count + 1):
                                bot.send_media_group(chat_id, [telebot.types.InputMediaDocument(open(doc, 'rb')) for doc in files[x*10:x*10+10]])
                                time.sleep(wait_time)

                    
                except Exception as e:
                    print (e)
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    logging.error(exc_type, fname, exc_tb.tb_lineno)
                    pass
                
        elif (command.isdigit() and request.get(chat_id) and (int(command)-1 <= request_num.get(chat_id)) and (int(command)-1 >= 0)):
            request = {chat_id : False}
            request_drs = {chat_id : False}
            keys = list(request_str.get(chat_id).keys())
            src = request_str.get(chat_id).get(keys[int(command)-1])
            c = search_files(src)
            files = parse_pdf(c)
            request = {chat_id : False}
            
            if (len(files) == 0):
                bot.reply_to(message, "Нет файлов")
            else:
                count = len(files) // 10
                bot.reply_to(message, "Файлов нашлось: " + str(len(files)))
                
                for x in range(count + 1):
                    bot.send_media_group(chat_id, [telebot.types.InputMediaDocument(open(doc, 'rb')) for doc in files[x*10:x*10+10]])
                    time.sleep(wait_time)
                        
            
        else:
            pass
            
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
