import pickle
from pathlib import Path
import numpy as np

import pandas as pd  # pip install pandas openpyxl
import plotly.express as px  # pip install plotly-express
import streamlit as st  # pip install streamlit
import streamlit_authenticator as stauth  # pip install streamlit-authenticator
from streamlit_option_menu import option_menu
from funciones import  interactive_table
from st_aggrid import AgGrid, GridUpdateMode
import plotly.graph_objects as go

# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="Gestión de activos", page_icon=":bar_chart:")


# --- USER AUTHENTICATION ---
names = ["Gerencia", "Operacion y Mantenimiento"]
usernames = ["gerencia", "om"]

# load hashed passwords
file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
    "sales_dashboard", "abcdef", cookie_expiry_days=1)

name, authentication_status, username = authenticator.login("Ingresar", "main")

if authentication_status == False:
    st.error("Nombre de usuario o contraseña incorrecta")

if authentication_status == None:
    st.warning("Por favor, ingrese su nombre de usuario y contraseña")

if authentication_status:
    # ---- READ EXCEL ----
    st.sidebar.header(f"Bienvenido usuario: {name}")
    authenticator.logout("Cerrar sesión", "sidebar")

    menu_options = ["Transformadores","Líneas", "Celdas MT", "Gen. Diésel", "PV", "Equipos de medición"]
    menu_icons = ["lightning-charge","option","pc","hypnotize","sun-fill","speedometer"]

    menu_select = option_menu(menu_title = "Selección de activo", options = menu_options, 
                            icons = menu_icons, orientation= "horizontal")

    if menu_select == menu_options[0]:
        st.header("Análisis de flota de transformadores")

        HI_trafo = pd.read_excel("TransformerData.xlsx", sheet_name="HI")
        RI_trafo = pd.read_excel("TransformerData.xlsx", sheet_name="RI")  
        location_trafo = pd.read_excel("TransformerData.xlsx", sheet_name="Location")      

        location_trafo["Health index"] = RI_trafo["Health Index"]

        fig = px.scatter_mapbox(location_trafo, lat="Lat", lon="Lon", color="Health index",
                #   color_continuous_scale=px.colors.cyclical.IceFire, 
                  zoom=11)
        fig.update_traces(marker={'size': 12})
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        st.plotly_chart(fig)

        #RI_grid, gridOptions_RI = interactive_table(RI_trafo, cat = False)
        st.subheader("Índice de salud")
        AgGrid(HI_trafo, theme= "blue")
        st.subheader("Índice de riesgo")
        AgGrid(RI_trafo, theme= "blue")
        

        RI_trafo["HI range"] = pd.cut(RI_trafo['Health Index'], [0, 0.3, 0.7, 1], labels=['Normal', 'Intermedio', 'Crítico'])        
        HI_range = RI_trafo.groupby(['HI range']).count()
        
        fig = go.Figure(data=[go.Pie(labels=HI_range.index, values=HI_range.iloc[:,0].values)])
        fig.update_layout(title = "Cantidad de transformadores por índice de salud")
        st.plotly_chart(fig)



        st.header("Análisis de transformador individual")

        selected_trafo = st.selectbox("Seleccione el transformador", HI_trafo["No."])
              
        
        HI_trafo_scaled = HI_trafo.copy()
        for i in HI_trafo.columns:
            HI_trafo_scaled[i] = HI_trafo[i]/np.max(HI_trafo[i])
        HI_trafo_scaled = HI_trafo_scaled.drop(['No.'], axis=1)
        
        HI_trafo_scaled = HI_trafo_scaled.loc[HI_trafo["No."] == selected_trafo, :]
        HI_trafo_scaled = HI_trafo_scaled.T.reset_index()
        HI_trafo_scaled.columns = ["Indicador", "Valor"]
        
        fig = px.line_polar(HI_trafo_scaled, r='Valor', theta='Indicador', line_close=True)
        fig.update_traces(fill='toself')
        st.plotly_chart(fig)