#!/usr/bin/env python3

import traceback
import sys
import requests
import telebot
import os
import logging
import time
import re
import mysql.connector
import psycopg2
import gspread

from configparser import ConfigParser
from datetime import date, datetime, timezone
from contextlib import closing
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from pexpect import pxssh
from bs4 import BeautifulSoup
from pyzabbix import ZabbixAPI
from telebot import types

request_num = {}
request_str = {}
request = {}
multiple_zabbix_host = {}
multiple_op_host = {}
multiple_zabbix_graphs = {}
zabbix_num = {}
zabbix_hosts = {}
zabbix_graphs = {}
multiple_odf = {}
multiple_odf_num = {}

#грузим всё из конфига
config = ConfigParser()
config.read('config.ini')
bot_id = config.get('id', 'bot')
login = config.get('id', 'login')
password = config.get('id', 'password')
password2 = config.get('id', 'password2')
save_dir = config.get('vars', 'save_dir')
user_agent_val = config.get('vars', 'user_agent_val')
wait_time = int(config.get('vars', 'wait_time'))
access_list = dict(config.items('access_list'))
zabbix_host = config.get('zabbix', 'zabbix_host')
zabbix_login = config.get('zabbix', 'login')
zabbix_password = config.get('zabbix', 'password')
zabbix_domain = config.get('zabbix', 'zabbix_domain')
zabbix_graph_width = config.get('zabbix', 'width')
zabbix_graph_height = config.get('zabbix', 'height')
cam_login = config.get('cam', 'login')
cam_password = config.get('cam', 'password')
selenium_server = config.get('selenium', 'server')
selenium_username = config.get('selenium', 'username')
selenium_usernamecross = config.get('selenium', 'usernamecross')
selenium_password = config.get('selenium', 'password')
selenium_mo = config.get('selenium', 'mo')
selenium_it = config.get('selenium', 'it')
selenium_oe = config.get('selenium', 'oe')
selenium_root = config.get('selenium', 'root')
selenium_root_cross = config.get('selenium', 'root_cross')
selenium_cross_search = config.get('selenium', 'cross_search')
ping_hostname = config.get('ping', 'hostname')
ping_username = config.get('ping', 'username')
ping_password = config.get('ping', 'password')
google_oe = config.get('id', 'google_oe')
google_it = config.get('id', 'google_it')
log_chat_id = config.get('id', 'log')
sw_pass = config.get('id', 'sw_pass')
cacti_login = config.get('id', 'cacti_login')
cacti_password = config.get('id', 'cacti_password')
graph_port = config.get('id', 'graph_port')

url = {
    'root_url': config.get('url', 'root_url'),
    'ref_url_ref': config.get('url', 'ref_url_ref'),
    'cookie': config.get('url', 'cookie'),
    'host': config.get('url', 'host'),
    'auth_page': config.get('url', 'auth_page'),
    'search_url': config.get('url', 'search_url'),
    'cacti_auth': config.get('url', 'cacti_auth'),
    'cacti_search': config.get('url', 'cacti_search'),
    'cacti': config.get('url', 'cacti'),
}

netdb_vars = {
    'host': config.get('mysql_netdb', 'host'),
    'user': config.get('mysql_netdb', 'login'),
    'password': config.get('mysql_netdb', 'password'),
    'database': config.get('mysql_netdb', 'database')
}

contacts = {
    'oe1': config.get('contacts', 'oe1'),
    'oe2': config.get('contacts', 'oe2'),
    'oe3': config.get('contacts', 'oe3'),
    'oe4': config.get('contacts', 'oe4'),
    'oe5': config.get('contacts', 'oe5'),
    'oe6': config.get('contacts', 'oe6'),
    'it1': config.get('contacts', 'it1'),
    'it2': config.get('contacts', 'it2'),
    'it3': config.get('contacts', 'it3'),
    'it4': config.get('contacts', 'it4'),
    'it5': config.get('contacts', 'it5'),
    'it6': config.get('contacts', 'it6'),
    'it7': config.get('contacts', 'it7'),
    'it8': config.get('contacts', 'it8'),
}

bazadb_vars = {
    'host': config.get('mysql_baza', 'host'),
    'user': config.get('mysql_baza', 'login'),
    'password': config.get('mysql_baza', 'password'),
    'database': config.get('mysql_baza', 'database')
}

etraxisdb_vars = {
    'host': config.get('mysql_etraxis', 'host'),
    'user': config.get('mysql_etraxis', 'login'),
    'password': config.get('mysql_etraxis', 'password'),
    'database': config.get('mysql_etraxis', 'database')
}

pg_atk_bot_vars = {
    'host': config.get('pg_atk_bot', 'host'),
    'user': config.get('pg_atk_bot', 'login'),
    'password': config.get('pg_atk_bot', 'password'),
    'database': config.get('pg_atk_bot', 'database')
}

