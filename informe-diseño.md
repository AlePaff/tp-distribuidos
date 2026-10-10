# Informe de Diseño - Sistemas Distribuidos

Wikipedia Article Analysis


## Introducción y Objetivo
El presente documento describe el diseño de un sistema distribuido para el análisis de un conjunto de artículos de Wikipedia en francés e inglés. El sistema debe resolver cinco consultas específicas de manera concurrente y aislada para múltiples clientes

El diseño prioriza la escalabilidad horizontal, la reutilización de operaciones y el aislamiento de datos por cliente. A continuación se presentan las vistas arquitectónicas que modelan la solución.

## DAG (Directed Acyclic Graph)
Vista lógica de alto nivel que representa el flujo de tareas y dependencias del sistema.



!(Diagramas/DAG_inicial.jpg)[DAG]

El DAG muestra la reutilización del filtro <= 2020 para Q1 y Q2, y la bifurcación del extractor de palabras (QWords) hacia Q3, Q4 y Q5. Se observa la convergencia final de todos los resultados hacia el Gateway de salida.

## Diagrama de Robustez
Vista de infraestructura lógica que detalla colas, workers y escalabilidad.

!(Diagramas\Robustez inicial.jpg)[Robustez]


## Diagramas de Secuencia
Vista dinámica que muestra el intercambio de mensajes en el tiempo.

#### 4.1. Secuencia Q1 (Filtro Inglés)
TODO: copiar imagen

Flujo simple de un artículo. Muestra la propagación del mensaje EOF desde el cliente hasta el worker de Q1, el aislamiento por client_id y la emisión del resultado parcial y final (Q1_END).

#### 4.2. Secuencia Q3 (Palabras Compartidas)
TODO: copiar imagen

Evidencia el uso del hash(word) % N para garantizar que la misma palabra caiga en el mismo SharedWordAgg. Muestra cómo se emite un resultado parcial apenas se detecta la palabra en ambos idiomas (EN/FR).

## Diagrama de Despliegue
Vista física de nodos y contenedores]


## Diagrama de Actividades


## Diagrama de Paquetes

## Decisiones de Diseño y Consideraciones


## División de Tareas
Para este TP

| Integrante    | Responsabilidad Principal |
| -------- | ------- |
| A    | Secuencia (Q1, Q3, Q4, Q5) y Actividades (Q4, Q5)    |
| B    | Despliegue, Paquetes e informe     |
| C    | Actividades (Q1, Q2, Q3, etc) y revisión de DAG/Robustez    |


Para los siguientes hitos del TP

