# Flexible Job Shop Problem (FJSP) -- MILP con GurobiPy

Implementación y resolución de las 20 instancias de **Fattahi et
al. (2007)** mediante un modelo de Programación Entera Mixta (MILP)
usando **Gurobi 13.0.0** y **Python 3.10**.

El repositorio permite: - Leer y procesar instancias en formato
Fattahi. - Construir el modelo MILP del FJSP. - Resolver múltiples
instancias en batch. - Exportar resultados en formato **CSV** y
**Markdown** para informes.

## 1. Descripción general

El Flexible Job Shop Problem (FJSP) extiende el clásico Job Shop
permitiendo que cada operación pueda ser procesada en múltiples máquinas
alternativas. Este proyecto implementa un modelo MILP que minimiza el
**makespan** utilizando Gurobi.

El script principal genera automáticamente: - tamaño del modelo
(variables binarias, continuas y número de restricciones), - tiempos de
ejecución, - valor del objetivo (Cmax), - gap final reportado por el
solver, - estado de terminación de cada instancia.

## 2. Estructura del repositorio

    /
    ├── fjsp_solver.py          # Código principal (modelo + ejecución + parser)
    ├── /instancias/            # Instancias Fattahi (.txt, .dat, etc.)
    ├── resultados_fattahi.csv  # Resultados en formato tabular
    ├── resultados_fattahi.md   # Tabla estilo Markdown
    └── README.md               # Este archivo

## 3. Cómo ejecutar

Ejemplo de ejecución estándar:

``` bash
python3 fjsp_gurobi_fattahi.py \
    --repo_root fjsp-instances \
    --time_limit 3600 \
    --threads 1 \
    --out resultados_fattahi.csv

```

### Parámetros disponibles

  Parámetro           Descripción
  ------------------- ----------------------------------------
  `--repo_root`       Carpeta o archivo con las instancias
  `--time_limit`      Tiempo máximo por instancia (s)
  `--threads`         Número de threads del solver
  `--mipgap`          Gap objetivo opcional
  `--out`             Nombre del archivo CSV de salida
  `--max_instances`   Número máximo de instancias a resolver

El script imprime el progreso y genera automáticamente los archivos de
salida.

## 4. Modelo MILP (resumen técnico)

### Variables:

-   **Asignación a máquina:**\
    ( y\_{i,o} = 1 ) si la operación (o) se ejecuta en la máquina (i).

-   **Tiempo de inicio:**\
    ( s_o `\ge 0`{=tex} )

-   **Makespan:**\
    ( C\_{`\max`{=tex}} )

-   **Ordenamiento por máquina:**\
    ( x\_{i,a,b} = 1 ) si en máquina (i), la operación (a) precede a
    (b).

### Restricciones:

1.  **Asignación única:**\
    \[ `\sum`{=tex}*{i `\in `{=tex}M_o} y*{i,o} = 1 \]

2.  **Precedencias por job:**\
    \[ s_b `\ge `{=tex}s_a + p_a(i) `\cdot `{=tex}y\_{i,a} \]

3.  **Disyuntivas por máquina (Big-M):**\
    Para cada par de operaciones (a,b) que pueden procesarse en la misma
    máquina:

    -   (x\_{i,a,b} = 1): (a) antes que (b)\
    -   (x\_{i,a,b} = 0): (b) antes que (a)

4.  **Makespan:**\
    \[ C\_{`\max`{=tex}}
    `\ge `{=tex}s\_{`\text{última operación}`{=tex}} + p \]

### Objetivo:

\[ `\min `{=tex}C\_{`\max`{=tex}} \]

## 5. Resultados generados

El script produce automáticamente: - `resultados_fattahi.csv` -
`resultados_fattahi.md`

ambos con: - tamaño de instancia, - conteo de variables y
restricciones, - makespan, - gap, - tiempo de ejecución, - estado de
optimización.

## 6. Reproducir el experimento del informe

``` bash
python fjsp_solver.py     --repo_root instancias/     --time_limit 3600     --threads 1     --out resultados_fattahi.csv
```

## 7. Requisitos

-   Python 3.10+
-   Gurobi 9.0+ (idealmente 13.0)
-   Paquete `gurobipy` licenciado

## Autores

Trabajo desarrollado para el curso **Optimización I (546351)**,
Universidad de Concepción.

**Integrantes:** - Cristóbal Muñoz Barrios\
- Bastián Ceballos Zapata
