import requests
from urllib.parse import urlparse
import sys
import datetime
import os
import json
import logging
import http.client as httplib
import argparse


def make_short_date(ldate):
    """Длинную строковую дату в дату, потом дату в короткую строку"""
    dt = datetime.datetime.strptime(ldate, "%Y-%m-%dT%H:%M:%S+%f")
    short_date = dt.strftime("%Y.%m.%d")
    return short_date


def create_bitlink(logger, headers='', long_url='google.com'):
    """
    Функция создает короткие ссылки из длинных
    :param logger: logger object
    :param headers: Generic Access Token сформированнный на сайте
    :param long_url: Ссылка которую надо укоротить
    :return: созданная короткая ссылка
    """
    url_template = 'https://api-ssl.bitly.com/v4/{}'
    user, bit = ['user', 'bitlinks']
    with requests.Session() as s:
        bitl_user_info = s.get(url_template.format(user), headers=headers)
        logger.info(f'Получаем группу по пользователю ответ: {bitl_user_info.json()}')
        group_guid = bitl_user_info.json()['default_group_guid']
        payload = {'group_guid': group_guid, 'title': 'shortlink', 'long_url': long_url}
        response = s.post(url_template.format(bit), json=payload, headers=headers)
        bitlink = response.json()['id']
    return bitlink


def check_url(logger, headers, url):
    """Проверка что существует такая
    короткая ссылка url на данном clientid на сайте bitly.com
    :return: True ссылка короткая и уже зарегистрирована False ссылка длинная
    Передается результат для True по сссылке 2-м параметром или комментарий
    """
    url_template = 'https://api-ssl.bitly.com/v4/{}/{}'
    user, bit, groups = ['user', 'bitlinks', 'groups']
    url_tuple = urlparse(url)
    url = url.lstrip(url_tuple[0] + '://')
    with requests.Session() as s:
        resp = s.get(url_template.format(bit, url), headers=headers)
        logger.info(f'Результат проверки битлинка {url} на существование:{resp.text}')
        if not resp.ok:
            return None
        return resp.json()


def get_bitlinks(logger, headers):
    """    Функция возвращает словарь из битлинков
    на вход поддается объект логгирования и заголовок с Client Id
    """
    url_template = 'https://api-ssl.bitly.com/v4/{}/{}/{}/{}'
    user, bit, groups = ['user', 'bitlinks', 'groups']
    id_to_bitlink = dict()
    with requests.Session() as s:
        bitl_user_info = s.get(url_template.format(user, '', '', ''), headers=headers)
        logger.info(f'Получаем группу:{bitl_user_info.text}')
        if bitl_user_info.ok:
            group_guid = bitl_user_info.json()['default_group_guid']
            url = url_template.format(groups, group_guid, bit, '')
            list_of_links = s.get(url, headers=headers)
            logger.info('all bitlinks by guid:{}'.format(list_of_links.text))
            id_to_bitlink = dict((link.get('id'), link.get('link')) for link in list_of_links.json()['links'])
    return id_to_bitlink


def detailed_bit_info(logger, headers, bit_dict):
    """Функция возвращает структуру по детальное статистике
    :param logger: logger object
    :param headers : заголовки к запросу с clientID
    :param bit_dict: словарь из битлинков которые надо перебрать для детальной статистики
    :return url_stats: структура из линков и вложенной статистикой кликов по дням Дата:клики
    """
    url_template = 'https://api-ssl.bitly.com/v4/{}/{}/{}/{}'
    user, bit, groups = ['user', 'bitlinks', 'groups']
    clicks_param = {
        'unit': 'day',
        'units': '-1'
    }
    urls_stats = {}
    with requests.Session() as s:
        for bit_id, bitlink in bit_dict.items():
            url = url_template.format(bit, bit_id, 'clicks', '')
            resp_day = s.get(url, headers=headers, params=clicks_param)
            if not resp_day.ok:
                logger.error(f'битая ссылка: {resp_day.text}')
                urls_stats[bit_id] = None
            logger.info(f'Ответ по дням: {resp_day.text}')
            if len(resp_day.json()['link_clicks']) > 0:
                date_clicks = resp_day.json()['link_clicks']
                day_stats = [{make_short_date(click['date']): click['clicks']} for click in date_clicks]
                urls_stats[bit_id] = {
                    'bitlink': bitlink,
                    'stat_per_day': day_stats
                }
            else:
                urls_stats[bit_id] = {'bitlink': bitlink}
    return urls_stats


