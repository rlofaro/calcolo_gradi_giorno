import streamlit as st
import pandas as pd
import io
import locale
import datetime

st.set_page_config(page_title="Calcolo Gradi Giorno")

# Titolo dell'applicazione
st.title("CALCOLO GRADI GIORNO")

# Caricamento del file CSV tramite interfaccia Streamlit
uploaded_file = st.file_uploader("Carica un file CSV", type=["csv"])

# Messaggio informativo se nessun file è stato caricato
if uploaded_file is None:
    st.info(
        """
        📈 **Questa applicazione calcola i Gradi Giorno caricando i dati climatici.**
        
        ***
    
       **Si può caricare:**
        - Un file CSV già pronto
        - Oppure scaricare dati meteo in formato CSV da siti specializzati disponibili online (ad esempio portali meteorologici)

        **Il file deve contenere almeno queste colonne (i nomi possono essere diversi):**
         - **DATA** (formato gg/mm/aaaa o aaaa-mm-gg)
         - **TMEDIA** (temperatura media giornaliera)
         - *(opzionali)* **TMIN** e **TMAX** (temperatura minima e massima)
        
        ***
        
        **Nota:** Usare il punto e virgola (;) come separatore di campo.  
        Il separatore decimale può essere la virgola o il punto.
     """
    )

    st.warning("Occorre caricare un file CSV per continuare...")
    st.stop()

# Prova a leggere il file CSV e gestisce eventuali errori
try:
    df1 = pd.read_csv(uploaded_file, sep=";", decimal=",")
except Exception as e:
    st.error(f"Errore di lettura del file: {e}")
    st.stop()

# ---- Mappatura colonne ----
st.subheader("Mappatura colonne")
colonne_csv = list(df1.columns)
col_mapping = {}  # Dizionario per memorizzare la mappatura delle colonne

# Ciclo sulle colonne richieste per la mappatura interattiva
for rich in ["DATA", "TMEDIA", "TMIN", "TMAX"]:
    # Opzioni disponibili che non sono già state utilizzate
    opzioni = [c for c in colonne_csv if c not in col_mapping.values()]
    # Prova a indovinare la colonna giusta (case insensitive)
    predef = next((c for c in opzioni if rich in c.upper()), opzioni[0] if opzioni else None)
    if len(opzioni) > 0:
        # Seleziona la colonna da assegnare (obbligatorio per DATA e TMEDIA, facoltativo per TMIN/TMAX)
        col_sel = st.selectbox(
            f"Colonna per '{rich}'",
            ["-- Nessuna --"] + opzioni if rich in ["TMIN", "TMAX"] else opzioni,
            index=(opzioni.index(predef) + 1) if rich in ["TMIN", "TMAX"] else opzioni.index(predef)
        )
        if col_sel != "-- Nessuna --":
            col_mapping[rich] = col_sel
    else:
        # Errore se manca una colonna obbligatoria
        if rich in ["DATA", "TMEDIA"]:
            st.error(f"Colonna obbligatoria '{rich}' non trovata! Correggi il file.")
            st.stop()

# Verifica che siano state mappate DATA e TMEDIA
if "DATA" not in col_mapping or "TMEDIA" not in col_mapping:
    st.error("Devi selezionare obbligatoriamente una colonna DATA e una TMEDIA.")
    st.stop()

# Rinomina le colonne assegnando i nomi standard
rename_dict = {v: k for k, v in col_mapping.items()}
df1 = df1.rename(columns=rename_dict)

# ---- Conversione dati ----
# Conversione colonna DATA in formato datetime (solo data)
df1["DATA"] = pd.to_datetime(df1["DATA"], errors="coerce", dayfirst=True).dt.date

# Conversione delle colonne numeriche in float (gestisce anche errori di formato)
for col in ["TMEDIA", "TMIN", "TMAX"]:
    if col in df1.columns:
        df1[col] = pd.to_numeric(df1[col], errors="coerce")

# Rimozione delle righe senza DATA o TMEDIA validi, con messaggio di avviso
n_data_nan = df1["DATA"].isna().sum()
n_tmedia_nan = df1["TMEDIA"].isna().sum()
if n_data_nan or n_tmedia_nan:
    st.warning(f"{n_data_nan} righe con DATA non valida e {n_tmedia_nan} con TMEDIA non valida saranno escluse.")
df1 = df1.dropna(subset=["DATA", "TMEDIA"])
if df1.empty:
    st.error("Nessun dato valido rimasto dopo controlli su DATA e TMEDIA.")
    st.stop()

# ---- Filtro periodo in base alla data ----
st.header("Filtra per periodo")


data_min = df1["DATA"].min()
data_max = df1["DATA"].max()

# Selettori per la data di inizio e fine
col_data1, col_data2 = st.columns(2)

with col_data1:
    data_inizio = st.date_input("Data inizio", data_min, min_value=data_min, max_value=data_max, key="inizio")
with col_data2:
    data_fine = st.date_input("Data fine", data_max, min_value=data_min, max_value=data_max, key="fine")

if data_inizio > data_fine:
    st.error("La data di inizio è successiva a quella di fine!")
    st.stop()

# Applica la maschera di filtro
maschera = (df1["DATA"] >= data_inizio) & (df1["DATA"] <= data_fine)
df_filtrato = df1.loc[maschera].copy()

if df_filtrato.empty:
    st.error("Nessun dato nel periodo selezionato.")
    st.stop()

# ---- Calcolo e visualizzazione Gradi Giorno ----
T_rif = 20  # Temperatura di riferimento

# Calcola i Gradi Giorno (GG) come massimo tra 0 e (T_rif - TMEDIA)
df_filtrato['GG'] = (T_rif - df_filtrato['TMEDIA']).clip(lower=0)

# Selezione delle colonne da mostrare nella tabella
colonne_base = [c for c in ["DATA", "TMEDIA", "TMIN", "TMAX", "GG"] if c in df_filtrato.columns]
mostra_tutte = st.toggle("Mostra tutte le colonne", value=False)
colonne_da_mostrare = df_filtrato.columns if mostra_tutte else colonne_base

st.header("Tabella Gradi Giorno (GG)")
st.dataframe(df_filtrato[list(colonne_da_mostrare)])

# Calcolo della somma totale dei Gradi Giorno
somma_GG = df_filtrato['GG'].sum()
try:
    locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'it_IT')

# Formattazione delle date nel formato italiano (gg/mm/aaaa)
st.subheader(f"Gradi Giorno dal {data_inizio.strftime('%d/%m/%Y')} al {data_fine.strftime('%d/%m/%Y')}: {somma_GG:.1f}")

# ---- Visualizzazione grafico ----
st.header("Grafico Gradi Giorno")
st.line_chart(df_filtrato.set_index('DATA')[["GG"]])

# ---- Esportazione dati in Excel ----
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    df_filtrato.to_excel(writer, index=False, sheet_name='Gradi Giorno')
buffer.seek(0)
st.download_button(
    label="📥 Scarica i dati filtrati in Excel",
    data=buffer,
    file_name="GG_filtrati.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
