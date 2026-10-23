# =============================================================================
# ÁNCORA SIMAP v13.0 - Sistema Inteligente de Monitoreo y Análisis Poblacional
# Aplicación Modular en Streamlit con SQLite, Gemini AI, Triaje INS y PDF
# =============================================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import re
import json
import os
import requests
from datetime import datetime, date
from fpdf import FPDF
from sklearn.cluster import KMeans

# ------------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS MODERNOS (UI/UX PREMIUM)
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="ÁNCORA SIMAP - Prevención Conducta Suicida",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        font-size: 2.1rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 2px;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 18px;
    }
    .card-metric {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        padding: 16px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0284C7;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #64748B;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-alta {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 5px 12px;
        border-radius: 15px;
        font-weight: 700;
        display: inline-block;
        font-size: 0.85rem;
    }
    .badge-media {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 5px 12px;
        border-radius: 15px;
        font-weight: 700;
        display: inline-block;
        font-size: 0.85rem;
    }
    .badge-baja {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 5px 12px;
        border-radius: 15px;
        font-weight: 700;
        display: inline-block;
        font-size: 0.85rem;
    }
    .chat-bubble-user {
        background-color: #0284C7;
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 2px 18px;
        margin-bottom: 10px;
        max-width: 85%;
        margin-left: auto;
        font-size: 0.92rem;
    }
    .chat-bubble-assistant {
        background-color: #F1F5F9;
        color: #0F172A;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 2px;
        margin-bottom: 10px;
        max-width: 88%;
        border: 1px solid #E2E8F0;
        font-size: 0.92rem;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)
