# app/services/ai/prompts.py
from typing import Dict, Any, Optional

def get_generation_prompt(entity_type: str, context: Dict[str, Any], action: str = "generate") -> str:
    prompts = {
        "project": _project_generation_prompt,
        "study_plan": _study_plan_generation_prompt,
        "course": _course_generation_prompt,
        "module": _module_generation_prompt,
        "unit": _unit_generation_prompt,
        "task": _task_generation_prompt,
        "instructional_design": _instructional_design_generation_prompt,
        "author_content": _author_content_generation_prompt,
        "learning_activity": _learning_activity_generation_prompt,
    }
    
    prompt_func = prompts.get(entity_type, _default_generation_prompt)
    return prompt_func(context, action)

def get_analysis_prompt(analysis_type: str, content: str, context: Optional[Dict[str, Any]] = None) -> str:
    prompts = {
        "coherence": f"""Analiza la coherencia pedagógica del siguiente contenido:

{content}

Contexto adicional: {context if context else 'No proporcionado'}

Responde en JSON con:
{{
    "coherente": true/false,
    "nivel_coherencia": "alto/medio/bajo",
    "problemas_encontrados": ["problema1", "problema2"],
    "sugerencias": ["sugerencia1", "sugerencia2"]
}}""",
        
        "quality": f"""Analiza la calidad del siguiente contenido educativo:

{content}

Contexto adicional: {context if context else 'No proporcionado'}

Responde en JSON con:
{{
    "calidad_total": "alta/media/baja",
    "fortalezas": ["fortaleza1"],
    "debilidades": ["debilidad1"],
    "mejoras_sugeridas": ["mejora1"]
}}""",
        
        "accessibility": f"""Analiza la accesibilidad del siguiente contenido:

{content}

Responde en JSON con:
{{
    "es_accesible": true/false,
    "barreras_encontradas": ["barrera1"],
    "sugerencias_mejora": ["sugerencia1"],
    "cumplimiento_wcag": "completo/parcial/ninguno"
}}""",
        
        "learning_objectives": f"""Analiza los siguientes objetivos de aprendizaje:

{content}

Contexto: {context if context else 'No proporcionado'}

Responde en JSON con:
{{
    "son_apropiados": true/false,
    "son_medibles": true/false,
    "son_alcanzables": true/false,
    "problemas": ["problema1"],
    "mejoras": ["mejora1"]
}}""",
    }
    
    return prompts.get(analysis_type, prompts["quality"])

def get_improvement_prompt(content: str, entity_type: str, improvement_type: str = "general") -> str:
    base = f"""Mejora el siguiente contenido de tipo "{entity_type}" con enfoque "{improvement_type}":

Contenido original:
{content}

"""
    
    improvements = {
        "grammar": base + """Corrige errores gramaticales y ortográficos. 
Responde en JSON:
{"contenido_mejorado": "...", "correcciones": ["corrección1"]}""",

        "clarity": base + """Mejora la claridad y comprensión del texto.
Responde en JSON:
{"contenido_mejorado": "...", "cambios_realizados": ["cambio1"]}""",

        "pedagogical": base + """Mejora desde el punto de vista pedagógico.
Responde en JSON:
{"contenido_mejorado": "...", "mejoras_pedagogicas": ["mejora1"]}""",

        "engagement": base + """Mejora el engagement y motivación del aprendiz.
Responde en JSON:
{"contenido_mejorado": "...", "estrategias_engagement": ["estrategia1"]}""",

        "general": base + """Mejora el contenido de forma general.
Responde en JSON:
{"contenido_mejorado": "...", "mejoras": ["mejora1"]}""",
    }
    
    return improvements.get(improvement_type, improvements["general"])

# === PROMPTS ESPECÍFICOS POR ENTIDAD ===

