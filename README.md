🌿 Energy-Efficient CPU Scheduler

Authors:
👨‍💻 Sarthak Pandey
👨‍💻 Gaurav Rajbhar

🚀 Overview

This project implements a simple, clean, and explainable Energy-Efficient CPU Scheduling Algorithm using C++.
It uses a very intuitive idea:

score = burst_time × power_hint
energy = burst_time × power_hint


Lower score → more energy-efficient → scheduled first

power_hint:

1 → Low power

2 → Medium power

3 → High power

This scheduler is non-preemptive and easy

🧠 Core Idea Behind the Algorithm

We estimate the process’s “energy cost” using:

🔸 Scheduling Score
score = BT × PH

🔸 Energy Consumption
energy = BT × PH


This means:

✔ Shorter processes are good for CPU
✔ Lower-power processes are good for battery
✔ A combination of both is MOST energy-efficient

So the scheduler always picks the process with the lowest score first.

📊 Features

✔ Generates Gantt chart
✔ Computes

CT (Completion Time)

TAT (Turnaround Time)

WT (Waiting Time)
✔ Calculates total energy consumption
✔ Handles arrival times
✔ Very simple, clean logic (perfect for viva)

📁 Project Structure
📦 energy-efficient-cpu-scheduler
 ┣ 📄 simple_energy_scheduler.cpp     → main C++ code
 ┣ 📄 testcases.txt                   → example inputs
 ┣ 📄 README.md                       → documentation
 ┣ 📄 report.pdf                      → final OS project report
 ┗ 📄 (screenshots folder)            → GitHub commits/screenshots

🧪 Input Format

Enter number of processes:

3


Then enter each process as:

AT BT Priority PowerHint


Example:

0 5 1 3
1 3 2 1
2 2 1 2

🖥️ Output Example
Gantt Chart:
[P1:0-5] [P2:5-8] [P3:8-10]

PID AT BT PR PH CT TAT WT
1   0  5  1  3  5   5   0
2   1  3  2  1  8   7   4
3   2  2  1  2 10   8   6

Total Energy Used = 22

⚙️ How to Compile & Run
🔧 Compile
g++ -std=c++17 -O2 simple_energy_scheduler.cpp -o scheduler

▶️ Run
./scheduler

🧩 Simple Energy Formula (Easy Viva Answer)

Why BT × PH?

Because:

If a process runs longer → consumes more energy

If it uses higher power → consumes more energy

Multiplying them gives a simple, understandable, relative estimate of energy usage.

Perfect for OS classroom projects.


🛡️ Academic Honesty

This project is written and understood by the authors.
AI tools were used only for guidance, not for full code generation.
All logic, implementation, testing, and documentation are done by the us.

❤️ Support / Doubts?

If you need help running the code or understanding scheduling logic, feel free to check the comments or reach out.
