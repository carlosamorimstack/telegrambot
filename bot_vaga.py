import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

print("Bot iniciado...")

TOKEN = "SEU_TOKEN_AQUI"
CHAT_ID = "SEU_CHAT_ID_AQUI"

ultima_notificacao = None

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data, timeout=10)
    except:
        print("Erro ao enviar mensagem")

def iniciar_driver():

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    # caminho do chrome no servidor
    options.binary_location = "/usr/bin/chromium"

    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)

    return driver

driver = iniciar_driver()
wait = WebDriverWait(driver, 30)

while True:

    try:

        print("Verificando vagas...")

        driver.get("https://seati.segov.ma.gov.br/procon/agendamento/")

        wait.until(lambda d: len(d.find_elements(By.TAG_NAME, "select")) >= 2)

        time.sleep(2)

        selects = driver.find_elements(By.TAG_NAME, "select")

        cidade = Select(selects[0])

        for opt in cidade.options:
            if "Alto Alegre" in opt.text:
                cidade.select_by_visible_text(opt.text)
                break

        time.sleep(3)

        selects = driver.find_elements(By.TAG_NAME, "select")
        servico = Select(selects[1])

        for opt in servico.options:
            if "RG Nacional" in opt.text or "CIN" in opt.text:
                servico.select_by_visible_text(opt.text)
                break

        time.sleep(3)

        campo_data = wait.until(
            lambda d: d.find_element(By.CSS_SELECTOR, "input[placeholder='dd/mm/aaaa']")
        )

        driver.execute_script("arguments[0].removeAttribute('readonly');", campo_data)

        campo_data.click()

        time.sleep(3)

        dias = driver.find_elements(
            By.CSS_SELECTOR,
            ".ui-datepicker-calendar td:not(.ui-datepicker-unselectable) a"
        )

        if len(dias) > 0:

            for dia in dias:

                try:

                    driver.execute_script("arguments[0].click();", dia)

                    time.sleep(3)

                    horarios = driver.find_elements(
                        By.CSS_SELECTOR,
                        ".horarios div, .agenda div"
                    )

                    if len(horarios) > 0:

                        print("Horário disponível!")

                        global ultima_notificacao

                        if ultima_notificacao != "vaga":

                            enviar_telegram("🚨 VAGA DISPONÍVEL PARA RG!")

                            ultima_notificacao = "vaga"

                        break

                except:
                    pass

        else:
            print("Nenhuma data disponível")

        print("Nova verificação em 1 minuto...\n")

        time.sleep(60)

    except Exception as e:

        print("Erro detectado:", e)

        try:
            driver.quit()
        except:
            pass

        print("Reiniciando navegador...")

        driver = iniciar_driver()
        wait = WebDriverWait(driver, 30)

        time.sleep(10)
