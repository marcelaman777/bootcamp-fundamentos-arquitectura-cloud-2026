import boto3
from boto3.dynamodb.conditions import Key, Attr
import uuid  # para generar identificador único para el contenedor cuando este se inicializa

# ==============================================================================
# LÓGICA DE ESCALABILIDAD (FUERA DEL HANDLER - COLD START MONITORING)
# Esto se ejecuta SOLO cuando AWS Lambda escala horizontalmente y crea un contenedor nuevo.
# Si AWS reutiliza un contenedor existente, este ID se mantendrá idéntico.
# ==============================================================================
id_contenedor = str(uuid.uuid4())[:8]

# Conexión a sesión con las credenciales 
session = boto3.Session(region_name='us-east-1')

# Conexión a dynamo dentro de la sesión
dynamodb = session.resource('dynamodb')

nombre_tabla = 'acme-dydb-sensores'
table = dynamodb.Table(nombre_tabla)

SENSOR_IDS_CONOCIDOS = ['1', '2', '3', '4', '5', '6']   # En un escenario real, la lista vendría de la tabla `sensores` en RDS

def lambda_handler(event, context):
    # Imprimir el ID del contenedor actual en los logs de CloudWatch
    print(f"[ESCALABILIDAD] Procesando solicitud en el Contenedor ID: {id_contenedor}")
    
    resultados = []
    for sensor_id in SENSOR_IDS_CONOCIDOS:
        respuesta = table.query(
            KeyConditionExpression=Key('sensor_id').eq(sensor_id),
            FilterExpression=Attr('lectura_valida').eq(False)
        )
        items = respuesta['Items']
        if items:
            resultados.append({
                'proyecto_id': items[0]['proyecto_id'],
                'suscripcion_id': items[0]['suscripcion_id'],
                'sensor_id': sensor_id,
                'lecturas_invalidas': len(items),
            })

    # Log legible en formato tabla, visible en CloudWatch
    print(f"{'Proyecto':<10}{'Suscripción':<14}{'Sensor':<8}{'Lecturas inválidas':<20}")
    for r in resultados:
        print(f"{r['proyecto_id']:<10}{r['suscripcion_id']:<14}{r['sensor_id']:<8}{r['lecturas_invalidas']:<20}")

    return {
        'statusCode': 200,
        'suscripciones_con_fallas': resultados,
        'metadata_contenedor_id': id_contenedor  # Devuelto al script para facilitar el reporte
    }
