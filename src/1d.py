import tkinter as tk
import numpy as np
import random

# パラメータ
WIN_X, WIN_Y = 800, 800
# グリッドのパラメータ
n_grid = 64 # 格子点の数
dx = 1.0 / n_grid   # 格子点の間隔
grid_mass = np.zeros(n_grid)    # グリッドが持つの質量
grid_velocity = np.zeros(n_grid) # グリッドが持つ速度
# 粒子のパラメータ
n_particles = 10    # 粒子の数
p_position = np.zeros(n_particles)
p_velocity = np.zeros(n_particles)
p_mass = np.ones(n_particles)

def particles_init():
    global p_position, p_mass
    for p in range(n_particles):
        p_position[p] = random.uniform(0.2, 0.7)

# GUIセットアップと実行
window = tk.Tk()
window.title("Basic MPM Simulation")
window.geometry(f"{WIN_X}x{WIN_Y}")
window.resizable(False, False)

# キャンバスの作成
canvas = tk.Canvas(window, width=WIN_X, height=WIN_Y, bg="#4D4D4D", highlightthickness=0)
canvas.pack()

# ウィンドウイベントループ
window.mainloop()
