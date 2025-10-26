@echo off
echo ======================================
echo Dashboard en Tiempo Real - AutoAgent
echo ======================================
echo.
echo Iniciando dashboard en segundo plano...
start /B streamlit run dashboard_streamlit.py

echo Esperando 5 segundos para que el dashboard inicie...
timeout /t 5 /nobreak > nul

echo.
echo Dashboard disponible en: http://localhost:8501
echo.
echo Ejecutando tarea de prueba...
echo.

python coreee/sistema_agentes_supervisor_coder.py -q "Crea una herramienta simple que sume dos numeros y pruebala con 5 y 3"

echo.
echo ======================================
echo Tarea completada!
echo Revisa el dashboard para ver los eventos
echo ======================================
pause
