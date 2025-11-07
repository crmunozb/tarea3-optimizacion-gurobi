import pandas as pd
import matplotlib.pyplot as plt

# === Cargar CSV ===
df = pd.read_csv("resultados_fattahi.csv")

# === Limpieza rápida ===
# Solo tomamos las filas que tienen resultados válidos
df = df.dropna(subset=['objective', 'time_s', 'gap'])
df['instance'] = df['instance'].astype(str)

# === Gráfico 1: Tiempo de ejecución ===
plt.figure(figsize=(10,5))
plt.bar(df['instance'], df['time_s'], color='steelblue')
plt.xticks(rotation=45, ha='right')
plt.title('Tiempo de ejecución por instancia (segundos)')
plt.xlabel('Instancia')
plt.ylabel('Tiempo [s]')
plt.tight_layout()
plt.show()

# === Gráfico 2: GAP ===
plt.figure(figsize=(10,5))
plt.bar(df['instance'], df['gap'], color='orange')
plt.xticks(rotation=45, ha='right')
plt.title('Optimality GAP por instancia')
plt.xlabel('Instancia')
plt.ylabel('GAP')
plt.tight_layout()
plt.show()

# === Gráfico 3: Makespan (Objetivo) ===
plt.figure(figsize=(10,5))
plt.plot(df['instance'], df['objective'], marker='o', color='green')
plt.xticks(rotation=45, ha='right')
plt.title('Makespan (Cmax) por instancia')
plt.xlabel('Instancia')
plt.ylabel('Cmax (Objective)')
plt.tight_layout()
plt.show()

# === Gráfico 4: Comparación promedio por tipo ===
df['tipo'] = df['instance'].apply(lambda x: 'mfjs' if 'mfj' in x else 'sfjs')
promedios = df.groupby('tipo')[['time_s','gap','objective']].mean()

plt.figure(figsize=(8,5))
promedios[['time_s','gap']].plot(kind='bar', subplots=True, figsize=(10,5))
plt.suptitle('Promedios por tipo de instancia')
plt.tight_layout()
plt.show()
