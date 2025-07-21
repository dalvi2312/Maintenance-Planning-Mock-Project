# Maintenance Planning Mock Project 🚧

Pyomo-based Finite Capacity Scheduling (FCS) tool for LeanQubit’s maintenance planning. Generates conflict-free schedules for job‑shop environments by modeling machines, shift calendars, task dependencies, and capacity constraints to minimize makespan while boosting utilization.

---

## ⚙️ Features

- **Job‑shop scheduling** with sequential tasks and precedence rules  
- **Machine calendars** enforce shift timings and availability  
- **Conflict resolution** ensures no overlapping use of machines  
- **Minimizes makespan**, reduces WIP, and improves on‑time delivery  
- **Visual output** via Gantt charts and machine utilization stats  

---

## 📦 Installation

```bash
python -m venv env
source env/bin/activate        # Unix/macOS
.\env\Scripts\activate         # Windows PowerShell
pip install -r requirements.txt
```

##🚀 Usage

```bash
python factory_schedule.py
```

- ##Solves the scheduling problem
- ##Prints start/end times per task and total makespan
- ##Displays a Gantt chart of machine schedules
- ##Shows machine utilization percentages