def _project_generation_prompt(context: Dict[str, Any], action: str) -> str:
    if action == "description":
        return f"""Genera una descripción profesional para un proyecto educativo con estas características:

Nombre: {context.get('name', 'N/A')}
Tipo: {context.get('tipo_proyecto', 'N/A')}
Idioma: {context.get('idioma', 'Español')}
Público objetivo: {context.get('publico_objetivo', 'No especificado')}

Responde en JSON:
{{"descripcion": "..."}}"""

    elif action == "suggest_target":
        return f"""Sugiere público objetivo apropiado para un proyecto educativo:

Nombre del proyecto: {context.get('name', 'N/A')}
Tipo de proyecto: {context.get('tipo_proyecto', 'N/A')}
Duración en horas: {context.get('horas_curso', 'No especificado')}

Responde en JSON:
{{
    "publico_sugerido": ["perfil1", "perfil2"],
    "justificacion": "..."
}}"""

    else:
        return f"""Analiza el siguiente proyecto y sugiere mejoras:

{context}

Responde en JSON:
{{
    "analisis": "...",
    "sugerencias": ["sugerencia1"],
    "viabilidad": "alta/media/baja"
}}"""

def _study_plan_generation_prompt(context: Dict[str, Any], action: str) -> str:
    if action == "general_objective":
        return f"""Genera un objetivo general para un plan de estudio:

Nombre: {context.get('name', 'N/A')}
Modalidad: {context.get('modalidad', 'N/A')}
Duración: {context.get('duracion', 'N/A')} horas

Responde en JSON:
{{"objetivo_general": "..."}}"""

    elif action == "specific_objectives":
        return f"""Genera 5 objetivos específicos basados en el objetivo general:

Objetivo general: {context.get('objetivo_general', 'N/A')}

Responde en JSON:
{{
    "objetivos_especificos": [
        {{"id": 1, "objetivo": "...", "verbo": "identificar", "nivel_bloom": "comprensión"}}
    ]
}}"""

    elif action == "learning_outcomes":
        return f"""Genera resultados de aprendizaje para un plan de estudio:

Objetivos específicos: {context.get('objetivos', 'N/A')}
Modalidad: {context.get('modalidad', 'N/A')}

Responde en JSON:
{{"resultados_aprendizaje": ["resultado1", "resultado2"]}}"""

    else:
        return f"""Genera estructura de plan de estudio:

{context}

Responde en JSON con estructura completa."""

def _course_generation_prompt(context: Dict[str, Any], action: str) -> str:
    if action == "description":
        return f"""Genera una descripción para un curso:

Nombre: {context.get('name', 'N/A')}
Módulo: {context.get('module_name', 'N/A')}
Duración: {context.get('horas', 'N/A')} horas

Responde en JSON:
{{"descripcion": "..."}}"""

    elif action == "syllabus":
        return f"""Genera un temario/syllabus para un curso:

Nombre: {context.get('name', 'N/A')}
Descripción: {context.get('description', 'N/A')}
Duración: {context.get('horas', 'N/A')} horas

Responde en JSON:
{{
    "unidades": [
        {{"nombre": "Unidad 1", "temas": ["tema1"], "duracion_horas": 4}}
    ]
}}"""

    else:
        return f"""Mejora el contenido del curso:

{context}

Responde en JSON."""

def _module_generation_prompt(context: Dict[str, Any], action: str) -> str:
    if action == "keywords":
        return f"""Genera palabras clave para un módulo:

Nombre: {context.get('name', 'N/A')}
Curso: {context.get('course_name', 'N/A')}

Responde en JSON:
{{"palabras_clave": ["palabra1", "palabra2"]}}"""

    elif action == "structure":
        return f"""Sugiere estructura de unidades para un módulo:

Módulo: {context.get('name', 'N/A')}
Curso: {context.get('course_name', 'N/A')}
Duración: {context.get('horas', 'N/A')} horas

Responde en JSON:
{{
    "unidades_sugeridas": [
        {{"nombre": "Unidad 1", "descripcion": "...", "duracion_horas": 4}}
    ]
}}"""

    else:
        return f"""Genera contenido para módulo:

{context}

Responde en JSON."""

def _unit_generation_prompt(context: Dict[str, Any], action: str) -> str:
    if action == "content":
        return f"""Genera contenido para una unidad:

Nombre: {context.get('name', 'N/A')}
Módulo: {context.get('module_name', 'N/A')}
Objetivos: {context.get('objectives', 'N/A')}

Responde en JSON:
{{
    "contenido": "...",
    "puntos_clave": ["punto1"]
}}"""

    elif action == "glossary":
        return f"""Genera glosario de términos para:

Unidad: {context.get('name', 'N/A')}
Contenido: {context.get('content', 'N/A')}

Responde en JSON:
{{
    "terminos": [
        {{"termino": "...", "definicion": "..."}}
    ]
}}"""

    else:
        return f"""Mejora contenido de unidad:

{context}

Responde en JSON."""

