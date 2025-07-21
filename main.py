#Frist define all the require variables

machines = ['LaserCutter', 'CNC_Mill', 'PaintStation']


#Considered the time in minutes, as said in PS
calendar = {
    'LaserCutter': list(range(480, 1020)),    
    'CNC_Mill': list(range(480, 960)),        
    'PaintStation': list(range(540, 1080))      
}


# Jobs with tasks (job_id, task_id, machine, duration_in_hours, predecessor_task_id)

tasks = [
    ('Job1', 'Cutting', 'LaserCutter', 180, None),
    ('Job1', 'Milling', 'CNC_Mill', 120, 'Cutting'),
    ('Job1', 'Painting', 'PaintStation', 60, 'Milling'),

    ('Job2', 'Cutting', 'LaserCutter', 120, None),
    ('Job2', 'Painting', 'PaintStation', 60, 'Cutting'),

    ('Job3', 'Milling', 'CNC_Mill', 240, None),
    ('Job3', 'Painting', 'PaintStation', 120, 'Milling'),
]



#importing all pyomo libraries
from pyomo.environ import *

model = ConcreteModel() #creating an empty template
# print(model)

# defining the tasks and machines in the template
model.TASKS = RangeSet(0, len(tasks)-1)
model.MACHINES = Set(initialize=machines)

# print(model.TASKS)

# indexing each job one by one using enumerate fucntion
task_dict = {i: t for i, t in enumerate(tasks)}
# print(task_dict)


# initialtizing the start, end & makespan variable
model.start = Var(model.TASKS, domain=NonNegativeReals) #For every task, create a variable called start time & a end time, which must be zero or more (no negatives).
model.end = Var(model.TASKS, domain=NonNegativeReals)
model.makespan = Var(domain=NonNegativeReals) #makespan = the time when the last task finishes (i.e., total time to complete all jobs).

# Constraints or Rules

def duration_rule(m, i):
    return m.end[i] == m.start[i] + task_dict[i][3] #This function is use to keep the timing of eash tasks accurate.

model.task_duration = Constraint(model.TASKS, rule=duration_rule) #Constraint():Tells Pyomo what conditions must always be true

# Precedence constraints
def precedence_rule(m, i):
    pred = task_dict[i][4] #it will return the 4th item of the job's rows, which is the predecessor task
    if pred is None:
        return Constraint.Skip #if no predecessor task, then skip
    job = task_dict[i][0]
    for j in model.TASKS:
        if task_dict[j][0] == job and task_dict[j][1] == pred:  #  Checks: “Is task j in the same job, and is its name the one we depend on (pred)?”
            return m.start[i] >= m.end[j]  # Task i can only start once its predecessor j has finished.
    return Constraint.Skip
model.precedence = Constraint(model.TASKS, rule=precedence_rule)

# No overlap on same machine
def no_overlap_rule(m, i, j):
    if i >= j: 
        return Constraint.Skip  # Skip any pair where i is not strictly less than j.
    if task_dict[i][2] != task_dict[j][2]:
        return Constraint.Skip  # Skip if tasks i and j are on different machines.
    return inequality(
        m.end[i] <= m.start[j] + (1 - binary[i, j]) * 1e5,
        m.start[i] >= m.end[j] + binary[i, j] * 1e5
    )

# Enforce two inequalities at once using a “big‑M” trick (M = 1e5):
# end[i] ≤ start[j] + (1–b)*M
# start[i] ≥ end[j] + b*M

# Here b = binary[i,j] is 0 or 1:
# If b = 0, the first line becomes end[i] ≤ start[j] (i before j) & If b = 1, the second line becomes start[i] ≥ end[j] (j before i).

model.no_overlap = ConstraintList() #Defines empty list of constraints
binary = {}

#Pairs should be on different machines.
for i in model.TASKS:
    for j in model.TASKS:
        if i >= j:
            continue
        if task_dict[i][2] != task_dict[j][2]:
            continue

        #Creating a binary variable b_{i,j}, 0 or 1
        binary[i, j] = Var(domain=Binary) 
        model.add_component(f"binary_{i}_{j}", binary[i, j])

        #Add both sides of the big‑M constraint to the no_overlap list:
        #If b=0, forces task i to finish before task j starts & If b=1, forces task j to finish before task i starts.

        model.no_overlap.add(expr=(
            model.end[i] <= model.start[j] + (1 - binary[i, j]) * 1e5
        ))
        model.no_overlap.add(expr=(
            model.start[i] >= model.end[j] + binary[i, j] * 1e5
        ))

# Makespan constraint
def makespan_rule(m, i):
    return m.makespan >= m.end[i]  # makes sure 'makespan' must be at least as large as this task’s finish time.
model.make_span_con = Constraint(model.TASKS, rule=makespan_rule)

# Objective of the whole model
model.obj = Objective(expr=model.makespan, sense=minimize)  #Defines the objective that “Minimize the value of model.makespan.”



solver = SolverFactory('glpk') #linear/integer optimizer
result = solver.solve(model, tee=False) # Running the solver
print(result)

print("Schedule:")
for i in model.TASKS:
    t = task_dict[i]
    print(f"{t[0]} - {t[1]} ({t[2]}): Start={model.start[i]():.1f} End={model.end[i]():.1f}")

print(f"\nTotal Makespan: {model.makespan():.1f} minutes")


# Gantt chart

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 4))
colors = {'LaserCutter': 'skyblue', 'CNC_Mill': 'lightgreen', 'PaintStation': 'lightcoral'}
machine_ypos = {m: i for i, m in enumerate(machines)}

for i in model.TASKS:
    job, task, machine, duration, _ = task_dict[i]
    start = model.start[i]()
    end = model.end[i]()
    ypos = machine_ypos[machine]
    ax.barh(ypos, end - start, left=start, height=0.4, color=colors[machine])
    ax.text(start + 2, ypos, f"{job}-{task}", va='center', ha='left', fontsize=8)

ax.set_yticks(list(machine_ypos.values()))
ax.set_yticklabels(machines)
ax.set_xlabel("Time (minutes)")
ax.set_title("Factory Schedule - Gantt Chart")
ax.grid(True)
plt.tight_layout()
plt.show()


# Machine working minutes (in percentage)
working_minutes = {m: len(calendar[m]) for m in machines} #Build a dictionary mapping each machine to its total working time in minutes.
busy_minutes = {m: 0 for m in machines} #how many minutes each machine is actually busy.

for i in model.TASKS:
    machine = task_dict[i][2] #machine name for task i (it’s the 3rd element in each task tuple).
    busy_minutes[machine] += model.end[i]() - model.start[i]()

print("\nMachine Utilization:")
for m in machines:
    utilization = (busy_minutes[m] / working_minutes[m]) * 100
    print(f"{m}: {utilization:.2f}%")
