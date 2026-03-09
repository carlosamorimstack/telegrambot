import time
import requests

TOKEN = "SEU_TOKEN_AQUI"
CHAT_ID = "SEU_CHAT_ID_AQUI"

URL = "https://seati.segov.ma.gov.br/procon/agendamento/"

ultima_notificacao = False


def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data, timeout=10)
    except:
        print("Erro ao enviar mensagem")


def verificar_vagas():

    global ultima_notificacao

    try:

        resposta = requests.get(URL, timeout=20)

        if resposta.status_code != 200:
            print("Erro ao acessar site")
            return

        html = resposta.text

        # Verificação simples de vagas
        if "horarios" in html.lower() or "agenda" in html.lower():

            print("Possível vaga detectada!")

            if not ultima_notificacao:

                enviar_telegram("🚨 POSSÍVEL VAGA DISPONÍVEL PARA RG!")

                ultima_notificacao = True

        else:

            print("Nenhuma vaga encontrada")
            ultima_notificacao = False

    except Exception as e:

        print("Erro:", e)


print("Bot iniciado...")

while True:

    print("Verificando vagas...")

    verificar_vagas()

    print("Nova verificação em 60 segundos...\n")

    time.sleep(60)
