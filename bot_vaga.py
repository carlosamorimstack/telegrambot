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

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

wait = WebDriverWait(driver, 30)

while True:
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

                    enviar_telegram("🚨 VAGA DISPONÍVEL PARA RG!")

                    break

            except:
                pass

    print("Nova verificação em 1 minuto...\n")
    time.sleep(60)