#включаем логи в файл и в stdout
logging.basicConfig(filename=os.path.basename(sys.argv[0]) + '.log', \
                                                level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

try:
    bot = telebot.TeleBot(bot_id)
    zapi = ZabbixAPI(zabbix_host)
    zapi.login(zabbix_login, zabbix_password)
except Exception as e:
    print (e)
    msg = traceback.format_exc()
    print (msg)
    sys.exit(0)

#отлавливаем ошибки и постим в тележный канал под логи
def error_capture(**kwargs):
    options = {
            'e' : None,
            'message' : None,}

    options.update(kwargs)
    e = options.get('e')
    message = options.get('message')

    if e is not None:
        print (e)
        msg = traceback.format_exc()
        try:
            bot.send_message(log_chat_id, msg)
        except:
            msg = '! telebot error log msg not send. ' + msg
        if message is not None:
            try:
                bot.reply_to(message, e)
            except:
                 pass
        logging.error(msg)
try:
    gc = gspread.service_account()
    sh_oe = gc.open_by_url(google_oe)
    sh_it = gc.open_by_url(google_it)
except Exception as e:
    error_capture(e=e)

#каждую команду пишем в лог для истории запросов, включая неавторизованные
def cmd_log(message, auth):
    _chat_id = str(message.chat.id)
    _lng = ''
    _username = ''
    _first_name = ''
    _last_name = ''
    _title = ''
    _user_id = str(message.from_user.id)
    _language_code = ''
    if _user_id != _chat_id:
        _chat_id = _chat_id + ', from user id: ' + _user_id
    if (message.chat.type == 'group' or message.chat.type == 'supergroup' \
                                    or message.chat.type == 'channel'):
        if message.chat.title is not None:
            _title = message.chat.title
    else:
        _title = 'private message'
    if message.from_user.username is not None:
        _username = message.from_user.username
    if message.from_user.last_name is not None:
        _last_name = message.from_user.last_name
    if message.from_user.first_name is not None:
        _first_name = message.from_user.first_name
    if message.from_user.language_code is not None:
        _language_code = message.from_user.language_code
    msg = 'request from chat id: ' + _chat_id + ', chat name: ' + _title \
            + ', username: @' + _username + ', first name: ' + _first_name \
            + ', last name: ' + _last_name + ', language code: ' \
            + _language_code + '. REQUEST: ' + message.text
    if auth:
        logging.info(msg)
    else:
        msg = '‼️ UNAUTORIZED ' + msg
        logging.warning(msg)
        bot.send_message(log_chat_id, msg)

#ищем в базе id здания
def search_ids(street, house):
    bazadb = bazadb_connect()
    cur = bazadb.cursor(buffered=True)
    if house == '%':
        _sql = """select b.id from buildings b 
                join streets s on s.id = b.street_id 
                where s.name like %s
                and s.city = 'Владивосток';"""
        cur.execute(_sql, (street, ))
    else:
        _sql = """select b.id from buildings b 
                    join streets s on s.id = b.street_id 
                    where s.name like %s 
                    and b.number like %s
                    and s.city = 'Владивосток';"""
        cur.execute(_sql, (street, house))
    result = cur.fetchall()
    cur.close()
    bazadb.close()
    return result

#постим графики трафика юриков
def jur_graph(args, message):
    jid = 'Network traffic on jur' + str(args)
    records = ''
    conn = psycopg2.connect(dbname='zabbix', \
                            user='postgres', \
                            host='172.16.0.246')
    cursor = conn.cursor()
    _sql = """select graphid from graphs
                where name = %s limit 1;"""
    cursor.execute(_sql, (str(jid), ))
    records = cursor.fetchall()
    cursor.close()
    conn.close()

    if records:
        h = zapi.host.get(search={'host': 'r-jurs'}, output=['hostid'])
        _id = h[0].get('hostid')
        _gid = str(records[0])[1:-2]
        _name = save_dir + 'jur.png'
        zabbix_get_graph(_name, _gid)
        img = open(_name, 'rb')
        bot.send_photo(message.chat.id, img)
        img.close()
    else:
        bot.reply_to(message, "Нет такого графика юрика")
    return

#ищем графики в заббиксе, захардкожен диапазон -- 3 дня
def zabbix_get_graph(n, gid):
    h = zabbix_host + '/chart2.php?graphid=' + gid \
            + '&from=now-3d&to=now&profileIdx=web.graphs.filter&width=' \
            + zabbix_graph_width + '&height=' + zabbix_graph_height
    f = open(n, "wb")
    s = requests.Session()
    r = s.get(zabbix_host, headers={'User-Agent': user_agent_val})
    cookie = s.cookies.get('zbx_session', domain=zabbix_domain )
    s.headers.update({'Referer': zabbix_host})
    p = s.post(zabbix_host + '/index.php?login=1', {
    'name': zabbix_login,
    'password': zabbix_password,
    'enter': 'Enter'
    })
    r = s.get(h, headers={'User-Agent': user_agent_val})
    r.close()
    f.write(r.content)
    f.close()

#проверка на русский алфавит
def match(text, alphabet=set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')):
    return not alphabet.isdisjoint(text.lower())

#достаём из базы инфу по коммутатору на основе id здания
def find_switch_by_address(args):
    #return [[switch 1 of street 1, switch 2 of street 1], [switch 1 of street 2], [...]]
    result = []

    def search_vars(street_id):
        netdb = netdb_connect()
        cur = netdb.cursor(buffered=True)
        _sql = ("""select name, status, address, comments, ip 
                    from commutators where building_id = %s""")
        cur.execute(_sql, (street_id,))
        result = cur.fetchall()
        cur.close()
        netdb.close()
        return result

    if match(args):
        if args.find(', ') != -1:
            house = ' '.join(args.split(', ')[-1:])
            street = ' '.join(args.split(', ')[:-1])

            if house.find('?') != -1:
                house = house[:-1]
                _ids = search_ids(street + '%', house + '%')
            else:
                _ids = search_ids(street + '%', house)
                
            if _ids is not None:
                result = []
                for key in _ids:
                    result.append(search_vars(key[0]))
            
        elif args.find(' ') != -1:
            house = args.split(' ')[1]
            street = args.split(' ')[0]
            
            if house.find('?') != -1:
                house = house[:-1]
                _ids = search_ids(street + '%', house + '%')
            else:
                _ids = search_ids(street + '%', house)
                
            if _ids is not None:
                result = []
                for key in _ids:
                    result.append(search_vars(key[0]))
        else:
            street = args
            _ids = search_ids(street + '%', '%')
            if _ids is not None:
                result = []
                for key in _ids:
                    result.append(search_vars(key[0]))
    
    else:
        result = []
        name = args
        netdb = netdb_connect()
        cur = netdb.cursor(buffered=True)
        _sql = ("""select name, status, address, comments, ip 
                    from commutators where name like %s""")
        cur.execute(_sql, (name + '%', ))
        result.append(cur.fetchall())
        cur.close()
        netdb.close()
    
    result = [x for x in result if x]
    return result

#статус коммутаторов
def switch_status(args, message):
    result = ''
    _streets = find_switch_by_address(args)
    _status = '❓'

    if _streets is not None:
        result = '💚 up, 💔 down, 🤍 stock\n\n'
        for switches in _streets:
            for key in switches:
                if key[1] == "up":
                    _status = "💚 "
                elif key[1] == "down":
                    _status = "💔 "
                elif key[1] == "stock":
                    _status = "🤍 "
                if key[0][:2] == ('A-') or key[0][:4] == ('MIK-'):
                    result += _status + key[0] + ' ' + key[2] + ' ' + key[3] + '\n'
                else:
                    result += _status + key[0] + ' ' + key[4] + '\n'
    send_msg_with_split(message, result, 4000)

#подключаемся к локальной базе, нужна для определения привязки по районам
def pg_connect():
#    pg = psycopg2.connect(
    pg = mysql.connector.connect(
        host = pg_atk_bot_vars.get('host'),
        user = pg_atk_bot_vars.get('user'),
        password = pg_atk_bot_vars.get('password'),
#        dbname = pg_atk_bot_vars.get('database')
	database = pg_atk_bot_vars.get('database')
        )
    return pg

#база трекера
def etraxisdb_connect():
    etraxisdb = mysql.connector.connect(
        host = etraxisdb_vars.get('host'),
        user = etraxisdb_vars.get('user'),
        password = etraxisdb_vars.get('password'),
        database = etraxisdb_vars.get('database')
        )
    return etraxisdb

#база коммутаторов
def netdb_connect():
    netdb = mysql.connector.connect(
        host = netdb_vars.get('host'),
        user = netdb_vars.get('user'),
        password = netdb_vars.get('password'),
        database = netdb_vars.get('database')
        )
    return netdb

#схемы, здания
def bazadb_connect():
    bazadb = mysql.connector.connect(
        host = bazadb_vars.get('host'),
        user = bazadb_vars.get('user'),
        password = bazadb_vars.get('password'),
        database = bazadb_vars.get('database')
        )
    return bazadb

#от малышева
def check_comm_aviability(ip):
    netdb = netdb_connect()
    #Получаем id коммутатора
    comm_cur = netdb.cursor(buffered=True)
    comm_cur.execute("select id from commutators where ip = %s", (ip, ))
    comm_res = comm_cur.fetchall()
    comm_cur.close()
    netdb.close()
    return len(comm_res)

#свободные порты в коммутаторах
def free_ports(message, args):
    def fnd(ip):
        netdb = netdb_connect()
        comm_cur = netdb.cursor(buffered=True)
        _sql =("""select id from commutators 
                where ip = %s""")
        comm_cur.execute(_sql, (ip, ))
        comm_res = comm_cur.fetchone()
        comm_cur.close()
        comm_cur = netdb.cursor(buffered=True)
        comm_id = comm_res[0]
        _sql =("""select p.number from net.ports p left outer 
                    join UTM5.ip_groups g on p.commutator_id = g.switch_id 
                                                and p.number = g.port_id 
                    where p.commutator_id = %s
                    and p.type = 'empty' 
                    and g.account_id is null 
                    and (p.comment = '' or p.comment is null) 
                    order by p.number""")
        comm_cur.execute(_sql, (str(comm_id), ))
        rez = comm_cur.fetchall()
        comm_cur.close()
        netdb.close()
        return rez

    ip = check_IPV4(args)
    if ip:
        if check_comm_aviability(ip) > 0:
            msg = "Свободные порты на коммутаторе " + ip + ":\n"
            port_res = fnd(ip)
            for port in port_res :
                msg = msg + str(port[0]) + ", "
            bot.reply_to(message, msg[:-2])
        else:
            bot.reply_to(message, "Коммутатора с ip адресом: " + ip + " нет в базе.")
    else:
        bot.reply_to(message, "Неправильный ip адрес.")

#ищем все схемы
def get_scheme(args, message, stype):
    result = []
    def link(street_id, stype):
        bazadb = bazadb_connect()
        cur = bazadb.cursor(buffered=True)
        if stype != 'drs':
            stype = '%'
            
        _sql = """select CONCAT('https://atk.is/schemes/', 
                                        i.building_id, '/', 
                                        i.date_upd, '.', 
                                        i.fext) as link 
                            from buildings b 
                            join building_image i on b.id = i.building_id 
                            join streets s on s.id = b.street_id 
                            where b.id = %s and i.type like %s;"""
        cur.execute(_sql, (street_id, stype))
        _link = cur.fetchall()
        _sql = """select i.title from buildings b 
                    join building_image i on b.id = i.building_id 
                    join streets s on s.id = b.street_id 
                    where b.id = %s and i.type like %s;"""
        cur.execute(_sql, (street_id, stype))
        _name = cur.fetchall()
        _sql = """select CONCAT(s.name, ' ', b.number) from buildings b 
            join building_image i on b.id = i.building_id 
                    join streets s on s.id = b.street_id 
                    where b.id = %s and i.type like %s;"""
        cur.execute(_sql, (street_id, stype))
        _address = cur.fetchall()
        cur.close()
        bazadb.close()
        result = {'link': _link, 'name': _name, 'address': _address}
        return result
    
    if match(args):
        if args.find(', ') != -1:
            house = ' '.join(args.split(', ')[-1:])
            street = ' '.join(args.split(', ')[:-1])
            
            _ids = search_ids(street + '%', house)
            
            if _ids is not None:
                for street_id in _ids:
                    result.append(link(street_id[0], stype))
                
        elif args.find(' ') != -1:
            house = args.split(' ')[1]
            street = args.split(' ')[0]
            
            _ids = search_ids(street + '%', house)
            
            if _ids is not None:
                for street_id in _ids:
                    result.append(link(street_id[0], stype))
    else:
        name = args
        netdb = netdb_connect()
        cur = netdb.cursor(buffered=True)
        _sql = ("""select name, status, address, comments, ip 
                    from commutators where name like %s""")
        cur.execute(_sql, (name + '%', ))
        res = cur.fetchall()
        cur.close()
        netdb.close()
        
        if res:
            args = res[0][2]
            
            if args.find(' ') != -1:
                house = args.split(' ')[1]
                street = args.split(' ')[0]
                _ids = search_ids(street + '%', house)
                
                if _ids is not None:
                    for street_id in _ids:
                        result.append(link(street_id[0], stype))
    
    if result:
        files = []
        _name = []
        _link = []
        _address = []
        
        for b in result:
            lnk = b.get('link')
            name = b.get('name')
            address = b.get('address')
            
            for k in range(len(lnk)):
                _link.append(str(lnk[k]).replace('\'','')[1:-2])
            
            for k in range(len(name)):
                _name.append(str(name[k]).replace('\'','')[1:-2])
                
            for k in range(len(address)):
                _address.append(str(address[k]).replace('\'','')[1:-2])

        _sum = [list(tup) for tup in zip(_name, _link, _address)]
            
        for key in _sum:
            if (key[1][-3:]) != 'vsd':
                n = key[2] + ' (' + key[0] + ')' + key[1][-4:]
                n = n.replace('/','-')
                write_scheme(save_dir + 'scheme/' + n, key[1])
                files.append(save_dir + 'scheme/' + n)
                        
        if (len(files) == 0):
            bot.reply_to(message, "Нет файлов")
        else:
            count = len(files) // 10
            bot.reply_to(message, "Файлов нашлось: " + str(len(files)))
        
            for x in range(count + 1):
                bot.send_media_group(message.chat.id, [telebot.types.InputMediaDocument(open(doc, 'rb')) for doc in files[x*10:x*10+10]])
                time.sleep(wait_time)
    else:
        msg = "Ничего не нашлось."
        bot.reply_to(message, msg)                
    
    return result

#инфа по зданию
def get_house_info(args, message):
    res = ''
    if match(args):
        if args.find(', ') != -1:
            house = ' '.join(args.split(', ')[-1:])
            street = ' '.join(args.split(', ')[:-1])
            _ids = search_ids(street + '%', house)
            if _ids:
                bazadb = bazadb_connect()
                cur = bazadb.cursor(buffered=True)
                street_id = _ids[0][0]
                _sql = """select description, key_name from buildings b 
                            join streets s on s.id = b.street_id 
                            where b.id = %s;"""
                cur.execute(_sql, (street_id,))
                res = cur.fetchall()
                cur.close()
                bazadb.close()
                
                _info = ''
                _keys = ''
                
                if res[0][0]:
                    _info = res[0][0]
                
                if res[0][1]:
                    _keys = res[0][1]
                
                if len(res) == 0:
                    res = '?'
                elif len(res[0][0]) == 0:
                    res = '?'
                else:
                    res = street + ', ' + house + '\n' + _info + '\n\n' + _keys
            else:
                res = '?'
                
        else:
            if args.find(' ') != -1:
                street = args.split(' ')[0]
                house = args.split(' ')[1]
                _ids = search_ids(street + '%', house)
                
                if _ids:
                    bazadb = bazadb_connect()
                    cur = bazadb.cursor(buffered=True)
                    street_id = _ids[0][0]
                    _sql = """select description, key_name from buildings b  
                                join streets s on s.id = b.street_id 
                                where b.id = %s;"""
                    cur.execute(_sql, (street_id,))
                    res = cur.fetchall()

                    _info1 = res[0][0]
                    _info2 = res[0][1]

                    if not _info1:
                        _info1 = ''

                    if not _info2:
                        _info2 = ''

                    res = street + ', ' + house + '\n' + _info1 + '\n\n' + _info2
                    cur.close()
                    bazadb.close()
                else:
                    res = '?'
                
            else:
                res = "?"
    else:
        name = args
        netdb = netdb_connect()
        cur = netdb.cursor(buffered=True)
        _sql = ("""select name, status, address, comments, ip 
                    from commutators where name like %s""")
        cur.execute(_sql, (name + '%', ))
        res = cur.fetchall()
        cur.close()
        netdb.close()
        
        args = res[0][2]
        
        house = args.split(' ')[1]
        street = args.split(' ')[0]

        if args.find(' ') != -1:
            _ids = search_ids(street + '%', house)
            if _ids:
                bazadb = bazadb_connect()
                cur = bazadb.cursor(buffered=True)
                street_id = _ids[0][0]
                _sql = """select description, key_name from buildings b 
                            join building_image i on b.id = i.building_id 
                            join streets s on s.id = b.street_id 
                            where b.id = %s;"""
                cur.execute(_sql, (street_id,))
                res = cur.fetchall()
                if len(res) == 0:
                    res = '?'
                elif len(res[0][0]) == 0:
                    res = '?'
                else:
                    res = street + ', ' + house + '\n' + res[0][0] + '\n\n' + res[0][1]
            else:
                res = '?'
            cur.close()
            bazadb.close()
        else:
            res = "?"
        
    msg = ""
    if (res != "" and res != "?"):
        msg = res
    else:
        msg = "Ничего не нашлось."
    send_msg_with_split(message, msg, 4000)

#проверяем доступность команды для определённого чата
def check_command_allow(message, command):
    full_cmd = access_list.get('command_list').split()
    chat_id = message.chat.id
    _auth = False
    if command in full_cmd:
        for key in access_list: 
            access = access_list.get(key).split()
            if (str(chat_id) == key) and command in access:
                _auth = True
        cmd_log(message, _auth)
    return _auth

#от малышева
def check_IPV4(ip):
    def isIPv4(s):
        try: return str(int(s)) == s and 0 <= int(s) <= 255
        except: return False
    if ip.count(".") == 3 and all(isIPv4(i) for i in ip.split(".")):
        return ip
    elif ip.count(".") == 1 and all(isIPv4(i) for i in ip.split(".")):
        return "10.254." + ip
    else:
        return False

#отрезали команду, оставили всё остальное
def extract_arg(arg):
    return arg.split(maxsplit=1)[1:]

#оставили команду, отрезали всё остальное
def get_command(arg):
    return arg.split(' ', 1)[0]

#стартуем сессию для парсинга плд, притворяемся браузером, логинимся
def start_session():
    s = requests.Session()
    r = s.get(url.get('root_url'), headers={'User-Agent': user_agent_val})
    cookie = s.cookies.get(url.get('cookie'), domain=url.get('host'))
    s.headers.update({'Referer':url.get('ref_url_ref')})
    s.headers.update({'User-Agent':user_agent_val})
    r = s.get(url.get('auth_page'), headers={'User-Agent': user_agent_val})
    p = s.post(url.get('auth_page'), {
    'sectok': '', 
    'id': 'start',
    'do': 'login',
    'u': login,
    'p': password,
    'r': 1
    })
    return s

#стартуем сессию для кактуса, на данный момент нереализовано, можно выпилить
def start_cacti_session():
    s = requests.Session()
    r = s.get(url.get('cacti_auth'), headers={'User-Agent': user_agent_val})
    #cookie = s.cookies.get(url.get('cookie'), domain=url.get('host'))
    s.headers.update({'Referer':url.get('cacti_auth')})
    s.headers.update({'User-Agent':user_agent_val})
    r = s.get(url.get('cacti_auth'), headers={'User-Agent': user_agent_val})
    p = s.post(url.get('cacti_auth'), {
    'action': 'login',
    'login_username': cacti_login,
    'login_password': cacti_password,
    })
    return s

#поиск страничек в вики с плд
def search_pages(arg):
    s = start_session()
    r = s.get(url.get('search_url') + arg, \
            headers={'User-Agent': user_agent_val})
    c = r.content
    soup = BeautifulSoup(c,'lxml')
    svars = {}
    for var in soup.findAll('a', class_="wikilink1"):
        svars[var['title']] = var['href']
    num = 0
    msg = ""
    for key in svars:
        num += 1
        key = key.replace('corp:pld:', '').replace('_', ' ')
        key = key.replace('corp:','').replace('pld1:', '').replace('it:', '')
        key = key.replace('tp:', '')
        msg += "➡️ " + str(num) + " " + key + "\n"
    msg = "Нашлось совпадений: " + str(num) + "\n\n" + msg
    r.close()
    return msg, num, svars

#это нужно скрестить с парсингом файлов
def search_files(arg):
    s = s = start_session()
    r = s.get(url.get('root_url') + arg, \
            headers={'User-Agent': user_agent_val})
    c = r.content
    r.close()
    return c

#получаем урл файла
def get_file(arg):
    s = start_session()
    r = s.get(url.get('root_url') + arg, \
            headers={'User-Agent': user_agent_val})
    r.close()
    return r

#сохраняем файл на диск
def write_file(n, h):
    f = open(n, "wb")
    r = get_file(h)
    f.write(r.content)
    f.close()

#сохраняем схему на диск
def write_scheme(n, h):
    s = requests.Session()
    r = s.get('https://atk.is/', headers={'User-Agent': user_agent_val})
    f = open(n, "wb")
    r = s.get(h, headers={'User-Agent': user_agent_val})
    f.write(r.content)
    f.close()
    r.close()

#поиск файлов на страничках с плд
def parse_pdf(arg):
    files = []
    soup = BeautifulSoup(arg,'lxml')
    for var in soup.findAll('a', class_="media mediafile mf_pdf"):
        n = var["title"]
        h = var['href']
        n = ('.pdf'.join(n.split('.pdf')[:-1]) + '.pdf')
        n = n.replace('corp', '').replace('pld', '')
        n = n.replace('corp:pld:', '').replace('_', ' ').replace('corp:','')
        n = n.replace('pld1:', '').replace('it:', '').replace('tp:', '')
        n = n.replace('/', '').replace('\\', '').replace(':', '')
        path = (save_dir) + 'pld/' + n
        write_file(path, h)
        files.append(path)
    return files

#получаем картинку с камер хиквижн и хайвотч
def send_camera_image(args, message):
    ip = check_IPV4(args)
    if ip:
        link = 'http://' + cam_login + ':' + cam_password + '@' + ip \
                + '/ISAPI/Streaming/channels/101/picture/'
        imageFile = save_dir + 'cams/' + ip + "_" \
                + str(datetime.timestamp(datetime.now())) + '.jpg'
        os.system('wget '+link+' -O '+imageFile)
        if os.path.getsize(imageFile) > 0:
            img = open(imageFile, 'rb')
            bot.send_photo(message.chat.id, img, caption = ip)
        else:
            link = 'http://' + cam_login + ':' + cam_password + '@' + ip \
                    + '/cgi-bin/snapshot.cgi'
            imageFile = save_dir + 'cams/' + ip + "_" \
                    + str(datetime.timestamp(datetime.now())) + '.jpg'
            os.system('wget '+link+' -O '+imageFile)
            if os.path.getsize(imageFile) > 0:
                img = open(imageFile, 'rb')
                bot.send_photo(message.chat.id, img, caption = ip)
            else:
                bot.reply_to(message, "Изображение недоступно")
    else:
        bot.reply_to(message, "Неправильный ip.")

#график МО, разрешение экрана захардкожено!
def send_mo(message):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Remote(command_executor=selenium_server, \
                options=chrome_options)
        driver.set_window_size(1400, 600)
        driver.get(selenium_root)
        driver.find_element(By.ID, "login").send_keys(selenium_username)
        driver.find_element(By.ID, "pwd").send_keys(selenium_password)
        driver.find_element(By.ID, "loginButton").click()
        driver.get(selenium_mo)
        timeout = 60
        try:
            element_present = EC.presence_of_element_located((By.ID, \
                    'ws-canvas-graphic-overlay'))
            WebDriverWait(driver, timeout).until(element_present)
        except TimeoutException:
            pass
        finally:
            time.sleep(2)
            html_source = driver.page_source
            driver.save_screenshot(save_dir + "screenshot.png")
            driver.quit()  
            file = open(save_dir + 'screenshot.png', 'rb')
            bot.send_photo(message.chat.id, file)
            file.close()
    except Exception as e:
        error_capture(e=e, message=message)
        try:
            driver.quit()
            bot.reply_to(message, e)
        except:
            pass
        
#график ИТ/ЦУС, разрешение экрана захардкожено!
def send_it(message):
    send_work_graph("it", message)

#график ОЭ, разрешение экрана захардкожено!
def send_oe(message):
    send_work_graph("oe", message)

def send_work_graph(type, message):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Remote(command_executor=selenium_server, options=chrome_options)
        
        if type == "oe":
            driver.set_window_size(1500, 1000)
            driver.get(selenium_oe)
        elif type = "it":
            driver.set_window_size(1400, 500)
            driver.get(google_it)

        timeout = 60
        try:
            element_present = EC.presence_of_element_located((By.ID, 'goog-inline-block grid4-inner-container'))
            WebDriverWait(driver, timeout).until(element_present)
        except TimeoutException:
            pass
        finally:
            time.sleep(1)
            html_source = driver.page_source
            driver.save_screenshot(save_dir + "screenshot.png")
            driver.quit()
            file = open(save_dir + 'screenshot.png', 'rb')
            bot.send_photo(message.chat.id, file)
            file.close()
    except Exception as e:
        error_capture(e=e, message=message)
        try:
            driver.quit()
            bot.reply_to(message, e)
        except:
            pass

#поиск по карте оптики, самая жрущая ресурсы хрень, тут костыль на костыле, тайминги подстроены под быстродействие конкретного тазика
def send_map(message, text):
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--incognito")
        driver = webdriver.Remote(command_executor=selenium_server, options=chrome_options)
        driver.set_window_size(1200, 910)
        driver.get(selenium_root_cross)
        timeout = 3
        try:
            element_present = EC.presence_of_element_located((By.ID, 'loginform'))
            WebDriverWait(driver, timeout).until(element_present)
        except TimeoutException:
            pass
        finally:
            
            driver.find_element(By.NAME, "Login").send_keys(selenium_usernamecross)
            driver.find_element(By.NAME, "Password").send_keys(selenium_password)
            driver.find_element(By.NAME, "enter").click()
            timeout = 3
            try:
                element_present = EC.presence_of_element_located((By.ID, 'loginform'))
                WebDriverWait(driver, timeout).until(element_present)
            except TimeoutException:
                pass
            except Exception as e:
                error_capture(e=e, message=message)
            finally:
                driver.find_element(By.NAME, "SelectZone").click()
                driver.get(selenium_cross_search)
                timeout = 80
                try:
                    element_present = EC.presence_of_element_located((By.ID, 'searchtree_set_new_8_span'))
                    WebDriverWait(driver, timeout).until(element_present)
                except TimeoutException:
                    print("Timed out waiting for page to load")
                except Exception as e:
                    error_capture(e=e, message=message)
                finally:
                    try:
                        element_present = EC.presence_of_element_located((By.XPATH, "//*[@class='Building SearchOL ItemInactive olButton ']"))
                        WebDriverWait(driver, timeout).until(element_present)
                        driver.find_element(By.XPATH, "//*[@class='Building SearchOL ItemInactive olButton ']").click()
                    except TimeoutException:
                        pass
                    except Exception as e:
                        error_capture(e=e, message=message)
                    finally:
                        try:
                            element_present = EC.presence_of_element_located((By.XPATH, "//*[@class='ui-layout-toggler ui-layout-toggler-west ui-layout-toggler-open ui-layout-toggler-west-open']"))
                            WebDriverWait(driver, timeout).until(element_present)
                            driver.find_element(By.XPATH, "//*[@class='ui-layout-toggler ui-layout-toggler-west ui-layout-toggler-open ui-layout-toggler-west-open']").click()
                        except TimeoutException:
                            pass
                        except Exception as e:
                            error_capture(e=e, message=message)
                        finally:
                            try:
                                time.sleep(3)
                                element_present = EC.presence_of_element_located((By.XPATH, "//*[@class='ui-layout-toggler ui-layout-toggler-east ui-layout-toggler-open ui-layout-toggler-east-open']"))
                                WebDriverWait(driver, timeout).until(element_present)
                                driver.find_element(By.XPATH, "//*[@class='ui-layout-toggler ui-layout-toggler-east ui-layout-toggler-open ui-layout-toggler-east-open']").click()
                            except TimeoutException:
                                pass
                            except Exception as e:
                                error_capture(e=e, message=message)
                            finally:
                                try:
                                    time.sleep(2)
                                    element_present = EC.presence_of_element_located((By.NAME, 'templateId'))
                                    WebDriverWait(driver, timeout).until(element_present)
                                    driver.find_element(By.NAME, 'templateId').send_keys("Россия, Приморский край, Владивосток " + text)
                                    driver.find_element(By.ID, "SearchButton").click()
                                    try:
                                        time.sleep(15)
                                        element_present = EC.presence_of_element_located((By.XPATH, "//*[@class='firstAddress']"))
                                        WebDriverWait(driver, timeout).until(element_present)
                                        driver.find_element(By.XPATH, "//*[@class='firstAddress']").click()
                                        time.sleep(20)
                                    except TimeoutException:
                                        pass
                                    except Exception as e:
                                        #error_capture(e=e, message=message)
                                        pass
                                except TimeoutException:
                                    pass
                                except Exception as e:
                                    error_capture(e=e, message=message)
                                finally:
                                    try:
                                        element_present = EC.presence_of_element_located((By.ID, "OpenLayers.Control.PanZoomBar_41_zoomin"))
                                        WebDriverWait(driver, timeout).until(element_present)
                                        driver.find_element(By.ID, "OpenLayers.Control.PanZoomBar_41_zoomin").click()
                                        element_present = EC.presence_of_element_located((By.ID, "OpenLayers.Control.PanZoomBar_41_zoomin"))
                                        WebDriverWait(driver, timeout).until(element_present)
                                        driver.find_element(By.ID, "OpenLayers.Control.PanZoomBar_41_zoomin").click()
                                        element_present = EC.presence_of_element_located((By.XPATH, "//*[@class='buttonSearchPanel buttonClose']"))
                                        WebDriverWait(driver, timeout).until(element_present)
                                        driver.find_element(By.XPATH, "//*[@class='buttonSearchPanel buttonClose']").click()
                                    except TimeoutException:
                                        pass
                                    except Exception as e:
                                        error_capture(e=e, message=message)
                                    time.sleep(2)
                                    driver.save_screenshot(save_dir + "screenshot.png")
                                    file = open(save_dir + "screenshot.png", 'rb')
                                    bot.send_photo(message.chat.id, file)
                                    file.close()
        driver.quit()
    except Exception as e:
        error_capture(e=e, message=message)
        try:
            driver.quit()
            bot.reply_to(message, e)
        except:
            pass
    
#пинг обычный и флудом
def ping (message, ping_type, args):
    p_num = 10
    if ' ' in args: 
        ip = check_IPV4(args.split()[0])
        if ip:
            p_num = args.split()[1]
        if not ip:
            ip = check_IPV4(args.split()[1])
            if ip:
                p_num = args.split()[0]
    else:
        ip = check_IPV4(args)
    
    if ip and str(p_num).isdigit():
        if int(p_num) > 1000:
            bot.reply_to(message, "Максимальное количество пакетов: 1000.")
            p_num = str(1000)
        try:
            s = pxssh.pxssh(timeout=300)
            hostname = ping_hostname
            username = ping_username
            password = ping_password
            ssh_prompt = '\r\n' + username + ':~'
            if not s.login(hostname, username, password, auto_prompt_reset=False):
                result = "ssh to monitoring failed"
            else:
                if ping_type == 1 :
                    s.sendline('ping -c '+str(p_num)+' -i 0.2 ' + ip)
                    s.expect(ssh_prompt)
                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                elif ping_type == 2 :
                    s.sendline('pingf -c '+str(p_num)+' -s 1470 ' + ip)
                    s.expect(ssh_prompt)
                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                result = answer[-3] + '\n' + answer[-2]
            s.logout()
            
            msg = '`' + re.escape(result) + '`'
            bot.reply_to(message, msg, parse_mode='MarkdownV2') 
            
        except Exception as e:
            error_capture(e=e)
            result = "pxssh failed on login"
            msg = "timeout"
            bot.reply_to(message, msg, parse_mode='MarkdownV2') 

           
    else:
        bot.reply_to(message, "Неправильный ip.")
    return

#получаем инфу от кастрюли по снмп
def op_info(ip):
    result = []
    try:
        s = pxssh.pxssh()
        hostname = ping_hostname
        username = login
        password = password2
        ssh_prompt = '\r\n' + login + ':~'
        if not s.login(hostname, username, password, auto_prompt_reset=False):
            result = "ssh to monitoring failed"
        else:
            s.sendline('sudo snmpwalk -v2c -c public %s SNMPv2-MIB::sysDescr.0' % ip)
            s.expect(ssh_prompt)
            model = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1]
            if model == '72GE':
                #аттенюатор
                s.sendline('sudo snmpwalk -v2c -c public %s SNMPv2-SMI::enterprises.11195.1.5.9.1.2.1' % ip)
                s.expect(ssh_prompt)
                att = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1]
                try:
                    att = str(round(float(att) * 0.1))
                except:
                    att = 'a'
                
                #эквалайзер
                s.sendline('sudo snmpwalk -v2c -c public %s SNMPv2-SMI::enterprises.11195.1.5.11.1.2.1' % ip)
                s.expect(ssh_prompt)
                eq = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1]
                try:
                    eq = str(round(float(eq) * 0.1))
                except:
                    eq = 'eq'
                    
                #оптический усилитель
                s.sendline('sudo snmpwalk -v2c -c public %s SNMPv2-SMI::enterprises.11195.1.5.13.0' % ip)
                s.expect(ssh_prompt)
                g = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1]
                
                try:
                    if int(g) == 256:
                        g = 'auto'
                    elif int(g) == 1:
                        g = 'off'
                    else:
                        g = str(int(g)-1) + 'dB'
                except:
                    g = 'g'
                    
                #электрический сигнал 1
                s.sendline('sudo snmpwalk -v2c -c public %s SNMPv2-SMI::enterprises.11195.1.5.16.1.2.2' % ip)
                s.expect(ssh_prompt)
                rf = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1]
                
                #оптический сигнал 1
                s.sendline('sudo snmpwalk -v2c -c public %s .1.3.6.1.4.1.11195.1.5.5.1.4.1' % ip)
                s.expect(ssh_prompt)
                op = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1] + '.0'
                    
                try:
                    op = str(round(float(op) * 0.1, 2))
                except:
                    op = 'op'
                    
                #оптический сигнал 2
                s.sendline('sudo snmpwalk -v2c -c public %s .1.3.6.1.4.1.11195.1.5.5.1.4.2' % ip)
                s.expect(ssh_prompt)
                op2 = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1] + '.0'
                try:
                    op2 = str(round(float(op2) * 0.1, 2))
                except:
                    op2 = 'NaN'
                    
                #температура
                s.sendline('sudo snmpwalk -v2c -c public %s SNMPv2-SMI::enterprises.5591.1.3.1.13.0' % ip)
                s.expect(ssh_prompt)
                temp = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1] + '.0'
                
                try:
                    temp = str(round(float(temp)))
                except:
                    temp = 'NaN'

                #аптайм
                s.sendline('sudo snmpwalk -v2c -c public %s DISMAN-EVENT-MIB::sysUpTimeInstance' % ip)
                s.expect(ssh_prompt)
                _uptime = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(') ')[-1]
                    
            else:
                #аттенюатор
                s.sendline('sudo snmpwalk -v2c -c public %s .1.3.6.1.4.1.17409.1.10.11.1.9.1' % ip)
                s.expect(ssh_prompt)
                att = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1]
                try:
                    att = str(round(float(att) * 0.1))
                except:
                    att = 'a'
                
                #эквалайзер
                s.sendline('sudo snmpwalk -v2c -c public %s .1.3.6.1.4.1.17409.1.10.11.1.10.1' % ip)
                s.expect(ssh_prompt)
                eq = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1]
                try:
                    eq = str(round(float(eq) * 0.1))
                except:
                    eq = 'eq'
                    
                #оптический усилитель
                s.sendline('sudo snmpwalk -v2c -c public %s .1.3.6.1.4.1.17409.1.10.28.0' % ip)
                s.expect(ssh_prompt)
                g = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1]
                try:
                    g = str(round(float(g) * 0.1))
                except:
                    g = 'g'
                    
                #электрический сигнал 1
                s.sendline('sudo snmpwalk -v2c -c public %s enterprises.17409.1.10.11.1.4.1' % ip)
                s.expect(ssh_prompt)
                rf = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1]
                
                #оптический сигнал 1
                s.sendline('sudo snmpwalk -v2c -c public %s enterprises.17409.1.10.5.1.2.1' % ip)
                s.expect(ssh_prompt)
                op = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1] + '.0'
                
                try:
                    op = str(round(float(op) * 0.1, 2))
                except:
                    op = 'op'
                    
                #оптический сигнал 2
                s.sendline('sudo snmpwalk -v2c -c public %s enterprises.17409.1.10.5.1.2.2' % ip)
                s.expect(ssh_prompt)
                op2 = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1] + '.0'
                try:
                    op2 = str(round(float(op2) * 0.1, 2))
                except:
                    op2 = 'NaN'
            
                #температура
                s.sendline('sudo snmpwalk -v2c -c public %s .1.3.6.1.4.1.17409.1.3.3.2.2.1.12.1' % ip)
                s.expect(ssh_prompt)
                temp = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1] + '.0'
                
                try:
                    temp = str(round(float(temp)))
                except:
                    temp = 'NaN'

                #аптайм
                s.sendline('sudo snmpwalk -v2c -c public %s DISMAN-EVENT-MIB::sysUpTimeInstance' % ip)
                s.expect(ssh_prompt)
                _uptime = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(') ')[-1]

                #вольтаж
                _avg_voltage = 9999
                for i in range(20):
                    s.sendline('sudo snmpwalk -v2c -c public %s .1.3.6.1.4.1.17409.1.10.19.1.2.1 | awk \'{print$4}\'' % ip)
                    s.expect(ssh_prompt)
                    _voltage = s.before.decode('utf-8', "ignore").split('\r\n')[-1]
                    if int(_avg_voltage) > int(_voltage):
                        _avg_voltage = int(_voltage)

                _avg_voltage = _avg_voltage/10

            result.append(att)
            result.append(eq)
            result.append(g)
            result.append(op)
            result.append(rf)
            result.append(model)
            result.append(op2)
            result.append(temp)
            result.append(_uptime)
            result.append(str(_avg_voltage))
    except Exception as e:
        error_capture(e=e)
    return result