def _task_generation_prompt(context: Dict[str, Any], action: str) -> str:
    if action == "subtasks":
        return f"""Sugiere subtareas para una tarea:

Título: {context.get('titulo', 'N/A')}
Descripción: {context.get('descripcion', 'N/A')}
Fecha entrega: {context.get('fecha_entrega', 'N/A')}

Responde en JSON:
{{
    "subtareas": [
        {{"titulo": "Subtarea 1", "descripcion": "...", "duracion_estimada": "1 hora"}}
    ]
}}"""

    elif action == "time_estimate":
        return f"""Estima el tiempo necesario para completar:

Título: {context.get('titulo', 'N/A')}
Descripción: {context.get('descripcion', 'N/A')}
Complejidad: {context.get('complejidad', 'media')}

Responde en JSON:
{{
    "tiempo_estimado_horas": 0,
    "desglose": {{"analisis": 1, "desarrollo": 2, "revision": 1}},
    "factores_considerados": ["factor1"]
}}"""

    else:
        return f"""Mejora descripción de tarea:

{context}

Responde en JSON."""

def _instructional_design_generation_prompt(context: Dict[str, Any], action: str) -> str:
    if action == "objective":
        return f"""Genera un objetivo instruccional para:

Curso: {context.get('course_name', 'N/A')}
Módulo: {context.get('module_name', 'N/A')}
Mensaje clave: {context.get('mensaje_clave', 'N/A')}

Responde en JSON:
{{
    "objetivo_instruccional": "...",
    "verbo_bloom": "identificar",
    "nivel_bloom": "comprensión"
}}"""

    elif action == "activities":
        return f"""Sugiere actividades de aprendizaje para:

Objetivo: {context.get('objetivo', 'N/A')}
Público: {context.get('publico', 'N/A')}
Duración: {context.get('duracion', 'N/A')}

Responde en JSON:
{{
    "actividades": [
        {{"tipo": "actividad", "descripcion": "...", "duracion": "30 min"}}
    ]
}}"""

    elif action == "validate":
        return f"""Valida la coherencia del diseño instruccional:

{json.dumps(context, indent=2, ensure_ascii=False)}

Responde en JSON:
{{
    "es_coherente": true/false,
    "problemas": ["problema1"],
    "sugerencias": ["sugerencia1"]
}}"""

    else:
        return f"""Mejora diseño instruccional:

{context}

Responde en JSON."""

def _author_content_generation_prompt(context: Dict[str, Any], action: str) -> str:
    if action == "structure":
        return f"""Sugiere estructura/índice para:

Curso: {context.get('course_name', 'N/A')}
Módulo: {context.get('module_name', 'N/A')}
Horas: {context.get('horas_curso', 'N/A')}

Responde en JSON:
{{
    "indice": [
        {{"capitulo": "1. Introducción", "secciones": ["1.1", "1.2"]}}
    ]
}}"""

    elif action == "glossary":
        return f"""Genera glosario para:

Contenido: {context.get('contenido', 'N/A')}

Responde en JSON:
{{
    "terminos": [
        {{"termino": "...", "definicion": "..."}}
    ]
}}"""

    elif action == "improve":
        return f"""Mejora el siguiente contenido educativo:

{context.get('contenido', 'N/A')}

Responde en JSON:
{{
    "contenido_mejorado": "...",
    "mejoras": ["mejora1"]
}}"""

    else:
        return f"""Genera contenido para autor:

{context}

Responde en JSON."""

def _learning_activity_generation_prompt(context: Dict[str, Any], action: str) -> str:
    if action == "suggest":
        return f"""Sugiere tipo de actividad de aprendizaje para:

Unidad: {context.get('unit_name', 'N/A')}
Objetivo: {context.get('objective', 'N/A')}

Responde en JSON:
{{
    "tipo_actividad": "...",
    "descripcion": "...",
    "instrucciones": ["instruccion1"],
    "recursos_necesarios": ["recurso1"],
    "criterios_exito": ["criterio1"]
}}"""

    else:
        return f"""Mejora actividad de aprendizaje:

{context}

Responde en JSON."""

def _default_generation_prompt(context: Dict[str, Any], action: str) -> str:
    return f"""Genera contenido educativo basado en:

{json.dumps(context, indent=2, ensure_ascii=False)}

Responde en JSON válido."""
