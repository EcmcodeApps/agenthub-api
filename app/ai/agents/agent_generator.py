"""
Generador de equipos de agentes IA basado en la industria y objetivo de la misión.
En modo mock retorna agentes predefinidos; con API real usará LLM para generarlos.
"""
from typing import List
from app.schemas.agent import AgentSuggestion
from app.core.config import get_settings

AGENT_TEMPLATES = {
    "Comercio minorista": [
        AgentSuggestion(
            name="Agente de Ventas",
            role="Analista de ventas",
            goal="Analizar datos de ventas, identificar tendencias y productos top",
            tools=["document_search", "spreadsheet_analyzer"],
            modelRecommendation="deepseek-chat",
            prompt="Eres un analista experto en comercio minorista. Analiza los datos de ventas proporcionados e identifica patrones, productos más vendidos, picos de demanda y oportunidades de mejora.",
            order=1,
            outputType="analysis_report",
        ),
        AgentSuggestion(
            name="Agente de Inventario",
            role="Gestor de inventario",
            goal="Detectar productos de baja rotación y oportunidades de optimización",
            tools=["document_search", "spreadsheet_analyzer"],
            modelRecommendation="deepseek-chat",
            prompt="Eres un experto en gestión de inventario. Analiza el stock actual, identifica productos de baja rotación, exceso de inventario y recomienda acciones concretas.",
            order=2,
            outputType="inventory_report",
        ),
        AgentSuggestion(
            name="Agente de Marketing",
            role="Estratega de marketing",
            goal="Crear campañas y contenido basado en datos de ventas",
            tools=["web_search", "document_search"],
            modelRecommendation="mistral-small",
            prompt="Eres un estratega de marketing digital para comercio minorista. Basándote en los análisis de ventas e inventario, crea estrategias de campaña efectivas.",
            order=3,
            outputType="marketing_plan",
        ),
        AgentSuggestion(
            name="Agente Redactor",
            role="Redactor de informes ejecutivos",
            goal="Consolidar hallazgos y redactar el informe final",
            tools=["document_search"],
            modelRecommendation="mistral-large",
            prompt="Eres un redactor ejecutivo. Consolida todos los análisis anteriores en un informe estructurado, claro y con recomendaciones accionables para la gerencia.",
            order=4,
            outputType="executive_report",
        ),
    ],
    "Restaurantes": [
        AgentSuggestion(
            name="Agente de Menú",
            role="Analista de menú y precios",
            goal="Analizar rentabilidad de platos y optimizar la carta",
            tools=["document_search", "spreadsheet_analyzer"],
            modelRecommendation="deepseek-chat",
            prompt="Eres un consultor experto en restaurantes. Analiza la rentabilidad de cada plato, costos de ingredientes y sugiere optimizaciones de menú y precios.",
            order=1,
            outputType="menu_analysis",
        ),
        AgentSuggestion(
            name="Agente de Operaciones",
            role="Analista de operaciones",
            goal="Optimizar procesos y reducir desperdicios",
            tools=["document_search"],
            modelRecommendation="deepseek-chat",
            prompt="Eres un experto en operaciones de restaurante. Identifica ineficiencias, desperdicios y oportunidades para mejorar la operación diaria.",
            order=2,
            outputType="operations_report",
        ),
        AgentSuggestion(
            name="Agente Redactor",
            role="Redactor de informes",
            goal="Generar informe consolidado con recomendaciones",
            tools=[],
            modelRecommendation="mistral-large",
            prompt="Consolida todos los análisis del restaurante en un informe ejecutivo con recomendaciones claras y priorizadas.",
            order=3,
            outputType="executive_report",
        ),
    ],
    "default": [
        AgentSuggestion(
            name="Agente Investigador",
            role="Investigador principal",
            goal="Recopilar información relevante sobre el tema de la misión",
            tools=["web_search", "wikipedia", "document_search"],
            modelRecommendation="deepseek-chat",
            prompt="Eres un investigador experto. Recopila y analiza toda la información disponible sobre el tema de la misión, identificando datos clave, tendencias y contexto relevante.",
            order=1,
            outputType="research_notes",
        ),
        AgentSuggestion(
            name="Agente Analista",
            role="Analista de datos",
            goal="Analizar documentos e información recopilada",
            tools=["document_search", "spreadsheet_analyzer"],
            modelRecommendation="deepseek-chat",
            prompt="Eres un analista de datos. Procesa toda la información recopilada, identifica patrones, hallazgos clave y extrae insights accionables.",
            order=2,
            outputType="analysis_report",
        ),
        AgentSuggestion(
            name="Agente Redactor",
            role="Redactor ejecutivo",
            goal="Redactar el informe final consolidado",
            tools=[],
            modelRecommendation="mistral-large",
            prompt="Eres un redactor ejecutivo experto. Toma todos los análisis e investigaciones y redacta un informe profesional, claro y con recomendaciones concretas.",
            order=3,
            outputType="executive_report",
        ),
    ],
}


def generate_agent_team(industry: str, objective: str, depth: str) -> List[AgentSuggestion]:
    """
    Genera un equipo de agentes sugerido para la misión.
    En modo mock usa plantillas predefinidas por industria.
    """
    settings = get_settings()

    templates = AGENT_TEMPLATES.get(industry, AGENT_TEMPLATES["default"])

    # En modo deep, agregar agente revisor
    if depth == "deep":
        templates = list(templates) + [
            AgentSuggestion(
                name="Agente Revisor",
                role="Revisor de calidad",
                goal="Revisar y validar la calidad del informe final",
                tools=[],
                modelRecommendation="mistral-large",
                prompt="Eres un revisor de calidad experto. Revisa el informe generado, verifica coherencia, identifica posibles errores o vacíos de información y sugiere mejoras.",
                order=len(templates) + 1,
                outputType="quality_review",
            )
        ]

    return templates