#ребутаем коммутаторы, определение модели коммутатора надо вынести отдельно, так как используется дальше в коде кучу раз
def reboot(args, message):
    ip = check_IPV4(args)
    if ip:
        result = ''
        answer = 'ушёл курить'
        try:
            s = pxssh.pxssh()
            hostname = ping_hostname
            username = ping_username
            password = ping_password
            ssh_prompt = '~$ '
            if not s.login(hostname, username, password, auto_prompt_reset=False):
                result = "ssh to monitoring failed"
            else:
                s.sendline('telnet %s' % ip)
                login = s.expect(['.*[Uu]sername:', '.*[Ll]ogin:', '.*User Name:', '.*~'])
                if login == 0 or login == 1:
                    s.sendline('admin')
                    s.expect(['[Pp]assword:', '[Pp]assword:'])
                    s.sendline(sw_pass)
                    mode = s.expect([">", "#", '.*:~'])
                    if mode == 0:
                        s.sendline("enable")
                        s.expect("[Pp]assword:")
                        s.sendline(sw_pass)
                        mode = 1
                    if mode == 1:
                        s.sendline('show ver')
                        s.expect("#")
                        switch = str(s.before)
                        s.sendline("terminal length 0")
                        s.expect("#")
                        s.sendline("")
                        s.expect("#")
                        hostname = s.before.decode('utf-8', "ignore").split('\r\n')[1]          
                        if (switch.find("S2226G") != -1):
                            s.sendline('reboot')
                            s.sendline('y')
                            result = ip + " S2226G ушёл в ребут"
                        elif (switch.find("SNR-S2950-24G") != -1):
                            s.sendline('reload')
                            s.sendline('y')
                            result = ip + " SNR-S2950-24G ушёл в ребут"
                        elif (switch.find("Series Software, Version 2.1.1A Build 16162, RELEASE SOFTWARE") != -1):
                            result = ip + " S2548GX..."
                        elif (switch.find("Orion Alpha A26 Device") != -1):
                            s.sendline('reload')
                            s.sendline('y')
                            result = ip + " Orion Alpha A26 ушёл в ребут"
                        elif (switch.find("Alpha-A28F") != -1):
                            s.sendline('reload')
                            s.sendline('y')
                            result = ip + " Orion Alpha-A28F ушёл в ребут"
                        elif (switch.find("SNR-S2985G-24T") != -1):
                            s.sendline('reload')
                            s.sendline('y')
                            result = ip + " SNR-S2985G-24T ушёл в ребут"
                        elif (switch.find("SNR-S2965-24T") != -1):
                            s.sendline('reload')
                            s.sendline('y')
                            result = ip + " SNR-S2965-24T ушёл в ребут"
                        elif (switch.find("SNR-S2960-24G") != -1):
                            s.sendline('reload')
                            s.sendline('y')
                            result = ip + " SNR-S2960-24G ушёл в ребут"
                        elif (switch.find("SNR-S2965-8T") != -1):
                            s.sendline('reload')
                            s.sendline('y')
                            result = ip + " SNR-S2965-8T ушёл в ребут"
                        elif (switch.find("Image text-base: 0x80010000") != -1):
                            s.sendline('reboot')
                            s.sendline('y')
                            result = ip + " S2210G ушёл в ребут"
                        else:
                            s.sendline('exit')
                            s.sendline('exit')
                            result = 'неизвестная модель'
                    if mode == 2:
                        result = "can\'t connect to host"
                elif login == 2:
                    result = "can\'t connect to eltex switch"
                else:
                    result = "can\'t connect to host"
                try:
                    time.sleep(1)
                    s.logout()
                except:
                    pass
        except Exception as e:
            error_capture(e = e)
            result = "pxssh failed on login"
        bot.reply_to(message, result)
    else:
        bot.reply_to(message, args + " не является ip адресом.")

