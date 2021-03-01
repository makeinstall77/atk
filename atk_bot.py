#!/usr/bin/python
 
from configparser import ConfigParser
from bs4 import BeautifulSoup
import requests
import telebot

#config init
config = ConfigParser()
config.read('config.ini')
bot_id = config.get('id', 'bot')
login = config.get('id', 'login')
password = config.get('id', 'password')
valid_chat = config.get('id', 'valid_chat')

request_num = {}
request_str = {}
request = {}

bot = telebot.TeleBot(bot_id)

user_agent_val = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36'

url = {
    'root_url' : 'http://wiki-jur.inetvl.corp',
    'ref_url_ref' : 'http://wiki-jur.inetvl.corp/doku.php',
    'cookie' : 'DokuWiki',
    'host' : 'wiki-jur.inetvl.corp',
    'auth_page' : 'http://wiki-jur.inetvl.corp/doku.php?id=start&do=login&sectok=',
    'search_url' : 'http://wiki-jur.inetvl.corp/doku.php?do=search&id='
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
    
    if (str(_chat_id) == str(valid_chat)):
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
                
                for var in soup.findAll('a', class_="media mediafile mf_pdf"):
                    #var['title'] = var['href']
                    f = open('pld/' + var.string, "wb") #открываем файл для записи, в режиме wb
                    r = s.get(url.get('root_url') + var['href'], headers = {'User-Agent': user_agent_val}) #делаем запрос
                    print(r)
                    f.write(r.content) #записываем содержимое в файл; как видите - content запроса
                    f.close()
                    doc = open('pld/' + var.string, 'rb')
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
            
        elif (_command.isdigit() and request.get(_chat_id) and (int(_command)-1 <= request_num.get(_chat_id)) and (int(_command)-1 > 0)):
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
            
            for var in soup.findAll('a', class_="media mediafile mf_pdf"):
                #var['title'] = var['href']
                f = open('pld/' + var.string, "wb") #открываем файл для записи, в режиме wb
                r = s.get(url.get('root_url') + var['href'], headers = {'User-Agent': user_agent_val}) #делаем запрос
                print(r)
                f.write(r.content) #записываем содержимое в файл; как видите - content запроса
                f.close()
                doc = open('pld/' + var.string, 'rb')
                bot.send_document(_chat_id, doc)
                
            request = {_chat_id : False}
            
        else:
            pass
    else:
        print (_chat_id)
        
bot.polling(none_stop = True)