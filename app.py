from datetime import datetime, timedelta
import os
import pandas as pd
import requests
import streamlit as st

DB_FILE = "produtos_cosmeticos.csv"

# Definições do Bot do Telegram para envio imediato
TOKEN = "8443441268:AAE9GOMo1J93Pvt8tuGHvBiHZZFjjodR9-o"
CHAT_ID = "1344111409"


def enviar_mensagem_telegram(mensagem):
  url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
  try:
    response = requests.post(url, json=payload)
    return response.status_code == 200
  except Exception:
    return False


def carregar_dados():
  if os.path.exists(DB_FILE):
    return pd.read_csv(DB_FILE)
  else:
    return pd.DataFrame(
        columns=[
            "Codigo_Barras",
            "Produto",
            "Lote",
            "Validade",
            "Data_Cadastro",
        ]
    )


def salvar_dados(df):
  df.to_csv(DB_FILE, index=False)


st.set_page_config(page_title="Controle de Validade - Cosméticos", layout="wide")

st.title("💄 Controle de Validade - Cosméticos")
st.write(
    "Sistema de cadastro e alerta de vencimentos para a seção de cosméticos."
)

df = carregar_dados()

aba1, aba2, aba3 = st.tabs(
    ["📥 Cadastrar Produto", "📋 Produtos Cadastrados", "🚨 Alertas (5 Dias)"]
)

with aba1:
  st.subheader("Cadastrar Novo Produto")

  with st.form("form_cadastro", clear_on_submit=True):
    codigo = st.text_input(
        "Código de Barras", placeholder="Ex: 7891035000000"
    )
    nome_produto = st.text_input(
        "Nome do Produto / Marca", placeholder="Ex: Hidratante Natura Tododia"
    )
    lote = st.text_input("Lote (Opcional)", placeholder="Ex: L1234")
    validade = st.date_input("Data de Validade")

    enviar = st.form_submit_button("Salvar Produto")

    if enviar:
      if codigo and nome_produto:
        data_val_str = str(validade)
        novo_registro = pd.DataFrame(
            [{
                "Codigo_Barras": str(codigo),
                "Produto": nome_produto,
                "Lote": lote if lote else "N/D",
                "Validade": data_val_str,
                "Data_Cadastro": str(datetime.now().date()),
            }]
        )
        df = pd.concat([df, novo_registro], ignore_index=True)
        salvar_dados(df)

        # Verificação imediata se vence nos próximos 5 dias ou já venceu
        hoje = datetime.now().date()
        validade_dt = datetime.strptime(data_val_str, "%Y-%m-%d").date()
        dias_restantes = (validade_dt - hoje).days

        if dias_restantes <= 5:
          if dias_restantes < 0:
            status_txt = f"🔴 *VENCIDO há {abs(dias_restantes)} dias!*"
          elif dias_restantes == 0:
            status_txt = "⚠️ *VENCE HOJE!*"
          else:
            status_txt = f"⏳ Vence em *{dias_restantes} dias*"

          msg_alerta = (
              "🚨 *ALERTA DE VALIDADE IMEDIATO* 🚨\n\n"
              f"Novo produto cadastrado em situação crítica:\n\n"
              f"• *{nome_produto}*\n"
              f"  Cód: `{codigo}` | Lote: {lote if lote else 'N/D'}\n"
              f"  Validade: {data_val_str} -> {status_txt}"
          )
          enviar_mensagem_telegram(msg_alerta)
          st.success(
              f"Produto **{nome_produto}** cadastrado e alerta enviado para o"
              " Telegram com sucesso! 🚀"
          )
        else:
          st.success(
              f"Produto **{nome_produto}** cadastrado com sucesso! (Fora do"
              " prazo de alerta)"
          )
      else:
        st.error(
            "Preencha pelo menos o Código de Barras e o Nome do Produto!"
        )

with aba2:
  st.subheader("Lista de Produtos Cadastrados")
  if not df.empty:
    busca = st.text_input("🔍 Buscar por nome ou código de barras")
    df_exibicao = df.copy()
    if busca:
      df_exibicao = df_exibicao[
          df_exibicao["Produto"].str.contains(busca, case=False, na=False)
          | df_exibicao["Codigo_Barras"].str.contains(
              busca, case=False, na=False
          )
      ]

    st.dataframe(df_exibicao, use_container_width=True)

    if st.button("🗑️ Excluir todos os registros"):
      if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
      st.rerun()
  else:
    st.info("Nenhum produto cadastrado ainda.")

with aba3:
  st.subheader("🚨 Produtos Próximos do Vencimento (Próximos 5 Dias)")
  if not df.empty:
    hoje = datetime.now().date()
    limite = hoje + timedelta(days=5)

    df["Validade_dt"] = pd.to_datetime(df["Validade"]).dt.date
    alerta_df = df[df["Validade_dt"] <= limite].sort_values(by="Validade_dt")

    if not alerta_df.empty:
      st.warning(
          "Atenção! Os seguintes produtos estão vencidos ou vencem em breve:"
      )
      for index, row in alerta_df.iterrows():
        dias_restantes = (row["Validade_dt"] - hoje).days
        if dias_restantes < 0:
          status = f"🔴 **VENCIDO há {abs(dias_restantes)} dias!**"
        elif dias_restantes == 0:
          status = "⚠️ **VENCE HOJE!**"
        else:
          status = f"⏳ Vence em **{dias_restantes} dias**"

        st.markdown(
            f"- **{row['Produto']}** (Cód: {row['Codigo_Barras']}) | Lote:"
            f" {row['Lote']} | Validade: **{row['Validade']}** -> {status}"
        )
    else:
      st.success("Tudo em ordem! Nenhum produto vencendo nos próximos 5 dias.")
  else:
    st.info("Cadastre produtos para ver os alertas.")
