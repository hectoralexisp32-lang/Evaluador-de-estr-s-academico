import streamlit as st
from openai import OpenAI
import json

client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://console.api.groq.com/openai/"
)

MODELO = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """
Eres un asistente empático y profesional especializado en evaluación de estrés 
relacionado con trabajo y estudios universitarios. 

Tu objetivo es:
1. Mantener una conversación natural y empática.
2. Detectar señales de estrés, agotamiento, ansiedad, desmotivación, sobrecarga, 
   falta de control, síntomas físicos y pensamientos de renuncia o abandono.
3. Hacer preguntas de seguimiento inteligentes.
4. Cuando tengas suficiente información, genera un análisis estructurado.

Cuando generes el análisis final, responde ÚNICAMENTE con este JSON 
(sin texto adicional):

{
  "nivel_estres": "bajo | moderado | alto | muy_alto",
  "riesgo_renuncia_trabajo": "bajo | moderado | alto",
  "riesgo_abandono_universidad": "bajo | moderado | alto",
  "señales_detectadas": ["lista", "de", "señales"],
  "resumen": "resumen breve y empático de la situación",
  "recomendaciones": ["recomendación 1", "recomendación 2", "recomendación 3"],
  "urgencia": "ninguna | media | alta"
}

Sé cuidadoso. No diagnostiques enfermedades. Si el riesgo es alto, 
recomienda buscar ayuda profesional.
"""

st.set_page_config(page_title="Evaluador de Estrés", page_icon="🧠", layout="centered")
st.title("🧠 Evaluador de Estrés con IA")
st.caption("Conversación natural para detectar estrés y riesgo de renuncia o abandono universitario")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hola 👋 Puedes contarme cómo te estás sintiendo respecto a tu trabajo o tus estudios. ¿Cómo te has sentido últimamente?"
        }
    ]

if "analisis_final" not in st.session_state:
    st.session_state.analisis_final = None

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Cuéntame cómo te sientes..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                response = client.chat.completions.create(
                    model=MODELO,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] +
                             [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    temperature=0.7,
                )
                respuesta = response.choices[0].message.content
                st.markdown(respuesta)
            except Exception as e:
                st.error(f"Error: {e}")
                respuesta = "Lo siento, hubo un problema. Intenta de nuevo en unos segundos."

    st.session_state.messages.append({"role": "assistant", "content": respuesta})

    if "{" in respuesta and "nivel_estres" in respuesta:
        try:
            inicio = respuesta.find("{")
            fin = respuesta.rfind("}") + 1
            analisis = json.loads(respuesta[inicio:fin])
            st.session_state.analisis_final = analisis
        except:
            pass

if st.session_state.analisis_final:
    st.divider()
    st.subheader("📊 Resultado del análisis")

    a = st.session_state.analisis_final

    col1, col2, col3 = st.columns(3)
    col1.metric("Nivel de estrés", a.get("nivel_estres", "—").replace("_", " ").upper())
    col2.metric("Riesgo renuncia trabajo", a.get("riesgo_renuncia_trabajo", "—").upper())
    col3.metric("Riesgo abandono universidad", a.get("riesgo_abandono_universidad", "—").upper())

    st.markdown("**Resumen:**")
    st.info(a.get("resumen", ""))

    if a.get("señales_detectadas"):
        st.markdown("**Señales detectadas:**")
        for s in a["señales_detectadas"]:
            st.write(f"• {s}")

    if a.get("recomendaciones"):
        st.markdown("**Recomendaciones:**")
        for r in a["recomendaciones"]:
            st.write(f"• {r}")

    if a.get("urgencia") == "alta":
        st.error("⚠️ Se recomienda buscar apoyo profesional lo antes posible.")
    elif a.get("urgencia") == "media":
        st.warning("Es aconsejable hablar con alguien de confianza o un profesional.")

if st.button("🔄 Empezar nueva evaluación"):
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hola 👋 ¿Cómo te has estado sintiendo últimamente con el trabajo o los estudios?"
        }
    ]
    st.session_state.analisis_final = None
    st.rerun()

st.markdown("---")
st.caption("Este es un screening orientativo. No sustituye la evaluación de un profesional de la salud mental.")