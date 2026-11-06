# Despliegue público de GameSentiment AI

Fecha: 30 de octubre de 2026.

- Aplicación: https://gamesentiment-ai.onrender.com/
- Repositorio: https://github.com/BrianEspino/gamesentiment-ai
- Servicio Render: `srv-dbi9iroae00c73bjj11g`
- Configuración: Docker, región Oregon, rama `main`, contexto `.`, Dockerfile `./Dockerfile`, variable `PORT=7860`, salud `/api/health`.
- Instancia: **Free, US$0/mes, 512 MB RAM, 0.1 CPU**. No se contrató un plan de pago ni se añadió disco persistente.
- Primera versión desplegada: `a5615f5d84eae08b8cc3253275e7d4368fc38f9c`.
- El primer despliegue terminó en aproximadamente 2 minutos y 11 segundos. La construcción Docker descargó y cargó correctamente el modelo en Linux.

## Prueba de IA en el servidor público

Se introdujo el comentario de ejemplo «Los gráficos son hermosos, pero tiene muchos errores 🙄». El servidor gratuito devolvió **NEGATIVO, confianza 0.6863**, con probabilidades positivo 0.0385, neutral 0.2752 y negativo 0.6863. Se conservaron las alertas de opinión mixta y posible sarcasmo.

La respuesta se comprobó en la interfaz publicada, no únicamente con la ruta de salud. Después se cargó el CSV de ejemplo: tres comentarios procesados correctamente. Se eligieron las etiquetas finales POSITIVO, NEGATIVO y NEUTRAL, y se descargó y verificó el CSV con tres filas REVISADO y las etiquetas del modelo preservadas. Esta prueba demuestra que la configuración actual pudo ejecutar el modelo en la instancia gratuita. No garantiza capacidad para tráfico simultáneo o comentarios de longitud máxima. La medición local de memoria en Windows no se trasladó como una exigencia de memoria idéntica en Linux.

## Operación

La instancia gratuita se suspende cuando está inactiva. Render advierte que reactivarla puede retrasar las solicitudes 50 segundos o más; después puede sumarse la carga de RoBERTuito. Mantén abierta la pestaña mientras procesa. Si no responde, revisa los registros del servicio antes de repetir solicitudes.

La revisión de cada usuario permanece en su pestaña. Debe descargarse antes de cerrarla. Los resultados históricos no cambian por esas revisiones.

La fuente se conectó como repositorio Git público. No se ampliaron permisos de la integración GitHub existente. Para publicar cambios de código, sube el commit a GitHub y, en el servicio Render, utiliza **Manual Deploy → Deploy latest commit**. No actives despliegues con planes de pago; `render.yaml` fija `plan: free` para futuras creaciones por Blueprint.

YouTube exige aprobación del caso de uso para publicar análisis de sentimiento derivados de comentarios de su API. Solicítala bajo **Analytics & Reporting** según las [políticas para métricas derivadas](https://developers.google.com/youtube/terms/derived-metrics-policy). Una vez aprobada, configura `YOUTUBE_API_KEY` en **Environment** del servicio Render con la clave del proyecto aprobado y guárdala fuera del repositorio.

La traducción automática continúa dependiendo de Google y puede bloquearse. El analizador de texto y CSV permite aportar una traducción manual.
