##################################################################################
### Importa as libs necessárias
##################################################################################

import os
import streamlit as st
import uuid
import pyodbc
from dotenv import dotenv_values
from azure.storage.blob import BlobServiceClient

##################################################################################
### Carrega as variaveis de ambiente
##################################################################################

config = dotenv_values("conf.env")

##################################################################################
### Define as variaveis de conexão ao blob storage
##################################################################################

blobConnect   = config.get("blobConnect")
blobContainer = config.get("blobContainer")
blobAccount   = config.get("blobAccount")

##################################################################################
### Define as variaveis de conexão ao banco de dados
##################################################################################

DB_SERVER   = config.get("DB_SERVER")
DB_DATABASE = config.get("DB_DATABASE")
DB_USER     = config.get("DB_USER")
DB_PASSWORD = config.get("DB_PASSWORD")

##################################################################################
### Cria o form de cadastro de produtos com o streamlit
##################################################################################

st.header("Kids Shopping - Cadastro de Produtos")

product_name = st.text_input("Nome do produto:")
product_price = st.number_input("Valor do produto:", min_value=0.0, format="%.2f")
product_description = st.text_input("Descrição do produto:")
product_image = st.file_uploader("Upload da imagem do produto", type=["jpg", "jpeg", "png", "webp"])

##################################################################################
### Salva as imagens no blob Storage e retorna a url da imagem salva
##################################################################################

def upload_blob(file):
    blob_service_client = BlobServiceClient.from_connection_string(blobConnect)
    container_client = blob_service_client.get_container_client(blobContainer)
    blob_name = str(uuid.uuid4()) + file.name
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file, overwrite=True)
    image_url = f"https://{blobAccount}.blob.core.windows.net/{blobContainer}/{blob_name}"
    return image_url

##################################################################################
### Cadastra um novo produto no banco de dados
##################################################################################

def insert_product(name, price, description, image_file):

    try:
        image_url = upload_blob(image_file)
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_DATABASE};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD}"
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Produtos (nome, preco, descricao, imagem_url) VALUES (?, ?, ?, ?)",
            (name, price, description, image_url)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir produto: {e}")
        return False

##################################################################################
### Lista de produtos cadastrados no banco de dados
##################################################################################

def list_products():

    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_DATABASE};"
            f"UID={DB_USER};"
            f"PWD={DB_PASSWORD}"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Produtos")
        rows = cursor.fetchall()
        conn.close()
        return rows

    except Exception as e:
        st.error(f"Erro ao listar produtos: {e}")
        return []

##################################################################################
### Exibe os produtos cadastrados em cards
##################################################################################

def list_products_screen():
    products = list_products()

    if products:
        cards_por_linha = 4
        cols = st.columns(cards_por_linha)

        for i, product in enumerate(products):

            with cols[i % cards_por_linha]:
                st.markdown(f'### {product[1]}')  # Nome
                st.write(f'**Descrição:** {product[2]}')  # Descrição

                try:
                    preco_formatado = f'R${float(product[3]):.2f}'  # Preço
                except (ValueError, TypeError):
                    preco_formatado = 'Preço inválido'
                st.write(f'**Preço:** {preco_formatado}')

                if product[4]:  # Imagem
                    html_img = f'<img src="{product[4]}" width="250" height="350" alt="{product[1]}">'
                    st.markdown(html_img, unsafe_allow_html=True)
                st.markdown('---')

    else:
        st.write("Nenhum produto cadastrado.")

##################################################################################
### Insere o produto no banco de dados e salva a imagem no blob Storage
##################################################################################

if st.button("Salvar"):

    if product_name and product_description and product_price and product_image is not None:
        success = insert_product(product_name, product_price, product_description, product_image)

        if success:
            st.success("Produto salvo com sucesso.")

        else:
            st.warning("Você deve preencher todos os campos e enviar uma imagem para o produto.")

##################################################################################
### Lista os produtos já cadastrados
##################################################################################

st.header('Valide os produtos já cadastrados')

if st.button('Atualizar lista de produtos'):
    list_products_screen()

##################################################################################
### Lista os produtos já cadastrados
##################################################################################    

list_products_screen()