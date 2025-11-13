import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("resultados_fattahi.csv")
df = df.dropna(subset=["objective","gap","time_s"])

# --- Gráfico 1: Tiempo por instancia ---
plt.figure(figsize=(10,4.5))
plt.bar(df["instance"], df["time_s"])
plt.xticks(rotation=60, ha="right")
plt.xlabel("Instancia"); plt.ylabel("Tiempo [s]")
plt.title("Tiempo de ejecución por instancia")
plt.tight_layout()
plt.savefig("g_tiempo.png", dpi=300)

# --- Gráfico 2: GAP por instancia (en %) ---
plt.figure(figsize=(10,4.5))
plt.bar(df["instance"], 100*df["gap"])
plt.xticks(rotation=60, ha="right")
plt.xlabel("Instancia"); plt.ylabel("GAP [%]")
plt.title("GAP por instancia")
plt.tight_layout()
plt.savefig("g_gap.png", dpi=300)

# --- Gráfico 3: Makespan ---
plt.figure(figsize=(10,4.5))
plt.plot(df["instance"], df["objective"], marker="o")
plt.xticks(rotation=60, ha="right")
plt.xlabel("Instancia"); plt.ylabel("Cmax")
plt.title("Makespan (Cmax) por instancia")
plt.tight_layout()
plt.savefig("g_cmax.png", dpi=300)
