import imgkit
import vk
from exchangelib import Credentials, Account, FileAttachment, ItemAttachment
import random
from requests import post
from bs4 import BeautifulSoup
from transliterate import translit


vk_bad_files = ('html', 'htm', 'zip', 'exe', 'rar', 'js')

chat_id = 2000000002 #id of your group chat
mail_login = 'myemail@edu.hse.ru'
mail_password = 'mypassword'
session = vk.Session(access_token='VKTOKEN')
group_email = 'groupemail@edu.hse.ru'

vk_api = vk.API(session, v='5.103')
credentials = Credentials(mail_login, mail_password)
account = Account(mail_login, credentials=credentials, autodiscover=True)

def getGreeting():
	greetingsList = ('Пщ пщ... Bleep Bloop...', 'БЛЯЯЯ, Я ПИСЬМО ПОЙМАЛ!1', 'Дзынь!', 'Вам повестка! Возможно...', 'Опять хуйню пишут', 'Ура, новый спам!', 'Все! Не звони и не пиши мне больше! Ах ты...', 'Пщщщ... в эфире ваша любимая рубрика «письма счастья»!', 'Мля, письмо словил')
	return random.choice(greetingsList)
	
def printPlain(text):
	if len(text)<10:
		text += '\n(По всей видимости, текст письма отсутствует)'
	vk_api.messages.send(peer_id=chat_id, message='Содержание письма:\n' + text, random_id=random.getrandbits(64))
	
def replaceAttachmentWithBase64(text, attachs):
	for attachment in attachs:
		if 'cid:'+attachment.content_id in text:
			text = text.replace('cid:'+attachment.content_id, 'data:'+attachment.content_type+';base64,'+base64.b64encode(attachment.content).decode())
	return text
	
def processLetter(item, attached=False):
	sender = item.sender.name + ' (' + item.sender.email_address + ')' if item.sender.name is not None and len (item.sender.name) > 0 else item.sender.email_address
	subj = ' с темой «'+item.subject+'»' if item.subject is not None else ' без темы'
	if item.sender.email_address == 'tskobeleva@hse.ru' and item.subject is None:
		subj = ', как обычно, без темы'
	if attached:
		msg = 'Вложенное письмо от '+sender+subj
	else:
		msg = getGreeting()+'\n\n'+sender+' пишет нам письмо'+subj
	
	if item.body is None:
		vk_api.messages.send(peer_id=chat_id, message=msg+'. И оно пустое :(', random_id=random.getrandbits(64))
		return
	if 'срочно' in item.body.lower():
		msg += '\n БЕГИТЕ ЧИТАТЬ РОНЯЯ КАЛ, ПОСАНЫ!11'
	
	vk_api.messages.send(peer_id=chat_id, message=msg, random_id=random.getrandbits(64))
	if not BeautifulSoup(item.body, "html.parser").find():
		printPlain(item.body)
	else:
		soup = BeautifulSoup(item.body, 'lxml')
		try:
			picture = imgkit.from_string(item.body, False, options={ 'load-error-handling': 'ignore', 'load-media-error-handling': 'ignore', 'disable-local-file-access': None, 'quiet': None})
			width, height = Image.open(BytesIO(picture)).size
			if (width < 50 or height < 50):
				printPlain(soup.text)
			else:
				pfile = post(vk_api.photos.getMessagesUploadServer(peer_id = chat_id)['upload_url'], files = {'photo': ('pic.png', picture)}).json()
				photo = vk_api.photos.saveMessagesPhoto(server = pfile['server'], photo = pfile['photo'], hash = pfile['hash'])[0]
				vk_api.messages.send(peer_id=chat_id, message='Содержание письма:', attachment = 'photo%s_%s'%(photo['owner_id'], photo['id']), random_id=random.getrandbits(64))
				links = [a.get('href') for a in soup.find_all('a', href=True)]
				if links is not None and len(links) > 0:
					vk_api.messages.send(peer_id=chat_id, message='Ссылки из письма:\n'+'\n'.join(set(links)), random_id=random.getrandbits(64))
		except Exception as ex:
			vk_api.messages.send(peer_id=chat_id, message='Не удалось отрендерить содержимое HTML. Вылетел эксепшн '+type(ex).__name__+'. Вывожу тело письма обычным текстом:', random_id=random.getrandbits(64))
			printPlain(soup.text)
	

with open('lastletter.txt', 'r') as content_file:
    last_email = content_file.read()


written = False



dmail = list(account.inbox.all().only('to_recipients', 'cc_recipients', 'bcc_recipients', 'datetime_received').order_by('-datetime_received')[:10]) + list(account.sent.all().only('to_recipients', 'cc_recipients', 'bcc_recipients', 'datetime_received').order_by('-datetime_received')[:10])
dmail = sorted(dmail, key = lambda i: i.datetime_received, reverse=True)
	
for item in dmail:
	if item.to_recipients is not None and group_email in item.to_recipients or item.cc_recipients is not None and group_email in item.cc_recipients or item.bcc_recipients is not None and group_email in item.bcc_recipients:
		if str(item.datetime_received) == str(last_email) and not written:
			exit(0)
		if not written:
			written = True
			with open("lastletter.txt","w+") as f:
				f.write (str(item.datetime_received))
				
mail = list(account.inbox.all().order_by('-datetime_received')[:10]) + list(account.sent.all().order_by('-datetime_received')[:10])
mail = sorted(mail, key = lambda i: i.datetime_received, reverse=True)

for item in mail:
	if item.to_recipients is not None and group_email in item.to_recipients or item.cc_recipients is not None and group_email in item.cc_recipients or item.bcc_recipients is not None and group_email in item.bcc_recipients:
		if str(item.datetime_received) == str(last_email):
			exit(0)
		item.body = replaceAttachmentWithBase64(item.body, item.attachments)
		processLetter(item)
		attachs = list()
		uploadedattachs = ''
		for attachment in item.attachments:
			if isinstance(attachment, FileAttachment):
				if attachment.name.split('.')[-1] in vk_bad_files:
					attachs.append((translit(attachment.name, 'ru', reversed=True)+'.vkpisossosi', attachment.content))
				else:
					attachs.append((translit(attachment.name, 'ru', reversed=True), attachment.content))
			elif isinstance(attachment, ItemAttachment):
				if isinstance(attachment.item, Message):
					processLetter(attachment.item, True)
			
		if len(attachs) > 0:
			for a in attachs:
				if len (a[0]) > 0 and len(a[1]) > 0:
					ufile = post(vk_api.docs.getMessagesUploadServer(type = 'doc', peer_id = chat_id)['upload_url'], files = {'file': a}).json()['file']
					u = vk_api.docs.save(file = ufile, title = a[0])['doc']
					uploadedattachs+='doc%s_%s,'%(u['owner_id'], u['id'])
			uploadedattachs=uploadedattachs[:-1]
			vk_api.messages.send(peer_id=chat_id, message='Вложения:', attachment = uploadedattachs, random_id=random.getrandbits(64))
