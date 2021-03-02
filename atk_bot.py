#!/usr/bin/python
 
from configparser import ConfigParser
from bs4 import BeautifulSoup
import requests
import telebot
import sys
import os

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

request_num = {}
request_str = {}
request = {}

bot = telebot.TeleBot(bot_id)

url = {
    'root_url' : config.get('url', 'root_url'),
    'ref_url_ref' : config.get('url', 'ref_url_ref'),
    'cookie' : config.get('url', 'cookie'),
    'host' : config.get('url', 'host'),
    'auth_page' : config.get('url', 'auth_page'),
    'search_url' : config.get('url', 'search_url')
}

def extract_arg(arg):
    return arg.split(maxsplit=1)[1:]
    
def get_command(arg):
    return arg.split(' ', 1)[0]
    
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
        pass
    try:
        if (str(_chat_id) == str(valid_chat) or str(_chat_id) == str(valid_chat2)):
            if (_command == 'плд'):
                #bot.reply_to(message, "Ищу плд по имени: " + _args)
                
                s = requests.Session()
                r = s.get(url.get('root_url'), headers = {'User-Agent': user_agent_val})
                print ("set User Agent: "+user_agent_val)
                
                _cookie = s.cookies.get(url.get('cookie'), domain=url.get('host'))
                s.headers.update({'Referer':url.get('ref_url_ref')})
                s.headers.update({'User-Agent':user_agent_val})
                print ("set " + url.get('cookie')+" to "+str(_cookie))
                       
                r = s.get(url.get('auth_page'), headers = {'User-Agent': user_agent_val})
                print ("try to auth on "+url.get('auth_page'))
                
                post_request = s.post(url.get('auth_page'), {
                'sectok' : '', 
                'id' : 'start',
                'do' : 'login',
                'u' : login,
                'p' : password,
                'r' : 1
                })
                
                r = s.get(url.get('search_url')+_args, headers = {'User-Agent': user_agent_val})
                print ("searching "+url.get('search_url')+_args)
                
                c = r.content
                soup = BeautifulSoup(c,'lxml')
                svars = {}
                
                for var in soup.findAll('a', class_="wikilink1"):
                    svars[var['title']] = var['href']
                    
                num = 0
                msg = ""
                for key in svars:
                    num += 1
                    msg += "➡️ " + str(num) + " " + key.replace('corp:pld:', '').replace('_', ' ').replace('corp:','') + "\n"
                
                if (len(msg) > 1023):
                    msg = msg[:1023]
                    msg = '➡️'.join(msg.split('➡️')[:-1])
                    msg = "Нашлось совпадений: " + str(num) + "\nПревышена максимальная длина сообщения!\n\n" + msg
                else:
                    msg =  "Нашлось совпадений: " + str(num) + "\n\n" + msg
                
                if (num == 1):
                    bot.send_message(_chat_id, msg)
                    keys = list(svars.keys())
                    src = svars.get(keys[num-1])
                    
                    r = s.get(url.get('root_url') + src, headers = {'User-Agent': user_agent_val})
                    
                    c = r.content
                    soup = BeautifulSoup(c,'lxml')
                    
                    print("soup: " + url.get('root_url') + src)
                    
                    if (not soup.findAll('a', class_="media mediafile mf_pdf")):
                        bot.send_message(_chat_id, "Нет файлов")
                    else:
                        for var in soup.findAll('a', class_="media mediafile mf_pdf"):
                            _n = var["title"]
                            _h = var['href']
                            _n = ('.pdf'.join(_n.split('.pdf')[:-1]) + '.pdf').replace('_', ' ').replace('corp', '').replace('pld', '').replace('_', ' ')
                            f = open(save_dir + _n, "wb")
                            r = s.get(url.get('root_url') + _h, headers = {'User-Agent': user_agent_val})
                            print(r)
                            f.write(r.content)
                            f.close()
                            doc = open(save_dir + _n, 'rb')
                            bot.send_document(_chat_id, doc)
                        
                    request = {_chat_id : False}
                elif (num > 1):
                    msg += "\nКакой номер интересует?"
                    bot.send_message(_chat_id, msg)
                    request = {_chat_id : True}
                    request_str = {_chat_id : svars}
                    request_num = {_chat_id : num}
                else:
                    bot.send_message(_chat_id, msg)
                
            elif (_command.isdigit() and request.get(_chat_id) and (int(_command)-1 <= request_num.get(_chat_id)) and (int(_command)-1 >= 0)):
                request = {_chat_id : False}
                keys = list(request_str.get(_chat_id).keys())
                #bot.reply_to(message, request_str.get(_chat_id).get(keys[int(_command)-1]))
                
                src = request_str.get(_chat_id).get(keys[int(_command)-1])
                    
                s = requests.Session()
                r = s.get(url.get('root_url'), headers = {'User-Agent': user_agent_val})
                print ("set User Agent: "+user_agent_val)
                
                _cookie = s.cookies.get(url.get('cookie'), domain=url.get('host'))
                s.headers.update({'Referer':url.get('ref_url_ref')})
                s.headers.update({'User-Agent':user_agent_val})
                print ("set " + url.get('cookie')+" to "+str(_cookie))
                       
                r = s.get(url.get('auth_page'), headers = {'User-Agent': user_agent_val})
                print ("try to auth on "+url.get('auth_page'))
                
                post_request = s.post(url.get('auth_page'), {
                'sectok' : '', 
                'id' : 'start',
                'do' : 'login',
                'u' : login,
                'p' : password,
                'r' : 1
                })
                    
                r = s.get(url.get('root_url') + src, headers = {'User-Agent': user_agent_val})
                
                c = r.content
                soup = BeautifulSoup(c,'lxml')
                
                print("soup: " + url.get('root_url') + src)
                
                if (not soup.findAll('a', class_="media mediafile mf_pdf")):
                    bot.send_message(_chat_id, "Нет файлов")
                else:
                    for var in soup.findAll('a', class_="media mediafile mf_pdf"):
                        _n = var["title"]
                        _h = var['href']
                        _n = ('.pdf'.join(_n.split('.pdf')[:-1]) + '.pdf').replace('_', ' ').replace('corp', '').replace('pld', '')
                        f = open(save_dir + _n, "wb")
                        r = s.get(url.get('root_url') + _h, headers = {'User-Agent': user_agent_val})
                        print(r)
                        f.write(r.content)
                        f.close()
                        doc = open(save_dir + _n, 'rb')
                        bot.send_document(_chat_id, doc)
                
                request = {_chat_id : False}
                
            else:
                pass
        else:
            print (_chat_id)
    except Exception as e:
            print (e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            #logging.error(exc_type, fname, exc_tb.tb_lineno)
            bot.reply_to(message, e)
            pass
        
bot.polling(none_stop = True)
