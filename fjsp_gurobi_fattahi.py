# -*- coding: utf-8 -*-
"""
FJSP con GUROBIpy – Modelo MILP, ejecución por lotes y tabla de resultados

• Instancias: formato del repo SchedulingLab/fjsp-instances (carpeta 'fattahi').
  Formato (README del repo):
    - Primera línea: <n_jobs> <n_machines>
    - Luego, por cada job: <n_operaciones> y, para cada operación,
      <k_maquinas> seguido de k pares <maquina> <tiempo> (índice de máquina inicia en 0)

• Modelo: Flexible Job Shop clásico, objetivo minimizar makespan (C_max).
  Variables:
    - y[i,j,h] ∈ {0,1}: 1 si la operación (j,h) se procesa en máquina i.
    - s[j,h] ≥ 0: tiempo de inicio de (j,h).
    - x[a,b,i] ∈ {0,1}: orden en máquina i entre operaciones a y b.
  Restricciones (esquema):
    1) Asignación única: sum_i y[i,j,h] = 1 para toda operación (j,h).
    2) Precedencia en cada job: s[j,h+1] ≥ s[j,h] + p(j,h).
    3) Capacidad de máquina (disyuntivas con Big-M):
       s_b ≥ s_a + p_a − M*(1 − x_{a,b,i} + 2 − y_{i,a} − y_{i,b})
       s_a ≥ s_b + p_b − M*(x_{a,b,i} + 2 − y_{i,a} − y_{i,b})
    4) Makespan: Cmax ≥ s[j,last] + p(j,last)

• Parámetros GUROBI: TimeLimit=3600s.
• Salidas: CSV y Markdown con tamaño de instancia, #vars, #restricciones, función objetivo, gap y tiempo.
"""
from __future__ import annotations
import os, math, time, argparse, csv
from dataclasses import dataclass
from typing import Dict, List

try:
    import gurobipy as gp
    from gurobipy import GRB
except Exception as e:
    gp = None
    GRB = None


@dataclass
class Operation:
    job: int
    op: int
    alts: Dict[int, int]  # machine -> proc time


@dataclass
class Instance:
    name: str
    n_jobs: int
    n_machs: int
    ops: List[Operation]
    job_ops_idx: List[List[int]]


# -------------------- LECTURA DE INSTANCIAS --------------------

def parse_fjsp_instance(path: str) -> Instance:
    name = os.path.basename(path)
    with open(path, 'r') as f:
        tokens = f.read().strip().split()
    it = iter(tokens)
    n_jobs = int(next(it)); n_machs = int(next(it))
    ops: List[Operation] = []
    job_ops_idx: List[List[int]] = []
    for j in range(n_jobs):
        n_ops = int(next(it))
        job_list = []
        for h in range(n_ops):
            k = int(next(it))
            alts: Dict[int, int] = {}
            for _ in range(k):
                m = int(next(it)); p = int(next(it))
                alts[m] = p
            idx = len(ops)
            ops.append(Operation(job=j, op=h, alts=alts))
            job_list.append(idx)
        job_ops_idx.append(job_list)
    return Instance(name=name, n_jobs=n_jobs, n_machs=n_machs, ops=ops, job_ops_idx=job_ops_idx)


# -------------------- CONSTRUCCIÓN DEL MODELO MILP --------------------

def build_model(inst: Instance, time_limit: int = 3600, threads: int | None = None, mipgap: float | None = None):
    if gp is None:
        raise RuntimeError("gurobipy no está instalado en este entorno.")

    m = gp.Model(f"FJSP_{inst.name}")
    if threads is not None:
        m.Params.Threads = threads
    m.Params.TimeLimit = time_limit
    if mipgap is not None:
        m.Params.MIPGap = mipgap

    O = list(range(len(inst.ops)))
    I = list(range(inst.n_machs))

    sum_max = sum(max(op.alts.values()) for op in inst.ops)
    M = sum_max + 1

    y = {}
    for o in O:
        for i in inst.ops[o].alts:
            y[i, o] = m.addVar(vtype=GRB.BINARY, name=f"y_{i}_{o}")

    s = {o: m.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"s_{o}") for o in O}
    Cmax = m.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="Cmax")

    # Asignación única
    for o in O:
        m.addConstr(gp.quicksum(y[i, o] for i in inst.ops[o].alts) == 1, name=f"assign_{o}")

    # Precedencias
    for j, job_list in enumerate(inst.job_ops_idx):
        for a, b in zip(job_list[:-1], job_list[1:]):
            p_a = gp.quicksum(inst.ops[a].alts[i] * y[i, a] for i in inst.ops[a].alts)
            m.addConstr(s[b] >= s[a] + p_a, name=f"prec_{j}_{a}_{b}")
        last = job_list[-1]
        p_last = gp.quicksum(inst.ops[last].alts[i] * y[i, last] for i in inst.ops[last].alts)
        m.addConstr(Cmax >= s[last] + p_last, name=f"mk_{j}")

    # Disyuntivas
    ops_by_machine = {i: [] for i in I}
    for o in O:
        for i in inst.ops[o].alts:
            ops_by_machine[i].append(o)

    x = {}
    for i in I:
        ops_i = ops_by_machine[i]
        for idx_a in range(len(ops_i)):
            a = ops_i[idx_a]
            for idx_b in range(idx_a + 1, len(ops_i)):
                b = ops_i[idx_b]
                x[i, a, b] = m.addVar(vtype=GRB.BINARY, name=f"x_{i}_{a}_{b}")
                p_a = gp.quicksum(inst.ops[a].alts[ii] * y[ii, a] for ii in inst.ops[a].alts)
                p_b = gp.quicksum(inst.ops[b].alts[ii] * y[ii, b] for ii in inst.ops[b].alts)
                ya = y.get((i, a)); yb = y.get((i, b))
                m.addConstr(s[b] >= s[a] + p_a - M * (1 - x[i, a, b] + 2 - ya - yb), name=f"disj1_{i}_{a}_{b}")
                m.addConstr(s[a] >= s[b] + p_b - M * (x[i, a, b] + 2 - ya - yb), name=f"disj2_{i}_{a}_{b}")

    m.setObjective(Cmax, GRB.MINIMIZE)
    m.update()
    return m


