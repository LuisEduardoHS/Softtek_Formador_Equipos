# Frontend de Complementa

Cliente React + Vite de la plataforma de formación de equipos. Consume FastAPI para autenticación, perfiles revisados, proyectos, recomendaciones, invitaciones y equipos.

La instalación completa (MySQL, Ollama, backend y frontend) está en el [README principal](../README.md). Para un frontend ya instalado, desde esta carpeta:

```powershell
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

La API por defecto es `http://127.0.0.1:8000`. Para un backend QA aislado:

```powershell
$env:VITE_API_URL='http://127.0.0.1:8011'
npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

No apuntes ese servidor QA a la base principal. La preparación y los datos están en la [guía manual](../docs/pruebas-manuales/guia-completa.md). Las variables Vite se leen al iniciar el proceso; reinícialo después de cambiarlas.

```powershell
npm test
npm run build
npm run lint
```

La landing y la ruta de diseño contienen ejemplos identificados como demostración; las recomendaciones del flujo autenticado proceden del backend. Las constantes de calendario se comparten con esos ejemplos, pero no deben utilizarse personas de mockData como identidad o resultados reales.
