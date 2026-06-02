WEBHOOK = "https://discord.com/api/webhooks/1511435238503350362/-8ee_JJ2Q_zKv61PKcGRSPJDlMkeIndtk_60B--pUCDbG72Bp0JrqYhLYh6_T-edinav"

import requests
import time

webhook_url = WEBHOOK
payload = {
        "title": "------Infinity------ ",
        "content": "Promoção encontrada! ",
        "content": "colocar a porra da promocao aq ",
        "username": "Bot da Infinity ",
        "avatar_url": "https://i.pinimg.com/736x/0f/f4/6c/0ff46c4906fa179a044a649e7d1b15e4.jpg"
}
time.sleep(1)
response = requests.post(webhook_url, json=payload)
print(response.status_code)
