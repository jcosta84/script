import streamlit as st
import pymysql
import pandas as pd
import time
from streamlit_option_menu import option_menu
import plotly.express as px
import numpy as np



#criar conexão com base de dados
conexao = pymysql.connect(host="localhost",
                          port=3306,
                          database="facturas",
                          user="pj",
                          password="loucoste9850053")


#criar cursor
cursor = conexao.cursor()
print("conexão realizada")


#configurar extrutura de pagina do streamlit
st.set_page_config(page_title="Projecto Facturação - EDEC",
                   page_icon=":bar_chart:",
                   layout="wide")

#criar importação de cache
def carregar_factura():
    factura = pd.read_excel(upload_file, engine="openpyxl")
    return factura

def carregar_contrato():
    contrato = pd.read_excel(upload_file, engine="openpyxl")
    return contrato

def carregar_contacto():
    contacto = pd.read_excel(upload_file, engine="openpyxl")
    return contacto



#criar um menu na lateral esquerda da pagina
with st.sidebar:
    select = option_menu(
        menu_title="Menu Principal",
        options=["Importação", "DashBoard", "Consulta e Analise Por CIL"],
        icons=["database", "bar-chart", "clipboard"],
        default_index=0,
    )

#criar opções de importação de base de dados para o aplicativo
if select == "Importação":
    st.title(f"{select}")
    #importar facturação
    upload_file = st.file_uploader("Importar Facturação", type="xlsx")
    if upload_file:
        st.markdown("---")
        factura = carregar_factura()
        factura.head()

        #inserir dados na base de dados do mysql
        #Script facturação
        inicio = time.time()
        for index, row in factura.iterrows():
            sql = "insert into facturas (Ref, Emp, UC, Prod, Dat_Emi, Dat_Fact, Doc, ID, Cliente, CIL, Estado, Tip, Tarifa, Valor_Total, Cons, Kwh, Valor_Cons)" \
                  "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            val = (row['Ref'], row['Emp'], row['UC'], row['Prod'], row['Dat_Emi'], row['Dat_Fact'], row['Doc'], row['ID'], row['Cliente'], row['CIL'],
                   row['Estado'], row['Tip'], row['Tarifa'], row['Valor_Total'], row['Cons'], row['Kwh'], row['Valor_Cons'])
            cursor.execute(sql, val)
            conexao.commit()
        final = time.time()

    #Script contratos
    upload_file = st.file_uploader("Importar Contratos", type="xlsx")
    if upload_file:
        st.markdown("---")
        contrato = carregar_contrato()
        contrato.head()
        inicio = time.time()
        for index, row in contrato.iterrows():
            sql = "insert into contratos (CIL, NOME, MORADA, LOCALIDADE)" \
                  "values (%s, %s, %s, %s)"
            val = (row['CIL'], row['NOME'], row['MORADA'], row['LOCALIDADE'])
            cursor.execute(sql, val)
            conexao.commit()
        final = time.time()

    #Script contactos
    upload_file = st.file_uploader("Importar Contactos", type="xlsx")
    if upload_file:
        st.markdown("---")
        contacto = carregar_contacto()
        contacto.head()
        incicio = time.time()
        for index, row in contacto.iterrows():
            sql = "insert into contactos (CIL, Fixo)" \
                  "values(%s, %s)"
            val = (row['CIL'], row['Fixo'])
            cursor.execute(sql, val)
            conexao.commit()
    final = time.time()

#importar da base de dados
factura = pd.read_sql('select * from facturas', conexao)
factura.head()
contrato = pd.read_sql('select * from contratos', conexao)
contrato.head()
contacto = pd.read_sql('select * from contactos', conexao)
contacto.head()
unidade = pd.read_sql('select * from unidade', conexao)
unidade.head()
produto = pd.read_sql('select * from produto', conexao)
produto.head()
tipo = pd.read_sql('select * from tipo', conexao)
tipo.head()
estado = pd.read_sql('select * from estado', conexao)
estado.head()


#alterar codigos
factuni = pd.merge(factura, unidade, on='UC', how='left')
factpro = pd.merge(factuni, produto, on='Prod', how='left')
factest = pd.merge(factpro, estado, on='Estado', how='left')
factip = pd.merge(factest, tipo, on='Tip', how='left')


#inserir informação de contratos e contactos
factcontr = pd.merge(factip, contrato, on='CIL', how='left')
factcont = pd.merge(factcontr, contacto, on='CIL', how='left')


#filtar conseito X30
tabela_geral = factcont.loc[factcont['Cons'] == 'X30']
tabela_geral.head()