def get_input(logger):
    """Обработка ввода пользователя
    выбор задачи и проверка ссылки на Ок если задача 1
    отдает задачу и ссылку если задача 1
    :param logger: объект логгирования
    """
    url = None
    logger.info('СТАРТ')
    task = input('Что будем делать: Добавить ссылку:1/ вывод статистики:2? ')
    if task not in ('1', '2'):
        logger.info(f'Пользователь ввел:{task} это неверный выбор. 1 и 2 на input')
        print(f'Вы ввели:{task}. возможные варианты ввода (1 или 2)')
        sys.exit(0)
    elif task == '1':
        logger.info(f'Пользователь выбрал :{task} - добавление ссылки, спросим ссылку')
        url = input('укажите ссыллку для обработки:')
        try:
            logger.info(f'проверяем {url} на 200')
            resp = requests.get(url)
            if not resp.ok:
                logger.error(f'Ссылка {url} неверна. Результат ответа{resp.text}')
                print(f'Ссылка {url} неверна. Результат ответа{resp.text}')
                sys.exit(1)
        except requests.exceptions.RequestException as e:
            logger.error(f'Получили Исключение на обработке введенной пользователм ссылке: {e}')
            print(f'Ошибка проверки ссылки:{e}')
            sys.exit(1)
    elif task == '2':
        logger.info('Пользователь выбрал вывод статистики')
    return task, url


def get_args(logger):
    logger.info('START')
    parser = argparse.ArgumentParser(description="Shortened long link using bitly.com")
    parser.add_argument('mode', default='list',  choices=['create', 'list'],
                        help='create - Create a short link , list - Output statistics')
    parser.add_argument('-u', '--url',  help='Long url for handling, that should be shortened')
    args = parser.parse_args()
    if args.mode == 'create':
        logger.info(f'Пользователь выбрал :{args.mode} - добавление ссылки, спросим ссылку')
        try:
            logger.info(f'проверяем {args.url} на 200')
            resp = requests.get(args.url)
            if not resp.ok:
                logger.error(f'Ссылка {args.url} неверна. Результат ответа{resp.text}')
                print(f'Ссылка {args.url} неверна. Результат ответа{resp.text}')
                sys.exit(1)
        except requests.exceptions.RequestException as e:
            logger.error(f'Получили Исключение на обработке введенной пользователм ссылке: {e}')
            print(f'Ошибка проверки ссылки:{e}')
            sys.exit(1)
    elif args.mode == 'list':
        logger.info('Пользователь выбрал вывод статистики')
    return args


def main():
    log_format = "%(levelname)s %(asctime)s - %(message)s"
    httplib.HTTPConnection.debuglevel = 0  # 1 -включает
    logging.basicConfig(filename='bitly.log', level=logging.DEBUG, format=log_format, filemode='w')
    logger = logging.getLogger("requests.packages.urllib3")
    clientid = os.getenv("ClientId")
    headers = {
        'Host': 'api-ssl.bitly.com',
        'Connection': 'Keep-Alive',
        'Authorization': clientid
    }
    args = get_args(logger)
    if args.mode == 'create':
        try:
            bitlink_info = check_url(logger=logger, headers=headers, url=args.url)
            if bitlink_info is not None:
                logger.info(f"Пользователь ввел корооткую ссылку:{bitlink_info['title']} вместо динной")
                print(f"Короткий битлинк {args.url} создан {make_short_date(bitlink_info['created_at'])}")
                print(f"Исходная ссылка: {bitlink_info['long_url']}")
                print(f"Называется:{bitlink_info['title']}")
                sys.exit(1)
            try:  # Длинная short_link_ok
                link = create_bitlink(logger=logger, headers=headers, long_url=args.url)
                logger.info(f'Результат создания динной ссылки:{args.url}, битлинк:{link}')
                print(f'Для ссылки {args.url} Создана короткая ссылка:{link}')
                sys.exit(0)
            except requests.exceptions.RequestException as e:
                logger.error(f'Ошибка при создании ссылки:{e} функция create_bitlink()')
                print(f'Ошибка при создании ссылки:{e}')
                sys.exit(1)
        except requests.exceptions.RequestException as e:
            logger.error(f'Ошибка в функции check_url:{e}')
            print(f'Ошибка в функции check_url:{e}')
            sys.exit(1)
    elif args.mode == 'list':
        try:
            id_to_bitlink = get_bitlinks(logger, headers)
            logger.info(f'Все битлинки:{id_to_bitlink.values()}')
            bit_stat = detailed_bit_info(logger, headers, id_to_bitlink)
            print(json.dumps(bit_stat, sort_keys=True, indent=2))
            sys.exit(0)
        except requests.exceptions.RequestException as e:
            logger.error(f'Суммарная статистика - Ошибка:{e}')
            sys.exit(1)


if __name__ == '__main__':
    main()
