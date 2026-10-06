# MinerTrack - Plan de implementación real

## 1. Objetivo del sistema

Implementar una solución de escritorio en Python para automatizar el pesaje vehicular, la identificación automática de unidades y el control de inventario en la caseta de pesaje de Corporación ATSA.

## 2. Requisitos extraídos del anteproyecto

- Integración en tiempo real con la báscula camionera.
- Lectura automática de peso bruto, tara y cálculo de peso neto.
- Interfaz de escritorio con validaciones para operación en la caseta.
- Registro de entradas, salidas y traslados internos de material.
- Base de datos MongoDB para trazabilidad e historial.
- Reconocimiento automático de vehículos mediante visión artificial.
- Pruebas reales con flujo de operación en sitio.

## 3. Arquitectura recomendada

### Capa de hardware
- Indicador de báscula con comunicación serial RS232/RS485 o TCP/IP.
- Cámara web o cámara IP para lectura de placas.
- Equipo de cómputo industrial con Windows o Linux.

### Capa de software
- Python 3.x
- Tkinter para la interfaz de escritorio
- `pyserial` o sockets para la comunicación con la báscula
- OpenCV + EasyOCR para OCR/visón artificial
- MongoDB para persistencia

### Flujo de datos
1. La báscula envía la trama de peso.
2. El sistema procesa el peso y calcula bruto/tara/neto.
3. La cámara identifica la placa o el vehículo.
4. El operador valida el movimiento.
5. El registro se guarda en MongoDB.
6. El sistema genera trazabilidad e inventario disponible.

## 4. Fases de ejecución

### Fase 1. Levantamiento técnico real
- Confirmar el modelo exacto de la báscula.
- Validar el puerto, velocidad de baudios y protocolo del indicador.
- Definir si la conexión será serial o TCP/IP.
- Verificar la ubicación física y potencia de la cámara.

### Fase 2. Comunicación estable con la báscula
- Ajustar el parser para la trama real de la báscula.
- Implementar reconexión automática.
- Añadir validación de integridad de tramas.
- Guardar el último peso válido y alertar si el valor es nulo.

### Fase 3. Interfaz operativa
- Mejorar los formularios con flujo real de entrada/salida.
- Añadir login y perfiles de operador/supervisor.
- Bloquear edición manual del peso neto.
- Agregar mensajes claros de validación y estado del equipo.

### Fase 4. OCR y trazabilidad vehicular
- Validar la cámara real de la planta.
- Ajustar EasyOCR para placas en condiciones reales.
- Implementar fallback manual cuando el OCR falle.
- Asociar cada movimiento con placa, transportista y material.

### Fase 5. Persistencia y consultas
- Diseñar colecciones para movimientos, vehículos, inventario y usuarios.
- Crear índices por placa, fecha, material y folio.
- Generar reportes de entradas, salidas y saldo por material.

### Fase 6. Pruebas y puesta en producción
- Pruebas en ambiente real con camiones.
- Prueba de estrés con varios movimientos consecutivos.
- Validación de trazabilidad y consistencia de inventario.
- Capacitación al personal operativo.

## 5. Riesgos y mitigación

- Riesgo: la cámara no reconoce placas en condiciones reales.
  Mitigación: fallback manual + mejora de iluminación.

- Riesgo: la báscula usa un protocolo distinto al esperado.
  Mitigación: capturar tramas reales y adaptar el parser.

- Riesgo: pérdida de conexión al MongoDB.
  Mitigación: cola de transacciones y mensajes de aviso.

- Riesgo: la aplicación queda frágil en producción.
  Mitigación: logs, manejo de excepciones y validación de estado.

## 6. Siguientes tareas recomendadas para continuar

1. Crear un archivo de configuración global (`config.json` o `.env`).
2. Separar la lógica de red, OCR y base de datos en módulos más desacoplados.
3. Añadir registro de movimientos con folio único y saldo de inventario.
4. Implementar reportes y dashboard de inventario.
5. Validar la solución en la zona real de carga.

## 7. Evidencia actual del proyecto

La base del proyecto ya se encuentra validada en su arranque básico:
- Importación de módulos principales: OK
- Báscula simulada: OK
- Conexión local a MongoDB: OK

Esto indica que el proyecto ya tiene una base funcional sobre la cual continuar con la implementación real.
