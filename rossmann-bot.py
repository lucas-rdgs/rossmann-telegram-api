import pandas as pd
import requests
import json
import os
from flask import Flask, request, Response

TOKEN = '5619162120:AAGnpWldLR-hjo7a1prM1ZE1SfZyP6juTsE'

# Informações sobre o bot
# https://api.telegram.org/bot5619162120:AAGnpWldLR-hjo7a1prM1ZE1SfZyP6juTsE/getMe

# getUpdates
# https://api.telegram.org/bot5619162120:AAGnpWldLR-hjo7a1prM1ZE1SfZyP6juTsE/getUpdates

# getUpdates
# https://api.telegram.org/bot5619162120:AAGnpWldLR-hjo7a1prM1ZE1SfZyP6juTsE/sendMessage?chat_id=1999802448&text=Hi, Lucas

# Webhook Heroku
# https://api.telegram.org/bot5619162120:AAGnpWldLR-hjo7a1prM1ZE1SfZyP6juTsE/setWebhook?url=https://rossmann-bot-lr.herokuapp.com/

def send_message(chat_id, text):
    url = 'https://api.telegram.org/bot{}/'.format(TOKEN)
    url = url + 'sendMessage?chat_id={}'.format(chat_id)

    r = requests.post(url, json={'text': text})
    print('Status Code:', r.status_code)

    return None


def load_dataset(store_id):
    # carregando os dados de teste
    df10 = pd.read_csv('test.csv')
    df_store_raw = pd.read_csv('store.csv')

    # mesclando os dados de teste com os dados das lojas
    df_test = pd.merge(df10, df_store_raw, how='left', on='Store')

    # escolhendo lojas para fazer a previsão
    df_test = df_test[df_test['Store'] == store_id]

    if not df_test.empty:
    
        # removendo os dias em que as lojas estão fechadas
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop('Id', axis=1)

        # convertendo DataFrame para json
        data = json.dumps(df_test.to_dict(orient='records'))

    else:
        data = 'error'
    
    return data


def predict(data):
    # Chamada da API
    url = 'https://rossmann-test-lr.herokuapp.com/rossmann/predict'
    header = {'Content-type': 'application/json'} 
    data = data

    r = requests.post(url, data=data, headers=header)
    print('Status Code {}'.format(r.status_code))

    # Convertendo o json para DataFrame
    d1 = pd.DataFrame(r.json(), columns=r.json()[0].keys())

    return d1


def parse_message(message):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']

    store_id = store_id.replace('/', '')

    try:
        store_id = int(store_id)

    except ValueError:

        store_id = 'error'

    return chat_id, store_id


# Inicializando a API
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        message = request.get_json()

        chat_id, store_id = parse_message(message)

        if store_id == '/start':
            send_message('Digite um código de loja para iniciar') 
            return Response('Ok', status=200)      


        if store_id != 'error':
            # carregar dados
            data = load_dataset(store_id)

            if data != 'error':
                # previsão
                d1 = predict(data)

                # cálculo
                d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()

                # enviar mensagem
                msg = 'A loja número {} venderá ${:,.2f} nas próximas 6 semanas'.format(d2['store'].values[0], d2['prediction'].values[0])

                send_message(chat_id, msg)
                send_message(chat_id, 'Para continuar, insira outro código identificador')
                return Response('Ok', status=200)

            else:
                send_message(chat_id, 'Esta loja não está disponível')
                send_message(chat_id, 'Insira outro identificador')
                return Response('Ok', status=200)

        else:
            send_message(chat_id, 'Código de loja inválido')
            send_message(chat_id, 'Insira um código válido')
            return Response('Ok', status=200)

    else:
        return '<h1> Rossmann Telegram Bot </h1>'

if __name__ == '__main__':
    port = os.environ.get('PORT', 5000)
    app.run(host='0.0.0.0', port=port)

