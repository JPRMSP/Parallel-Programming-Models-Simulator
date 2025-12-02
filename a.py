import streamlit as st
import time
import random
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
import plotly.figure_factory as ff
import threading

# -------------------------------
# Helper functions
# -------------------------------

def simulate_task(task_id, duration):
    start = time.time()
    time.sleep(duration)
    end = time.time()
    return (task_id, start, end, multiprocessing.current_process().name)

def simulate_task_thread(task_id, duration):
    start = time.time()
    time.sleep(duration)
    end = time.time()
    return (task_id, start, end, threading.current_thread().name)

def pipeline_stage(stage_id, input_value):
    time.sleep(0.3)
    return input_value + 1

def demonstrate_race(num_updates, use_lock=False):
    shared = {"value": 0}
    lock = threading.Lock()

    def update():
        for _ in range(num_updates):
            if use_lock:
                with lock:
                    shared["value"] += 1
            else:
                shared["value"] += 1

    threads = [threading.Thread(target=update) for _ in range(8)]
    for t in threads: t.start()
    for t in threads: t.join()

    return shared["value"]

# -------------------------------
# Streamlit UI
# -------------------------------

st.title("Parallel Programming Models Simulator & Visualizer")
st.write("A real-time simulation tool for task parallelism, data parallelism, pipelining and race conditions.")

st.subheader("1. Task Simulation Parameters")
num_tasks = st.slider("Number of tasks", 1, 20, 6)
duration = st.slider("Duration per task (seconds)", 1, 5, 2)
mode = st.selectbox("Execution Mode", [
    "Sequential",
    "ThreadPool Parallel",
    "ProcessPool Parallel",
    "Pipeline Execution",
    "Master–Slave Model",
    "Data Parallel Split"
])

st.subheader("2. Run Simulation")
run_button = st.button("Run")

if run_button:
    tasks = list(range(num_tasks))
    records = []

    if mode == "Sequential":
        st.info("Running Sequential Execution")
        start_overall = time.time()
        for t_id in tasks:
            s = time.time()
            time.sleep(duration)
            e = time.time()
            records.append((t_id, s, e, "MainThread"))
        end_overall = time.time()

    elif mode == "ThreadPool Parallel":
        st.info("Running ThreadPool Parallel Execution")
        start_overall = time.time()
        with ThreadPoolExecutor() as ex:
            results = ex.map(lambda t: simulate_task_thread(t, duration), tasks)
            for r in results:
                records.append(r)
        end_overall = time.time()

    elif mode == "ProcessPool Parallel":
        st.info("Running ProcessPool Parallel Execution")
        start_overall = time.time()
        with ProcessPoolExecutor() as ex:
            results = ex.map(lambda t: simulate_task(t, duration), tasks)
            for r in results:
                records.append(r)
        end_overall = time.time()

    elif mode == "Pipeline Execution":
        st.info("Running 3-Stage Pipeline")
        start_overall = time.time()
        for t in tasks:
            val = t
            s = time.time()
            val = pipeline_stage(1, val)
            val = pipeline_stage(2, val)
            val = pipeline_stage(3, val)
            e = time.time()
            records.append((t, s, e, "Pipeline"))
        end_overall = time.time()

    elif mode == "Master–Slave Model":
        st.info("Running Master–Slave")
        start_overall = time.time()
        with ThreadPoolExecutor() as ex:
            futures = []
            for t in tasks:
                futures.append(ex.submit(simulate_task_thread, t, duration))
            for f in futures:
                records.append(f.result())
        end_overall = time.time()

    elif mode == "Data Parallel Split":
        st.info("Running Data Parallel (split tasks into chunks)")
        chunk_size = max(1, num_tasks // multiprocessing.cpu_count())
        chunks = [tasks[i:i+chunk_size] for i in range(0, len(tasks), chunk_size)]
        start_overall = time.time()
        with ProcessPoolExecutor() as ex:
            futures = []
            for chunk in chunks:
                futures.append(ex.submit(lambda ch: [simulate_task(c, duration) for c in ch], chunk))
            for f in futures:
                for r in f.result():
                    records.append(r)
        end_overall = time.time()

    # -----------------------
    # Visualization
    # -----------------------
    st.subheader("3. Timeline Visualization")

    df = []
    for (tid, s, e, worker) in records:
        df.append(dict(Task=f"Task {tid}", Start=s, Finish=e, Resource=worker))
    
    fig = ff.create_gantt(df, index_col='Resource', show_colorbar=True, group_tasks=True)
    st.plotly_chart(fig, use_container_width=True)

    st.success(f"Total Execution Time: {round(end_overall - start_overall, 3)} seconds")

# -------------------------------
# Race Condition Demonstration
# -------------------------------
st.subheader("4. Race Condition Demonstration")

if st.button("Run Without Lock"):
    wrong = demonstrate_race(20000, use_lock=False)
    st.error(f"Final value without lock (should be 160000): {wrong}")

if st.button("Run With Lock"):
    correct = demonstrate_race(20000, use_lock=True)
    st.success(f"Final value with lock: {correct}")