#ordenar dados da tabela
tabela_geral1 = tabela_geral.loc[:,['Unidade', 'CIL', 'Cliente', 'ID', 'NOME', 'LOCALIDADE', 'MORADA', 'Tip_Cliente', 'Produto',
                                    'Doc', 'Descrição', 'Tarifa', 'Dat_Fact', 'Dat_Emi', 'Valor_Total', 'Cons', 'Kwh', 'Valor_Cons',
                                    'Fixo', 'Movel', 'Email']]




#separador do dashboard
if select == "DashBoard":

    #definir campos de pesquisa
    st.sidebar.header("Definir Procura Por:")
    un = st.sidebar.multiselect(
        "Filtrar Unidade",
        options=tabela_geral1['Unidade'].unique(),

    )

    cliente = st.sidebar.multiselect(
        "Filtrar Por Tipo Cliente",
        options=tabela_geral1['Tip_Cliente'].unique(),

    )

    prod = st.sidebar.multiselect(
        "Filtrar Produto",
        options=tabela_geral1['Produto'].unique(),

    )

    geral_selection = tabela_geral1.query(
        "`Unidade` == @un & `Tip_Cliente` == @cliente & `Produto` == @prod"
    )

    # informação na parte superior da folha
    quantidade_de_clientes = int(geral_selection["CIL"].count())
    quantidade_facturado = int(geral_selection["Kwh"].sum())
    valor_facturado = int(geral_selection["Valor_Total"].sum())

    # definir centralização dos dados na folha
    left_column, middle_column, right_column = st.columns(3)
    with left_column:
        st.subheader("Quantidade de Clientes")
        st.subheader(f"Locais {quantidade_de_clientes:,}")
    with middle_column:
        st.subheader("Quantidade Facturado")
        st.subheader(f"Kwh {quantidade_facturado:,}")
    with right_column:
        st.subheader("Valor Facturado")
        st.subheader(f"ECV {valor_facturado:,}")

    st.markdown("---")

    #criar tabela de dinamica com as informações necessaria para inserção dos graficos
    unifact = pd.pivot_table(geral_selection, index='Unidade', values='Valor_Total', aggfunc=np.sum)
    uniquant = pd.pivot_table(geral_selection, index='Unidade', values='Kwh', aggfunc=np.sum)
    factquant = pd.merge(uniquant, unifact, on='Unidade', how='left')

    st.markdown("---")

    #grafico valor facturado
    fig_val = px.bar(
        factquant,
        x=factquant.index,
        y=['Valor_Total'],
        orientation="v",
        title="<b>Grafico Valor Facturado (ECV)</b>",
        color_discrete_sequence=["#5F9EA0"],
        template="plotly_white",
    )
    fig_val.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=(dict(showgrid=False))
    )

    #grafico valor consumido
    fig_quant = px.bar(
        factquant,
        x=['Kwh'],
        y=factquant.index,
        orientation="h",
        title="<b>Grafico Consumo (Kwh)</b>",
        color_discrete_sequence=["#B22222"],
        template="plotly_white",
        )
    fig_quant.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=(dict(showgrid=False))
    )

    #definir apresentação de grafico
    left_column, right_column = st.columns(2)
    left_column.plotly_chart(fig_val, use_container_width=True)
    right_column.plotly_chart(fig_quant, use_container_width=True)

    st.markdown("---")

    # alteração de nome das colunas
    factura_geral = geral_selection.rename(
        columns={'Unidade': 'Unidade', 'CIL': 'CIL', 'CLiente': 'CLiente', 'ID': 'Cliente Conta', 'NOME': 'Nome',
                 'LOCALIDADE': 'Localidade', 'MORADA': 'Morada',
                 'Tip_Cliente': 'Tipo Cliente', 'Produto': 'Produto', 'Doc': 'Nº Documento',
                 'Descrição': 'Estado Factura',
                 'Tarifa': 'Tarifa', 'Dat_Fact': 'Data Facturação', 'Dat_Emi': 'Data Emissão',
                 'Valor_Total': ' Valor Facturado',
                 'Cons': 'Conseito', 'Kwh': 'Consumo', 'Valor_Cons': 'Valor Consumido'})

    # remover sequenciador
    factura_geral2 = factura_geral.set_index('Unidade', inplace=False)

    #criar botão para exportar daddos para ficheiro excel
    @st.cache_data
    def convert_df(df):
        #IMPORTANT: cache the conversion to prevent computation on every rerun
        return df.to_csv().encode("utf-8")

    csv = convert_df(factura_geral2)

    st.download_button(
        label="Download Facturação",
        data=csv,
        file_name="Facturação.csv",
        mime="text/csv",
    )

