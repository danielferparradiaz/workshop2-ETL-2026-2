import os

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

st.set_page_config(page_title='Grammy × Spotify', layout='wide')
st.title('Grammy × Spotify · Catálogo analítico')
st.caption('Fuente: vistas dimensionales PostgreSQL dw.* · Snapshot Spotify sin fecha de captura conocida')
st.info('Entradas Grammy del archivo suministrado; no se interpreta winner como clasificación verificada. Coincidencias conservadoras de título y artista.')


@st.cache_resource
def database():
    return create_engine(os.environ['MUSIC_DB_URL'], pool_pre_ping=True)


try:
    with database().connect() as conn:
        entries = pd.read_sql(text('SELECT * FROM dw.v_entries'), conn)
except SQLAlchemyError:
    st.warning('DW aún no disponible. Ejecuta la preparación de fuente y una corrida exitosa del DAG.')
    st.stop()

if entries.empty:
    st.warning('El DW no contiene entradas.')
    st.stop()
categories = st.multiselect('Categorías', sorted(entries.category.unique()), default=sorted(entries.category.unique()))
minimum, maximum = int(entries.year.min()), int(entries.year.max())
years = st.slider('Año fuente Grammy', minimum, maximum, (minimum, maximum)) if minimum < maximum else (minimum, maximum)
df = entries[entries.category.isin(categories) & entries.year.between(*years)]
matched = df[df.matched.eq(1)]
a, b, c = st.columns(3)
a.metric('AR1 · Cobertura', f'{100 * df.matched.mean():.1f}%' if len(df) else 'Sin datos')
b.metric('AR2 · Popularidad media', f'{matched.popularity.mean():.1f}' if len(matched) else 'Sin coincidencias')
c.metric('AR3 · Energía media', f'{matched.energy.mean():.3f}' if len(matched) else 'Sin coincidencias')
st.caption(f'Entradas: {len(df)} · Coincidencias: {len(matched)} · Ambiguas: {df.match_status.eq("ambiguous").sum()} · Sin coincidencia: {df.match_status.eq("unmatched").sum()}')
coverage = df.groupby(['year', 'category'], as_index=False).agg(coverage_pct=('matched', lambda x: 100*x.mean()), entries=('entry_key', 'count'))
st.plotly_chart(px.line(coverage, x='year', y='coverage_pct', color='category', markers=True, hover_data=['entries'], title='AR1 · Cobertura por año fuente'), use_container_width=True)
means = matched.groupby('category', as_index=False).agg(popularity=('popularity', 'mean'), n=('entry_key', 'count'))
st.plotly_chart(px.bar(means, x='category', y='popularity', hover_data=['n'], title='AR2 · Popularidad media por categoría'), use_container_width=True)
st.plotly_chart(px.scatter(matched, x='danceability', y='energy', color='category', hover_data=['nominee', 'artist', 'year'], title='AR3 · Energía y bailabilidad de las entradas emparejadas'), use_container_width=True)
st.dataframe(df, use_container_width=True, hide_index=True)
st.caption('Popularidad y energía son promedios por entrada Grammy, no por pista distinta. Ausencias y ambigüedades no se imputan como cero. Recarga la página para consultar el snapshot actual.')