# -------------------- EJECUCIÓN Y REPORTE --------------------

def find_fattahi_files(root: str):
    files = []
    if os.path.isfile(root):
        return [root]
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(('.fjs', '.fjsp', '.txt', '.dat')):
                files.append(os.path.join(dirpath, fn))
    fattahi = [p for p in files if 'fattahi' in p.lower()]
    return sorted(fattahi) if fattahi else sorted(files)


def solve_instance(path: str, time_limit: int = 3600, threads: int | None = None, mipgap: float | None = None):
    inst = parse_fjsp_instance(path)
    start = time.time()
    model = build_model(inst, time_limit=time_limit, threads=threads, mipgap=mipgap)
    model.optimize()
    runtime = model.Runtime
    status = model.Status
    obj = model.ObjVal if model.SolCount > 0 else float('nan')
    gap = model.MIPGap if hasattr(model, 'MIPGap') else float('nan')
    return {
        'instance': os.path.basename(path),
        'jobs': inst.n_jobs,
        'machines': inst.n_machs,
        'ops': len(inst.ops),
        'vars': model.NumVars,
        'constrs': model.NumConstrs,
        'objective': obj,
        'gap': gap,
        'time_s': runtime,
        'status': status
    }


def main():
    ap = argparse.ArgumentParser(description="Resolver FJSP (instancias Fattahi) con Gurobi y generar tabla.")
    ap.add_argument('--repo_root', type=str, required=True)
    ap.add_argument('--time_limit', type=int, default=3600)
    ap.add_argument('--threads', type=int, default=None)
    ap.add_argument('--mipgap', type=float, default=None)
    ap.add_argument('--out', type=str, default="resultados_fattahi.csv")
    ap.add_argument('--max_instances', type=int, default=None)
    args = ap.parse_args()

    files = find_fattahi_files(args.repo_root)
    if args.max_instances:
        files = files[:args.max_instances]

    print(f"Encontradas {len(files)} instancias (Fattahi).")

    rows = []
    for p in files:
        print(f"-> Resolviendo {os.path.basename(p)} ...")
        try:
            row = solve_instance(p, time_limit=args.time_limit, threads=args.threads, mipgap=args.mipgap)
        except Exception as e:
            row = {'instance': os.path.basename(p), 'error': str(e)}
        rows.append(row)

    fieldnames = ['instance','jobs','machines','ops','vars','constrs','objective','gap','time_s','status']
    with open(args.out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in fieldnames})
    print(f"\nCSV guardado en {args.out}")

    md_path = os.path.splitext(args.out)[0] + '.md'
    def fmt(x):
        if isinstance(x, float):
            if math.isnan(x): return '-'
            return f"{x:.4g}"
        return str(x)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('| Instancia | |J| | |M| | |Ops| | Vars | Restr. | Obj (Cmax) | GAP | t (s) |\n')
        f.write('|:--|--:|--:|--:|--:|--:|--:|--:|--:|\n')
        for r in rows:
            if 'error' in r:
                f.write(f"| {r['instance']} | - | - | - | - | - | ERROR: {r['error']} | - | - |\n")
            else:
                f.write(f"| {r['instance']} | {r['jobs']} | {r['machines']} | {r['ops']} | {r['vars']} | {r['constrs']} | {fmt(r['objective'])} | {fmt(r['gap'])} | {fmt(r['time_s'])} |\n")
    print(f"Markdown guardado en {md_path}")


if __name__ == '__main__':
    if gp is None:
        print("ADVERTENCIA: gurobipy no está instalado. El script construye el modelo pero no podrá resolver.")
    main()
