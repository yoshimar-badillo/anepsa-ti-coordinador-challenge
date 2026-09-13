import json
import os
import sys
from datetime import datetime, timedelta

DATA_FILE = 'sprint_data.json'

def generate_sample_data():
    """Genera el archivo JSON con 15 tareas simuladas si no existe."""
    today = datetime.now()
    
    #Funciones auxiliares para simular fechas relativas
    def days_ago(days): return (today - timedelta(days=days)).strftime("%Y-%m-%d")
    def days_ahead(days): return (today + timedelta(days=days)).strftime("%Y-%m-%d")

    tasks = [
        #Completadas (Hecho)
        {"id": "DEV-101", "title": "Configurar BD", "assignee": "Ana", "status": "Done", "story_points": 5, "due_date": days_ago(1), "last_updated": days_ago(2)},
        {"id": "DEV-102", "title": "Crear repo", "assignee": "Carlos", "status": "Done", "story_points": 3, "due_date": days_ago(2), "last_updated": days_ago(2)},
        {"id": "DEV-103", "title": "Setup CI/CD", "assignee": "Beatriz", "status": "Done", "story_points": 8, "due_date": days_ahead(1), "last_updated": days_ago(1)},
        {"id": "DEV-104", "title": "Migrar usuarios", "assignee": "Ana", "status": "Done", "story_points": 5, "due_date": days_ago(0), "last_updated": days_ago(1)},
        
        #En progreso (Sanas)
        {"id": "DEV-105", "title": "API de pagos", "assignee": "Carlos", "status": "In Progress", "story_points": 8, "due_date": days_ahead(3), "last_updated": days_ago(1)},
        {"id": "DEV-106", "title": "Frontend Login", "assignee": "Ana", "status": "In Progress", "story_points": 5, "due_date": days_ahead(2), "last_updated": days_ago(0)},
        
        #En riesgo (Vencidas y no completadas)
        {"id": "DEV-107", "title": "Fix bug crítico", "assignee": "Beatriz", "status": "In Progress", "story_points": 3, "due_date": days_ago(1), "last_updated": days_ago(1)},
        {"id": "DEV-108", "title": "Actualizar Nginx", "assignee": "Carlos", "status": "To Do", "story_points": 5, "due_date": days_ago(2), "last_updated": days_ago(4)},
        
        #En riesgo (Sin movimiento en más de 3 dias)
        {"id": "DEV-109", "title": "Documentación API", "assignee": "Ana", "status": "In Progress", "story_points": 3, "due_date": days_ahead(5), "last_updated": days_ago(4)},
        {"id": "DEV-110", "title": "Revisar logs", "assignee": "Beatriz", "status": "To Do", "story_points": 2, "due_date": days_ahead(4), "last_updated": days_ago(5)},
        
        #Por hacer (To do)
        {"id": "DEV-111", "title": "Testing E2E", "assignee": "Carlos", "status": "To Do", "story_points": 5, "due_date": days_ahead(6), "last_updated": days_ago(1)},
        {"id": "DEV-112", "title": "Refactor Auth", "assignee": "Ana", "status": "To Do", "story_points": 8, "due_date": days_ahead(7), "last_updated": days_ago(2)},
        {"id": "DEV-113", "title": "Diseño Base Datos", "assignee": "Beatriz", "status": "To Do", "story_points": 5, "due_date": days_ahead(5), "last_updated": days_ago(1)},
        {"id": "DEV-114", "title": "Implementar caché", "assignee": "Carlos", "status": "To Do", "story_points": 5, "due_date": days_ahead(8), "last_updated": days_ago(1)},
        {"id": "DEV-115", "title": "Auditoría SEO", "assignee": "Beatriz", "status": "To Do", "story_points": 3, "due_date": days_ahead(4), "last_updated": days_ago(2)}
    ]
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=4, ensure_ascii=False)
    print(f"[SISTEMA] Archivo '{DATA_FILE}' generado con éxito.\n")