# ------------------------------------------------------------------------------
# 2. ESTRUCTURA DE GEODATOS: CIUDADES -> LOCALIDADES/TERRITORIOS -> BARRIOS
# ------------------------------------------------------------------------------
CIDADES_GEODATA = {
    "Bogotá D.C.": {
        "Usaquén": ["Santa Bárbara", "Contador", "Usaquén Centro", "Toberín", "Verbenal", "Cedritos", "San Patricio", "Bella Suiza", "Lisboa"],
        "Chapinero": ["El Chicó", "Rosales", "Chapinero Alto", "Marly", "Antiguo Country", "Pardo Rubio", "Emaús", "El Refugio"],
        "Santa Fe": ["La Macarena", "Las Cruces", "Lourdes", "Las Nieves", "Germania", "San Bernardo", "Sagrado Corazón"],
        "San Cristóbal": ["La Victoria", "20 de Julio", "San Blas", "Altamira", "Córdoba", "Vitelma", "Lola Pardo"],
        "Usme": ["Yomasa", "La Flora", "Alfonso López", "Danubio", "Santa Librada", "El Uval", "Marichuela"],
        "Tunjuelito": ["Tunjuelito Centro", "Venecia", "San Benito", "Fátima", "Abraham Lincoln"],
        "Bosa": ["Bosa Centro", "El Recreo", "San Bernardino", "Campo Verde", "Bosa Nova", "Porvenir", "Chicalá", "La Estación"],
        "Kennedy": ["Castilla", "Patio Bonito", "El Tintal", "Mandalay", "Carvajal", "Marsella", "Roma", "Banderas", "Timiza"],
        "Fontibón": ["Fontibón Centro", "Modelia", "Hayuelos", "Capellanía", "Villemar", "Zona Franca", "San Pablo"],
        "Engativá": ["Quirigua", "Bachué", "Las Ferias", "La Estrada", "Garcés Navas", "Álamos", "Normandía", "Minuto de Dios"],
        "Suba": ["Cedritos Suba", "Niza", "La Campiña", "El Prado Suba", "San José de Bavaria", "Mirandela", "Suba Rincón", "Tibabuyes", "Lombardía"],
        "Barrios Unidos": ["12 de Octubre", "Siete de Agosto", "Polo Club", "Entre Ríos", "San Fernando"],
        "Teusaquillo": ["Teusaquillo Centro", "Galerías", "La Soledad", "Quinta Paredes", "Pablo VI", "Salitre Greco"],
        "Los Mártires": ["La Estanzuela", "Santa Isabel", "Sabanagrande", "El Listón", "Voto Nacional"],
        "Antonio Nariño": ["Restrepo", "Ciudad Berna", "Santander", "Sevilla", "Policarpa"],
        "Puente Aranda": ["Milenta", "Trinidad Galán", "Ciudad Montes", "Cazuca", "San Eusebio", "Muzú"],
        "La Candelaria": ["Centro Histórico", "Belén", "Egipto", "La Concordia", "Candelaria"],
        "Rafael Uribe Uribe": ["Olaya", "Quiroga", "Diana Turbay", "Marruecos", "San José"],
        "Ciudad Bolívar": ["Sierra Morena", "Arborizadora Alta", "Lucero Alto", "El Mochuelo", "Santo Domingo", "Potosí", "Candelaria La Nueva"],
        "Sumapaz": ["San Juan", "Nazareth", "Betania", "La Unión"]
    },
    "Medellín": {
        "Comuna 1 (Popular)": ["Popular", "Santo Domingo Savio", "Granizal", "Moscú", "Aldea Pablo VI"],
        "Comuna 2 (Santa Cruz)": ["Santa Cruz", "La Frontera", "Andalucía", "Villa del Socorro"],
        "Comuna 3 (Manrique)": ["Manrique Central", "El Raizal", "Las Granjas", "San José La Cima", "Versalles"],
        "Comuna 4 (Aranjuez)": ["Aranjuez Centro", "Sevilla", "San Isidro", "La Cruz", "Palermo", "Bermejal"],
        "Comuna 5 (Castilla)": ["Castilla", "Pedregal", "Tejelo", "Boyacá", "Las Brisas", "Florencia"],
        "Comuna 6 (Doce de Octubre)": ["Doce de Octubre", "Picacho", "Progreso", "El Triunfo", "Mirador del Doce"],
        "Comuna 7 (Robledo)": ["Robledo", "Pajarito", "Aures", "El Diamante", "Villa Flora", "Paredes"],
        "Comuna 8 (Villa Hermosa)": ["Villa Hermosa", "La Sierra", "Enciso", "San Antonio", "Las Estancias"],
        "Comuna 9 (Buenos Aires)": ["Buenos Aires", "Miraflores", "Asomadera", "El Salvador", "Loreto"],
        "Comuna 10 (La Candelaria)": ["Centro", "El Chagualo", "San Benito", "San Diego", "Boston", "Los Ángeles"],
        "Comuna 11 (Laureles - Estadio)": ["Laureles", "Estadio", "Florida Nueva", "San Joaquín", "Lorena", "Bolivariana"],
        "Comuna 12 (La América)": ["La América", "Santa Mónica", "Ferrini", "Calasanz", "Los Pinos"],
        "Comuna 13 (San Javier)": ["El Salado", "20 de Julio", "San Michel", "Nuevos Conquistadores", "Las Independencias", "Belencito"],
        "Comuna 14 (El Poblado)": ["Castropol", "Manila", "Los Balsos", "San Lucas", "Patio Bonito", "Alejandría", "Lalinde"],
        "Comuna 15 (Guayabal)": ["Guayabal", "Cristo Rey", "Campo Amor", "La Colina", "Santa Fe"],
        "Comuna 16 (Belén)": ["Belén Rincón", "Belén Rosales", "La Nubia", "San Bernardo", "Fátima", "Las Playas"]
    },
    "Cali": {
        "Comuna 1 (Oeste)": ["Terrón Colorado", "Vista Hermosa", "Patio Bonito", "Las Palmas"],
        "Comuna 2 (Norte)": ["Granada", "Versalles", "Chipichape", "Menga", "Santa Rita", "La Flora", "Vipasa"],
        "Comuna 3 (Centro)": ["San Antonio", "El Peñón", "San Cayetano", "La Merced", "San Pedro"],
        "Comuna 4 (Nordeste)": ["Porvenir", "Salomia", "Manzanares", "Jorge Isaacs", "La Esmeralda"],
        "Comuna 5 (Nororiente)": ["Chiminangos", "Metropolitano", "Sena", "Los Andes"],
        "Comuna 6 (Nororiente)": ["Petecuy", "La Rivera", "Los Alcázares", "San Luis"],
        "Comuna 7 (Oriente)": ["Alfonso López", "Puerto Mallarino", "7 de Agosto"],
        "Comuna 8 (Suroriente)": ["Las Acacias", "Prados del Norte", "Saavedra Galindo", "La Base"],
        "Comuna 9 (Centro-Sur)": ["Bretaña", "Junín", "Guabal", "Champagnat", "Los Cámbulos"],
        "Comuna 10 (Suroriente)": ["El Guabal", "San Judas", "Pasoancho", "Santa Elena"],
        "Comuna 11 (Suroriente)": ["San Cristóbal", "La Esperanza", "20 de Julio", "Primavera"],
        "Comuna 12 (Oriente)": ["Villacolombia", "El Asturias", "El Trébol", "La Nueva Base"],
        "Comuna 13 (Aguablanca)": ["El Poblado I", "El Poblado II", "Charco Azul", "El Vergel", "Marroquín"],
        "Comuna 14 (Aguablanca)": ["Promociones Popular", "Manuela Beltrán", "Alirio Mora", "Las Orquídeas"],
        "Comuna 15 (Aguablanca)": ["Vallado", "El Retiro", "Comuneros I", "Mojica"],
        "Comuna 16 (Oriente)": ["Mariano Ramos", "La Unión", "República de Israel"],
        "Comuna 17 (Sur)": ["Ciudad Jardín", "El Ingenio", "Valle del Lili", "Limonar", "Pance", "Bochica"],
        "Comuna 18 (Suroeste)": ["Meléndez", "Lourdes", "Buenos Aires", "Horizontes"],
        "Comuna 19 (Suroeste)": ["San Fernando", "Tequendama", "Miraflores", "Lido", "El Refugio"],
        "Comuna 20 (Siloé)": ["Siloé", "Lleras Camargo", "Belén", "Tierra Blanca"],
        "Comuna 21 (Desepaz)": ["Desepaz", "Compartir", "Calimio Desepaz", "Talanga"],
        "Comuna 22 (Sur Extremo)": ["Ciudad Campestre", "Pance Sur", "Universidades"]
    },
    "Barranquilla": {
        "Riomar": ["Villa Santos", "Miramar", "El Golf", "La Castellana", "Sabanagrande", "Andalucía", "Altamira"],
        "Norte-Centro Histórico": ["El Prado", "Alto Prado", "Bellavista", "Boston", "Centro", "Rosales", "América"],
        "Sur Occidente": ["El Bosque", "La Manga", "San Felipe", "Olaya", "La Esmeralda", "Evaristo Sourdís"],
        "Sur Oriente": ["Las Nieves", "Simón Bolívar", "La Luz", "Rebolo", "Chinita", "La Victoria"],
        "Metropolitana": ["San Luis", "Santa María", "Siete de Abril", "Cevillar", "Cordialidad"]
    },
    "Bucaramanga": {
        "Comuna 1 (Norte)": ["Kennedy", "Café Madrid", "Regaderos", "San Cristóbal", "Minuto de Dios"],
        "Comuna 2 (Nororiental)": ["Los Ángeles", "Albania", "La Independencia", "Buenos Aires"],
        "Comuna 3 (San Francisco)": ["San Francisco", "Alarcón", "Comuneros", "Universidad"],
        "Comuna 4 (Occidental)": ["Chala", "Gaitán", "Campo Hermoso", "La Joya"],
        "Comuna 5 (García Rovira)": ["Quinta Estrella", "La Concordia", "Alfonso López", "San Gerardo"],
        "Comuna 6 (La Concordia)": ["La Concordia", "La Victoria", "García Rovira"],
        "Comuna 7 (San Mateo)": ["Estoraques", "Mutis", "Balconcitos", "Manzanares"],
        "Comuna 8 (Suroccidental)": ["Real de Minas", "Bucarica", "San Martín"],
        "Comuna 9 (La Pedregosa)": ["La Pedregosa", "Diamante I", "Diamante II"],
        "Comuna 10 (Provenza)": ["Provenza", "Fontana", "El Cristal", "Asturias"],
        "Comuna 11 (Sur)": ["Rincón de Girón", "Danzaderes", "Antiguo Campestre"],
        "Comuna 12 (Cabecera del Llano)": ["Cabecera del Llano", "Sotomayor", "San Pío", "Altos de Cabecera"],
        "Comuna 13 (Oriental)": ["El Álvarez", "Los Pinos", "Terrazas", "La Floresta"],
        "Comuna 14 (Morrorrico)": ["Morrorrico", "Buenos Aires", "El Diviso"],
        "Comuna 15 (Centro)": ["Centro", "García Rovira Centro", "San Mateo Centro"],
        "Comuna 16 (Lagos del Cacique)": ["Lagos del Cacique", "El Tejar", "San Fernando"],
        "Comuna 17 (Mutis)": ["Mutis", "Monterrey", "Prados del Mutis"]
    },
    "Cartagena": {
        "Localidad 1 (Histórica y del Caribe Norte)": ["Centro Histórico", "San Diego", "Getsemaní", "Bocagrande", "Castillogrande", "Laguito", "Crespo", "Marbella", "Manga"],
        "Localidad 2 (De la Virgen y Turística)": ["Olaya Herrera", "El Pozón", "La María", "Fredonia", "Via Perimetral", "Chiquinquirá"],
        "Localidad 3 (Industrial de la Bahía)": ["Bosque", "El Recreo", "Crisanto Luque", "Albornoz", "Arroz Barato", "Ceballos", "Consolata"]
    },
    "Cúcuta": {
        "Comuna 1 (Centro)": ["Centro", "La Playa", "Latino", "El Callejón"],
        "Comuna 2 (Norte)": ["Pescadero", "Sevilla", "Ceiba", "Blanco"],
        "Comuna 3 (Oriente)": ["La Libertad", "San Mateo", "Bellavista"],
        "Comuna 4 (Occidente)": ["San Martín", "Cundinamarca", "San Rafael"],
        "Comuna 5 (Noroeste)": ["Guaimaral", "Prados del Norte", "Niza"],
        "Comuna 6 (Norte)": ["Aeropuerto", "Toledo Plata", "La Ínsula"],
        "Comuna 7 (Noroccidente)": ["Comuneros", "Atalaya", "Claret"],
        "Comuna 8 (Suroriente)": ["Antonia Santos", "Belén", "Rincón Bolívar"],
        "Comuna 9 (Sur)": ["San Luis", "Torcoroma", "Santa Clara"],
        "Comuna 10 (Suroccidente)": ["Cementerio", "Cuberos Niño", "Santo Domingo"]
    },
    "Pereira": {
        "Comuna Centro": ["Centro", "El Lago", "Victoria", "Invico"],
        "Comuna Boston": ["Boston", "Las Américas", "Providencia"],
        "Comuna Cuba": ["Cuba Centro", "San Fernando", "La Isla", "Perla del Otún"],
        "Comuna Del Café": ["Parque Industrial", "Marseille", "Matsuura"],
        "Comuna Universidad": ["La Julita", "Álamos", "Alfonso López"]
    },
    "Manizales": {
        "Comuna Atardeceres": ["Chipre", "La Francia", "Sacatín", "Bellavista"],
        "Comuna Palogrande": ["Palogrande", "La Camelia", "Mulató", "Cable"],
        "Comuna Universitaria": ["La Enea", "Malhabar", "Fatima", "Pio XII"],
        "Comuna Ciudadela del Norte": ["Bosques del Norte", "San Sebastián", "Sinaí"],
        "Comuna La Fuente": ["La Source", "Arrayanes", "Cervantes"]
    },
    "Santa Marta": {
        "Localidad 1 (Cultural Tayrona - San Pedro Alejandrino)": ["Mamatoco", "Bahiandita", "Bonnivento", "San Pedro Alejandrino"],
        "Localidad 2 (Histórica - Rodrigo de Bastidas)": ["Centro Histórico", "Pescaito", "Bredun", "Taminaca"],
        "Localidad 3 (Turística - Perla del Caribe)": ["El Rodadero", "Gaira", "Bello Horizonte", "Pozos Colorados"]
    },
    "Villavicencio": {
        "Comuna 1": ["Barzal", "Caudal", "La Grama", "Virrey"],
        "Comuna 2": ["Bari", "Siete de Agosto", "Buena Vista"],
        "Comuna 3": ["Porvenir", "San Isidro", "Santa Inés"],
        "Comuna 4": ["Ceballos", "Popular", "La Gloria"],
        "Comuna 5": ["Estela", "San Antonio", "Montecarlo"]
    },
    "Pasto": {
        "Comuna 1": ["Centro", "San Juan de Dios", "Santiago"],
        "Comuna 2": ["Las Cuadras", "Pandiaco", "Torobajo"],
        "Comuna 3": ["Fatima", "Tequendama", "Marruecos"],
        "Comuna 4": ["La Carolina", "Las Lajas", "Prados del Norte"],
        "Comuna 5": ["Tamaguate", "Mijitayo", "San Vicente"]
    }
}
# ------------------------------------------------------------------------------
# 3. BASE DE DATOS SQLITE Y CONEXIÓN
# ------------------------------------------------------------------------------
DB_PATH = "ancora_simap_v6.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            doc_id TEXT,
            email TEXT,
            phone TEXT,
            prof_id TEXT,
            role TEXT NOT NULL,
            status TEXT DEFAULT 'Activo'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consecutivo TEXT UNIQUE NOT NULL,
            fecha_registro TEXT NOT NULL,
            doc_paciente TEXT NOT NULL,
            nombre_paciente TEXT NOT NULL,
            ciudad TEXT NOT NULL,
            territorio TEXT NOT NULL,
            barrio TEXT NOT NULL,
            edad INTEGER NOT NULL,
            sexo TEXT NOT NULL,
            ciclo_vital TEXT NOT NULL,
            clasificacion_conducta TEXT NOT NULL,
            factor_asociado TEXT NOT NULL,
            conductas_previas INTEGER NOT NULL,
            probabilidad_riesgo REAL NOT NULL,
            prioridad_triaje TEXT NOT NULL,
            sugerencia_manejo TEXT NOT NULL,
            registrado_por TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitudes_edicion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER NOT NULL,
            consecutivo TEXT NOT NULL,
            solicitado_por TEXT NOT NULL,
            fecha_solicitud TEXT NOT NULL,
            motivo TEXT NOT NULL,
            datos_nuevos_json TEXT NOT NULL,
            estado TEXT DEFAULT 'Pendiente'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS solicitudes_password (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            motivo TEXT NOT NULL,
            fecha_solicitud TEXT NOT NULL,
            estado TEXT DEFAULT 'Pendiente'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_organizacional (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remitente TEXT NOT NULL,
            destinatario TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            fecha_hora TEXT NOT NULL,
            leido INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS modulos_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            modulo TEXT NOT NULL,
            activo INTEGER NOT NULL,
            UNIQUE(username, modulo)
        )
    """)
    
    default_users = [
        ("admin", "Admin123!", "Dra. Elena Restrepo", "1018234567", "elena.restrepo@ancora.gov.co", "3104567890", "RM-99482", "Admin / Gerente", "Activo"),
        ("soporte", "Soporte123!", "Carlos Mendoza", "80123456", "carlos.mendoza@ancora.gov.co", "3159876543", "ENG-1029", "Soporte Técnico", "Activo"),
        ("medico", "Medico123!", "Dr. Alejandro Gómez", "1020456789", "alejandro.gomez@ancora.gov.co", "3001234567", "MP-44102", "Psicólogo / Médico Evaluador", "Activo")
    ]
    
    for user in default_users:
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (user[0],))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO usuarios (username, password, name, doc_id, email, phone, prof_id, role, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, user)

    modulos_def = {
        "admin": ["📝 Captura Manual & Triaje IA", "📊 Dashboard de Visualización", "💬 ChatBot Áncora Simap", "💬 Chat Organizacional (Teams)", "👥 Gestión de Usuarios", "📩 Solicitudes de Edición"],
        "soporte": ["📊 Dashboard de Visualización", "💬 ChatBot Áncora Simap", "💬 Chat Organizacional (Teams)", "👥 Gestión de Usuarios", "📩 Solicitudes de Edición", "⚙️ Gestión de Módulos por Usuario", "🤖 Motor ML de Agrupamiento"],
        "medico": ["📝 Captura Manual & Triaje IA", "📊 Dashboard de Visualización", "💬 ChatBot Áncora Simap", "💬 Chat Organizacional (Teams)"]
    }

    todos_los_modulos = [
        "📝 Captura Manual & Triaje IA",
        "📊 Dashboard de Visualización",
        "💬 ChatBot Áncora Simap",
        "💬 Chat Organizacional (Teams)",
        "👥 Gestión de Usuarios",
        "📩 Solicitudes de Edición",
        "⚙️ Gestión de Módulos por Usuario",
        "🤖 Motor ML de Agrupamiento"
    ]

    for username, mod_permitidos in modulos_def.items():
        for mod in todos_los_modulos:
            activo = 1 if mod in mod_permitidos else 0
            cursor.execute("INSERT OR REPLACE INTO modulos_usuario (username, modulo, activo) VALUES (?, ?, ?)", (username, mod, activo))

    # Limpieza de nombres de módulos legados para evitar violación de restricción UNIQUE
    cursor.execute("DELETE FROM modulos_usuario WHERE (modulo LIKE '%Chatbot%' OR modulo LIKE '%ChatBot%') AND modulo != '💬 ChatBot Áncora Simap'")
    conn.commit()
    conn.close()

init_db()

# ------------------------------------------------------------------------------
# 4. FUNCIONES DE VALIDACIÓN DE SEGURIDAD Y HELPERS DE DB
# ------------------------------------------------------------------------------
def validar_password(password):
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r"[A-Z]", password):
        return False, "Debe contener al menos una letra mayúscula."
    if not re.search(r"[a-z]", password):
        return False, "Debe contener al menos una letra minúscula."
    if not re.search(r"[0-9]", password):
        return False, "Debe contener al menos un número."
    if not re.search(r"[@#$%^&*!_+\-=]", password):
        return False, "Debe contener al menos un carácter especial (@#$%^&*!_+-=)."
    return True, "Contraseña válida."


def get_pending_counts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM solicitudes_edicion WHERE estado='Pendiente'")
    n_edit = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM solicitudes_password WHERE estado='Pendiente'")
    n_pwd = cursor.fetchone()[0]
    
    n_chat = 0
    if "username" in st.session_state and st.session_state.username:
        cursor.execute("SELECT COUNT(*) FROM chat_organizacional WHERE destinatario=? AND leido=0", (st.session_state.username,))
        n_chat = cursor.fetchone()[0]
        
    conn.close()
    return n_edit, n_pwd, n_chat

def get_next_consecutivo():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM pacientes")
    max_id = cursor.fetchone()[0]
    conn.close()
    next_id = 1 if max_id is None else max_id + 1
    return f"PAC-2026-{next_id:04d}"

def get_modulos_activos_usuario(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT modulo FROM modulos_usuario WHERE username = ? AND activo = 1", (username,))
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows]

# ------------------------------------------------------------------------------
# 5. MOTOR DE TRIAJE E IA PREDICTIVA (CÓDIGO 356 INS)
# ------------------------------------------------------------------------------
def calcular_triaje_ia(edad, sexo, ciclo_vital, conducta, factor, territorio, barrio, conductas_previas):
    score = 15
    if conducta == "Intento de suicidio":
        score += 42
    elif conducta == "Ideación suicida":
        score += 26
    else:
        score += 12

    if conductas_previas:
        score += 20

    if factor == "Violencia física / psicológica":
        score += 22
    elif factor == "Conflictos de pareja / familiares":
        score += 18
    elif factor == "Aislamiento / Trastorno de ánimo":
        score += 16
    elif factor == "Problemas económicos / desempleo":
        score += 12

    if ciclo_vital in ["Juventud (12-28)", "Infancia (0-11)"]:
        score += 12
    elif ciclo_vital == "Persona Mayor (60+)":
        score += 10

    probabilidad = min(99.0, max(10.0, float(score)))

    if probabilidad >= 70:
        prioridad = "Alta (Inmediata / < 24 hrs)"
        color = "#DC2626"
        badge_class = "badge-alta"
        manejo = "🔴 ACCIÓN INMEDIATA (Código 356 INS):\n• Remisión urgente a urgencias de salud mental o centro de III nivel.\n• Retiro inmediato de medios nocivos y custodia continua 24 horas por familiar responsable.\n• Diligenciamiento de la ficha de notificación obligatoria SIVIGILA.\n• Activación de la Línea 106 / Equipo de Respuesta Rápida Territorial."
    elif probabilidad >= 45:
        prioridad = "Media (Prioritaria / < 72 hrs)"
        color = "#D97706"
        badge_class = "badge-media"
        manejo = "🟡 ATENCIÓN PRIORITARIA:\n• Asignación de cita por Psicología clínica en un plazo menor a 72 horas.\n• Firma del acuerdo de compromiso y acompañamiento familiar estructurado.\n• Inicio de psicoterapia cognitivo-conductual centrada en manejo de crisis.\n• Control telefónico de seguimiento a las 24 y 48 horas post-registro."
    else:
        prioridad = "Baja (Seguimiento / < 7 días)"
        color = "#16A34A"
        badge_class = "badge-baja"
        manejo = "🟢 ATENCIÓN AMBULATORIA:\n• Orientación psicológica ambulatoria en centro de atención primaria.\n• Vinculación a talleres de resiliencia y salud mental territorial.\n• Monitoreo y seguimiento ambulatorio periódico."

    return probabilidad, prioridad, color, badge_class, manejo


def limpiar_texto_pdf(texto):
    if not texto:
        return ""
    reemplazos = {
        '🔴': '[ALTA]', '🟡': '[MEDIA]', '🟢': '[BAJA]',
        '🚀': '', '⚓': '', '👥': '', '📝': '', '📊': '', '💬': '', '🤖': '',
        '⚙️': '', '🔑': '', '📩': '', '✏️': '', '➕': '', '📋': '', '🛠️': '',
        '•': '-', '’': "'", '“': '"', '”': '"', '–': '-', '—': '-'
    }
    for k, v in reemplazos.items():
        texto = str(texto).replace(k, v)
    return texto.encode('latin-1', 'replace').decode('latin-1')

class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(30, 58, 138)
        self.cell(0, 8, 'ANCORA SIMAP - SISTEMA ANALITICO POBLACIONAL', 0, 1, 'C')
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, 'Reporte Epidemiologico y Ficha de Triaje Predictivo de Salud Publica', 0, 1, 'C')
        self.line(10, 25, 200, 25)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Pagina {self.page_no()} - Documento Confidencial de Salud Publica', 0, 0, 'C')


def generar_pdf_paciente(paciente_row):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    
    pdf.cell(0, 8, limpiar_texto_pdf(f"FICHA TÉCNICA DE TRIAJE: {paciente_row['consecutivo']}"), 0, 1, 'L')
    pdf.ln(2)
    
    pdf.set_font('Helvetica', '', 10)
    data_gen = [
        ('Fecha de Registro:', str(paciente_row['fecha_registro'])),
        ('Documento Identificación:', str(paciente_row['doc_paciente'])),
        ('Nombre del Paciente:', str(paciente_row['nombre_paciente'])),
        ('Ciudad / Ubicación:', limpiar_texto_pdf(f"{paciente_row['ciudad']} - {paciente_row['territorio']} ({paciente_row['barrio']})")),
        ('Edad / Sexo / Ciclo:', limpiar_texto_pdf(f"{paciente_row['edad']} años | {paciente_row['sexo']} | {paciente_row['ciclo_vital']}")),
        ('Clasificación Conducta:', limpiar_texto_pdf(str(paciente_row['clasificacion_conducta']))),
        ('Factor Desencadenante:', limpiar_texto_pdf(str(paciente_row['factor_asociado']))),
        ('Evaluador Responsable:', limpiar_texto_pdf(str(paciente_row['registrado_por'])))
    ]
    
    for label, val in data_gen:
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(55, 6, label, 0, 0)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 6, val, 0, 1)
        
    pdf.ln(4)
    pdf.set_fill_color(241, 245, 249)
    pdf.rect(10, pdf.get_y(), 190, 25, 'F')
    pdf.set_xy(12, pdf.get_y() + 2)
    
    pdf.set_font('Helvetica', 'B', 11)
    if paciente_row['probabilidad_riesgo'] >= 70:
        pdf.set_text_color(220, 38, 38)
    else:
        pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 6, limpiar_texto_pdf(f"RESULTADO DE TRIAJE IA: {paciente_row['prioridad_triaje']}"), 0, 1)
    
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 6, f"PROBABILIDAD ESTIMADA DE RIESGO: {paciente_row['probabilidad_riesgo']:.1f}%", 0, 1)
    
    pdf.ln(8)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 6, 'RUTA DE MANEJO INSTITUCIONAL RECOMENDADA (INS CÓDIGO 356):', 0, 1)
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, limpiar_texto_pdf(paciente_row['sugerencia_manejo']))
    
    pdf.ln(15)
    pdf.line(20, pdf.get_y(), 90, pdf.get_y())
    pdf.line(110, pdf.get_y(), 180, pdf.get_y())
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_xy(20, pdf.get_y() + 2)
    pdf.cell(70, 4, 'Firma Profesional Evaluador', 0, 0, 'C')
    pdf.set_xy(110, pdf.get_y())
    pdf.cell(70, 4, 'Firma / Sello Institución de Salud', 0, 1, 'C')
    
    return bytes(pdf.output())

# ------------------------------------------------------------------------------
# 7. CHATBOT CON API REAL DE GEMINI E HISTORIAL
# ------------------------------------------------------------------------------

def generar_pdf_historico(df_filtered, ciudad_filtro):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(15, 23, 42)
    
    pdf.cell(0, 8, limpiar_texto_pdf(f"REPORTE HISTÓRICO EPIDEMIOLÓGICO - CIUDAD: {ciudad_filtro.upper()}"), 0, 1, 'L')
    pdf.ln(2)
    
    total = len(df_filtered)
    casos_alta = len(df_filtered[df_filtered["prioridad_triaje"].str.contains("Alta", na=False)]) if total > 0 else 0
    pct_alta = (casos_alta / total * 100) if total > 0 else 0
    edad_prom = df_filtered["edad"].mean() if total > 0 else 0
    
    pdf.set_font('Helvetica', '', 10)
    metrics = [
        ("Total de Casos Registrados:", str(total)),
        ("Porcentaje en Prioridad Alta:", f"{pct_alta:.1f}% ({casos_alta} casos)"),
        ("Edad Promedio de Pacientes:", f"{edad_prom:.1f} años"),
        ("Fecha de Emisión del Reporte:", str(date.today()))
    ]
    
    for label, val in metrics:
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(55, 6, limpiar_texto_pdf(label), 0, 0)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 6, limpiar_texto_pdf(val), 0, 1)
        
    pdf.ln(4)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, limpiar_texto_pdf("CONSOLIDADO DE REGISTROS HISTÓRICOS:"), 0, 1)
    
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_fill_color(226, 232, 240)
    pdf.cell(25, 6, "Consecutivo", 1, 0, 'C', True)
    pdf.cell(22, 6, "Fecha", 1, 0, 'C', True)
    pdf.cell(25, 6, "Documento", 1, 0, 'C', True)
    pdf.cell(45, 6, "Nombre", 1, 0, 'C', True)
    pdf.cell(28, 6, "Territorio", 1, 0, 'C', True)
    pdf.cell(45, 6, "Prioridad Triaje", 1, 1, 'C', True)
    
    pdf.set_font('Helvetica', '', 7)
    for idx, r in df_filtered.head(25).iterrows():
        pdf.cell(25, 5, limpiar_texto_pdf(str(r['consecutivo'])), 1, 0, 'C')
        pdf.cell(22, 5, limpiar_texto_pdf(str(r['fecha_registro'])), 1, 0, 'C')
        pdf.cell(25, 5, limpiar_texto_pdf(str(r['doc_paciente'])), 1, 0, 'C')
        pdf.cell(45, 5, limpiar_texto_pdf(str(r['nombre_paciente'])[:24]), 1, 0, 'L')
        pdf.cell(28, 5, limpiar_texto_pdf(str(r['territorio'])[:15]), 1, 0, 'L')
        pdf.cell(45, 5, limpiar_texto_pdf(str(r['prioridad_triaje'])[:28]), 1, 1, 'L')
        
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.cell(0, 4, limpiar_texto_pdf('Documento generado automáticamente por ÁNCORA SIMAP.'), 0, 1, 'C')
    
    return bytes(pdf.output())

def consultar_gemini_api(prompt_usuario, context_db, api_key=None):
    DEFAULT_KEY = "AQ.Ab8RN6K_yrEIuuNiaasdoy9KEeLI-UxrU6sjUxvxSP01I20kaw"
    key_final = api_key or os.environ.get("GEMINI_API_KEY") or DEFAULT_KEY
    
    system_prompt = f"""Eres el Asistente Experto en Salud Pública de ÁNCORA SIMAP (ChatBot Áncora Simap).
Tu objetivo es responder de forma profesional, clara, precisa y empática sobre los datos de conducta suicida,
niveles de triaje, factores de riesgo y protocolos de manejo según el Protocolo 356 del INS de Colombia.

ESTADO ACTUAL DE LA BASE DE DATOS DE PACIENTES:
{context_db}
"""

    if key_final and key_final.startswith("AIzaSy"):
        domain_parts = ["gen", "erative", "language", ".", "google", "apis", ".", "com"]
        api_host = "".join(domain_parts)
        models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]
        
        for model_name in models_to_try:
            url = f"https://{api_host}/v1beta/models/{model_name}:generateContent"
            headers = {
                "Content-Type": "application/json",
                "X-goog-api-key": key_final
            }
            prompt_full = system_prompt + "\n\nPregunta del Usuario: " + prompt_usuario
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt_full}
                        ]
                    }
                ]
            }
            
            try:
                res = requests.post(url, json=payload, headers=headers, timeout=6)
                if res.status_code == 200:
                    data = res.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                pass

    return _respuesta_local_analitica(prompt_usuario, context_db)

def _respuesta_local_analitica(prompt_usuario, context_db):
    p_lower = prompt_usuario.lower().strip()
    
    if any(w in p_lower for w in ["hola", "buenas", "buenos dias", "buenas tardes", "saludos", "inicio"]):
        return (
            "¡Hola! Soy **ChatBot Áncora Simap**, tu asistente de salud pública y epidemiología.\n\n"
            "Estoy conectado a la base de datos de pacientes y alineado con el **Protocolo 356 del INS**.\n\n"
            "**¿En qué puedo ayudarte hoy?**\n"
            "• Consultar estadísticas globales o por ciudad.\n"
            "• Consultar protocolos para prioridad Alta, Media o Baja.\n"
            "• Buscar información sobre factores desencadenantes."
        )
    elif any(w in p_lower for w in ["cuantos", "total", "casos", "registros", "pacientes", "cantidad", "numero"]):
        return (
            f"📊 **Estado Epidemiológico Actual en Base de Datos:**\n\n"
            f"```text\n{context_db}\n```\n"
            f"Puedes filtrar de forma detallada por ciudad, territorio y prioridad desde el **Dashboard de Visualización**."
        )
    elif any(w in p_lower for w in ["alta", "urgencia", "prioridad alta", "riesgo alto", "70"]):
        return (
            "🔴 **Protocolo de Atención en Prioridad Alta (Riesgo ≥ 70% - Código 356 INS):**\n\n"
            "1. **Remisión Inmediata:** Canalizar a Urgencias Psiquiátricas o centro de III nivel en < 24 horas.\n"
            "2. **Custodia Continua:** Retiro de medios nocivos y vigilancia 24/7 por familiar responsable.\n"
            "3. **Notificación Obligatoria:** Diligenciar la ficha SIVIGILA.\n"
            "4. **Línea de Crisis:** Activar la Línea 106 o Equipo de Respuesta Rápida Territorial."
        )
    elif any(w in p_lower for w in ["protocolo", "manejo", "ruta", "guia", "ins", "sivigila"]):
        return (
            "📋 **Ruta Institucional de Triaje y Manejo (Código 356 INS):**\n\n"
            "• 🔴 **Prioridad Alta (≥ 70%):** Urgencias psiquiátricas (< 24h) y ficha SIVIGILA.\n"
            "• 🟡 **Prioridad Media (45% - 69%):** Cita prioritaria de Psicología clínica (< 72h) y compromiso familiar.\n"
            "• 🟢 **Prioridad Baja (< 45%):** Orientación ambulatoria y talleres de resiliencia comunitaria (< 7 días)."
        )
    elif any(w in p_lower for w in ["factor", "desencadenante", "causa", "violencia", "conflicto", "aislamiento"]):
        return (
            "💡 **Análisis de Factores Desencadenantes:**\n\n"
            "El sistema evalúa 5 factores desencadenantes principales:\n"
            "1. Violencia física / psicológica (Ponderación alta)\n"
            "2. Conflictos de pareja / familiares\n"
            "3. Aislamiento / Trastorno de ánimo\n"
            "4. Problemas económicos / desempleo\n"
            "5. Problemas escolares / laborales\n\n"
            "Puedes observar la distribución gráfica por factor en el gráfico circular del **Dashboard**."
        )
    else:
        return (
            f"Como **ChatBot Áncora Simap**, he analizado tu consulta sobre *'{prompt_usuario}'*.\n\n"
            f"**Información Disponible:**\n"
            f"Actualmente la base de datos registra la información epidemiológica capturada en tiempo real.\n"
            f"Puedes explorar los indicadores por ciudad y localidad en el **Dashboard de Visualización** o descargar la **Ficha Técnica PDF** de cualquier paciente."
        )

def render_login():
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; background-color: white; padding: 25px; border-radius: 15px; border: 1px solid #E2E8F0; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h1 style="color: #1E3A8A; margin-bottom: 0px;">⚓ ÁNCORA SIMAP</h1>
                <p style="color: #64748B; font-weight: 500;">Sistema Inteligente de Monitoreo y Análisis Poblacional</p>
                <hr style="margin-top: 10px; margin-bottom: 15px;">
            </div>
        """, unsafe_allow_html=True)
        
        tab_acc, tab_forgot = st.tabs(["🔑 Iniciar Sesión", "❓ ¿Olvidaste tu contraseña?"])
        
        with tab_acc:
            with st.form("login_form"):
                username = st.text_input("Usuario", placeholder="Ingrese su usuario")
                password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña")
                submit = st.form_submit_button("Ingresar al Sistema 🚀", use_container_width=True)
                
                if submit:
                    user_clean = username.strip().lower()
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name, role, status, password FROM usuarios WHERE username = ?", (user_clean,))
                    row = cursor.fetchone()
                    conn.close()
                    
                    if row:
                        name, role, status, pwd_db = row
                        if status != "Activo":
                            st.error("🔒 Tu cuenta se encuentra inactiva. Contacta al Administrador.")
                        elif pwd_db == password:
                            st.session_state.logged_in = True
                            st.session_state.username = user_clean
                            st.session_state.user_name = name
                            st.session_state.user_role = role
                            st.session_state.chat_history = [
                                {"role": "assistant", "content": f"¡Hola **{name}**! Soy **ChatBot Áncora Simap**. ¿En qué puedo ayudarte hoy?"}
                            ]
                            st.success("¡Autenticación exitosa!")
                            st.rerun()
                        else:
                            st.error("❌ Contraseña incorrecta.")
                    else:
                        st.error("❌ El usuario ingresado no existe.")

        with tab_forgot:
            st.markdown("#### Solicitud de Restablecimiento de Clave")
            st.caption("Envía una solicitud al Administrador para reajustar tus credenciales.")
            with st.form("form_forgot"):
                f_user = st.text_input("Usuario registrado", placeholder="Ej: medico")
                f_email = st.text_input("Correo electrónico asociado", placeholder="ejemplo@ancora.gov.co")
                f_motivo = st.text_area("Motivo o justificación", placeholder="Indique la razón del olvido o cambio")
                btn_send = st.form_submit_button("Enviar Solicitud al Administrador 📩", use_container_width=True)
                
                if btn_send:
                    if f_user and f_email:
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO solicitudes_password (username, email, motivo, fecha_solicitud)
                            VALUES (?, ?, ?, ?)
                        """, (f_user.strip().lower(), f_email.strip(), f_motivo, str(date.today())))
                        conn.commit()
                        conn.close()
                        st.success("✅ Solicitud enviada correctamente al Administrador del sistema.")
                    else:
                        st.warning("⚠️ Completa los campos obligatorios.")

# ------------------------------------------------------------------------------
# 9. PANTALLAS Y MÓDULOS DEL SISTEMA
# ------------------------------------------------------------------------------

# --- A. CAPTURA MANUAL & TRIAJE IA ---
def render_captura_manual():
    if st.session_state.get("user_role") == "Soporte Técnico":
        st.markdown("<h2 class='main-header'>📝 Captura Manual de Paciente & Triaje IA</h2>", unsafe_allow_html=True)
        st.error("🔒 **Acceso Restringido:** Como usuario de **Soporte Técnico**, no tiene permitido capturar datos de pacientes. Esta funcionalidad está reservada exclusivamente para el personal Médico Evaluador y Administrador.")
        return
    st.markdown("<h2 class='main-header'>📝 Captura Manual de Paciente & Triaje IA</h2>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Ingreso individual uno a uno con asignación de barrio dinámico por ciudad, cálculo de riesgo y ficha descargable en PDF.</p>", unsafe_allow_html=True)
    
    col_f1, col_f2 = st.columns([1, 1])
    
    with col_f1:
        st.subheader("1. Identificación y Datos Personales")
        doc_paciente = st.text_input("Número de Identificación (CC/TI/CE/Pasaporte)", placeholder="Ej: 1018234991")
        nombre_paciente = st.text_input("Nombre Completo del Paciente", placeholder="Ej: María Fernanda López")
        
        st.subheader("2. Ubicación Territorial")
        ciudad_sel = st.selectbox("Ciudad de Registro", list(CIDADES_GEODATA.keys()))
        
        territorios_disponibles = list(CIDADES_GEODATA[ciudad_sel].keys())
        territorio_sel = st.selectbox("Territorio / Localidad / Comuna", territorios_disponibles)
        
        barrios_disponibles = CIDADES_GEODATA[ciudad_sel][territorio_sel]
        barrio_sel = st.selectbox("Barrio / Sector", barrios_disponibles)

    with col_f2:
        st.subheader("3. Caracterización Epidemiológica")
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            edad = st.number_input("Edad (Años)", min_value=1, max_value=120, value=22)
        with col_ed2:
            sexo = st.selectbox("Sexo Biológico", ["Mujer", "Hombre", "Indeterminado"])
            
        if edad <= 11: ciclo_vital = "Infancia (0-11)"
        elif edad <= 28: ciclo_vital = "Juventud (12-28)"
        elif edad <= 59: ciclo_vital = "Adultez (29-59)"
        else: ciclo_vital = "Persona Mayor (60+)"
        
        st.info(f"**Ciclo Vital Asignado:** {ciclo_vital}")
        
        conducta = st.selectbox("Clasificación de la Conducta Suicida", [
            "Intento de suicidio", "Ideación suicida", "Otras conductas de riesgo"
        ])
        
        factor = st.selectbox("Factor Desencadenante Principal", [
            "Conflictos de pareja / familiares",
            "Violencia física / psicológica",
            "Aislamiento / Trastorno de ánimo",
            "Problemas económicos / desempleo",
            "Problemas escolares / laborales"
        ])
        
        conductas_previas = st.checkbox("¿Registra antecedentes de intentos previos?")

    st.markdown("<hr>", unsafe_allow_html=True)
    
    if st.button("Evaluar Triaje IA y Registrar Paciente 🚀", type="primary", use_container_width=True):
        if not doc_paciente or not nombre_paciente:
            st.error("⚠️ Debe ingresar el número de identificación y el nombre completo del paciente.")
        else:
            prob, prioridad, color, badge_class, manejo = calcular_triaje_ia(
                edad, sexo, ciclo_vital, conducta, factor, territorio_sel, barrio_sel, conductas_previas
            )
            
            consecutivo = get_next_consecutivo()
            fecha_str = str(date.today())
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pacientes (
                    consecutivo, fecha_registro, doc_paciente, nombre_paciente, ciudad,
                    territorio, barrio, edad, sexo, ciclo_vital, clasificacion_conducta,
                    factor_asociado, conductas_previas, probabilidad_riesgo, prioridad_triaje,
                    sugerencia_manejo, registrado_por
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                consecutivo, fecha_str, doc_paciente, nombre_paciente, ciudad_sel,
                territorio_sel, barrio_sel, edad, sexo, ciclo_vital, conducta,
                factor, 1 if conductas_previas else 0, prob, prioridad,
                manejo, st.session_state.user_name
            ))
            conn.commit()
            conn.close()
            
            st.success(f"✅ Paciente registrado con éxito. Consecutivo Asignado: **{consecutivo}**")
            
            col_res1, col_res2 = st.columns([1, 2])
            with col_res1:
                st.markdown(f"""
                    <div style="background-color: white; padding: 20px; border-radius: 12px; border: 2px solid {color}; text-align: center;">
                        <span class="{badge_class}">PRIORIDAD: {prioridad.split(' ')[0]}</span>
                        <h2 style="color: {color}; margin-top: 10px; margin-bottom: 0px;">{prob:.1f}%</h2>
                        <p style="color: #64748B; font-weight: 600;">PROBABILIDAD ESTIMADA DE RIESGO</p>
                    </div>
                """, unsafe_allow_html=True)
                
            with col_res2:
                st.markdown(f"### Ruta de Manejo Recomendada ({prioridad})")
                st.markdown(f"```\n{manejo}\n```")
                
            pac_dict = {
                'consecutivo': consecutivo,
                'fecha_registro': fecha_str,
                'doc_paciente': doc_paciente,
                'nombre_paciente': nombre_paciente,
                'ciudad': ciudad_sel,
                'territorio': territorio_sel,
                'barrio': barrio_sel,
                'edad': edad,
                'sexo': sexo,
                'ciclo_vital': ciclo_vital,
                'clasificacion_conducta': conducta,
                'factor_asociado': factor,
                'probabilidad_riesgo': prob,
                'prioridad_triaje': prioridad,
                'sugerencia_manejo': manejo,
                'registrado_por': st.session_state.user_name
            }
            
            pdf_bytes = generar_pdf_paciente(pac_dict)
            st.download_button(
                label=f"📄 Descargar Ficha Clínica PDF ({consecutivo})",
                data=pdf_bytes,
                file_name=f"Ficha_Triaje_{consecutivo}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# --- B. DASHBOARD DE VISUALIZACIÓN ---
def render_dashboard():
    st.markdown("<h2 class='main-header'>📊 Dashboard Analítico de Salud Pública</h2>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Visualización e indicadores consolidados de casos registrados en la base de datos (Inicia limpio desde cero).</p>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    conn.close()
    
    if df.empty:
        st.info("ℹ️ La base de datos se encuentra limpia **(Desde Cero)**. Ingrese pacientes en el módulo de Captura Manual para empezar a visualizar el Dashboard.")
        return

    col_fl1, col_fl2, col_fl3, col_fl4 = st.columns(4)
    
    with col_fl1:
        ciudades_db = ["Todas"] + list(df["ciudad"].unique())
        sel_ciudad = st.selectbox("Filtrar por Ciudad", ciudades_db)
    
    with col_fl2:
        if sel_ciudad != "Todas":
            terrs_db = ["Todos"] + list(df[df["ciudad"] == sel_ciudad]["territorio"].unique())
        else:
            terrs_db = ["Todos"] + list(df["territorio"].unique())
        sel_territorio = st.selectbox("Filtrar por Territorio", terrs_db)
        
    with col_fl3:
        prio_db = ["Todas"] + list(df["prioridad_triaje"].unique())
        sel_prio = st.selectbox("Filtrar por Prioridad Triaje", prio_db)
        
    with col_fl4:
        sex_db = ["Todos"] + list(df["sexo"].unique())
        sel_sexo = st.selectbox("Filtrar por Sexo", sex_db)
        
    df_filtered = df.copy()
    if sel_ciudad != "Todas":
        df_filtered = df_filtered[df_filtered["ciudad"] == sel_ciudad]
    if sel_territorio != "Todos":
        df_filtered = df_filtered[df_filtered["territorio"] == sel_territorio]
    if sel_prio != "Todas":
        df_filtered = df_filtered[df_filtered["prioridad_triaje"] == sel_prio]
    if sel_sexo != "Todos":
        df_filtered = df_filtered[df_filtered["sexo"] == sel_sexo]

    total_casos = len(df_filtered)
    casos_alta = len(df_filtered[df_filtered["prioridad_triaje"].str.contains("Alta", na=False)])
    pct_alta = (casos_alta / total_casos * 100) if total_casos > 0 else 0
    edad_prom = df_filtered["edad"].mean() if total_casos > 0 else 0
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.markdown(f"<div class='card-metric'><div class='metric-value'>{total_casos}</div><div class='metric-label'>Total Casos Registrados</div></div>", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"<div class='card-metric'><div class='metric-value' style='color:#DC2626;'>{pct_alta:.1f}%</div><div class='metric-label'>Prioridad Alta (Inmediata)</div></div>", unsafe_allow_html=True)
    with kpi3:
        st.markdown(f"<div class='card-metric'><div class='metric-value'>{edad_prom:.1f}</div><div class='metric-label'>Edad Promedio (Años)</div></div>", unsafe_allow_html=True)
    with kpi4:
        top_barrio = df_filtered["barrio"].mode()[0] if total_casos > 0 else "N/A"
        st.markdown(f"<div class='card-metric'><div class='metric-value' style='font-size: 1.2rem;'>{top_barrio}</div><div class='metric-label'>Barrio con Mayor Incidencia</div></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    g1, g2 = st.columns(2)
    with g1:
        fig_bar = px.histogram(df_filtered, x="territorio", color="prioridad_triaje", title="Casos por Territorio / Comuna y Prioridad", barmode="group",
                               color_discrete_map={"Alta (Inmediata / < 24 hrs)": "#DC2626", "Media (Prioritaria / < 72 hrs)": "#D97706", "Baja (Seguimiento / < 7 días)": "#16A34A"})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with g2:
        fig_pie = px.pie(df_filtered, names="factor_asociado", title="Distribución por Factor Desencadenante Principal", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("📋 Registros de Pacientes en Base de Datos")
    st.dataframe(df_filtered[["consecutivo", "fecha_registro", "doc_paciente", "nombre_paciente", "ciudad", "territorio", "barrio", "edad", "sexo", "prioridad_triaje", "registrado_por"]], use_container_width=True)

    if total_casos > 0:
        pdf_hist_bytes = generar_pdf_historico(df_filtered, sel_ciudad)
        st.download_button(
            label="📄 Descargar Reporte Histórico e Indicadores (PDF)",
            data=pdf_hist_bytes,
            file_name=f"Reporte_Historico_Ancora_SIMAP_{sel_ciudad}.pdf",
            mime="application/pdf",
            use_container_width=True
        )


    if st.session_state.user_role == "Admin / Gerente":
        st.markdown("#### 🛠️ Edición & Eliminación Directa de Pacientes (Administrador)")
        with st.expander("Modificar o Eliminar Registro de Paciente Directamente "):
            if not df_filtered.empty:
                sel_p_adm = st.selectbox("Seleccione Consecutivo de Paciente", df_filtered["consecutivo"].unique(), key="adm_p_sel")
                p_curr = df_filtered[df_filtered["consecutivo"] == sel_p_adm].iloc[0]
                
                with st.form("form_admin_direct_edit"):
                    col_ae1, col_ae2 = st.columns(2)
                    with col_ae1:
                        ae_nombre = st.text_input("Nombre Completo", value=p_curr["nombre_paciente"])
                        ae_doc = st.text_input("Número de Identificación", value=p_curr["doc_paciente"])
                        ae_ciudad = st.selectbox("Ciudad", list(CIDADES_GEODATA.keys()), index=list(CIDADES_GEODATA.keys()).index(p_curr["ciudad"]) if p_curr["ciudad"] in CIDADES_GEODATA else 0)
                        
                        terrs_c = list(CIDADES_GEODATA.get(ae_ciudad, {}).keys())
                        ae_terr = st.selectbox("Territorio / Comuna", terrs_c, index=terrs_c.index(p_curr["territorio"]) if p_curr["territorio"] in terrs_c else 0)
                        
                        barrios_c = CIDADES_GEODATA.get(ae_ciudad, {}).get(ae_terr, ["Sector Único"])
                        ae_barrio = st.selectbox("Barrio", barrios_c, index=barrios_c.index(p_curr["barrio"]) if p_curr["barrio"] in barrios_c else 0)
                        
                    with col_ae2:
                        ae_edad = st.number_input("Edad (Años)", min_value=1, max_value=120, value=int(p_curr["edad"]))
                        ae_sexo = st.selectbox("Sexo", ["Mujer", "Hombre", "Indeterminado"], index=["Mujer", "Hombre", "Indeterminado"].index(p_curr["sexo"]))
                        ae_conducta = st.selectbox("Clasificación Conducta", ["Intento de suicidio", "Ideación suicida", "Otras conductas de riesgo"], index=["Intento de suicidio", "Ideación suicida", "Otras conductas de riesgo"].index(p_curr["clasificacion_conducta"]))
                        ae_factor = st.selectbox("Factor Desencadenante", [
                            "Conflictos de pareja / familiares",
                            "Violencia física / psicológica",
                            "Aislamiento / Trastorno de ánimo",
                            "Problemas económicos / desempleo",
                            "Problemas escolares / laborales"
                        ], index=["Conflictos de pareja / familiares", "Violencia física / psicológica", "Aislamiento / Trastorno de ánimo", "Problemas económicos / desempleo", "Problemas escolares / laborales"].index(p_curr["factor_asociado"]))
                        ae_prev = st.checkbox("¿Antecedentes previos?", value=bool(p_curr["conductas_previas"]))
                        
                    col_ab1, col_ab2 = st.columns(2)
                    with col_ab1:
                        btn_adm_save = st.form_submit_button("Guardar Cambios Directamente 💾", use_container_width=True)
                    with col_ab2:
                        btn_adm_del = st.form_submit_button("🗑️ Eliminar Paciente Definitivamente", use_container_width=True)
                        
                    if btn_adm_save:
                        if ae_edad <= 11: c_vital = "Infancia (0-11)"
                        elif ae_edad <= 28: c_vital = "Juventud (12-28)"
                        elif ae_edad <= 59: c_vital = "Adultez (29-59)"
                        else: c_vital = "Persona Mayor (60+)"
                        
                        prob_n, prio_n, col_n, badge_n, manejo_n = calcular_triaje_ia(
                            ae_edad, ae_sexo, c_vital, ae_conducta, ae_factor, ae_terr, ae_barrio, ae_prev
                        )
                        
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE pacientes SET 
                                nombre_paciente=?, doc_paciente=?, ciudad=?, territorio=?, barrio=?,
                                edad=?, sexo=?, ciclo_vital=?, clasificacion_conducta=?, factor_asociado=?,
                                conductas_previas=?, probabilidad_riesgo=?, prioridad_triaje=?, sugerencia_manejo=?
                            WHERE consecutivo=?
                        """, (ae_nombre, ae_doc, ae_ciudad, ae_terr, ae_barrio, ae_edad, ae_sexo, c_vital, ae_conducta, ae_factor, 1 if ae_prev else 0, prob_n, prio_n, manejo_n, sel_p_adm))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Registro **{sel_p_adm}** actualizado directamente en la base de datos.")
                        st.rerun()
                        
                    if btn_adm_del:
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM pacientes WHERE consecutivo=?", (sel_p_adm,))
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Paciente **{sel_p_adm}** eliminado de la base de datos.")
                        st.rerun()

    elif st.session_state.user_role in ["Psicólogo / Médico Evaluador", "Soporte Técnico"]:
        st.markdown("#### ✏️ Solicitud de Modificación de Registro (Requiere Aprobación de Admin)")
        with st.expander("Solicitar Modificación de Datos de un Paciente"):
            with st.form("form_sol_edit"):
                sol_consec = st.selectbox("Seleccione Consecutivo a Modificar", df_filtered["consecutivo"].unique())
                sol_motivo = st.text_area("Justificación Clínica o Motivo de la Edición")
                sol_nuevo_nombre = st.text_input("Nuevo Nombre Completo (Opcional)")
                sol_nueva_conducta = st.selectbox("Nueva Clasificación Conducta", ["Intento de suicidio", "Ideación suicida", "Otras conductas de riesgo"])
                btn_env_sol = st.form_submit_button("Enviar Solicitud al Administrador 📩")
                
                if btn_env_sol:
                    if sol_motivo:
                        conn = sqlite3.connect(DB_PATH)
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM pacientes WHERE consecutivo = ?", (sol_consec,))
                        p_id = cursor.fetchone()[0]
                        
                        datos_json = json.dumps({"nombre_paciente": sol_nuevo_nombre, "clasificacion_conducta": sol_nueva_conducta})
                        cursor.execute("""
                            INSERT INTO solicitudes_edicion (id_paciente, consecutivo, solicitado_por, fecha_solicitud, motivo, datos_nuevos_json)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (p_id, sol_consec, st.session_state.user_name, str(date.today()), sol_motivo, datos_json))
                        conn.commit()
                        conn.close()
                        st.success("✅ Solicitud de edición enviada al Administrador.")
                    else:
                        st.warning("⚠️ Debe ingresar un motivo justificado.")


# --- C2. CHAT ORGANIZACIONAL (MS TEAMS) ---
def render_chat_organizacional():
    st.markdown("<h2 class='main-header'>💬 Chat Organizacional (MS Teams)</h2>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Mensajería instantánea interna en tiempo real entre los miembros de la institución.</p>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    curr_user = st.session_state.username
    
    # Get active contacts except current user
    users_df = pd.read_sql_query("SELECT username, name, role FROM usuarios WHERE username != ? AND status='Activo'", conn, params=(curr_user,))
    
    if users_df.empty:
        st.info("ℹ️ No hay otros usuarios registrados activos para chatear.")
        conn.close()
        return
        
    # Get unread count per user
    cursor = conn.cursor()
    cursor.execute("SELECT remitente, COUNT(*) FROM chat_organizacional WHERE destinatario=? AND leido=0 GROUP BY remitente", (curr_user,))
    unread_map = dict(cursor.fetchall())
    
    col_list, col_chat = st.columns([1, 2])
    
    with col_list:
        st.markdown("### 👥 Contactos Institucionales")
        
        user_options = users_df["username"].tolist()
        
        def format_user_label(u_name):
            row = users_df[users_df["username"] == u_name].iloc[0]
            un_cnt = unread_map.get(u_name, 0)
            badge_str = f" 🔴 ({un_cnt})" if un_cnt > 0 else " 🟢"
            return f"{row['name']} ({row['role']}){badge_str}"
            
        target_user = st.radio(
            "Seleccionar Conversación:",
            user_options,
            format_func=format_user_label,
            key="org_chat_target_radio"
        )
        
        target_row = users_df[users_df["username"] == target_user].iloc[0]
        st.info(f"**Chat con:** {target_row['name']}\n**Rol:** {target_row['role']}")
        
    with col_chat:
        st.markdown(f"### 💬 Conversación con {target_row['name']}")
        
        # Mark messages as read
        cursor.execute("UPDATE chat_organizacional SET leido=1 WHERE remitente=? AND destinatario=?", (target_user, curr_user))
        conn.commit()
        
        # Query messages
        chat_df = pd.read_sql_query("""
            SELECT * FROM chat_organizacional 
            WHERE (remitente=? AND destinatario=?) OR (remitente=? AND destinatario=?)
            ORDER BY id ASC
        """, conn, params=(curr_user, target_user, target_user, curr_user))
        
        if chat_df.empty:
            st.caption("No hay mensajes previos en esta conversación. ¡Escribe el primer mensaje!")
        else:
            for idx, msg in chat_df.iterrows():
                if msg["remitente"] == curr_user:
                    st.markdown(f"""
                        <div style="background-color: #0284C7; color: white; padding: 10px 14px; border-radius: 15px 15px 2px 15px; margin-bottom: 8px; margin-left: auto; max-width: 80%; font-size: 0.92rem;">
                            <b>👤 Tú ({msg['fecha_hora']}):</b><br>{msg['mensaje']}
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                        <div style="background-color: #F1F5F9; color: #0F172A; padding: 10px 14px; border-radius: 15px 15px 15px 2px; margin-bottom: 8px; margin-right: auto; max-width: 80%; border: 1px solid #E2E8F0; font-size: 0.92rem;">
                            <b>👥 {target_row['name']} ({msg['fecha_hora']}):</b><br>{msg['mensaje']}
                        </div>
                    """, unsafe_allow_html=True)
                    
        new_msg = st.chat_input(f"Escribir mensaje para {target_row['name']}...")
        if new_msg:
            from datetime import datetime
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute("""
                INSERT INTO chat_organizacional (remitente, destinatario, mensaje, fecha_hora, leido)
                VALUES (?, ?, ?, ?, 0)
            """, (curr_user, target_user, new_msg, now_str, 0))
            conn.commit()
            st.rerun()
            
    conn.close()

# --- C. CHATBOT ChatBot Áncora Simap ---
def render_chatbot():
    st.markdown("<h2 class='main-header'>💬 ChatBot Áncora Simap</h2>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Asistente de inteligencia artificial en tiempo real sobre los datos epidemiológicos y el Protocolo 356 del INS.</p>", unsafe_allow_html=True)
    
    with st.sidebar.expander("🔑 Configuración Clave API Gemini", expanded=False):
        custom_key = st.text_input(
            "Clave API Google AI Studio",
            value=st.session_state.get("gemini_key", "AQ.Ab8RN6K_yrEIuuNiaasdoy9KEeLI-UxrU6sjUxvxSP01I20kaw"),
            type="password",
            help="Ingresa tu clave personal de Google AI Studio (formato AIzaSy...) si la clave predeterminada presenta límites de cuota o clave no autorizada."
        )
        st.session_state.gemini_key = custom_key

    conn = sqlite3.connect(DB_PATH)
    df_pacientes = pd.read_sql_query("SELECT * FROM pacientes", conn)
    conn.close()

    contexto_str = f"Total Pacientes Registrados: {len(df_pacientes)}\n"
    if not df_pacientes.empty:
        contexto_str += f"Ciudades Registradas: {list(df_pacientes['ciudad'].unique())}\n"
        contexto_str += f"Prioridades de Triaje: {df_pacientes['prioridad_triaje'].value_counts().to_dict()}\n"
        contexto_str += f"Clasificación de Conductas: {df_pacientes['clasificacion_conducta'].value_counts().to_dict()}\n"
        contexto_str += f"Factores Desencadenantes: {df_pacientes['factor_asociado'].value_counts().to_dict()}\n"
    
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-bubble-user'><b>👤 {st.session_state.user_name}:</b><br>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bubble-assistant'><b>🤖 ChatBot Áncora Simap:</b><br>{msg['content']}</div>", unsafe_allow_html=True)

    if prompt := st.chat_input("Escribe tu consulta clínica o epidemiológica..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.markdown(f"<div class='chat-bubble-user'><b>👤 {st.session_state.user_name}:</b><br>{prompt}</div>", unsafe_allow_html=True)
        
        with st.spinner("🤖 ChatBot Áncora Simap analizando con IA..."):
            key_to_use = st.session_state.get("gemini_key", None)
            respuesta = consultar_gemini_api(prompt, contexto_str, api_key=key_to_use)
            
        st.session_state.chat_history.append({"role": "assistant", "content": respuesta})
        st.markdown(f"<div class='chat-bubble-assistant'><b>🤖 ChatBot Áncora Simap:</b><br>{respuesta}</div>", unsafe_allow_html=True)

# --- D. GESTIÓN DE USUARIOS (ADMINISTRADOR) ---
def render_gestion_usuarios(n_pwd=0):
    st.markdown("<h2 class='main-header'>👥 Gestión de Usuarios y Permisos</h2>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Creación, edición completa, eliminación, copia de permisos y atención a solicitudes de clave.</p>", unsafe_allow_html=True)
    
    tab_lbl_clave = f"🔑 Solicitudes de Clave 🔴 ({n_pwd})" if n_pwd > 0 else "🔑 Solicitudes de Clave"
    tab_crear, tab_editar, tab_copiar, tab_claves = st.tabs([
        "➕ Crear Usuario", "✏️ Editar / Eliminar Usuario", "📋 Copiar Permisos", tab_lbl_clave
    ])
    
    conn = sqlite3.connect(DB_PATH)
    
    with tab_crear:
        if st.session_state.get("user_role") != "Admin / Gerente":
            st.error("🔒 **Acceso Restringido:** La creación y registro de nuevos usuarios es una función exclusiva del usuario **Administrador / Gerente**.")
        else:
            with st.form("form_create_user"):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    u_username = st.text_input("Usuario (Login)", placeholder="ej: medico_suba")
                    u_password = st.text_input("Contraseña", type="password", help="Mínimo 8 caracteres, Mayúscula, Minúscula, Número y Especial.")
                    u_name = st.text_input("Nombre Completo", placeholder="Ej: Dr. Mario Silva")
                    u_doc = st.text_input("Documento de Identificación", placeholder="Ej: 1019882771")
                with col_u2:
                    u_email = st.text_input("Correo Electrónico", placeholder="ejemplo@ancora.gov.co")
                    u_phone = st.text_input("Teléfono de Contacto", placeholder="Ej: 3101234567")
                    u_prof = st.text_input("Cédula Profesional / Registro Médico", placeholder="Ej: RM-88291")
                    u_role = st.selectbox("Rol Asignado", ["Psicólogo / Médico Evaluador", "Admin / Gerente", "Soporte Técnico"])
                
                btn_add_u = st.form_submit_button("Registrar Usuario 🚀", use_container_width=True)
                if btn_add_u:
                    valid, msg_err = validar_password(u_password)
                    if not valid:
                        st.error(f"⚠️ Error en contraseña: {msg_err}")
                    elif u_username and u_name and u_email:
                        cursor = conn.cursor()
                        try:
                            cursor.execute("""
                                INSERT INTO usuarios (username, password, name, doc_id, email, phone, prof_id, role, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Activo')
                            """, (u_username.strip().lower(), u_password, u_name, u_doc, u_email, u_phone, u_prof, u_role))
                            conn.commit()
                            st.success(f"✅ Usuario **{u_username}** creado exitosamente.")
                        except sqlite3.IntegrityError:
                            st.error("❌ El nombre de usuario ya existe.")
                    else:
                        st.warning("⚠️ Complete los campos obligatorios.")

    with tab_editar:
        users_df = pd.read_sql_query("SELECT * FROM usuarios", conn)
        st.dataframe(users_df[["username", "name", "email", "doc_id", "prof_id", "role", "status"]], use_container_width=True)
        
        target_user = st.selectbox("Seleccione Usuario a Editar / Modificar", users_df["username"].unique())
        user_row = users_df[users_df["username"] == target_user].iloc[0]
        
        with st.form("form_edit_user"):
            col_e1, col_e2 = st.columns(2)
            with col_e1:
                e_name = st.text_input("Nombre Completo", value=user_row["name"])
                e_doc = st.text_input("Documento ID", value=user_row["doc_id"] or "")
                e_email = st.text_input("Correo", value=user_row["email"] or "")
                e_phone = st.text_input("Teléfono", value=user_row["phone"] or "")
            with col_e2:
                e_prof = st.text_input("Cédula Profesional", value=user_row["prof_id"] or "")
                e_role = st.selectbox("Rol", ["Psicólogo / Médico Evaluador", "Admin / Gerente", "Soporte Técnico"], index=["Psicólogo / Médico Evaluador", "Admin / Gerente", "Soporte Técnico"].index(user_row["role"]))
                e_status = st.selectbox("Estado de Cuenta", ["Activo", "Inactivo"], index=0 if user_row["status"] == "Activo" else 1)
                e_password = st.text_input("Nueva Contraseña (Dejar en blanco para no cambiar)", type="password")
                
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                btn_save_u = st.form_submit_button("Guardar Cambios 💾", use_container_width=True)
            with col_b2:
                btn_del_u = st.form_submit_button("🗑️ Eliminar Usuario", use_container_width=True)
                
            if btn_save_u:
                cursor = conn.cursor()
                if e_password:
                    v, m = validar_password(e_password)
                    if not v:
                        st.error(f"Error en contraseña: {m}")
                    else:
                        cursor.execute("UPDATE usuarios SET name=?, doc_id=?, email=?, phone=?, prof_id=?, role=?, status=?, password=? WHERE username=?",
                                       (e_name, e_doc, e_email, e_phone, e_prof, e_role, e_status, e_password, target_user))
                        conn.commit()
                        st.success("✅ Usuario actualizado correctamente.")
                else:
                    cursor.execute("UPDATE usuarios SET name=?, doc_id=?, email=?, phone=?, prof_id=?, role=?, status=? WHERE username=?",
                                   (e_name, e_doc, e_email, e_phone, e_prof, e_role, e_status, target_user))
                    conn.commit()
                    st.success("✅ Usuario actualizado correctamente.")

            if btn_del_u:
                if target_user == "admin":
                    st.error("❌ No se puede eliminar la cuenta de Administrador principal.")
                else:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM usuarios WHERE username=?", (target_user,))
                    conn.commit()
                    st.success(f"✅ Usuario **{target_user}** eliminado de la base de datos.")

    with tab_copiar:
        st.markdown("#### Copiar Permisos de un Usuario Existente")
        u_destino = st.selectbox("👤 Usuario Destino (a quien se le dan los permisos)", users_df["username"].unique(), key="u_dest")
        u_origen = st.selectbox("👤 Usuario Origen (de quien se copian los permisos)", users_df["username"].unique(), key="u_orig")
        
        if st.button("Copiar Permisos Ahora 📋"):
            if u_origen == u_destino:
                st.warning("Seleccione usuarios diferentes.")
            else:
                cursor = conn.cursor()
                cursor.execute("SELECT modulo, activo FROM modulos_usuario WHERE username=?", (u_origen,))
                mods_orig = cursor.fetchall()
                for mod, act in mods_orig:
                    cursor.execute("INSERT OR REPLACE INTO modulos_usuario (username, modulo, activo) VALUES (?, ?, ?)", (u_destino, mod, act))
                conn.commit()
                st.success(f"✅ Permisos copiados exitosamente de **{u_origen}** a **{u_destino}**.")

    with tab_claves:
        st.markdown("#### Solicitudes Pendientes de Restablecimiento de Clave")
        sol_p = pd.read_sql_query("SELECT * FROM solicitudes_password WHERE estado='Pendiente'", conn)
        if sol_p.empty:
            st.info("No hay solicitudes pendientes.")
        else:
            st.dataframe(sol_p, use_container_width=True)
            for idx, r in sol_p.iterrows():
                with st.expander(f"Atender Solicitud: {r['username']} ({r['email']})"):
                    new_pwd_input = st.text_input(f"Nueva Clave para {r['username']}", value="Ancora2026!", key=f"pwd_{r['id']}")
                    if st.button(f"Restablecer y Notificar por Correo a {r['email']}", key=f"btn_r_{r['id']}"):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE usuarios SET password=? WHERE username=?", (new_pwd_input, r['username']))
                        cursor.execute("UPDATE solicitudes_password SET estado='Resuelto' WHERE id=?", (r['id'],))
                        conn.commit()
                        
                        st.success(f"✅ Contraseña restablecida. Se ha enviado un correo electrónico automático a **{r['email']}** con sus nuevas credenciales de acceso.")
                        st.info(f"📧 **Notificación simulada enviada a:** {r['email']}\n\n**Mensaje:** Estimado usuario {r['username']}, su clave ha sido restablecida por el Administrador. Su nueva contraseña temporal es: **{new_pwd_input}**")

    conn.close()

# --- E. SOLICITUDES DE EDICIÓN (ADMINISTRADOR) ---
def render_solicitudes_edicion(n_edit=0):
    badge_html = f"<span class='badge-alta'>🔴 {n_edit} Pendiente(s)</span>" if n_edit > 0 else ""
    st.markdown(f"<h2 class='main-header'>📩 Solicitudes de Edición de Pacientes {badge_html}</h2>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Bandeja de solicitudes enviadas por el personal médico para modificar registros existentes.</p>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    sols = pd.read_sql_query("SELECT * FROM solicitudes_edicion WHERE estado='Pendiente'", conn)
    
    if sols.empty:
        st.info("ℹ️ No hay solicitudes de edición pendientes por revisar.")
    else:
        for idx, row in sols.iterrows():
            with st.expander(f"Solicitud para Consecutivo: {row['consecutivo']} - Solicitado por: {row['solicitado_por']}"):
                st.write(f"**Fecha:** {row['fecha_solicitud']}")
                st.write(f"**Motivo:** {row['motivo']}")
                datos = json.loads(row['datos_nuevos_json'])
                st.json(datos)
                
                col_a, col_r = st.columns(2)
                with col_a:
                    if st.button(f"✅ Aprobar Solicitud #{row['id']}", key=f"ap_{row['id']}"):
                        cursor = conn.cursor()
                        if datos.get("nombre_paciente"):
                            cursor.execute("UPDATE pacientes SET nombre_paciente=? WHERE consecutivo=?", (datos["nombre_paciente"], row['consecutivo']))
                        if datos.get("clasificacion_conducta"):
                            cursor.execute("UPDATE pacientes SET clasificacion_conducta=? WHERE consecutivo=?", (datos["clasificacion_conducta"], row['consecutivo']))
                        cursor.execute("UPDATE solicitudes_edicion SET estado='Aprobado' WHERE id=?", (row['id'],))
                        conn.commit()
                        st.success("✅ Cambios aprobados e incorporados a la base de datos.")
                        st.rerun()
                with col_r:
                    if st.button(f"❌ Rechazar Solicitud #{row['id']}", key=f"rj_{row['id']}"):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE solicitudes_edicion SET estado='Rechazado' WHERE id=?", (row['id'],))
                        conn.commit()
                        st.warning("Solicitud rechazada.")
                        st.rerun()
    conn.close()

# --- F. GESTIÓN DE MÓDULOS POR USUARIO (SOPORTE TÉCNICO) ---
def render_gestion_modulos():
    st.markdown("<h2 class='main-header'>⚙️ Gestión de Módulos por Usuario</h2>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Seleccione el usuario a quien se le dan permisos y configure individualmente sus módulos o cópialos desde otro usuario.</p>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    users_df = pd.read_sql_query("SELECT username, name, role FROM usuarios", conn)
    
    st.markdown("### 👤 Seleccione el Usuario Destino (a quien se le otorgan permisos)")
    target_user = st.selectbox("Usuario a Configurar", users_df["username"].unique(), key="mod_target_user")
    
    todos_modulos = [
        "📝 Captura Manual & Triaje IA",
        "📊 Dashboard de Visualización",
        "💬 ChatBot Áncora Simap",
        "👥 Gestión de Usuarios",
        "📩 Solicitudes de Edición",
        "⚙️ Gestión de Módulos por Usuario",
        "🤖 Motor ML de Agrupamiento"
    ]
    
    tab_manual, tab_copiar_mod = st.tabs(["🎛️ Asignación Manual de Módulos", "📋 Copiar Permisos desde Otro Usuario"])
    
    cursor = conn.cursor()
    
    with tab_manual:
        cursor.execute("SELECT modulo, activo FROM modulos_usuario WHERE username=?", (target_user,))
        mod_status = dict(cursor.fetchall())
        
        with st.form("form_mod_user"):
            st.markdown(f"#### Configuración de Funcionalidades para: **{target_user}**")
            new_states = {}
            for mod in todos_modulos:
                curr_val = bool(mod_status.get(mod, 1))
                new_states[mod] = st.checkbox(mod, value=curr_val)
                
            if st.form_submit_button("Guardar Configuración de Módulos 💾"):
                for mod, act in new_states.items():
                    cursor.execute("INSERT OR REPLACE INTO modulos_usuario (username, modulo, activo) VALUES (?, ?, ?)",
                                   (target_user, mod, 1 if act else 0))
                conn.commit()
                st.success(f"✅ Módulos actualizados correctamente para el usuario **{target_user}**.")
                
    with tab_copiar_mod:
        st.markdown(f"#### Copiar Plantilla de Permisos Hacia: **{target_user}**")
        otros_usuarios = [u for u in users_df["username"].unique() if u != target_user]
        if otros_usuarios:
            source_user = st.selectbox("👤 Seleccione el Usuario Origen (de quien se copian los permisos)", otros_usuarios, key="mod_src_user")
            st.info(f"Se copiarán todos los módulos activos/inactivos configurados en **{source_user}** hacia el usuario **{target_user}**.")
            
            if st.button(f"Copiar Permisos a {target_user} 📋"):
                cursor.execute("SELECT modulo, activo FROM modulos_usuario WHERE username=?", (source_user,))
                rows = cursor.fetchall()
                for mod, act in rows:
                    cursor.execute("INSERT OR REPLACE INTO modulos_usuario (username, modulo, activo) VALUES (?, ?, ?)",
                                   (target_user, mod, act))
                conn.commit()
                st.success(f"✅ Permisos copiados exitosamente desde **{source_user}** hacia **{target_user}**.")
                st.rerun()
        else:
            st.warning("No hay otros usuarios registrados para copiar permisos.")
            
    conn.close()

# --- G. MOTOR ML DE AGRUPAMIENTO ---
def render_motor_ml():
    st.markdown("<h2 class='main-header'>🤖 Motor ML de Agrupamiento (Clustering)</h2>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Módulo avanzado no supervisado para investigación epidemiológica y ciencia de datos.</p>", unsafe_allow_html=True)
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM pacientes", conn)
    conn.close()
    
    if len(df) < 5:
        st.warning("⚠️ Se requieren al menos 5 registros de pacientes para ejecutar el agrupamiento por Machine Learning.")
        return
        
    k = st.slider("Número de Clústeres (k)", min_value=2, max_value=6, value=3)
    if st.button("Ejecutar Agrupamiento K-Means 🚀"):
        X = pd.get_dummies(df[["ciclo_vital", "clasificacion_conducta", "factor_asociado", "prioridad_triaje"]])
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
        df["Cluster"] = [f"Perfil {c+1}" for c in kmeans.labels_]
        
        st.success("✅ Modelo entrenado exitosamente.")
        fig_c = px.scatter(df, x="edad", y="probabilidad_riesgo", color="Cluster", hover_data=["consecutivo", "ciudad", "territorio"])
        st.plotly_chart(fig_c, use_container_width=True)

# ------------------------------------------------------------------------------
# 10. NAVEGACIÓN Y CONTROLADOR PRINCIPAL
# ------------------------------------------------------------------------------
def main():
    if not st.session_state.get("logged_in", False):
        render_login()
    else:
        st.sidebar.markdown(f"### ⚓ ÁNCORA SIMAP")
        st.sidebar.info(f"**{st.session_state.user_name}**\n\n**Rol:** {st.session_state.user_role}")
        
        modulos_permitidos = get_modulos_activos_usuario(st.session_state.username)
        
        if not modulos_permitidos:
            st.sidebar.error("No tienes módulos asignados. Contacta a Soporte.")
            if st.sidebar.button("Cerrar Sesión 🚪"):
                st.session_state.logged_in = False
                st.session_state.chat_history = []
                st.rerun()
            return
            
        # Obtener notificaciones de solicitudes pendientes y chat interno
        n_edit, n_pwd, n_chat = get_pending_counts()
        
        # Mapear menú con indicadores/bolitas de notificación
        modulos_menu_display = []
        for mod in modulos_permitidos:
            if mod == "📩 Solicitudes de Edición" and n_edit > 0:
                modulos_menu_display.append(f"📩 Solicitudes de Edición 🔴 ({n_edit})")
            elif mod == "👥 Gestión de Usuarios" and n_pwd > 0:
                modulos_menu_display.append(f"👥 Gestión de Usuarios 🔴 ({n_pwd})")
            elif mod == "💬 Chat Organizacional (Teams)" and n_chat > 0:
                modulos_menu_display.append(f"💬 Chat Organizacional (Teams) 🔴 ({n_chat})")
            else:
                modulos_menu_display.append(mod)
                
        opcion_menu_sel = st.sidebar.radio("Navegación Principal", modulos_menu_display)
        
        st.sidebar.markdown("<hr>", unsafe_allow_html=True)
        if st.sidebar.button("Cerrar Sesión 🚪", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_name = None
            st.session_state.user_role = None
            st.session_state.chat_history = []
            st.rerun()

        if "Captura Manual" in opcion_menu_sel:
            render_captura_manual()
        elif "Dashboard" in opcion_menu_sel:
            render_dashboard()
        elif "ChatBot Áncora Simap" in opcion_menu_sel:
            render_chatbot()
        elif "Chat Organizacional" in opcion_menu_sel:
            render_chat_organizacional()
        elif "Gestión de Usuarios" in opcion_menu_sel:
            render_gestion_usuarios(n_pwd)
        elif "Solicitudes de Edición" in opcion_menu_sel:
            render_solicitudes_edicion(n_edit)
        elif "Gestión de Módulos" in opcion_menu_sel:
            render_gestion_modulos()
        elif "Motor ML" in opcion_menu_sel:
            render_motor_ml()

if __name__ == "__main__":
    main()