#separador de consulta e analise por cil
if select == "Consulta e Analise Por CIL":

    st.sidebar.header("Filtrar Por CIL:")
    cil = st.sidebar.multiselect(
        "Filtrar CIL",
        options=tabela_geral1["CIL"].unique(),
    )

    geral_selection2 = tabela_geral1.query(
        "`CIL` == @cil"
    )

    #calcular quantidade de facturas valor consumo e valor facturado
    cil_quantidade = int(geral_selection2["CIL"].count())
    val_consumido = int(geral_selection2["Kwh"].sum())
    val_facturado = int(geral_selection2["Valor_Total"].sum())

    #definir as colunas em cada informação sera apresentado
    left_column, middle_column, right_column = st.columns(3)
    with left_column:
        st.subheader("Quant Facturas")
        st.subheader(f"Quant {cil_quantidade:,}")
    with middle_column:
        st.subheader("Consumo Kwh")
        st.subheader(f"Consumo {val_consumido:,}")
    with right_column:
        st.subheader("Valor Facturado (ECV)")
        st.subheader(f"ECV {val_facturado:,}")

    st.markdown("---")


    #calcular a media e e bem como a informação a ser apresentado como obs:
    factunico = geral_selection2[0:1]
    quantfact = int(factunico["Kwh"].sum())
    valfact = int(factunico["Valor_Total"].sum())

    #definir formula para calcular media
    x = val_facturado
    y = val_facturado
    media = (x / y) if y else 0
    media = y and (x / y)

    numero = media
    numero = str(numero).replace('.', ',')

    num = numero
    formatted_num = "{:.8}".format(num)

    st.markdown("---")

    test = ("Média:")

    #definir as colunas e as informações a paresentar nas colunas na folha
    left_column, middle_column = st.columns(2)

    with left_column:
        st.subheader(f" {test:}")
    with middle_column:
        st.subheader(f"Kwh {formatted_num:}")

    #função SE:
    if quantfact > media:
        st.text("O ESPAÇO ENCONTRA-SE COM CONSUMO SUPERIOR A MEDIA")

    elif quantfact == media:
        st.text("O ESPAÇO COM CONSUMO REGULAR")

    else:
        st.text("PROGRAMAR OS DE AVERIGUAÇÃO")


    st.markdown("---")

    st.markdown("---")

    #tabela da procura realizada do cil em causa
    tabela_cil = geral_selection2.rename(
        columns={'Unidade': 'Unidade', 'CIL': 'CIL', 'CLiente': 'CLiente', 'ID': 'Cliente Conta', 'NOME': 'Nome',
                 'LOCALIDADE': 'Localidade', 'MORADA': 'Morada',
                 'Tip_Cliente': 'Tipo Cliente', 'Produto': 'Produto', 'Doc': 'Nº Documento',
                 'Descrição': 'Estado Factura',
                 'Tarifa': 'Tarifa', 'Dat_Fact': 'Data Facturação', 'Dat_Emi': 'Data Emissão',
                 'Valor_Total': ' Valor Facturado',
                 'Cons': 'Conseito', 'Kwh': 'Consumo', 'Valor_Cons': 'Valor Consumido'})

    tabela_cil2 = tabela_cil.set_index('Unidade', inplace=False)


    st.markdown("---")

    #definir tabela dinamica
    tabdicil = pd.pivot_table(geral_selection2, index='Dat_Emi', values='Valor_Total' ,aggfunc=np.sum)
    tabdikw = pd.pivot_table(geral_selection2, index='Dat_Emi', values='Valor_Total', aggfunc=np.sum)
    tbcilkw = pd.merge(tabdicil, tabdikw, on='Dat_Emi', how='left')

    #definir grafico a ser inserido
    fig_val2 = px.bar(
        tbcilkw,
        x=tbcilkw.index,
        y=['Valor_Total'],
        orientation="v",
        title="<b>Grafico Valor Facturado (ECV)</b>",
        color_discrete_sequence=["#5F9EA0"],
        template="plotly_white",
    )
    fig_val2.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=(dict(showgrid=False))
    )

    fig_quant2 = px.bar(
        tbcilkw,
        x=['Kwh'],
        y=tbcilkw.index,
        orientation="h",
        title="<b>Grafico Valor Consumido (Kwh)",
        color_discrete_sequence=["#B22222"],
        template="plotly_white"
    )
    fig_quant2.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=(dict(showgrid=False))
    )

    #definir centralização dos graficos
    left_column, right_column = st.columns(2)
    left_column.plotly_chart(fig_val2, use_container_width=True)
    right_column.plotly_chart(fig_quant2, use_container_width=True)

    st.markdown("---")

    st.dataframe(tabela_cil2)

    #criar opção de download dos dados de factura do cil
    @st.cache_data
    def convert_df(df):
        return df.to_csv().encode('utf-8')

    csv = convert_df(tabela_cil2)

    st.download_button(
        label="Download Facturação CIL",
        data=csv,
        file_name='facturação cil.csv',
        mime='text/csv',
    )


conexao.close()
cursor.close()


hide_st_style = """
                    <style>
                   
                    </style>
                    """

st.markdown(hide_st_style, unsafe_allow_html=True)
