import pymongo

try:
    client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
    # Probar conexión
    client.server_info()
    
    db = client['MinerTrackDB']
    movimientos = list(db['movimientos'].find())
    
    print("\n==============================================")
    print("      REGISTROS GUARDADOS EN MONGODB          ")
    print("==============================================")
    
    if len(movimientos) == 0:
        print("La base de datos existe pero aún no tiene movimientos guardados.")
    else:
        for i, m in enumerate(movimientos):
            print(f"[{i+1}] Placas: {m.get('placas')} | Material: {m.get('material')} | Neto: {m.get('peso_neto_kg')} kg | Fecha: {m.get('fecha_hora')}")
            
    print("==============================================")
    print(f"Total de registros encontrados: {len(movimientos)}\n")
    
except Exception as e:
    print(f"\n[ERROR] No me pude conectar a MongoDB en tu PC. Verifica que esté instalado y corriendo.\nDetalle: {e}\n")
