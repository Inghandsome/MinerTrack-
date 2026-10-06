import pymongo
from datetime import datetime
import json
from bson import json_util

class GestorBaseDatos:
    def __init__(self, uri="mongodb://localhost:27017/", nombre_bd="MinerTrackDB"):
        self.uri = uri
        self.nombre_bd = nombre_bd
        self.cliente = None
        self.bd = None
        
    def conectar(self):
        try:
            # serverSelectionTimeoutMS bajo para que no se quede colgado si MongoDB no está instalado
            self.cliente = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=2000)
            # Forzamos una consulta para verificar la conexión real
            self.cliente.server_info()
            self.bd = self.cliente[self.nombre_bd]
            print(f"[BD] Conectado exitosamente a MongoDB en {self.uri}")
            return True
        except Exception as e:
            print(f"[BD ERROR] No se pudo conectar a MongoDB (¿Está iniciado el servicio?): {e}")
            self.cliente = None
            self.bd = None
            return False

    def guardar_movimiento(self, placas, material, peso_bruto, peso_tara, peso_neto, chofer="", tipo_movimiento="SALIDA", operador=""):
        if self.bd is None:
            print("[BD ERROR] No hay conexión activa a MongoDB.")
            return False
            
        coleccion = self.bd["movimientos"]
        
        # Generar Folio consecutivo (Ej. 0003066)
        try:
            ultimo = coleccion.find_one(sort=[("folio", -1)])
            if ultimo and "folio" in ultimo:
                nuevo_folio = str(int(ultimo["folio"]) + 1).zfill(7)
            else:
                nuevo_folio = "0000001"
        except Exception:
            nuevo_folio = "0000001"

        # Estructura del documento (JSON) a guardar
        documento = {
            "folio": nuevo_folio,
            "placas": placas.upper(),
            "chofer": chofer.upper(),
            "material": material,
            "tipo_movimiento": tipo_movimiento,
            "peso_bruto_kg": round(peso_bruto, 2),
            "peso_tara_kg": round(peso_tara, 2),
            "peso_neto_kg": round(peso_neto, 2),
            "operador": operador,
            "fecha_hora": datetime.now(),
            "estado": "Completado"
        }
        
        try:
            resultado = coleccion.insert_one(documento)
            print(f"[BD INFO] Movimiento guardado. ID: {resultado.inserted_id}")
            return True
        except Exception as e:
            print(f"[BD ERROR] Fallo al insertar el documento: {e}")
            return False

    def obtener_movimientos(self, limite=200):
        """Obtiene los últimos movimientos ordenados por fecha (más recientes primero)."""
        if self.bd is None:
            return []
        try:
            coleccion = self.bd["movimientos"]
            cursor = coleccion.find().sort("fecha_hora", -1).limit(limite)
            return list(cursor)
        except Exception as e:
            print(f"[BD ERROR] Fallo al consultar movimientos: {e}")
            return []

    def buscar_por_placa(self, placa):
        """Busca movimientos que contengan el texto de la placa (búsqueda parcial)."""
        if self.bd is None:
            return []
        try:
            coleccion = self.bd["movimientos"]
            filtro = {"placas": {"$regex": placa.upper(), "$options": "i"}}
            cursor = coleccion.find(filtro).sort("fecha_hora", -1)
            return list(cursor)
        except Exception as e:
            print(f"[BD ERROR] Fallo al buscar por placa: {e}")
            return []

    def obtener_movimientos_hoy(self):
        """Obtiene solo los movimientos registrados hoy."""
        if self.bd is None:
            return []
        try:
            from datetime import time as dtime
            hoy_inicio = datetime.combine(datetime.now().date(), dtime.min)
            hoy_fin = datetime.combine(datetime.now().date(), dtime.max)
            coleccion = self.bd["movimientos"]
            filtro = {"fecha_hora": {"$gte": hoy_inicio, "$lte": hoy_fin}}
            cursor = coleccion.find(filtro).sort("fecha_hora", -1)
            return list(cursor)
        except Exception as e:
            print(f"[BD ERROR] Fallo al consultar movimientos de hoy: {e}")
            return []

    def eliminar_movimiento(self, id_movimiento):
        """Elimina un movimiento por su ID de MongoDB."""
        if self.bd is None:
            return False
        try:
            from bson import ObjectId
            coleccion = self.bd["movimientos"]
            resultado = coleccion.delete_one({"_id": ObjectId(id_movimiento)})
            return resultado.deleted_count > 0
        except Exception as e:
            print(f"[BD ERROR] Fallo al eliminar movimiento: {e}")
            return False

    # ═══════════════════════════════════════════════════
    #  MÉTODOS PARA CATÁLOGO DE CAMIONES Y TARAS
    # ═══════════════════════════════════════════════════
    
    def agregar_camion(self, placa, chofer, tara_kg, id_interno):
        """Agrega o actualiza un camión en el catálogo fijo."""
        if self.bd is None: return False
        try:
            coleccion = self.bd["camiones"]
            # Usamos update_one con upsert=True para que si la placa ya existe, solo la actualice
            filtro = {"placa": placa.upper().strip()}
            datos = {
                "$set": {
                    "placa": placa.upper().strip(),
                    "chofer": chofer.upper().strip(),
                    "tara_kg": float(tara_kg),
                    "id_interno": str(id_interno).strip(),
                    "fecha_actualizacion": datetime.now()
                }
            }
            coleccion.update_one(filtro, datos, upsert=True)
            return True
        except Exception as e:
            print(f"[BD ERROR] Fallo al agregar/actualizar camión: {e}")
            return False

    def obtener_camiones(self):
        """Devuelve la lista completa de camiones registrados."""
        if self.bd is None: return []
        try:
            coleccion = self.bd["camiones"]
            # Ordenamos por ID interno para mantener el orden de su lista impresa
            cursor = coleccion.find().sort("id_interno", 1)
            return list(cursor)
        except Exception as e:
            print(f"[BD ERROR] Fallo al obtener camiones: {e}")
            return []

    def buscar_camion_por_placa(self, placa):
        """Busca un camión exacto por su placa. Retorna el diccionario o None."""
        if self.bd is None or not placa: return None
        try:
            coleccion = self.bd["camiones"]
            # Búsqueda exacta (el OCR debe coincidir)
            return coleccion.find_one({"placa": placa.upper().strip()})
        except Exception as e:
            print(f"[BD ERROR] Fallo al buscar camión por placa: {e}")
            return None

    def eliminar_camion(self, placa):
        """Elimina un camión del catálogo por su placa."""
        if self.bd is None: return False
        try:
            coleccion = self.bd["camiones"]
            resultado = coleccion.delete_one({"placa": placa.upper().strip()})
            return resultado.deleted_count > 0
        except Exception as e:
            print(f"[BD ERROR] Fallo al eliminar camión: {e}")
            return False

    def exportar_respaldo(self, ruta_archivo):
        """Exporta todos los movimientos a un archivo JSON."""
        if self.bd is None:
            return False, "Base de datos no conectada."
        try:
            movimientos = list(self.bd["movimientos"].find())
            # Convertimos a JSON usando json_util para manejar los tipos de BSON (ObjectId, datetime, etc)
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(json_util.dumps(movimientos, indent=4))
            return True, f"Respaldo exportado exitosamente con {len(movimientos)} registros."
        except Exception as e:
            return False, str(e)

    def importar_respaldo(self, ruta_archivo):
        """Importa movimientos desde un archivo JSON (limpia la BD actual)."""
        if self.bd is None:
            return False, "Base de datos no conectada."
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                datos = json_util.loads(f.read())
            
            if not datos:
                return False, "El archivo de respaldo está vacío."
                
            coleccion = self.bd["movimientos"]
            # Limpiamos la colección actual
            coleccion.delete_many({})
            # Insertamos los datos importados
            coleccion.insert_many(datos)
            return True, f"Respaldo importado exitosamente. Se cargaron {len(datos)} registros."
        except Exception as e:
            return False, str(e)