def port_info(args, message):
    def get_file(arg):
        s = start_session()
        r = s.get(arg, headers={'User-Agent': user_agent_val})
        r.close()
        return r
    
    def write_file(n, h):
        f = open(n, "wb")
        r = get_file(h)
        f.write(r.content)
        f.close()
    
    if args.find(' ') != -1:
        ip = args.split(' ')[0]
        port = args.split(' ')[1]
    else:
        args = args.replace(' ', '')
        if args.find(',') != -1:
            ip = args.split(',')[0]
            port = args.split(',')[1]
        
        elif args.find(':') != -1:
            ip = args.split(':')[0]
            port = args.split(':')[1]
        else:
            bot.reply_to(message, "Формат команды: 'порт-инфо ip port'.")
            return
        
    ip = check_IPV4(ip)   
    if (ip and port.isdigit()):
        if check_comm_aviability(ip) > 0 :
            result = ''
            answer = ''
            try:
                s = pxssh.pxssh(timeout=90)
                hostname = ping_hostname
                username = ping_username
                password = ping_password
                ssh_prompt = '~$ '
                if not s.login(hostname, username, password, auto_prompt_reset=False):
                    result = "ssh to monitoring failed"
                else:
                    s.sendline('telnet %s' % ip)
                    login = s.expect(['.*[Uu]sername:', '.*[Ll]ogin:', '.*User Name:', '.*~'])
                    if login == 0 or login == 1 or login == 2:
                        s.sendline('admin')
                        s.expect(['[Pp]assword:', '[Pp]assword:'])
                        s.sendline(sw_pass)
                        mode = s.expect([">", "#", '.*:~'])
                        if mode == 0:
                            s.sendline("enable")
                            s.expect("[Pp]assword:")
                            s.sendline(sw_pass)
                            mode = 1
                            print("ena")
                        if mode == 1:
                            s.sendline('show ver')
                            s.expect("#")
                            switch = str(s.before)
                            s.sendline("terminal length 0")
                            s.expect("#")
                            s.sendline("")
                            s.expect("#")
                            hostname = s.before.decode('utf-8', "ignore").split('\r\n')[1]
                            if (switch.find("S2226G") != -1):
                                if int(port) > 0 and int(port) <= 24:
                                    s.sendline('show int f0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac ad int f0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                elif int(port) == 25:
                                    s.sendline('show int g0/1')
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'   
                                    s.sendline('show mac ad int g0/1')
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                elif int(port) == 26:
                                    s.sendline('show int g0/2')
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'   
                                    s.sendline('show mac ad int g0/2')
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                else:
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                            elif (switch.find("Version 2.0.1N") != -1):
                                if int(port) > 0 and int(port) <= 8:
                                    s.sendline('show int f0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac ad int f0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                elif int(port) == 9:
                                    s.sendline('show int g1/1')
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'   
                                    s.sendline('show mac ad int g1/1')
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                else:
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2950-24G") != -1):
                                if int(port) > 0 and int(port) <= 26:
                                    s.sendline('show int e1/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac-address-table int e1/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'     
                                    s.sendline('exit')
                            elif (switch.find("Series Software, Version 2.1.1A Build") != -1):
                                if int(port) > 0 and int(port) <= 48:
                                    s.sendline('show int g0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac ad int g0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                            elif (switch.find("Orion Alpha A26 Device") != -1):
                                if int(port) > 0 and int(port) <= 26:
                                    s.sendline('show int e1/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac-address-table int e1/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n' 
                                    s.sendline('exit')
                            elif (switch.find("Alpha-A28F") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('show int port %s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show int port %s statistics' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac-address-table l2-address port %s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n' 
                                    s.sendline('exit')
                            elif (switch.find("SW version    1.1.48") != -1):
                                if int(port) > 0 and int(port) <= 26:
                                    s.sendline('show interfaces status GigabitEthernet 1/0/%s' % port)
                                    s.expect('#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac address-table interface GigabitEthernet 1/0/%s' % port)
                                    s.expect('#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n' 
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2985G-24T") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('show int e1/0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac-address-table int e1/0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n' 
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2960-24G") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('show int e1/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac-address-table int e1/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n' 
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2965-8T") != -1):
                                if int(port) > 0 and int(port) <= 10:
                                    s.sendline('show int e1/0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac-address-table int e1/0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n' 
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2965-24T") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('show int e1/0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac-address-table int e1/0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n' 
                                    s.sendline('exit')
                            elif (switch.find("Image text-base: 0x80010000") != -1):
                                if int(port) > 0 and int(port) <= 8:
                                    s.sendline('show int f0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac ad int f0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                elif int(port) == 25:
                                    s.sendline('show int g1/1')
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac ad int g1/1')
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                elif int(port) == 26:
                                    s.sendline('show int g1/2')
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('show mac ad int g1/2')
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'    
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                else:
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                            else:
                                s.sendline('exit')
                                s.sendline('exit')
                                result = 'unknown model'
                        if mode == 2:
                            result = "can\'t connect to host"
                    else:
                        result = "can\'t connect to the host"
                    time.sleep(1)
                    s.logout()
            
            except Exception as e:
                error_capture(e=e)
                result = "pxssh failed on login"
            msg = result
            if (len(msg) > 4000):
                msg = "message is too long!\n\n" + msg[:4000]
                msg = '`' + re.escape(msg) + '`'
            else:
                msg = '`' + re.escape(msg) + '`'
            bot.reply_to(message, msg, parse_mode='MarkdownV2')
            _url_t = graph_port+'?ip='+ip+'&if='+port+'&ds=0'
            _url_f = graph_port+'?ip='+ip+'&if='+port+'&ds=1'
            
            name_t = 'traff_'+ip+'_'+port+'_'+str(datetime.timestamp(datetime.now()))+'.png'
            name_f = 'error_'+ip+'_'+port+'_'+str(datetime.timestamp(datetime.now()))+'.png'
            
            write_file(save_dir+'cacti/'+name_t, _url_t)
            write_file(save_dir+'cacti/'+name_f, _url_f)
            
            img_t = open(save_dir+'cacti/'+name_t, 'rb')
            img_f = open(save_dir+'cacti/'+name_f, 'rb')
            
            bot.send_media_group(message.chat.id, [telebot.types.InputMediaPhoto(img_t), telebot.types.InputMediaPhoto(img_f)])
            
            img_t.close()
            img_f.close()
        else:
            bot.reply_to(message, "Коммутатор " + ip + " недоступен или не существует.")

#показываем ошибки на портах
def show_errors(args, message):
    msg = ""

    if args.find(' ') != -1:
        ip = args.split(' ')[0]
        port = args.split(' ')[1]
    else:
        args = args.replace(' ', '')
        if args.find(',') != -1:
            ip = args.split(',')[0]
            port = args.split(',')[1]
        
        elif args.find(':') != -1:
            ip = args.split(':')[0]
            port = args.split(':')[1]
        else:
            bot.reply_to(message, "Формат команды: 'сброс ip port'.")
            return

    result = '?'
    ip = check_IPV4(ip)
    if ip:
        if check_comm_aviability(ip) > 0:
            try:
                s = pxssh.pxssh()
                hostname = ping_hostname
                username = login
                password = password2
                ssh_prompt = '\r\n' + login + ':~'
                if not s.login(hostname, username, password, auto_prompt_reset=False):
                    result = "ssh to monitoring failed"
                else:
                    msg = ip + ':' + port + '\n'
                    s.sendline('sudo snmpwalk -v2c -c switch-comm %s  IF-MIB::ifInErrors.%s' % (ip, port))
                    s.expect(ssh_prompt)
                    result = str(s.before, 'utf-8').split(': ')[-1]
                    msg = 'Входящие ошибки: ' + result + '\n'
                    s.sendline('sudo snmpwalk -v2c -c switch-comm %s  IF-MIB::ifOutErrors.%s' % (ip, port))
                    s.expect(ssh_prompt)
                    result = str(s.before, 'utf-8').split(': ')[-1]
                    msg += 'Исходящие ошибки: ' + result
            except Exception as e:
                error_capture(e=e)
                result = "pxssh failed on login"
    else:
        msg = "Коммутатор " + ip + " недоступен или не существует."
    bot.reply_to(message, msg)     

#сбрасываем ошибки на портах
def err_reset(args, message):
    def get_file(arg):
        s = start_session()
        r = s.get(arg, headers={'User-Agent': user_agent_val})
        r.close()
        return r
    
    def write_file(n, h):
        f = open(n, "wb")
        r = get_file(h)
        f.write(r.content)
        f.close()
    
    if args.find(' ') != -1:
        ip = args.split(' ')[0]
        port = args.split(' ')[1]
    else:
        args = args.replace(' ', '')
        if args.find(',') != -1:
            ip = args.split(',')[0]
            port = args.split(',')[1]
        
        elif args.find(':') != -1:
            ip = args.split(':')[0]
            port = args.split(':')[1]
        else:
            bot.reply_to(message, "Формат команды: 'сброс ip port'.")
            return
        
    ip = check_IPV4(ip)
    if (ip and port.isdigit()):
        if check_comm_aviability(ip) > 0 :
            result = 'Счётчики на порту успешно сброшены.'
            answer = ''
            try:
                s = pxssh.pxssh(timeout=90)
                hostname = ping_hostname
                username = ping_username
                password = ping_password
                ssh_prompt = '~$ '
                if not s.login(hostname, username, password, auto_prompt_reset=False):
                    result = "ssh to monitoring failed"
                else:
                    s.sendline('telnet %s' % ip)
                    login = s.expect(['.*[Uu]sername:', '.*[Ll]ogin:', '.*User Name:', '.*~'])
                    if login == 0 or login == 1 or login == 2:
                        s.sendline('admin')
                        s.expect(['[Pp]assword:', '[Pp]assword:'])
                        s.sendline(sw_pass)
                        mode = s.expect([">", "#", '.*:~'])
                        if mode == 0:
                            s.sendline("enable")
                            s.expect("[Pp]assword:")
                            s.sendline(sw_pass)
                            mode = 1
                        if mode == 1:
                            s.sendline('show ver')
                            s.expect("#")
                            switch = str(s.before)
                            s.sendline("terminal length 0")
                            s.expect("#")
                            s.sendline("")
                            s.expect("#")
                            hostname = s.before.decode('utf-8', "ignore").split('\r\n')[1]
                            if (switch.find("S2226G") != -1):
                                if int(port) > 0 and int(port) <= 24:
                                    s.sendline('clear mib interface f0/%s' % port)
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                elif int(port) == 25:
                                    s.sendline('clear mib interface g0/1')
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                elif int(port) == 26:
                                    s.sendline('clear mib interface g0/2')
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                else:
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2950-24G") != -1):
                                if int(port) > 0 and int(port) <= 26:
                                    s.sendline('clear counters interface e1/%s' % port)
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                            elif (switch.find("Series Software, Version 2.1.1A Build") != -1):
                                if int(port) > 0 and int(port) <= 48:
                                    s.sendline('clear mib interface g0/%s' % port)
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                            elif (switch.find("Orion Alpha A26 Device") != -1):
                                if int(port) > 0 and int(port) <= 26:
                                    s.sendline('clear counters interface e1/%s' % port)
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                            elif (switch.find("Alpha-A28F") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('conf')
                                    s.expect(hostname + '#')
                                    s.sendline('clear interface port %s statistics' % port)
                                    s.expect(hostname + '#')
                                    s.sendline('q')
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                            elif (switch.find("SW version    1.1.48") != -1):
                                if int(port) > 0 and int(port) <= 26:
                                    s.sendline('clear counters GigabitEthernet 1/0/%s' % port)
                                    s.expect('#')
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2985G-24T") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('clear counters interface e1/0/%s' % port)
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2960-24G") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('clear counters interface e1/%s' % port)
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2965-8T") != -1):
                                if int(port) > 0 and int(port) <= 10:
                                    s.sendline('clear counters interface e1/0/%s' % port)
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2965-24T") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('clear counters interface e1/0/%s' % port)
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                            elif (switch.find("Image text-base: 0x80010000") != -1):
                                if int(port) > 0 and int(port) <= 8:
                                    s.sendline('clear mib interface f0/%s' % port)
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                elif int(port) == 25:
                                    s.sendline('clear mib interface g1/1')
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                elif int(port) == 26:
                                    s.sendline('clear mib interface g1/2')
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                else:
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                            else:
                                s.sendline('exit')
                                s.sendline('exit')
                                result = 'unknown model'
                        if mode == 2:
                            result = "couldn\'t connect to host"
                    else:
                        result = "couldn\'t connect to host"
                    time.sleep(1)
                    s.logout()
            
            except Exception as e:
                error_capture(e=e)
                result = "pxssh failed on login"
            
            msg = result
            
            if (len(msg) > 4000):
                msg = "message is too long!\n\n" + msg[:4000]
                msg = '`' + re.escape(msg) + '`'
            else:
                msg = '`' + re.escape(msg) + '`'
            bot.reply_to(message, msg, parse_mode='MarkdownV2')
            
        else:
            bot.reply_to(message, "Коммутатор " + ip + " недоступен или не существует.")

#смотрим оптический сигнал
def fiber(args, message): 
    if args.find(' ') != -1:
        ip = args.split(' ')[0]
        port = args.split(' ')[1]
    else:
        _args = args.replace(' ', '')
        if _args.find(',') != -1:
            ip = _args.split(',')[0]
            port = _args.split(',')[1]
        
        elif _args.find(':') != -1:
            ip = _args.split(':')[0]
            port = _args.split(':')[1]
        else:
            bot.reply_to(message, "Формат команды: 'сигнал ip port'.")
            return
        
    ip = check_IPV4(ip)
    if (ip and port.isdigit()):
        if check_comm_aviability(ip) > 0 :
            result = ''
            answer = ''
            try:
                s = pxssh.pxssh(timeout=90)
                hostname = ping_hostname
                username = ping_username
                password = ping_password
                ssh_prompt = '~$ '
                if not s.login(hostname, username, password, auto_prompt_reset=False):
                    result = "ssh to monitoring failed"
                else:
                    s.sendline('telnet %s' % ip)
                    login = s.expect(['.*[Uu]sername:', '.*[Ll]ogin:', '.*User Name:', '.*~'])
                    if login == 0 or login == 1 or login == 2:
                        s.sendline('admin')
                        s.expect(['[Pp]assword:', '[Pp]assword:'])
                        s.sendline(sw_pass)
                        mode = s.expect([">", "#", '.*:~'])
                        if mode == 0:
                            s.sendline("enable")
                            s.expect("[Pp]assword:")
                            s.sendline(sw_pass)
                            mode = 1
                        if mode == 1:
                            s.sendline('show ver')
                            s.expect("#")
                            switch = str(s.before)
                            s.sendline("terminal length 0")
                            s.expect("#")
                            s.sendline("")
                            s.expect("#")
                            hostname = s.before.decode('utf-8', "ignore").split('\r\n')[1]
                            if (switch.find("S2226G") != -1):
                                s.sendline('config')
                                s.expect(hostname + '_config#')
                                s.sendline('ddm enable')
                                s.expect(hostname + '_config#')
                                s.sendline('exit')
                                s.expect(hostname + '#')
                                s.sendline('exit')
                                s.sendline('exit')
                                port_info(args, message)
                                result = None
                            elif (switch.find("Series Software, Version 2.1.1A Build") != -1):
                                s.sendline('config')
                                s.expect(hostname + '_config#')
                                s.sendline('ddm enable')
                                s.expect(hostname + '_config#')
                                s.sendline('exit')
                                s.expect(hostname + '#')
                                s.sendline('exit')
                                s.sendline('exit')
                                port_info(args, message)
                                result = None
                            elif (switch.find("Image text-base: 0x80010000") != -1):
                                port_info(args, message)
                            elif (switch.find("SNR-S2950-24G") != -1):
                                if int(port) > 24 and int(port) <= 26:
                                    s.sendline('show transceiver interface ethernet 1/%s detail' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            elif (switch.find("Orion Alpha A26 Device") != -1):
                                if int(port) > 24 and int(port) <= 26:
                                    s.sendline('show transceiver interface ethernet 1/%s detail' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            elif (switch.find("Alpha-A28F") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('show interface port %s transceiver' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            elif (switch.find("SW version    1.1.48") != -1):
                                if int(port) > 24 and int(port) <= 26:
                                    s.sendline('show fiber-ports optical-transceiver interface GigabitEthernet 1/0/%s detailed' % port)
                                    s.expect('#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2985G-24T") != -1):
                                if int(port) > 24 and int(port) <= 28:
                                    s.sendline('show transceiver interface ethernet 1/0/%s detail' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2960-24G") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('show transceiver interface ethernet 1/%s detail' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2965-8T") != -1):
                                if int(port) > 8 and int(port) <= 10:
                                    s.sendline('show transceiver interface ethernet 1/0/%s detail' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2965-24T") != -1):
                                if int(port) > 24 and int(port) <= 28:
                                    s.sendline('show transceiver interface ethernet 1/0/%s detail' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            else:
                                s.sendline('exit')
                                s.sendline('exit')
                                result = 'unknown model'
                        if mode == 2:
                            result = "can\'t connect to host"
                    else:
                        result = "can\'t connect to the host"
                    time.sleep(1)
                    s.logout()
            
            except Exception as e:
                error_capture(e=e)
                result = "pxssh failed on login"
            
            if result is not None:
                msg = result
                
                if (len(msg) > 4000):
                    msg = "message is too long!\n\n" + msg[:4000]
                    msg = '`' + re.escape(msg) + '`'
                else:
                    msg = '`' + re.escape(msg) + '`'
                bot.reply_to(message, msg, parse_mode='MarkdownV2')
        else:
            bot.reply_to(message, "Коммутатор " + ip + " недоступен или не существует.")

#получаем аптайм через снмп
def uptime(message, args):
    result = '?'
    ip = check_IPV4(args)
    if ip:
        if check_comm_aviability(ip) > 0:
            try:
                s = pxssh.pxssh()
                hostname = ping_hostname
                username = login
                password = password2
                ssh_prompt = '\r\n' + login + ':~'
                if not s.login(hostname, username, password, auto_prompt_reset=False):
                    result = "ssh to monitoring failed"
                else:
                    s.sendline('sudo snmpwalk -v2c -c switch-comm %s DISMAN-EVENT-MIB::sysUpTimeInstance' % ip)
                    s.expect(ssh_prompt)
                    result = str(s.before, 'utf-8').split(') ')[-1]                  
            except Exception as e:
                error_capture(e=e)
                result = "pxssh failed on login"
        msg = "Аптайм " + ip + ' равен: ' + result
    else:
        msg = "Коммутатор " + args + " недоступен или не существует."
    bot.reply_to(message, msg)        

#отправляем в кастрюлю новые настройки
def op_set(ip, cmd):
    result = []
    try:
        s = pxssh.pxssh()
        hostname = ping_hostname
        username = login
        password = password2
        ssh_prompt = '\r\n' + login + ':~'
        if not s.login(hostname, username, password, auto_prompt_reset=False):
            result = "ssh to monitoring failed"
        else:
            s.sendline('sudo snmpwalk -v2c -c public %s SNMPv2-MIB::sysDescr.0' % ip)
            s.expect(ssh_prompt)
            model = s.before.decode('utf-8', "ignore").split('\r\n')[-1].split(' ')[-1]
            if model == '72GE':
                if cmd[:1] == 'A':
                    s.sendline('sudo snmpset -v1 -c private %s .1.3.6.1.4.1.11195.1.5.9.1.2.1 i %s' % (ip, cmd[1:] + '0'))
                if cmd[:1] == 'E':
                    s.sendline('sudo snmpset -v1 -c private %s .1.3.6.1.4.1.11195.1.5.11.1.2.1 i %s' % (ip, cmd[1:] + '0'))
                if cmd[:1] == 'G':
                    s.sendline('sudo snmpset -v1 -c private %s .1.3.6.1.4.1.11195.1.5.13.0 i %s' % (ip, cmd[1:]))
            else:
                if cmd[:1] == 'A':
                    s.sendline('sudo snmpset -v1 -c public %s .1.3.6.1.4.1.17409.1.10.11.1.9.1 i %s' % (ip, cmd[1:] + '0'))
                if cmd[:1] == 'E':
                    s.sendline('sudo snmpset -v1 -c public %s .1.3.6.1.4.1.17409.1.10.11.1.10.1 i %s' % (ip, cmd[1:] + '0'))
                if cmd[:1] == 'G':
                    s.sendline('sudo snmpset -v1 -c public %s .1.3.6.1.4.1.17409.1.10.28.0 i %s' % (ip, cmd[1:] + '0'))
    except Exception as e:
        error_capture(e = e)
        result = "pxssh failed on login"

#настройка кастрюли
def op_mgmt(args, message, mode, op_list):
    multi = False
    k = 0
    def op_request(message, _name, _hostid):
        _ip = zapi.hostinterface.get(filter={'hostid': _hostid}, output = ['ip'])[0].get('ip')
        _val = op_info(_ip)
        if _val:
            if _val[5] == '72GE':
                _payload = _ip + ',' + _name
                if _val[6] == 'NaN':
                    _op_power = '\nOptical In: ' + _val[3] + ' dBm\n'
                else:
                    _op_power = '\nOptical In1: ' + _val[3] + ' dBm\n' + 'Optical In2: ' + _val[6] + ' dBm\n'
                msg = "➡️ " + _name + '\nIP: ' + _ip + _op_power + 'RF Out: ' + _val[4] + ' dBuV\nATT: ' + _val[0] + '\nEQ: ' + _val[1] + '\nАРУ (AGC): ' + _val[2] + ' dB\nTemp: ' + _val[7] + '°C\nUptime: ' + _val[8] + '\n\n'
                bot.reply_to(message, msg)
                key = types.InlineKeyboardMarkup()
                but_1 = types.InlineKeyboardButton(text="Аттенюация", callback_data="OPA," + _payload)
                but_2 = types.InlineKeyboardButton(text="Эквалайзер", callback_data="OPE," + _payload)
                but_3 = types.InlineKeyboardButton(text="АРУ", callback_data="OPG," + _payload)
                key.add(but_1, but_2, but_3)
                bot.send_message(message.chat.id, "Настройка параметров", reply_markup=key)
            elif (_val[0] == 'a'):
                msg = "❌" + _name + '\nIP: ' + _ip + '\n\nОптический приёмник недоступен!\n\n'
                bot.reply_to(message, msg)
            else:
                _payload = _ip + ',' + _name
                if _val[6] == 'NaN':
                    _op_power = '\nOptical In: ' + _val[3] + ' dBm\n'
                else:
                    _op_power = '\nOptical In1: ' + _val[3] + ' dBm\n' + 'Optical In2: ' + _val[6] + ' dBm\n'
                msg = "➡️ " + _name + '\nIP: ' + _ip + _op_power + 'RF Out: ' + _val[4] + ' dBuV\nATT: ' + _val[0] + '\nEQ: ' + _val[1] + '\nАРУ (AGC): ' + _val[2] + ' dB\nTemp: ' + _val[7] + '°C\nUptime: ' + _val[8] + '\n' + _val[9]+ 'V\n\n'
                
                bot.reply_to(message, msg)
                key = types.InlineKeyboardMarkup()
                but_1 = types.InlineKeyboardButton(text="Аттенюация", callback_data="OPA," + _payload)
                but_2 = types.InlineKeyboardButton(text="Эквалайзер", callback_data="OPE," + _payload)
                but_3 = types.InlineKeyboardButton(text="АРУ", callback_data="OPG," + _payload)
                key.add(but_1, but_2, but_3)
                bot.send_message(message.chat.id, "Настройка параметров", reply_markup=key)
        else:
            bot.send_message(message.chat.id, "ОП недоступен")
            
    if mode == 1:
        _search = find_switch_by_address(args)
        _op = []
        op_list = []
        
        if _search:
            for streets in _search:
                for switches in streets:
                    switch = switches[0].replace('/','-')+'-OP'
                    h = zapi.host.get(search={'host': switch}, output=['hostid', 'name'])
                    if h:
                        _t = [h, switches]
                        _op.append(_t)
            
            if _op:
                count = len(_op)             

                if count == 1:
                    _name = _op[0][0][0].get('name')
                    _hostid = _op[0][0][0].get('hostid')
                    op_request(message, _name, _hostid)
                
                elif count > 1:
                    msg = ''
                    for i in range(count):
                        _name = _op[i][0][0].get('name')
                        _hostid = _op[i][0][0].get('hostid')
                        
                        if (_name[len(_name)-2:] == 'OP'):
                            k += 1
                            _ip = zapi.hostinterface.get(filter={'hostid': _hostid}, output = ['ip'])[0].get('ip')
                            op_list.append(_op[i])
                            msg += "➡️ " + str(k) + ' ' + _name + '\n'
                    
                    if k == 1:
                        op_request(message, _name, _hostid)
                    elif k > 1:
                        msg = 'Найдено совпадений: ' + str(k) + '\n' + msg
                        msg += "Какой номер интересует?"
                        send_msg_with_split(message, msg, 4000)
                        multi = True
            else:
                bot.reply_to(message, "Ничего не нашлось.")
        else:
            bot.reply_to(message, "Ничего не нашлось.")
            
    elif mode == 2:
        _op = op_list
        num = int(args) - 1
        _name = _op[num][0][0].get('name')
        _hostid = _op[num][0][0].get('hostid')
        # _switch = _op[num][1][0]
        # _status = _op[num][1][1]
        # _address = _op[num][1][2]
        # _comment = _op[num][1][3]
        # _switch_ip = _op[num][1][4]

        op_request(message, _name, _hostid)
        op_list.clear()
            
    return multi, op_list, k
                
#тут есть косяк в определении дежурного в ЦУСе на стыке первого и последнего дня месяца, надо бы исправить
def who(args, message):
    def month(x):
        return {
            1: "Январь",
            2: "Февраль",
            3: "Март",
            4: "Апрель",
            5: "Май",
            6: "Июнь",
            7: "Июль",
            8: "Август",
            9: "Сентябрь",
            10: "Октябрь",
            11: "Ноябрь",
            12: "Декабрь",
        }.get(x, "Январь")

    init = False
    name_sheet = month(int(date.today().strftime("%m"))) + ' ' + date.today().strftime("%Y")

    try:
        ws_it = sh_it.worksheet(name_sheet)
        ws_oe = sh_oe.worksheet(name_sheet)
        init = True
    except Exception as e:
        error_capture(e=e, message=message)

    if init:

        def oe_username(x):
            return {
                0: contacts.get('oe1'),
                1: contacts.get('oe2'),
                2: contacts.get('oe3'),
                3: contacts.get('oe4'),
                4: contacts.get('oe5'),
                5: contacts.get('oe6'),
            }[x]

        def it_username(x):
            return {
                0: contacts.get('it1'),
                1: contacts.get('it2'),
                2: contacts.get('it3'),
                3: contacts.get('it4'),
                4: contacts.get('it5'),
                5: contacts.get('it6'),
                6: contacts.get('it7'),
                7: contacts.get('it8'),
            }[x]

        msg = ''
        h = int(datetime.now().time().hour)

        if args.lower() == "оэ":
            day = date.today().strftime("%d")
            msg = 'Дежурный ОЭ:\n'

            for i in range(6):
                cell = ws_oe.cell(i + 3, 2 + int(day)).value
                name = ws_oe.cell(i + 3, 2).value

                if cell is not None:
                    if cell.lower() == '8':
                        if h >= 9 and h < 18:
                            msg += 'с 9:00 до 18:00: ' + name + ' @' + oe_username(i) + '\n'
                        else:
                            msg += 'с 9:00 до 18:00: ' + name + ' ' + oe_username(i) + '\n'

                    if cell.lower() == 'а':
                        msg += 'с 00:00 до 23:59: ' + name + ' @' + oe_username(i) + '\n'

        elif args.lower() == "ит":
            day = date.today().strftime("%d")
            msg = 'Дежурный ИТ:\n'

            for i in range(8):
                cell = ws_it.cell(i + 2, 1 + int(day)).value
                name = ws_it.cell(i + 2, 1).value
                uname = it_username(i)

                if cell is not None and cell.lower() == 'и':
                    if h >= 9 and h < 22:
                        msg += 'с 9:00 до 22:00: ' + name + ' @' + uname + '\n'
                    else:
                        msg += 'с 9:00 до 22:00: ' + name + ' ' + uname + '\n'

        elif args.lower() == "цус":
            _shift = False

            if h>0 and h<9:
                day = str(int(date.today().strftime("%d")) - 1)
            else:
                day = date.today().strftime("%d")

            msg = 'Дежурный ЦУС:\n'
            uname = ''

            for i in range(8):
                cell = ws_it.cell(i + 2, 1 + int(day)).value
                name = ws_it.cell(i + 2, 1).value
                uname = it_username(i)

                if cell is not None:
                    if cell.lower() == 'д':
                        if h>=9 and h<21:
                            msg += 'с 9:00 до 21:00: ' + name + ' @' + uname + '\n'
                        elif h>=21:
                            msg += 'с 9:00 до 21:00: ' + name + ' ' + uname + '\n'
                        elif h>=0 and h<9:
                            _shift = True

                    if cell.lower() == 'н':
                        if h >= 21 or h < 9:
                            msg += 'с 21:00 до 9:00: ' + name + ' @' + uname + '\n'
                        else:
                            msg += 'с 21:00 до 9:00: ' + name + ' ' + uname + '\n'

            if _shift:
                day = date.today().strftime("%d")

                for i in range(8):
                    cell = ws_it.cell(i + 2, 1 + int(day)).value
                    name = ws_it.cell(i + 2, 1).value
                    uname = it_username(i)

                    if cell is not None:
                        if cell.lower() == 'д':
                            msg += 'с 9:00 до 21:00: ' + name + ' ' + uname + '\n'

        else:
            msg = 'ты'

        if msg != 'ты':
            bot.reply_to(message, msg)
    else:
        msg = 'Ошибка в инициализации Google API'
        bot.reply_to(message, msg)

#актуалочка
def exp(message):
    etraxisdb = etraxisdb_connect()
    cur = etraxisdb.cursor(buffered=True)
    _sql = """select * FROM tbl_records 
            WHERE template_id = 85 
            and (state_id != 715 and state_id != 711 and state_id != 713) 
            and city = 'Владивосток' 
            and (subject NOT LIKE 'Текучка%' and subject NOT LIKE 'Задание%') 
            and (date_work is NULL or subject NOT LIKE 'Персональная%') 
            ORDER BY record_id DESC LIMIT 0,100 ;"""
    cur.execute(_sql)
    res = cur.fetchall()
    
    msg = ''
    for elements in res:
    
        _sql = '''select * FROM tbl_record_subrecords where record_id = %s;'''
        cur.execute(_sql, (elements[0],))
        subs = cur.fetchall()
        
        _sql = '''select child_id FROM tbl_children where parent_id = %s;'''
        cur.execute(_sql, (elements[0],))
        childs = cur.fetchall()
        
        e = ''
        if elements[2] == 697:
            e = '🟢'
        elif elements[2] == 707:
            e = '🔵'
        elif elements[2] == 735:
            e = '🔴'
        elif elements[2] == 701:
            e = '🟡'
        else:
            e = '🟤'
        escaped = str(elements[3]).replace('критичность-', '').replace(' Глобальная:', '').replace('Персональная ИНЕТ:','[Ю]')
    
        _ch = ''
        for e_ch in childs:
            _type = ''
            if e_ch:
                _sql = '''select template_id, closure_time FROM tbl_records where record_id = %s;'''
                cur.execute(_sql, (e_ch[0],))
                ch_res = cur.fetchall()
                if ch_res:
                    if ch_res[0][0] == 89:
                        if ch_res[0][1]:
                            _type = '[~ЖПК'+str(e_ch[0])+'~](https://atk.is/tracker/records/view.php?id=' + str(e_ch[0]) + ')'
                        else:
                            _type = '[ЖПК'+str(e_ch[0])+'](https://atk.is/tracker/records/view.php?id=' + str(e_ch[0]) + ')'
                    elif ch_res[0][0] == 45:
                        if ch_res[0][1]:
                            _type = '[~ВСО'+str(e_ch[0])+'~](https://atk.is/tracker/records/view.php?id=' + str(e_ch[0]) + ')'
                        else:
                            _type = '[ВСО'+str(e_ch[0])+'](https://atk.is/tracker/records/view.php?id=' + str(e_ch[0]) + ')'
                    elif ch_res[0][0] == 128:
                        if ch_res[0][1]:
                            _type = '[~СВЛ'+str(e_ch[0])+'~](https://atk.is/tracker/records/view.php?id=' + str(e_ch[0]) + ')'
                        else:
                            _type = '[СВЛ'+str(e_ch[0])+'](https://atk.is/tracker/records/view.php?id=' + str(e_ch[0]) + ')'
                    elif ch_res[0][0] == 85:
                        if ch_res[0][1]:
                            _type = '[~ЭКС'+str(e_ch[0])+'~](https://atk.is/tracker/records/view.php?id=' + str(e_ch[0]) + ')'
                        else:
                            _type = '[ЭКС'+str(e_ch[0])+'](https://atk.is/tracker/records/view.php?id=' + str(e_ch[0]) + ')'
                    elif ch_res[0][0] == 88:
                        pass
                    else:
                        _type = str(ch_res[0][0])
                    if _ch:
                        _ch += ' ' + _type
                    else:
                        _ch += _type
        if _ch:
            _ch = ' \[' + _ch +'\]'
        
        escaped = re.escape(escaped)
        escaped = ' *' + escaped[:5] + '*' + escaped[5:]
        escaped = '📞' + str(len(subs)) + _ch +  escaped

        address = elements[3].replace('критичность-3', '').replace('критичность-1', '').replace('критичность-2', '').replace(' Глобальная:', '').replace('Персональная ИНЕТ:','').replace('[','').replace(']','').replace('ктв','').replace('инет','').replace('лок','').replace('Лок','').replace('КТВ','').replace('ИНЕТ','').replace('Инет','').replace('|','').replace('+','').replace('юрики', '').replace('Помехи', '').replace('Юрики', '').strip()
        
        if (address.count(', ') > 0):
            address = address.split(', ')[0]
            
        if (address[len(address)-1:] == '-'):
            address = address[:-1]
            
        if (address.count(' ') > 1):
            _s = address.split(' ')
            if _s[1].isdigit():
                address = address.replace(' ', ', ', 1)               
                _d = district_find(address)
                if _d:
                    escaped = _d[2][0].upper() + escaped
                else:
                    escaped = '\?' + escaped
                
            elif _s[0].isdigit():
                address = address.split(' ', 2)
                address = address[0] + ' ' + address[1] + ' ' + address[2].replace(' ', ', ', 1)   
                _d = district_find(address)
                if _d:
                    escaped = _d[2][0].upper() + escaped
                else:
                    escaped = '\?' + escaped
                
            elif not _s[1].isdigit():
                address = address.split(' ', 1)
                address = address[0] + ' ' + address[1].replace(' ', ', ', 1)
                _d = district_find(address)
                if _d:
                    escaped = _d[2][0].upper() + escaped
                else:
                    escaped = '\?' + escaped
            
        else:
            _d = district_find(address)
            if _d:
                escaped = _d[2][0].upper() + escaped
            else:
                escaped = '\?' + escaped
        
        msg += '[' + e + '](https://atk.is/tracker/records/view.php?id=' + str(elements[0])+ ')[🌐]' + '(https://m.atk.is/#breakdowns/' + str(elements[0]) + ') ' + escaped + '\n'
    
    cur.close()
    etraxisdb.close()
    
    try:
        _sort = msg.split('\n')
        _sort = [x for x in _sort if x]
        _sort = sorted(_sort, key=lambda e: e.split(' ',1)[1][0])
        msg = ''
        for e in _sort:
            msg += e + '\n'
    except:
        pass
    
    if msg == '':
        msg = 'В базе пусто\!'
    _msg = '🟢 новая 🟡 в работе 🔵 ожидание компании 🔴 ожидание инженера 🟤 ожидание клиента\nНажатие на круг - ссылка в трекер, нажатие на 🌐 - ссылка в ЛК, п - первак, в - вторяк, ч - чуркин, ? - не определено, 📞 - количество обращений, [+СВЛ+ВСО+ЭКС] - найдены подзаписи, [3] - уровень критичности, адрес'
    bot.reply_to(message, _msg)
    bot.reply_to(message, msg, parse_mode='MarkdownV2') 

#поиск района, сами районы захардкожены вручную в локальной базе
def district_find(args):
    res = []
    if args.find(', ') != -1:
        s = args.split(', ')[0]
        h = args.split(', ')[1]
#        with closing(pg_connect()) as conn:
#            with conn.cursor() as cursor:
        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute("""SELECT name, house, district, street_id 
                        FROM districts 
                        WHERE upper(name) like upper(%s) 
                        and upper(house) like upper(%s)""", (s + '%', h))
        for row in cursor:
            res = row
        cursor.close()
        conn.close()
    elif args.find(' ') != -1:
        s = args.split(' ')[0]
        h = args.split(' ')[1]
#        with closing(pg_connect()) as conn:
#            with conn.cursor() as cursor:
        conn = pg_connect()
        cursor = conn.cursor()
        cursor.execute("""SELECT name, house, district, street_id 
                        FROM districts 
                        WHERE upper(name) like upper(%s) 
                        and upper(house) like upper(%s)""", (s + '%', h))
        for row in cursor:
            res = row
        cursor.close()
        conn.close()
    return res

#нужно ли это отдельно?
def district(args, message):
    res = ''
    row = district_find(args)
    if row:
        res += row[0] + ' ' + row[1] + ' это ' + row[2] + '.\n'
    if res == '' :
        res = 'Ничего не нашлось.'
    bot.reply_to(message, res)

#берём большое сообщение, режем на части и отправляем частями
def send_msg_with_split(message, msg, n):
    i = 0
    if len(msg) > n:
        _split = msg.split("\n")
        res = ''
        for key in _split:
            if i < 9:
                if len(res) < n:
                    res += key + '\n'
                else:
                    if res != '' and res != '\n':
                        bot.reply_to(message, res)
                        i += 1
                    res = ''
            else:
                res = 'Превышена максимальная длина сообщения'
        if res != '' and res != '\n':
            bot.reply_to(message, res)
    else:
        if msg != '' and msg != '\n':
            bot.reply_to(message, msg)

#обработка поиска графиков в заббиксе
def get_graph(args, message, mode, x_list):
    multi_h = False
    multi_g = False
    k = 0
    def g_request(_hostid, msg, message, x_list, multi_g):
        num = 0
        g = zapi.graph.get(filter={'hostid':_hostid}, output=['graphid', 'name'], expandName=1)    
        for i in range(len(g)):
            _gname = g[i].get('name')
            msg += "📊 " + (str(i + 1) + ' ' + _gname) + '\n'
        
        if len(g) > 1 :
            msg += "\nКакой номер интересует?"
            send_msg_with_split(message, msg, 4000)
            multi_g = True
            k = len(g)
            x_list = g
            num = len(g)
                                    
        elif len(g) == 1 :
            y = 0
            _gid = g[y].get('graphid')
            _name = save_dir + 'graph.png'
            zabbix_get_graph(_name, _gid)
            img = open(_name, 'rb')
            bot.send_photo(message.chat.id, img)
            img.close()
        else:
            bot.reply_to(message, "Нет графиков.")
        return x_list, multi_g, num
    
    if mode == 1:
        _search = find_switch_by_address(args)
        x_list = []
        _zhost = []
        _fnd = False
        if _search:
            for streets in _search:
                for switches in streets:
                    switch = switches[0]
                    switch = switch.replace('/','-')
                    h = zapi.host.get(search={'host': switch}, output=['hostid', 'name']) 
                    if h:
                        for _host in h:
                            g = zapi.graph.get(filter={'hostid':_host.get('hostid')}, output=['graphid', 'name'], expandName=1)
                            if g:
                                _t = [_host, switches]
                                _zhost.append(_t)
                    
                    if not _fnd:
                        _s = switches[0].split('-')
                        if not _s[0] == 'A':
                            _sw = _s[0]+'-'+_s[1]
                            _sw = _sw.replace('/','-')
                        else:
                            _sw = _s[0]+'-'+_s[1]+'-'+_s[2]
                        h = zapi.host.get(search={'host': 'EDFA-'+_sw}, output=['hostid', 'name']) 
                        if h:
                            for _host in h:
                                _t = [_host, switches]
                                _zhost.append(_t)
                                _fnd = True
                                
                        h = zapi.host.get(search={'host': 'OPSW-'+_sw}, output=['hostid', 'name']) 
                        if h:
                            for _host in h:
                                _t = [_host, switches]
                                _zhost.append(_t)
                                _fnd = True

                        h = zapi.host.get(search={'host': _sw}, output=['hostid', 'name'])
                        if h:
                            for _host in h:
                                if 'UPS' in _host.get('name'):
                                    _t = [_host, switches]
                                    _zhost.append(_t)
                                    _fnd = True
                                    
                        if h:
                            for _host in h:
                                if 'ERD' in _host.get('name'):
                                    _t = [_host, switches]
                                    _zhost.append(_t)
                                    _fnd = True
                        
                        if h:
                            for _host in h:
                                if 'UniPing' in _host.get('name'):
                                    _t = [_host, switches]
                                    _zhost.append(_t)
                                    _fnd = True

            if _zhost:
                count = len(_zhost)
                msg = 'Найдено совпадений: ' + str(count) + '\n'
                
                if count == 1:
                    _name = _zhost[0][0].get('name')
                    _hostid = _zhost[0][0].get('hostid')
                    msg += "➡️ " + _name + '\n\n'
                    _x, _g, _k = g_request(_hostid, msg, message, x_list, multi_g)
                    if _g:
                        multi_g = _g
                        x_list = _x
                        k = _k
                    
                elif count > 1:
                    for i in range(count):
                        _name = _zhost[i][0].get('name')
                        _hostid = _zhost[i][0].get('hostid')
                        msg += "➡️ " + str(i+1) + ' ' + _name + '\n'
                        
                    msg += "\nКакой номер интересует?"
                    send_msg_with_split(message, msg, 4000)
                    multi_h = True
                    k = count
                    x_list = _zhost
            
            else:
                bot.reply_to(message, "Ничего не нашлось.")
        elif 'edfa' in args:
            print('edfa')
        else:
            bot.reply_to(message, "Ничего не нашлось.")
            
    elif mode == 2:
        _zhost = x_list.get(message.chat.id)
        x_list.clear()
        num = int(args) - 1
        _name = _zhost[num][0].get('name')
        _hostid = _zhost[num][0].get('hostid')

        _x, _g, _k = g_request(_hostid, '', message, x_list, multi_g)
        if _g:
            multi_g = _g
            x_list = _x
            k = _k
        
    elif mode == 3:
        g = x_list.get(message.chat.id)
        x_list.clear()
        num = int(args) - 1
        _gid = g[num].get('graphid')
        _name = save_dir + 'graph.png'
        zabbix_get_graph(_name, _gid)
        img = open(_name, 'rb')
        bot.send_photo(message.chat.id, img)
        img.close()
        
    return multi_h, multi_g, x_list, k

#помощь по командам
def hlp(message):
    msg = """🔸 /help — выводит данное сообщение.
🔸 кто оэ — выводит список дежурных ОЭ.
🔸 кто цус — выводит список дежурных ЦУС.
🔸 кто ит — выводит список дежурных ИТ.
🔸 плд — поиск pdf файлов в wiki.inetvl.corp. Формат команды: 'плд <поисковый запрос>'.
🔸 порт — поиск свободных портов на коммутаторах. Формат команды: 'порт <ip>'.
🔸 дрс — поиск схем дрс в формате pdf по адресу. Формат команды: 'дрс <адрес/host>'.
🔸 схема — поиск всех схем в формате pdf по адресу. Формат команды: 'схема <адрес/host>'.
🔸 инфа — отображение информации по зданию. Формат команды: 'инфа <адрес/host>'.
🔸 график — отображение графика по запросу. Если написать 'график мо', то будет выведен график монтажного отдела. Если написать 'график оэ', то будет выведен график отдела эксплуатации (АВР/ППР). Если написать 'график цус' или 'график ит', то будет выведен график ит. Формат команды: 'график <название хоста>', например 'график LUK-20-172-UPS'. Так же выводит график трафика юрлиц: 'график <номер лицевого счёта>'.
🔸 камера — захватывает текущий кадр с камеры хиквижн, если она в данный момент доступна. Формат команды: 'камера <ip>'.
🔸 карта — показывает карту ВОЛС по указанному адресу. Работает нестабильно. Формат команды: 'карта <адрес>'.
🔸 пинг — пингует заданный хост командой ping -c 10 -i 0.2. Формат команды: 'пинг <ip> [количество пакетов]'. Если после айпи указать количество пакетов, то будет использоваться заданное значение вместо 10.
🔸 флуд — пингует заданный хост командой pingf -c 1000 -s 1470. Формат команды: 'флуд <ip>'.
🔸 порт-инфо — выводит информацию по указанному порту коммутатора. Умеет выводить только известные модели. Формат команды: 'порт-инфо <ip> <порт>'. В качестве разделителя можно использовать пробел, запятую или двоеточие.
🔸 статус — выводит статус коммутаторов по указанному адресу. Формат команды: 'статус <адрес/host>'. Если к номеру дома дописать знак вопроса, то поиск будет по маске 'дом*', таким образом можно вывести список всех строений, букв и дробей. Для всех коммутаторов с названием 'A-' и микротиков с названием 'MIK-' будет дополнительно выведен адрес и комментарий (как правило о наличии УБП).
🔸 аптайм — выводит аптайм коммутатора. Формат команды: 'аптайм <ip>'.
🔸 оп — выводит онлайн параметры кастрюли и позволяет менять настройки аттенюации, эквалайзера и параметра G. Формат команды: 'оп <адрес/host>'.
🔸 ребут — перезагружает коммутаторы моделей: S2226G, S2210G, SNR-S2950-24G, Orion Alpha A26, SNR-S2985G-24T, SNR-S2960-24G, SNR-S2965-8T. Формат команды: 'ребут <ip>'.
🔸 район  — выводит принадлежность адреса к району АВР. Формат команды: 'район <адрес>'.
🔸 сигнал — выводит информацию SFP модуля и уровни оптических сигналов по указанному порту коммутатора. Формат команды: 'сигнал <ip> <порт>'. В качестве разделителя можно использовать пробел, запятую или двоеточие.
🔸 питание — выводит информацию о статусе электропитания коммутатора, если тот поддерживает это: 'питание <ip>'.
🔸 кабельтест — проводит кабель тест на порту коммутатора, если тот поддерживает это: 'кабельтест <ip> <порт>'. В качестве разделителя можно использовать пробел, запятую или двоеточие.
🔸 сброс — сбрасывает статистику на порту (счётчики ошибок, пакетов и прочее). Формат команды: 'сброс <ip> <порт>'. В качестве разделителя можно использовать пробел, запятую или двоеточие.
🔸 актуалочка — выводит текущий список АВР/ППР/юриков с сортировкой по дате создания (сверху новые),
статусы: 🟢 новая 🟡 в работе 🔵 ожидание компании 🔴 ожидание инженера 🟤 ожидание клиента"""
    bot.reply_to(message, msg)

#нереализовано, можно выпилить
def cacti(message, args, action):
    def search(args):
        s = start_cacti_session()
        _links = []
        r = s.get(url.get('cacti_search'), headers={'User-Agent': user_agent_val})
        p = s.post(url.get('cacti_search'), {
        'host_id': 0,
        'graph_template_id': 0,
        'rows': -1,
        'filter': args,
        'graph_add': '',
        'graph_remove': '',
        'graph_list': '',
        })
        c = p.content

        soup = BeautifulSoup(c,'lxml')
        
        a = soup.find_all('a')
        for i in a:
            
            try:
                if i['href'].startswith('graph.php?local_graph_id='):
                    _links.append(url.get('cacti')+i['href'])
            except:
                pass
        return _links
        
    def send_img(message, args):
        s = start_cacti_session()
        r = s.get(args, headers={'User-Agent': user_agent_val})
        
        c = r.content
        soup = BeautifulSoup(c,'lxml')
        
        href = url.get('cacti')+soup.find_all('img', {"class": "graphimage"})[0]['src']
        
        r = s.get(href, headers={'User-Agent': user_agent_val})
        img = r.content
        
        bot.send_photo(message.chat.id, img, caption = args)
    
    if action == 'search':
        graphs = search(args)
        if graphs:
            count = len(graphs)
            
            if count == 1:
                send_img(message, graphs[0])

#шлём коммент из трекера
def send_comment(args, message):
    msg = ''
    if args.isdigit():
        comments = get_comments(args)

        for comment in comments:
            msg += comment + '\n'
    
    if not msg:
        msg = 'пусто'
        
    send_msg_with_split(message, msg, 2000)

#ищем комменты в трекерной записи
def get_comments(args):
    etraxisdb = etraxisdb_connect()
    cur = etraxisdb.cursor(buffered=True)

    if args.isdigit():
        _id = args
    else:
        _id = -1

    _sql = '''select event_id, originator_id, event_time FROM tbl_events where record_id = %s;'''
    
    cur.execute(_sql, (_id,))
    ids = cur.fetchall()
    
    comments = []
    
    _sql = '''select value_id FROM tbl_field_values where event_id = %s;''' 
    cur.execute(_sql, (ids[0][0],))
    _field_text = cur.fetchall()
    
    _post = ''
    
    if _field_text:
        print(_field_text)
        for vid in _field_text:
            if vid[0]:
                if (vid[0] > 100000 and vid[0] < 100000000):
                    print(vid[0])
                    _f = vid[0]

                
                    _sql = '''select * FROM tbl_text_values where value_id = %s;''' 
                    cur.execute(_sql, (_f,))
                    _text = cur.fetchall()
                
                    if _text:
                        _post = _text[0][-1]+'\n'
    
    if _post:
        comments.append(_post)

    for e in ids:
        _sql = '''select comment_body FROM tbl_comments where event_id = %s;''' 
        cur.execute(_sql, (e[0],))
        _t = cur.fetchall()
        
        _sql = '''select fullname FROM tbl_accounts where account_id = %s;''' 
        cur.execute(_sql, (e[1],))
        _name = cur.fetchall()
        
        if _t:
            utc_time = datetime.fromtimestamp(int(e[2]), timezone.utc)
            local_time = utc_time.astimezone()
            _time = local_time.strftime("%d-%m-%Y %H:%M")
            comments.append(str(_time) + ' ' + _name[0][0] + ': ' + _t[0][0] + '\n')
    
    cur.close()
    etraxisdb.close()
    
    return comments

#статус питания коммутатора AC -- от розетки, DC -- от батарейки
def power(message, args):
    ip = check_IPV4(args)
    if ip:
        if check_comm_aviability(ip) > 0 :

            result = ''
            answer = ''
            
            try:
                s = pxssh.pxssh(timeout=90)
                hostname = ping_hostname
                username = ping_username
                password = ping_password
                ssh_prompt = '~$ '
                if not s.login(hostname, username, password, auto_prompt_reset=False):
                    result = "ssh to monitoring failed"
                else:
                    s.sendline('telnet %s' % ip)
                    login = s.expect(['.*[Uu]sername:', '.*[Ll]ogin:', '.*User Name:', '.*~'])
                    if login == 0 or login == 1 or login == 2:
                        s.sendline('admin')
                        s.expect(['[Pp]assword:', '[Pp]assword:'])
                        s.sendline(sw_pass)
                        mode = s.expect([">", "#", '.*:~'])
                        if mode == 0:
                            s.sendline("enable")
                            s.expect("[Pp]assword:")
                            s.sendline(sw_pass)
                            mode = 1
                        if mode == 1:
                            s.sendline('show ver')
                            s.expect("#")
                            switch = str(s.before)
                            s.sendline("terminal length 0")
                            s.expect("#")
                            s.sendline("")
                            s.expect("#")
                            hostname = s.before.decode('utf-8', "ignore").split('\r\n')[1]
                            if (switch.find("S2226G") != -1):
                                result = 'S2226G не поддерживает мониторинг статуса электропитания.'
                                s.sendline('exit')
                                s.sendline('exit')
                            elif (switch.find("Series Software, Version 2.1.1A Build 16162, RELEASE SOFTWARE") != -1):
                                result = 'S2548GX не поддерживает мониторинг статуса электропитания.'
                                s.sendline('exit')
                                s.sendline('exit')
                            elif (switch.find("Image text-base: 0x80010000") != -1):
                                result = 'S2208 не поддерживает мониторинг статуса электропитания.'
                                s.sendline('exit')
                                s.sendline('exit')
                            elif (switch.find("SNR-S2950-24G") != -1):
                                result = 'SNR-S2950-24G не поддерживает мониторинг статуса электропитания.'
                                s.sendline('exit')
                            elif (switch.find("Orion Alpha A26 Device") != -1):
                                result = 'Orion Alpha A26 Device не поддерживает мониторинг статуса электропитания.'
                                s.sendline('exit')
                            elif (switch.find("Alpha-A28F") != -1):
                                result = 'Alpha-A28F не поддерживает мониторинг статуса электропитания.'
                                s.sendline('exit')
                            elif (switch.find("SW version    1.1.48") != -1):
                                result = 'Eltex не поддерживает мониторинг статуса электропитания.'
                                s.sendline('exit')
                            elif (switch.find("SNR-S2985G-24T") != -1):
                                s.sendline('show power status')
                                s.expect(hostname + '#')
                                answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                for element in answer:
                                    result += element + '\n'
                                s.sendline('exit')
                            elif (switch.find("SNR-S2960-24G") != -1):
                                result = 'SNR-S2960-24G не поддерживает мониторинг статуса электропитания.'
                                s.sendline('exit')
                            elif (switch.find("SNR-S2965-8T") != -1):
                                s.sendline('show power status')
                                s.expect(hostname + '#')
                                answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                for element in answer:
                                    result += element + '\n'
                                s.sendline('exit')
                            elif (switch.find("SNR-S2965-24T") != -1):
                                s.sendline('show power status')
                                s.expect(hostname + '#')
                                answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                for element in answer:
                                    result += element + '\n'
                                s.sendline('exit')
                            else:
                                s.sendline('exit')
                                s.sendline('exit')
                                result = 'unknown model'
                        if mode == 2:
                            result = "can\'t connect to host"
                    else:
                        result = "can\'t connect to the host"
                    time.sleep(1)
                    s.logout()
            
            except Exception as e:
                error_capture(e=e)
                result = "pxssh failed on login"
            
            msg = result
            
            if (len(msg) > 4000):
                msg = "message is too long!\n\n" + msg[:4000]
                msg = '`' + re.escape(msg) + '`'
            else:
                msg = '`' + re.escape(msg) + '`'
            bot.reply_to(message, msg, parse_mode='MarkdownV2')
        else:
            bot.reply_to(message, "Коммутатор " + ip + " недоступен или не существует.")

#кабельтест на порту
def cabletest(message, args):
    if args.find(' ') != -1:
        ip = args.split(' ')[0]
        port = args.split(' ')[1]
    else:
        args = args.replace(' ', '')
        if args.find(',') != -1:
            ip = args.split(',')[0]
            port = args.split(',')[1]
        
        elif args.find(':') != -1:
            ip = args.split(':')[0]
            port = args.split(':')[1]
        else:
            bot.reply_to(message, "Формат команды: 'порт-инфо ip port'.")
            return

    ip = check_IPV4(ip)
    if (ip and port.isdigit()):
        if check_comm_aviability(ip) > 0 :

            result = ''
            answer = ''
            
            try:
                s = pxssh.pxssh(timeout=90)
                hostname = ping_hostname
                username = ping_username
                password = ping_password
                ssh_prompt = '~$ '
                if not s.login(hostname, username, password, auto_prompt_reset=False):
                    result = "ssh to monitoring failed"
                else:
                    s.sendline('telnet %s' % ip)
                    login = s.expect(['.*[Uu]sername:', '.*[Ll]ogin:', '.*User Name:', '.*~'])
                    if login == 0 or login == 1 or login == 2:
                        s.sendline('admin')
                        s.expect(['[Pp]assword:', '[Pp]assword:'])
                        s.sendline(sw_pass)
                        mode = s.expect([">", "#", '.*:~'])
                        if mode == 0:
                            s.sendline("enable")
                            s.expect("[Pp]assword:")
                            s.sendline(sw_pass)
                            mode = 1
                        if mode == 1:
                            s.sendline('show ver')
                            s.expect("#")
                            switch = str(s.before)
                            s.sendline("terminal length 0")
                            s.expect("#")
                            s.sendline("")
                            s.expect("#")
                            hostname = s.before.decode('utf-8', "ignore").split('\r\n')[1]
                            if (switch.find("S2226G") != -1):
                                if int(port) > 0 and int(port) <= 24:
                                    s.sendline('config')
                                    s.expect(hostname + '_config#')
                                    s.sendline('int f0/%s' % port)
                                    s.expect(hostname + '_config_f0/%s#' % port)
                                    s.sendline('cable-diagnostic')
                                    s.expect(hostname + '_config_f0/%s#' % port)
                                    s.sendline('exit')
                                    s.expect(hostname + '_config#')
                                    s.sendline('exit')
                                    s.expect(hostname + '#')
                                    s.sendline('show int f0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('config')
                                    s.expect(hostname + '_config#')
                                    s.sendline('int f0/%s' % port)
                                    s.expect(hostname + '_config_f0/%s#' % port)
                                    s.sendline('no cable-diagnostic')
                                    s.expect(hostname + '_config_f0/%s#' % port)
                                    s.sendline('exit')
                                    s.expect(hostname + '_config#')
                                    s.sendline('exit')
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                elif int(port) == 25:
                                    s.sendline('config')
                                    s.expect(hostname + '_config#')
                                    s.sendline('int g0/1')
                                    s.expect(hostname + '_config_g0/1')
                                    s.sendline('cable-diagnostic')
                                    s.expect(hostname + '_config_g0/1')
                                    s.sendline('exit')
                                    s.expect(hostname + '_config#')
                                    s.sendline('exit')
                                    s.expect(hostname + '#')
                                    s.sendline('show int g0/1')
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('config')
                                    s.expect(hostname + '_config#')
                                    s.sendline('int g0/1')
                                    s.expect(hostname + '_config_g0/1')
                                    s.sendline('no cable-diagnostic')
                                    s.expect(hostname + '_config_g0/1')
                                    s.sendline('exit')
                                    s.expect(hostname + '_config#')
                                    s.sendline('exit')
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                                elif int(port) == 26:
                                    s.sendline('config')
                                    s.expect(hostname + '_config#')
                                    s.sendline('int g0/2')
                                    s.expect(hostname + '_config_g0/2')
                                    s.sendline('cable-diagnostic')
                                    s.expect(hostname + '_config_g0/2')
                                    s.sendline('exit')
                                    s.expect(hostname + '_config#')
                                    s.sendline('exit')
                                    s.expect(hostname + '#')
                                    s.sendline('show int g0/2')
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('config')
                                    s.expect(hostname + '_config#')
                                    s.sendline('int g0/2')
                                    s.expect(hostname + '_config_g0/2')
                                    s.sendline('no cable-diagnostic')
                                    s.expect(hostname + '_config_g0/2')
                                    s.sendline('exit')
                                    s.expect(hostname + '_config#')
                                    s.sendline('exit')
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2950-24G") != -1):
                                if int(port) > 0 and int(port) <= 26:
                                    s.sendline('virtual-cable-test int e1/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                            elif (switch.find("Series Software, Version 2.1.1A Build 16162, RELEASE SOFTWARE") != -1):
                                if int(port) > 0 and int(port) <= 4:
                                    s.sendline('config')
                                    s.expect(hostname + '_config#')
                                    s.sendline('int g0/%s' % port)
                                    s.expect(hostname + '_config_g0/%s' % port)
                                    s.sendline('cable-diagnostic')
                                    s.expect(hostname + '_config_g0/%s' % port)
                                    s.sendline('exit')
                                    s.expect(hostname + '_config#')
                                    s.sendline('exit')
                                    s.expect(hostname + '#')
                                    s.sendline('show int g0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('config')
                                    s.expect(hostname + '_config#')
                                    s.sendline('int g0/%s' % port)
                                    s.expect(hostname + '_config_g0/%s' % port)
                                    s.sendline('no cable-diagnostic')
                                    s.expect(hostname + '_config_g0/%s' % port)
                                    s.sendline('exit')
                                    s.expect(hostname + '_config#')
                                    s.sendline('exit')
                                    s.expect(hostname + '#')
                                    s.sendline('exit')
                                    s.expect(hostname + '>')
                                    s.sendline('exit')
                            elif (switch.find("Orion Alpha A26 Device") != -1):
                                if int(port) > 0 and int(port) <= 26:
                                    s.sendline('virtual-cable-test int e1/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            # elif (switch.find("Alpha-A28F") != -1):
                                # if int(port) > 0 and int(port) <= 28:
                                    # s.sendline('show int port %s' % port)
                                    # s.expect(hostname + '#')
                                    # answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    # for element in answer:
                                        # result += element + '\n'
                                    # s.sendline('show mac-address-table l2-address port %s' % port)
                                    # s.expect(hostname + '#')
                                    # answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    # for element in answer:
                                        # result += element + '\n' 
                                    # s.sendline('exit')
                            # elif (switch.find("SW version    1.1.48") != -1):
                                # if int(port) > 0 and int(port) <= 26:
                                    # s.sendline('show interfaces status GigabitEthernet 1/0/%s' % port)
                                    # s.expect('#')
                                    # answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    # for element in answer:
                                        # result += element + '\n'
                                    # s.sendline('show mac address-table interface GigabitEthernet 1/0/%s' % port)
                                    # s.expect('#')
                                    # answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    # for element in answer:
                                        # result += element + '\n' 
                                    # s.sendline('exit')
                            elif (switch.find("SNR-S2985G-24T") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('virtual-cable-test int e1/0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2960-24G") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('virtual-cable-test int e1/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2965-8T") != -1):
                                if int(port) > 0 and int(port) <= 10:
                                    s.sendline('virtual-cable-test int e1/0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            elif (switch.find("SNR-S2965-24T") != -1):
                                if int(port) > 0 and int(port) <= 28:
                                    s.sendline('virtual-cable-test int e1/0/%s' % port)
                                    s.expect(hostname + '#')
                                    answer = s.before.decode('utf-8', "ignore").split('\r\n')
                                    for element in answer:
                                        result += element + '\n'
                                    s.sendline('exit')
                            else:
                                s.sendline('exit')
                                s.sendline('exit')
                                result = 'unknown model'
                        if mode == 2:
                            result = "can\'t connect to host"
                    else:
                        result = "can\'t connect to the host"
                    time.sleep(1)
                    s.logout()
            
            except Exception as e:
                error_capture(e=e)
                result = "pxssh failed on login"
            
            msg = result
            
            if (len(msg) > 4000):
                msg = "message is too long!\n\n" + msg[:4000]
                msg = '`' + re.escape(msg) + '`'
            else:
                msg = '`' + re.escape(msg) + '`'
            bot.reply_to(message, msg, parse_mode='MarkdownV2')

        else:
            bot.reply_to(message, "Коммутатор " + ip + " недоступен или не существует.")

#обработка документации по узлам (нереализовано)
def odf(message, args, cmd):
    res = ''
    num = 0
    msg = ''
    status = ''
    chat_id = message.chat.id
    if cmd == 'info':
        row = district_find(args)
        if row:
            with closing(pg_connect()) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""SELECT name, comment 
                            FROM odf 
                            WHERE street_id = %s""", (row[3], ))
                    for row in cursor:
                        res = row
                        msg = str(row)
    elif cmd == 'list':
        with closing(pg_connect()) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""select o.id, o.name, d.name, d.house, o.comment from districts d
                            join odf o on o.street_id = d.street_id ORDER by o.id;""")
                for row in cursor:
                    msg += "➡️ " + str(row[0]) + " " + str(row[2]) + " " + str(row[3]) + "\n"
                    num += 1
                msg = "Нашлось совпадений: " + str(num) + "\n\n" + msg
                msg += "\nКакой номер интересует?"
                status = 'select'
    if msg:
        bot.reply_to(message, msg)
    
    return {'chat_id': chat_id, 'status': status, 'num': num}

#обрабатываем тыканье в кнопочки настройки кастрюлей
@bot.callback_query_handler(func=lambda c:True)
def inline(c):
    _cmd = c.data.split(',')[0]
    _ip = c.data.split(',')[1]
    _name = c.data.split(',')[2]
    _payback = c.data.split(',', 1)[1]
    msg = ''
    if _cmd == 'OPA':
        _val = op_info(_ip)
        
        if _val[6] == 'NaN':
            _op_power = '\nOptical In: ' + _val[3] + ' dBm\n'
        else:
            _op_power = '\nOptical In1: ' + _val[3] + ' dBm\n' + 'Optical In2: ' + _val[6] + ' dBm\n'
        
        if _val[5] == '72GE':
            key = types.InlineKeyboardMarkup()
            but_A = types.InlineKeyboardButton(text="☑️Аттенюация", callback_data="OPA," + _payback)
            but_E = types.InlineKeyboardButton(text="Эквалайзер", callback_data="OPE," + _payback)
            but_G = types.InlineKeyboardButton(text="АРУ", callback_data="OPG," + _payback)
            but_1 = types.InlineKeyboardButton(text="A0", callback_data="EA0," + _payback)
            but_2 = types.InlineKeyboardButton(text="A1", callback_data="EA1," + _payback)
            but_3 = types.InlineKeyboardButton(text="A2", callback_data="EA2," + _payback)
            but_4 = types.InlineKeyboardButton(text="A3", callback_data="EA3," + _payback)
            but_5 = types.InlineKeyboardButton(text="A4", callback_data="EA4," + _payback)
            but_6 = types.InlineKeyboardButton(text="A5", callback_data="EA5," + _payback)
            but_7 = types.InlineKeyboardButton(text="A6", callback_data="EA6," + _payback)
            but_8 = types.InlineKeyboardButton(text="A7", callback_data="EA7," + _payback)
            but_9 = types.InlineKeyboardButton(text="A8", callback_data="EA8," + _payback)
            but_10 = types.InlineKeyboardButton(text="A9", callback_data="EA9," + _payback)
            but_11 = types.InlineKeyboardButton(text="A10", callback_data="EA10," + _payback)
            but_12 = types.InlineKeyboardButton(text="A11", callback_data="EA11," + _payback)
            but_13 = types.InlineKeyboardButton(text="A12", callback_data="EA12," + _payback)
            but_14 = types.InlineKeyboardButton(text="A13", callback_data="EA13," + _payback)
            but_15 = types.InlineKeyboardButton(text="A14", callback_data="EA14," + _payback)
            but_16 = types.InlineKeyboardButton(text="A15", callback_data="EA15," + _payback)
            but_17 = types.InlineKeyboardButton(text="A16", callback_data="EA16," + _payback)
            but_18 = types.InlineKeyboardButton(text="A17", callback_data="EA17," + _payback)
            but_19 = types.InlineKeyboardButton(text="A18", callback_data="EA18," + _payback)
            but_20 = types.InlineKeyboardButton(text="A19", callback_data="EA19," + _payback)
            but_21 = types.InlineKeyboardButton(text="A20", callback_data="EA20," + _payback)
            key.add(but_A, but_E, but_G, but_1, but_2, but_3, but_4, but_5, but_6, but_7, but_8, but_9, but_10, but_11, but_12, but_13, but_14, but_15, but_16, but_17, but_18, but_19, but_20, but_21)
        else:
            key = types.InlineKeyboardMarkup()
            but_A = types.InlineKeyboardButton(text="☑️Аттенюация", callback_data="OPA," + _payback)
            but_E = types.InlineKeyboardButton(text="Эквалайзер", callback_data="OPE," + _payback)
            but_G = types.InlineKeyboardButton(text="АРУ", callback_data="OPG," + _payback)
            but_1 = types.InlineKeyboardButton(text="A0", callback_data="EA0," + _payback)
            but_2 = types.InlineKeyboardButton(text="A1", callback_data="EA1," + _payback)
            but_3 = types.InlineKeyboardButton(text="A2", callback_data="EA2," + _payback)
            but_4 = types.InlineKeyboardButton(text="A3", callback_data="EA3," + _payback)
            but_5 = types.InlineKeyboardButton(text="A4", callback_data="EA4," + _payback)
            but_6 = types.InlineKeyboardButton(text="A5", callback_data="EA5," + _payback)
            but_7 = types.InlineKeyboardButton(text="A6", callback_data="EA6," + _payback)
            but_8 = types.InlineKeyboardButton(text="A7", callback_data="EA7," + _payback)
            but_9 = types.InlineKeyboardButton(text="A8", callback_data="EA8," + _payback)
            but_10 = types.InlineKeyboardButton(text="A9", callback_data="EA9," + _payback)
            but_11 = types.InlineKeyboardButton(text="A10", callback_data="EA10," + _payback)
            but_12 = types.InlineKeyboardButton(text="A11", callback_data="EA11," + _payback)
            but_13 = types.InlineKeyboardButton(text="A12", callback_data="EA12," + _payback)
            but_14 = types.InlineKeyboardButton(text="A13", callback_data="EA13," + _payback)
            but_15 = types.InlineKeyboardButton(text="A14", callback_data="EA14," + _payback)
            but_16 = types.InlineKeyboardButton(text="A15", callback_data="EA15," + _payback)
            key.add(but_A, but_E, but_G, but_1, but_2, but_3, but_4, but_5, but_6, but_7, but_8, but_9, but_10, but_11, but_12, but_13, but_14, but_15, but_16)
        msg = "➡️ " + _name + '\nIP: ' + _ip + _op_power + 'RF Out: ' + _val[4] + ' dBuV\nATT: ' + _val[0] + '\nEQ: ' + _val[1] + '\nАРУ (AGC): ' + _val[2] + ' dB\nTemp: ' + _val[7] + '°C\nUptime: ' + _val[8] +'\n' + _val[9]+ 'V\n\n'
        msg = re.escape(msg)
        msg = 'Настройка *аттенюации* на\:\n' + msg
    if _cmd == 'OPE':
        _val = op_info(_ip)
        
        if _val[6] == 'NaN':
            _op_power = '\nOptical In: ' + _val[3] + ' dBm\n'
        else:
            _op_power = '\nOptical In1: ' + _val[3] + ' dBm\n' + 'Optical In2: ' + _val[6] + ' dBm\n'
        
        key = types.InlineKeyboardMarkup()
        but_A = types.InlineKeyboardButton(text="Аттенюация", callback_data="OPA," + _payback)
        but_E = types.InlineKeyboardButton(text="☑️Эквалайзер", callback_data="OPE," + _payback)
        but_G = types.InlineKeyboardButton(text="АРУ", callback_data="OPG," + _payback)
        but_1 = types.InlineKeyboardButton(text="E0", callback_data="EE0," + _payback)
        but_2 = types.InlineKeyboardButton(text="E1", callback_data="EE1," + _payback)
        but_3 = types.InlineKeyboardButton(text="E2", callback_data="EE2," + _payback)
        but_4 = types.InlineKeyboardButton(text="E3", callback_data="EE3," + _payback)
        but_5 = types.InlineKeyboardButton(text="E4", callback_data="EE4," + _payback)
        but_6 = types.InlineKeyboardButton(text="E5", callback_data="EE5," + _payback)
        but_7 = types.InlineKeyboardButton(text="E6", callback_data="EE6," + _payback)
        but_8 = types.InlineKeyboardButton(text="E7", callback_data="EE7," + _payback)
        but_9 = types.InlineKeyboardButton(text="E8", callback_data="EE8," + _payback)
        but_10 = types.InlineKeyboardButton(text="E9", callback_data="EE9," + _payback)
        but_11 = types.InlineKeyboardButton(text="E10", callback_data="EE10," + _payback)
        but_12 = types.InlineKeyboardButton(text="E11", callback_data="EE11," + _payback)
        but_13 = types.InlineKeyboardButton(text="E12", callback_data="EE12," + _payback)
        but_14 = types.InlineKeyboardButton(text="E13", callback_data="EE13," + _payback)
        but_15 = types.InlineKeyboardButton(text="E14", callback_data="EE14," + _payback)
        but_16 = types.InlineKeyboardButton(text="E15", callback_data="EE15," + _payback)
        key.add(but_A, but_E, but_G, but_1, but_2, but_3, but_4, but_5, but_6, but_7, but_8, but_9, but_10, but_11, but_12, but_13, but_14, but_15, but_16)
        msg = "➡️ " + _name + '\nIP: ' + _ip + _op_power + 'RF Out: ' + _val[4] + ' dBuV\nATT: ' + _val[0] + '\nEQ: ' + _val[1] + '\nАРУ (AGC): ' + _val[2] + ' dB\nTemp: ' + _val[7] + '°C\nUptime: ' + _val[8] + '\n' + _val[9]+ 'V\n\n'
        msg = re.escape(msg)
        msg = 'Настройка *эквалайзера* на\:\n' + msg
    if _cmd == 'OPG':
        _val = op_info(_ip)
        
        if _val[6] == 'NaN':
            _op_power = '\nOptical In: ' + _val[3] + ' dBm\n'
        else:
            _op_power = '\nOptical In1: ' + _val[3] + ' dBm\n' + 'Optical In2: ' + _val[6] + ' dBm\n'
        
        if _val[5] == '72GE':
            key = types.InlineKeyboardMarkup()
            but_A = types.InlineKeyboardButton(text="Аттенюация", callback_data="OPA," + _payback)
            but_E = types.InlineKeyboardButton(text="Эквалайзер", callback_data="OPE," + _payback)
            but_G = types.InlineKeyboardButton(text="☑️АРУ", callback_data="OPG," + _payback)
            but_1 = types.InlineKeyboardButton(text="OFF", callback_data="EG1," + _payback)
            but_2 = types.InlineKeyboardButton(text="1 dB", callback_data="EG2," + _payback)
            but_3 = types.InlineKeyboardButton(text="2 dB", callback_data="EG3," + _payback)
            but_4 = types.InlineKeyboardButton(text="3 dB", callback_data="EG4," + _payback)
            but_5 = types.InlineKeyboardButton(text="4 dB", callback_data="EG5," + _payback)
            but_6 = types.InlineKeyboardButton(text="5 dB", callback_data="EG6," + _payback)
            but_7 = types.InlineKeyboardButton(text="6 dB", callback_data="EG7," + _payback)
            but_8 = types.InlineKeyboardButton(text="7 dB", callback_data="EG8," + _payback)
            but_9 = types.InlineKeyboardButton(text="8 dB", callback_data="EG9," + _payback)
            but_10 = types.InlineKeyboardButton(text="9 dB", callback_data="EG10," + _payback)
            but_11 = types.InlineKeyboardButton(text="10 dB", callback_data="EG11," + _payback)
            but_12 = types.InlineKeyboardButton(text="11 dB", callback_data="EG12," + _payback)
            but_13 = types.InlineKeyboardButton(text="12 dB", callback_data="EG13," + _payback)
            but_14 = types.InlineKeyboardButton(text="13 dB", callback_data="EG14," + _payback)
            but_15 = types.InlineKeyboardButton(text="14 dB", callback_data="EG15," + _payback)
            but_16 = types.InlineKeyboardButton(text="15 dB", callback_data="EG16," + _payback)
            but_17 = types.InlineKeyboardButton(text="16 dB", callback_data="EG17," + _payback)
            but_18 = types.InlineKeyboardButton(text="17 dB", callback_data="EG18," + _payback)
            but_19 = types.InlineKeyboardButton(text="18 dB", callback_data="EG19," + _payback)
            but_20 = types.InlineKeyboardButton(text="19 dB", callback_data="EG20," + _payback)
            but_21 = types.InlineKeyboardButton(text="20 dB", callback_data="EG21," + _payback)
            but_22 = types.InlineKeyboardButton(text="Auto", callback_data="EG256," + _payback)
            key.add(but_A, but_E, but_G, but_1, but_2, but_3, but_4, but_5, but_6, but_7, but_8, but_9, but_10, but_11, but_12, but_13, but_14, but_15, but_16, but_17, but_18, but_19, but_20, but_21, but_22)
        else:
            key = types.InlineKeyboardMarkup()
            but_A = types.InlineKeyboardButton(text="Аттенюация", callback_data="OPA," + _payback)
            but_E = types.InlineKeyboardButton(text="Эквалайзер", callback_data="OPE," + _payback)
            but_G = types.InlineKeyboardButton(text="☑️АРУ", callback_data="OPG," + _payback)
            but_1 = types.InlineKeyboardButton(text="-7", callback_data="EG-7," + _payback)
            but_2 = types.InlineKeyboardButton(text="-8", callback_data="EG-8," + _payback)
            but_3 = types.InlineKeyboardButton(text="-9", callback_data="EG-9," + _payback)
            key.add(but_A, but_E, but_G, but_1, but_2, but_3)
        msg = "➡️ " + _name + '\nIP: ' + _ip + _op_power + 'RF Out: ' + _val[4] + ' dBuV\nATT: ' + _val[0] + '\nEQ: ' + _val[1] + '\nАРУ (AGC): ' + _val[2] + ' dB\nTemp: ' + _val[7] + '°C\nUptime: ' + _val[8] + '\n' + _val[9]+ 'V\n\n'
        msg = re.escape(msg)
        msg = 'Настройка *автоматической регулировки усиления* \(AGC\) на\:\n' + msg
    if _cmd[:2] == 'EA':
        op_set(_ip, 'A' + _cmd[2:])
        time.sleep(1)
        _val = op_info(_ip)
        
        if _val[6] == 'NaN':
            _op_power = '\nOptical In: ' + _val[3] + ' dBm\n'
        else:
            _op_power = '\nOptical In1: ' + _val[3] + ' dBm\n' + 'Optical In2: ' + _val[6] + ' dBm\n'
        
        if _val[5] == '72GE':
            key = types.InlineKeyboardMarkup()
            but_A = types.InlineKeyboardButton(text="☑️Аттенюация", callback_data="OPA," + _payback)
            but_E = types.InlineKeyboardButton(text="Эквалайзер", callback_data="OPE," + _payback)
            but_G = types.InlineKeyboardButton(text="АРУ", callback_data="OPG," + _payback)
            but_1 = types.InlineKeyboardButton(text="A0", callback_data="EA0," + _payback)
            but_2 = types.InlineKeyboardButton(text="A1", callback_data="EA1," + _payback)
            but_3 = types.InlineKeyboardButton(text="A2", callback_data="EA2," + _payback)
            but_4 = types.InlineKeyboardButton(text="A3", callback_data="EA3," + _payback)
            but_5 = types.InlineKeyboardButton(text="A4", callback_data="EA4," + _payback)
            but_6 = types.InlineKeyboardButton(text="A5", callback_data="EA5," + _payback)
            but_7 = types.InlineKeyboardButton(text="A6", callback_data="EA6," + _payback)
            but_8 = types.InlineKeyboardButton(text="A7", callback_data="EA7," + _payback)
            but_9 = types.InlineKeyboardButton(text="A8", callback_data="EA8," + _payback)
            but_10 = types.InlineKeyboardButton(text="A9", callback_data="EA9," + _payback)
            but_11 = types.InlineKeyboardButton(text="A10", callback_data="EA10," + _payback)
            but_12 = types.InlineKeyboardButton(text="A11", callback_data="EA11," + _payback)
            but_13 = types.InlineKeyboardButton(text="A12", callback_data="EA12," + _payback)
            but_14 = types.InlineKeyboardButton(text="A13", callback_data="EA13," + _payback)
            but_15 = types.InlineKeyboardButton(text="A14", callback_data="EA14," + _payback)
            but_16 = types.InlineKeyboardButton(text="A15", callback_data="EA15," + _payback)
            but_17 = types.InlineKeyboardButton(text="A16", callback_data="EA16," + _payback)
            but_18 = types.InlineKeyboardButton(text="A17", callback_data="EA17," + _payback)
            but_19 = types.InlineKeyboardButton(text="A18", callback_data="EA18," + _payback)
            but_20 = types.InlineKeyboardButton(text="A19", callback_data="EA19," + _payback)
            but_21 = types.InlineKeyboardButton(text="A20", callback_data="EA20," + _payback)
            key.add(but_A, but_E, but_G, but_1, but_2, but_3, but_4, but_5, but_6, but_7, but_8, but_9, but_10, but_11, but_12, but_13, but_14, but_15, but_16, but_17, but_18, but_19, but_20, but_21)
        else:
            key = types.InlineKeyboardMarkup()
            but_A = types.InlineKeyboardButton(text="☑️Аттенюация", callback_data="OPA," + _payback)
            but_E = types.InlineKeyboardButton(text="Эквалайзер", callback_data="OPE," + _payback)
            but_G = types.InlineKeyboardButton(text="АРУ", callback_data="OPG," + _payback)
            but_1 = types.InlineKeyboardButton(text="A0", callback_data="EA0," + _payback)
            but_2 = types.InlineKeyboardButton(text="A1", callback_data="EA1," + _payback)
            but_3 = types.InlineKeyboardButton(text="A2", callback_data="EA2," + _payback)
            but_4 = types.InlineKeyboardButton(text="A3", callback_data="EA3," + _payback)
            but_5 = types.InlineKeyboardButton(text="A4", callback_data="EA4," + _payback)
            but_6 = types.InlineKeyboardButton(text="A5", callback_data="EA5," + _payback)
            but_7 = types.InlineKeyboardButton(text="A6", callback_data="EA6," + _payback)
            but_8 = types.InlineKeyboardButton(text="A7", callback_data="EA7," + _payback)
            but_9 = types.InlineKeyboardButton(text="A8", callback_data="EA8," + _payback)
            but_10 = types.InlineKeyboardButton(text="A9", callback_data="EA9," + _payback)
            but_11 = types.InlineKeyboardButton(text="A10", callback_data="EA10," + _payback)
            but_12 = types.InlineKeyboardButton(text="A11", callback_data="EA11," + _payback)
            but_13 = types.InlineKeyboardButton(text="A12", callback_data="EA12," + _payback)
            but_14 = types.InlineKeyboardButton(text="A13", callback_data="EA13," + _payback)
            but_15 = types.InlineKeyboardButton(text="A14", callback_data="EA14," + _payback)
            but_16 = types.InlineKeyboardButton(text="A15", callback_data="EA15," + _payback)
            key.add(but_A, but_E, but_G, but_1, but_2, but_3, but_4, but_5, but_6, but_7, but_8, but_9, but_10, but_11, but_12, but_13, but_14, but_15, but_16)
        msg = "➡️ " + _name + '\nIP: ' + _ip + _op_power + 'RF Out: ' + _val[4] + ' dBuV\nATT: ' + _val[0] + '\nEQ: ' + _val[1] + '\nАРУ (AGC): ' + _val[2] + ' dB\nTemp: ' + _val[7] + '°C\nUptime: ' + _val[8] + '\n' + _val[9]+ 'V\n\n'
        msg = re.escape(msg)
        msg = 'Настройка *аттенюации* на\:\n' + msg
    if _cmd[:2] == 'EG':
        op_set(_ip, 'G' + _cmd[2:])
        time.sleep(1)
        _val = op_info(_ip)
        
        if _val[6] == 'NaN':
            _op_power = '\nOptical In: ' + _val[3] + ' dBm\n'
        else:
            _op_power = '\nOptical In1: ' + _val[3] + ' dBm\n' + 'Optical In2: ' + _val[6] + ' dBm\n'
        
        if _val[5] == '72GE':
            key = types.InlineKeyboardMarkup()
            but_A = types.InlineKeyboardButton(text="Аттенюация", callback_data="OPA," + _payback)
            but_E = types.InlineKeyboardButton(text="Эквалайзер", callback_data="OPE," + _payback)
            but_G = types.InlineKeyboardButton(text="☑️АРУ", callback_data="OPG," + _payback)
            but_1 = types.InlineKeyboardButton(text="OFF", callback_data="EG1," + _payback)
            but_2 = types.InlineKeyboardButton(text="1 dB", callback_data="EG2," + _payback)
            but_3 = types.InlineKeyboardButton(text="2 dB", callback_data="EG3," + _payback)
            but_4 = types.InlineKeyboardButton(text="3 dB", callback_data="EG4," + _payback)
            but_5 = types.InlineKeyboardButton(text="4 dB", callback_data="EG5," + _payback)
            but_6 = types.InlineKeyboardButton(text="5 dB", callback_data="EG6," + _payback)
            but_7 = types.InlineKeyboardButton(text="6 dB", callback_data="EG7," + _payback)
            but_8 = types.InlineKeyboardButton(text="7 dB", callback_data="EG8," + _payback)
            but_9 = types.InlineKeyboardButton(text="8 dB", callback_data="EG9," + _payback)
            but_10 = types.InlineKeyboardButton(text="9 dB", callback_data="EG10," + _payback)
            but_11 = types.InlineKeyboardButton(text="10 dB", callback_data="EG11," + _payback)
            but_12 = types.InlineKeyboardButton(text="11 dB", callback_data="EG12," + _payback)
            but_13 = types.InlineKeyboardButton(text="12 dB", callback_data="EG13," + _payback)
            but_14 = types.InlineKeyboardButton(text="13 dB", callback_data="EG14," + _payback)
            but_15 = types.InlineKeyboardButton(text="14 dB", callback_data="EG15," + _payback)
            but_16 = types.InlineKeyboardButton(text="15 dB", callback_data="EG16," + _payback)
            but_17 = types.InlineKeyboardButton(text="16 dB", callback_data="EG17," + _payback)
            but_18 = types.InlineKeyboardButton(text="17 dB", callback_data="EG18," + _payback)
            but_19 = types.InlineKeyboardButton(text="18 dB", callback_data="EG19," + _payback)
            but_20 = types.InlineKeyboardButton(text="19 dB", callback_data="EG20," + _payback)
            but_21 = types.InlineKeyboardButton(text="20 dB", callback_data="EG21," + _payback)
            but_22 = types.InlineKeyboardButton(text="Auto", callback_data="EG256," + _payback)
            key.add(but_A, but_E, but_G, but_1, but_2, but_3, but_4, but_5, but_6, but_7, but_8, but_9, but_10, but_11, but_12, but_13, but_14, but_15, but_16, but_17, but_18, but_19, but_20, but_21, but_22)
        else:
            key = types.InlineKeyboardMarkup()
            but_A = types.InlineKeyboardButton(text="Аттенюация", callback_data="OPA," + _payback)
            but_E = types.InlineKeyboardButton(text="Эквалайзер", callback_data="OPE," + _payback)
            but_G = types.InlineKeyboardButton(text="☑️АРУ", callback_data="OPG," + _payback)
            but_1 = types.InlineKeyboardButton(text="-7", callback_data="EG-7," + _payback)
            but_2 = types.InlineKeyboardButton(text="-8", callback_data="EG-8," + _payback)
            but_3 = types.InlineKeyboardButton(text="-9", callback_data="EG-9," + _payback)
            key.add(but_A, but_E, but_G, but_1, but_2, but_3)
        msg = "➡️ " + _name + '\nIP: ' + _ip + _op_power + 'RF Out: ' + _val[4] + ' dBuV\nATT: ' + _val[0] + '\nEQ: ' + _val[1] + '\nАРУ (AGC): ' + _val[2] + ' dB\nTemp: ' + _val[7] + '°C\nUptime: ' + _val[8] + '\n' + _val[9]+ 'V\n\n'
        msg = re.escape(msg)
        msg = 'Настройка *автоматической регулировки усиления* \(AGC\) на\:\n' + msg
        
    if _cmd[:2] == 'EE':
        op_set(_ip, 'E' + _cmd[2:])
        time.sleep(1)
        _val = op_info(_ip)
        
        if _val[6] == 'NaN':
            _op_power = '\nOptical In: ' + _val[3] + ' dBm\n'
        else:
            _op_power = '\nOptical In1: ' + _val[3] + ' dBm\n' + 'Optical In2: ' + _val[6] + ' dBm\n'
        
        key = types.InlineKeyboardMarkup()
        but_A = types.InlineKeyboardButton(text="Аттенюация", callback_data="OPA," + _payback)
        but_E = types.InlineKeyboardButton(text="☑️Эквалайзер", callback_data="OPE," + _payback)
        but_G = types.InlineKeyboardButton(text="АРУ", callback_data="OPG," + _payback)
        but_1 = types.InlineKeyboardButton(text="E0", callback_data="EE0," + _payback)
        but_2 = types.InlineKeyboardButton(text="E1", callback_data="EE1," + _payback)
        but_3 = types.InlineKeyboardButton(text="E2", callback_data="EE2," + _payback)
        but_4 = types.InlineKeyboardButton(text="E3", callback_data="EE3," + _payback)
        but_5 = types.InlineKeyboardButton(text="E4", callback_data="EE4," + _payback)
        but_6 = types.InlineKeyboardButton(text="E5", callback_data="EE5," + _payback)
        but_7 = types.InlineKeyboardButton(text="E6", callback_data="EE6," + _payback)
        but_8 = types.InlineKeyboardButton(text="E7", callback_data="EE7," + _payback)
        but_9 = types.InlineKeyboardButton(text="E8", callback_data="EE8," + _payback)
        but_10 = types.InlineKeyboardButton(text="E9", callback_data="EE9," + _payback)
        but_11 = types.InlineKeyboardButton(text="E10", callback_data="EE10," + _payback)
        but_12 = types.InlineKeyboardButton(text="E11", callback_data="EE11," + _payback)
        but_13 = types.InlineKeyboardButton(text="E12", callback_data="EE12," + _payback)
        but_14 = types.InlineKeyboardButton(text="E13", callback_data="EE13," + _payback)
        but_15 = types.InlineKeyboardButton(text="E14", callback_data="EE14," + _payback)
        but_16 = types.InlineKeyboardButton(text="E15", callback_data="EE15," + _payback)
        key.add(but_A, but_E, but_G, but_1, but_2, but_3, but_4, but_5, but_6, but_7, but_8, but_9, but_10, but_11, but_12, but_13, but_14, but_15, but_16)
        msg = "➡️ " + _name + '\nIP: ' + _ip + _op_power + 'RF Out: ' + _val[4] + ' dBuV\nATT: ' + _val[0] + '\nEQ: ' + _val[1] + '\nАРУ (AGC): ' + _val[2] + ' dB\nTemp: ' + _val[7] + '°C\nUptime: ' + _val[8] + '\n' + _val[9]+ 'V\n\n'
        msg = re.escape(msg)
        msg = 'Настройка *эквалайзера* на\:\n' + msg
    if msg != '':
        bot.reply_to(c.message, msg, parse_mode='MarkdownV2', reply_markup=key)

#добавляем обработку команд старт и хелп, нужно добавить команду send nudes
@bot.message_handler(commands=['start', 'help'])
def send_help(message):
    command = get_command(message.text).lower()
    if check_command_allow(message, command):
        hlp(message)

#бот фактически читает вообще весь текст в группе и выбирает в нём то, что ему кажется командами, возможны недопонимания со стороны человеков
#куча глобальных переменных, колхоз и костыли, надо переделать красиво, но когда?
@bot.message_handler(content_types=['text'])
def worker(message):
    global links
    global request_num
    global request_str
    global request
    global request_drs
    global multiple_zabbix_host
    global multiple_op_host
    global multiple_zabbix_graphs
    global zabbix_num
    global zabbix_hosts
    global zabbix_graphs
    global multiple_odf
    global multiple_odf_num
    chat_id = message.chat.id
    command = get_command(message.text).lower()
    try:
        args = extract_arg(message.text)[0]
    except:
        args = ''
    try:
        if check_command_allow(message, command):            
            if ((command == 'район') and (args != "")):
                district(args, message)
                
            elif ((command == 'тест') and (args != "")):
                cacti(message, args, 'search')
                
            elif ((command == 'кабельтест') and (args != "")):
                cabletest(message, args)
                
            elif ((command == 'узел') and (args != "")):
                odf(message, args, 'info')
                
            elif ((command == 'узел') and (args == "")):
                multiple_odf = odf(message, args, 'list')
                
            elif ((command == 'питание') and (args != "")):
                power(message, args)
              
            elif ((command == 'актуалочка') and (args == "")):
                exp(message)  

            elif ((command == 'аптайм') and (args != "")):
                uptime(message, args)
                
            elif ((command == 'кто') and (args != "")):
                who(args, message)
                
            #настройка кастрюлей
            elif ((command == 'оп') and (args != "")):
                multi, op_list, _num = op_mgmt(args, message, 1, [])
                _num -= 1
                multiple_op_host = {chat_id: multi}
                
                if multi:                
                    multiple_zabbix_graphs = {chat_id: False}
                    multiple_zabbix_host = {chat_id: False}
                
                multiple_zabbix_graphs = {chat_id: not multi}
                zabbix_num = {chat_id: _num}
                zabbix_hosts = {chat_id: op_list}

            elif ((command == 'статус') and (args != "")):
                switch_status(args, message)
                
            elif ((command == 'коммент') and (args != "")):
                send_comment(args, message)

            elif ((command == 'порт') and (args != "")):
                free_ports(message, args)
                
            elif ((command == 'порт-инфо') and (args != "")):
                port_info(args, message)

            elif ((command == 'ошибки') and (args != "")):
                show_errors(args, message)

            elif ((command == 'сброс') and (args != "")):
                err_reset(args, message)       

            elif ((command == 'сигнал') and (args != "")):
                fiber(args, message)
                
            elif ((command == 'ребут') and (args != "")):
                reboot(args, message)
        
            elif ((command == 'пинг') and (args != "")):
                ping(message, 1, args)

            elif ((command == 'флуд') and (args != "")):
                ping(message, 2, args)
                
            elif ((command == 'камера') and (args != "")):
                send_camera_image(args, message)
                
            elif ((command == 'карта') and (args != "")):
                send_map(message, args)
            
            #графики
            elif ((command == 'график') and (args != "")):
                if args.lower() == "мо":
                    send_mo(message)
                elif args.lower() == "цус":
                    send_it(message)
                elif args.lower() == "ит":
                    send_it(message)
                elif args.lower() == "оэ":
                    send_oe(message)   
                elif args.isdigit() and len(args) < 10:
                    jur_graph(args, message)
                else:
                    multi_h, multi_g, x_list, _num = get_graph(args, message, 1, [])
                    _num -= 1
                    multiple_zabbix_graphs = {chat_id: multi_g}
                    multiple_zabbix_host = {chat_id: multi_h}
                    if (multi_g or multi_h):
                        multiple_op_host = {chat_id: False}
                    zabbix_num = {chat_id: _num}
                    zabbix_graphs = {chat_id: x_list}
                    zabbix_hosts = {chat_id: x_list}
                
            elif ((command == 'инфа') and (args != "")):
                get_house_info(args, message)
                    
            elif ((command == 'схема') and (args != "")):
                get_scheme(args, message, 'scheme')

            #поиск по вики
            elif ((command == 'плд') and (args != "")):
                msg, num, svars = search_pages(args)
                if (num == 1):
                    bot.reply_to(message, msg)
                    keys = list(svars.keys())
                    src = svars.get(keys[num-1])
                    c = search_files(src)
                    files = parse_pdf(c)
                    request = {chat_id: False}
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
                    send_msg_with_split(message, msg, 4000)
                    request = {chat_id: True}
                    request_str = {chat_id: svars}
                    request_num = {chat_id: num}
                else:
                    bot.send_message(chat_id, msg)

            elif ((command == 'дрс') and (args != "")):
                get_scheme(args, message, 'drs')

        #если у нас нашлось больше одного графика в заббиксе, то спросим какой нужен в итоге
        if (command.isdigit() and multiple_zabbix_graphs.get(chat_id) and (int(command)-1 <= zabbix_num.get(chat_id)) and (int(command) > 0)):
            multiple_zabbix_graphs = {chat_id: False}
            multi_h, multi_g, x_list, k = get_graph(command, message, 3, zabbix_graphs)
            multiple_zabbix_graphs = {chat_id: multi_g}
            zabbix_num = {chat_id: k}
            zabbix_graphs = {chat_id: x_list}
            multiple_zabbix_host = {chat_id: multi_h}
            zabbix_hosts = {chat_id: x_list}

        #то же, но с хостами в заббиксе  
        elif (command.isdigit() and multiple_zabbix_host.get(chat_id) and (int(command)-1 <= zabbix_num.get(chat_id)) and (int(command) > 0)):
            multiple_zabbix_host = {chat_id: False}
            multi_h, multi_g, x_list, k = get_graph(command, message, 2, zabbix_hosts)
            multiple_zabbix_graphs = {chat_id: multi_g}
            zabbix_num = {chat_id: k}
            zabbix_graphs = {chat_id: x_list}
            multiple_zabbix_host = {chat_id: multi_h}
            zabbix_hosts = {chat_id: x_list}
            
        #то же, но с кастрюлями 
        elif (command.isdigit() and multiple_op_host.get(chat_id) and (int(command)-1 <= zabbix_num.get(chat_id)) and (int(command) > 0)):
            multiple_op_host = {chat_id: False}
            _op_list = zabbix_hosts.get(chat_id)
            multi, op_list, zabbix_num = op_mgmt(command, message, 2, _op_list)
            multiple_op_host = {chat_id: multi}
            #zabbix_num = {chat_id: i}
            zabbix_hosts = {chat_id: op_list}
        
        #выбор узлов связи, это нереализовано, можно выпилить
        elif (command.isdigit() and multiple_odf.get(chat_id) and (int(command)-1 <= zabbix_num.get(chat_id)) and (int(command) > 0)):
            multiple_op_host = {chat_id: False}
            _op_list = zabbix_hosts.get(chat_id)
            multi, op_list, zabbix_num = op_mgmt(command, message, 2, _op_list)
            multiple_op_host = {chat_id: multi}
            #zabbix_num = {chat_id: i}
            zabbix_hosts = {chat_id: op_list}

        #если нашлась куча страниц в вики, спрашиваем какая нужна
        elif (command.isdigit() and request.get(chat_id) and (int(command)-1 <= request_num.get(chat_id)) and (int(command)-1 >= 0)):
            request = {chat_id: False}
            request_drs = {chat_id: False}
            keys = list(request_str.get(chat_id).keys())
            src = request_str.get(chat_id).get(keys[int(command)-1])
            c = search_files(src)
            files = parse_pdf(c)
            request = {chat_id: False}
            if (len(files) == 0):
                bot.reply_to(message, "Нет файлов")
            else:
                count = len(files) // 10
                bot.reply_to(message, "Файлов нашлось: " + str(len(files)))
                for x in range(count + 1):
                    bot.send_media_group(chat_id, [telebot.types.InputMediaDocument(open(doc, 'rb')) for doc in files[x*10:x*10+10]])
                    time.sleep(wait_time)

    except Exception as e:
        error_capture(e=e, message=message)
        pass

#бот перепроверяет исправленные сообщения на предмет скрытых посланий ему лично
@bot.edited_message_handler(content_types=['text'])
def edit_worker(message):
    worker(message)

#вот это нерабочее говно, которое нельзя остановить по Ctrl+C, прибить бота получится только чем-то вроде:
#ps aux | grep 'python3 ./dog_bot.py' | grep -v grep | awk '{print$2}' | xargs kill
def main():
    while True:
        try:
            bot.polling(none_stop=True)
        except KeyboardInterrupt:
            print("quit by KeyboardInterrupt")
            sys.exit(0)
        except:
            pass

#запускаем
if __name__ == '__main__':
    main()
