import boto3
import base64
import os
import json
from email.parser import BytesParser
from email.policy import default

def lambda_handler(event, context):

    # Entrada
    headers = {
        k.lower(): v for k, v in event.get('headers', {}).items()
    }

    content_type = headers.get('content-type')

    if not content_type:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Falta Content-Type'})
        }

    body = event.get('body', '')

    if event.get('isBase64Encoded', False):
        contenido = base64.b64decode(body)
    else:
        contenido = body.encode('utf-8')

    # Procesar multipart/form-data
    mensaje = BytesParser(policy=default).parsebytes(
        b'Content-Type: ' + content_type.encode() +
        b'\r\nMIME-Version: 1.0\r\n\r\n' + contenido
    )

    bucket = ''
    directorio = ''
    archivo = ''
    contenido_archivo = None
    tipo_archivo = 'application/octet-stream'

    if not mensaje.is_multipart():
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Formato multipart/form-data requerido'})
        }

    for parte in mensaje.iter_parts():

        nombre = parte.get_param('name', header='content-disposition')

        if nombre == 'bucket':
            bucket = parte.get_content().strip()

        elif nombre == 'directorio':
            directorio = parte.get_content().strip()

        elif nombre == 'archivo':
            filename = parte.get_filename()

            if filename:
                archivo = os.path.basename(filename.replace('\\', '/'))
                contenido_archivo = parte.get_payload(decode=True)
                tipo_archivo = parte.get_content_type()

    # Validar entrada
    if not bucket or not directorio or not archivo or contenido_archivo is None:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Faltan datos o archivo'})
        }

    # Proceso
    s3 = boto3.client('s3')

    s3.put_object(
        Bucket=bucket,
        Key=directorio.strip('/') + '/' + archivo,
        Body=contenido_archivo,
        ContentType=tipo_archivo
    )

    return {
        'statusCode': 200,
        'body': json.dumps({
            'mensaje': 'Archivo subido correctamente',
            'bucket': bucket,
            'directorio': directorio,
            'archivo': archivo
        })
    }