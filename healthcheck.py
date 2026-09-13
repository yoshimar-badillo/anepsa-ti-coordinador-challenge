import urllib.request
import urllib.error
import socket
import time
import logging
import signal
import sys
import json

# 1. Configuración del logging (con timestamp persistente)
# Escribe los eventos en un archivo de texto plano de manera secuencial
logging.basicConfig(
    filename='healthcheck.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class HealthMonitor:
    def __init__(self, url, restart_cmd):
        self.url = url
        self.restart_cmd = restart_cmd
        self.consecutive_fails = 0
        self.running = True
        
        # 2. Manejo de señales de interrupción (Ctrl+C) para cierre limpio
        signal.signal(signal.SIGINT, self.handle_sigint)

    def handle_sigint(self, signum, frame):
        print("\n[INFO] Interrupción (Ctrl+C) detectada. Cerrando limpiamente...")
        logging.info("Monitor detenido manualmente por el usuario (SIGINT).")
        self.running = False
        sys.exit(0)

    def check_status(self):
        try:
            # Petición HTTP con timeout parametrizable de 2 segundos
            req = urllib.request.Request(self.url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.getcode() == 200:
                    self.consecutive_fails = 0
                    logging.info(f"Estado OK (200) para {self.url}")
                    return True
                else:
                    self.consecutive_fails += 1
                    logging.warning(f"Código HTTP no esperado: {response.getcode()} para {self.url}")
                    return False
        except (urllib.error.URLError, socket.timeout) as e:
            self.consecutive_fails += 1
            logging.error(f"Falla de conexión en {self.url}: {e}")
            return False

    def simulate_restart(self):
        logging.info(f"Ejecutando comando de reinicio: {self.restart_cmd}")
        print(f"\n[SISTEMA] -> Simulando reinicio de servicio: {self.restart_cmd}")
        time.sleep(1) # Simula el tiempo que tarda un reinicio

    def send_notification(self):
        # 3. Notificación simulada a Slack/PagerDuty en formato JSON
        payload = {
            "channel": "#alertas-produccion",
            "text": "[CRÍTICO] Servicio caído tras intento de auto-recuperación.",
            "service": self.url,
            "status": "DOWN"
        }
        print("\n--- NOTIFICACIÓN (Slack/PagerDuty) ---")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print("--------------------------------------\n")
        logging.error("Notificación de escalamiento enviada exitosamente.")

    def run(self, interval=30, test_mode=False, max_checks=None):
        checks_done = 0
        while self.running:
            if max_checks and checks_done >= max_checks:
                break
                
            is_ok = self.check_status()
            
            # 4. Lógica de reintentos (3 fallos consecutivos)
            if self.consecutive_fails == 3:
                logging.warning("3 fallos consecutivos detectados. Iniciando auto-recuperación...")
                self.simulate_restart()
                
                # Verificamos si el reinicio arregló el problema
                is_ok_after = self.check_status()
                
                if not is_ok_after:
                    self.send_notification()
                else:
                    logging.info("Auto-recuperación exitosa tras el reinicio.")
                    self.consecutive_fails = 0
                    
            if not test_mode:
                time.sleep(interval)
            
            checks_done += 1


# 5. Bloque de prueba (2 escenarios)
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--real":
        print("Iniciando monitor real (Ctrl+C para salir)...")
        monitor = HealthMonitor("https://httpstat.us/200", "systemctl restart my_app")
        monitor.run(interval=30)
    else:
        # Modo de prueba automatizado usando Mocks
        from unittest.mock import patch
        print("=========================================")
        print(" INICIANDO PRUEBAS DE ESCENARIOS")
        print("=========================================")
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            # ESCENARIO 1: Servicio sano
            print("\n>>> ESCENARIO 1: SERVICIO SANO (2 peticiones HTTP)")
            mock_response = mock_urlopen.return_value.__enter__.return_value
            mock_response.getcode.return_value = 200
            
            monitor_sano = HealthMonitor("http://servicio-sano.local", "systemctl restart api")
            monitor_sano.run(interval=0, test_mode=True, max_checks=2)
            
            # ESCENARIO 2: Servicio caído
            print("\n>>> ESCENARIO 2: SERVICIO CAÍDO (Falla 3 veces -> reinicia -> sigue caído -> notifica)")
            mock_urlopen.side_effect = socket.timeout("Timeout connection")
            
            monitor_caido = HealthMonitor("http://servicio-caido.local", "systemctl restart api")
            monitor_caido.run(interval=0, test_mode=True, max_checks=4)
        
        print("\n[OK] Pruebas finalizadas. Revisa el archivo 'healthcheck.log'.")