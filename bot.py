# -*- coding: utf-8 -*-
import telegram

import config



bot = telegram.Bot(token = config.TOKEN)
context = (config.CERT, config.CERT_KEY)