def process_sprint_data():
    if not os.path.exists(DATA_FILE):
        generate_sample_data()
        
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            tasks = json.load(f)
    except json.JSONDecodeError:
        print("[ERROR CRÍTICO] El archivo JSON está malformado. Favor de verificar la sintaxis.")
        sys.exit(1)
        
    today = datetime.now()
    
    #Métricas globales
    total_sp_committed = 0
    total_sp_completed = 0
    
    #Estructuras para análisis
    at_risk_tasks = []
    workload = {} #Formato: {"Ana": {"assigned": 0, "completed": 0}}

    for task in tasks:
        try:
            t_id = task['id']
            title = task['title']
            assignee = task['assignee']
            status = task['status']
            sp = task['story_points']
            due_date = datetime.strptime(task['due_date'], "%Y-%m-%d")
            last_updated = datetime.strptime(task['last_updated'], "%Y-%m-%d")
        except KeyError as e:
            print(f"[ERROR] Falta el campo obligatorio {e} en una de las tareas. Abortando análisis.")
            sys.exit(1)
        except ValueError:
            print(f"[ERROR] Formato de fecha inválido en la tarea {task.get('id', 'Desconocida')}. Use YYYY-MM-DD.")
            sys.exit(1)

        #1. Cálculos de velocity
        total_sp_committed += sp
        if status == "Done":
            total_sp_completed += sp
            
        #2. Cálculos de carga de trabajo
        if assignee not in workload:
            workload[assignee] = {"assigned": 0, "completed": 0}
        
        workload[assignee]["assigned"] += sp
        if status == "Done":
            workload[assignee]["completed"] += sp

        # 3. Detección de riesgos
        if status != "Done":
            days_inactive = (today - last_updated).days
            is_overdue = today > due_date
            
            reasons = []
            if is_overdue:
                reasons.append("Vencida")
            if days_inactive > 3:
                reasons.append(f"Sin movimiento por {days_inactive} días")
                
            if reasons:
                at_risk_tasks.append(f"- [{t_id}] {title} (Responsable: {assignee}) -> Motivo: {', '.join(reasons)}")

    # Generación de Reporte Ejecutivo
    velocity_percent = (total_sp_completed / total_sp_committed) * 100 if total_sp_committed > 0 else 0
    
    report = [
        "REPORTE EJECUTIVO DE ESTADO DE SPRINT",
        "=====================================",
        f"Fecha de corte: {today.strftime('%Y-%m-%d')}",
        "",
        "1. RESUMEN DE ENTREGA (VELOCITY)",
        "--------------------------------",
        f"Puntos comprometidos: {total_sp_committed} SP",
        f"Puntos completados:   {total_sp_completed} SP",
        f"Progreso del sprint:  {velocity_percent:.1f}%",
        "",
        "2. ALERTAS Y TAREAS EN RIESGO",
        "-----------------------------"
    ]
    
    if at_risk_tasks:
        report.extend(at_risk_tasks)
    else:
        report.append("No se detectan tareas en riesgo en este momento.")
        
    report.extend([
        "",
        "3. ANÁLISIS DE CARGA DE TRABAJO (CAPACIDAD VS ENTREGA)",
        "------------------------------------------------------"
    ])
    
    for member, data in workload.items():
        assigned = data["assigned"]
        completed = data["completed"]
        
        # Lógica sencilla para sobrecarga/subutilización (Umbrales teóricos)
        status_msg = "Equilibrado"
        if assigned > 15:
            status_msg = "ALERTA: Posible sobrecarga (>15 SP)"
        elif assigned < 8:
            status_msg = "ALERTA: Subutilización (<8 SP)"
            
        report.append(f"- {member}: {assigned} SP Asignados | {completed} SP Completados | Estado: {status_msg}")
        
    report.extend([
        "",
        "FIN DEL REPORTE",
        "====================================="
    ])

    print("\n".join(report))

if __name__ == "__main__":
    process_sprint_data()