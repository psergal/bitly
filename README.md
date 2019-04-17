# Bitlink management
***
## Why
THis is a training project for better understanding how to work with API services.
## Prerequisites  
The API-site for the testing is [bitly.com](https://bitly.com).  
You need to register there and obtain a token for the work, look [the guide](https://dev.bitly.com/get_started.html).  
The token provides authorization on the services. You should put it your system environment.  
After that program derives it by `os.getenv` function.  

## Installing
The code executes by __Python 3.7__, it should installed.   
Then use __pip__ for installing depended libraries:  
`pip install -r requirements.txt`

## Usage
You can get description using command line typing `python bitlink.py -h`  
There are 2 modes you should choose from:
1. Creating a short link from the long one `python bitlink.py 1 -u <URL>`
2. Output accumulated statistics  `python bitlink.py 2`

## Example
    python bitlink.py  
    Что будем делать: Добавить ссылку:1/ вывод статистики:2? *1*  
    укажите ссыллку для обработки: https://github.com/kennethreitz/requests  
    Для ссылки https://github.com/kennethreitz/requests Создана короткая ссылка:`bit.ly/2IC8JXj`  

## License
This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/psergal/bitly/blob/master/license.md) file for details  
