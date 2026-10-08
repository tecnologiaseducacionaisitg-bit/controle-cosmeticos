from datetime import datetime, timedelta
import os
import pandas as pd
import requests

# Definições do Bot do Telegram
TOKEN = "8443441268:AAE9GOMo1J93Pvt8tuGHvBiHZZFjjodR9-o"
CHAT_ID = "1344111409"
DB_FILE = "produtos_cosmeticos.csv"


def enviar_mensagem_telegram(mensagem):
  url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
  try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
      print("Alerta enviado com sucesso para o Telegram! 🚀")
    else:
      print(f"Erro ao enviar mensagem: {response.text}")
  except Exception as e:
    print(f"Erro de conexão com o Telegram: {e}")


def verificar_e_alertar():
  if not os.path.exists(DB_FILE):
    print("Nenhum banco de dados encontrado. Cadastre produtos no sistema web primeiro.")
    return

  df = pd.read_csv(DB_FILE)
  if df.empty:
    print("A base de dados está vazia. Nenhum produto para verificar.")
    return

  hoje = datetime.now().date()
  limite = hoje + timedelta(days=5)

  df["Validade_dt"] = pd.to_datetime(df["Validade"]).dt.date
  alerta_df = df[df["Validade_dt"] <= limite].sort_values(by="Validade_dt")

  if not alerta_df.empty:
    texto_msg = "🚨 *ALERTA DE VALIDADE - COSMÉTICOS* 🚨\n\nOs seguintes produtos estão vencidos ou vencem em breve (próximos 5 dias):\n\n"
    
    for _, row in alerta_df.iterrows():
      dias_restantes = (row["Validade_dt"] - hoje).days
      if dias_restantes < 0:
        status = f"🔴 *VENCIDO há {abs(dias_restantes)} dias!*"
      elif dias_restantes == 0:
        status = "⚠️ *VENCE HOJE!*"
      else:
        status = f"⏳ Vence em *{dias_restantes} dias*"

      texto_msg += f"• *{row['Produto']}*\n  Cód: `{row['Codigo_Barras']}` | Lote: {row['Lote']}\n  Validade: {row['Validade']} -> {status}\n\n"

    enviar_mensagem_telegram(texto_msg)
  else:
    print("Tudo em ordem! Nenhum produto em risco de vencimento nos próximos 5 dias.")


if __name__ == "__main__":
  verificar_e_alertar()