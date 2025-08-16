import azure.durable_functions as df
from datetime import timedelta
import logging
import json

async def main(context):

    try:
        # Alv todo esto namas porque lo guarda como un json string qpp
        body_string = context._OrchestrationContext__body
        body_dict = json.loads(body_string)
        event_uid = json.loads(body_dict['input'])

        if not event_uid:
            logging.error("No eventUID found in orchestration input.")
            return {"status": "error", "message": "No eventUID provided."}

        # Define las opciones de reintento. El host de Durable Functions
        # manejará los reintentos automáticamente.
        # Primer reintento después de 5 segundos, hasta 3 veces en total.
        retry_options = df.RetryOptions(first_retry_interval_in_milliseconds=5000, max_number_of_attempts=3)
        
        while True:
            # Llama a la actividad con reintentos
            # Si CallLaravelApi falla, el reintento se manejará automáticamente.
            should_continue = await context.call_activity_with_retry(
                'CallLaravelApi', retry_options, event_uid
            )

            if not should_continue:
                # Si la actividad devuelve un valor que evalúa a False,
                # salimos del bucle
                logging.info("Activity returned False. Exiting loop.")
                break

            # Crea un temporizador para esperar 10 segundos antes de la siguiente iteración
            await context.create_timer(
                context.current_utc_datetime + timedelta(seconds=10)
            )

    except Exception as e:
        # Captura cualquier error no manejado y lo registra
        logging.error(f"Orchestrator failed with an unexpected error: {e}")
        return json.dumps({"status": "error", "message": f"Orchestrator failed: {e}"})

    # Retorna un diccionario serializable a JSON para evitar errores
    return json.dumps("a")
