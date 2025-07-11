import tkinter as tk
import numpy as np
import random

# パラメータ
WIN_X, WIN_Y = 800, 800
# 物理パラメータ
DT = 1e-4
GRAVITY = -9.81
# グリッドのパラメータ
N_GRID_SIDE = 8 # 各軸の格子点
DX = 1.0 / N_GRID_SIDE   # 格子点の間隔
GRID_POINT_RADIUS = 2 # ピクセルで半径
GRID_POINT_RADIUS_NORM = GRID_POINT_RADIUS / WIN_X  # 半径を正規化座標に変換
# 粒子のパラメータ
PARTICLE_RADIUS = 15 # ピクセルで半径
PARTICLE_RADIUS_NORM = PARTICLE_RADIUS / WIN_X  # 半径を正規化座標に変換
N_PARTICLES = 10    # 粒子の数
PARTICLE_MASS = 1.0

# グローバル変数
particles = []
grid_points = []
# 計算用のグリッドデータ (NumPy配列)
grid_mass = np.zeros((N_GRID_SIDE, N_GRID_SIDE))
grid_vel = np.zeros((N_GRID_SIDE, N_GRID_SIDE, 2))

class Particle:
    def __init__(self, x, y, vx, vy, mass, radius, color, canvas):
        self.pos = [x, y]
        self.vel = [vx, vy]
        self.mass = mass
        self.radius = radius
        self.color = color
        self.canvas = canvas
        self.id = None

    def draw(self):
        # 正規化座標 ->  ピクセル
        x = self.pos[0] * WIN_X
        y = (1.0 - self.pos[1]) * WIN_Y

        x0 = x - PARTICLE_RADIUS
        y0 = y - PARTICLE_RADIUS
        x1 = x + PARTICLE_RADIUS
        y1 = y + PARTICLE_RADIUS

        # もし初回描写なら図形を生成、そうでなければ移動
        if self.id is None:
            self.id = self.canvas.create_oval(x0, y0, x1, y1, fill=self.color, outline="")
        else:
            self.canvas.coords(self.id, x0, y0, x1, y1)

class GridPoints:
    def __init__(self, x, y, vx, vy, mass, radius, color, canvas):
        self.pos = [x, y]
        self.vel = [vx, vy]
        self.mass = mass
        self.radius = radius
        self.color = color
        self.canvas = canvas
        self.id = None

    def draw(self):
        x = self.pos[0] * WIN_X
        y = (1.0 - self.pos[1]) * WIN_Y

        x0 = x - GRID_POINT_RADIUS
        y0 = y - GRID_POINT_RADIUS
        x1 = x + GRID_POINT_RADIUS
        y1 = y + GRID_POINT_RADIUS

        if self.id is None:
            self.id = self.canvas.create_oval(x0, y0, x1, y1, fill=self.color, outline="")
        else:
            self.canvas.coords(self.id, x0, y0, x1, y1);


def particles_init():
    global particles

    for p in range(N_PARTICLES):
        x = random.uniform(0.4, 0.6)
        y = random.uniform(0.4, 0.6)
        vx = 0
        vy = 0
        color = "#06D6A0"

        p = Particle(x, y, vx, vy, PARTICLE_MASS, PARTICLE_RADIUS_NORM, color, canvas)
        particles.append(p)

def grid_points_init():
    global grid_points

    x, y = 0.0, 0.0
    for i in range(N_GRID_SIDE):
        for j in range(N_GRID_SIDE):
            x = (j + 0.5) * DX
            y = (i + 0.5) * DX
            vx = 0
            vy = 0
            color = "#FFFFFF"

            g = GridPoints(x, y, vx, vy, 0.0, GRID_POINT_RADIUS_NORM, color, canvas)
            grid_points.append(g)

def main_loop():
    # グリッドのリセット
    grid_mass.fill(0)
    grid_vel.fill(0)

    # P2G
    for p in particles:
        # 粒子のy座標から、どのグリッドセルの間にいるか計算
        grid_pos_y = p.pos[1] / DX
        base_node_y = int(grid_pos_y)

        # 粒子から base_node と base_node+1 までの距離（重み）を計算
        fx = grid_pos_y = base_node_y
        w = np.array([1.0 - fx, fx])

        # 質量と運動量を近傍の2つのグリッド点に分配
        grid_mass[base_node_y : base_node_y + 2] += w * p.mass
        grid_vel[base_node_y : base_node_y + 2] += w * p.mass * p.vel[1] # Y方向の運動量

    # グリッド上での計算
    # 運動量を質量で割り、速度に変換
    # np.divide の where を使うとゼロ徐算を安全に避けられる
    np.divide(grid_vel, grid_mass, out=grid_vel, where=grid_mass != 0.0)

    # 重力を加える
    grid_vel[1] += DT * GRAVITY

    # 境界条件（床と天井で跳ね返る、または止まる）
    if grid_vel[1] < 0: # 床より下に行こうとしたら
        grid_vel[1] = 0 # 止める
    if grid_vel[N_GRID_SIDE - 1] > 0:   # 天井より上に行こうとしたら
        grid_vel[N_GRID_SIDE - 1] = 0   # 止める

    # G2P


    for p in particles:
        p.draw()

    for g in grid_points:
        g.draw()

    window.after(1, main_loop)

# GUIセットアップと実行
window = tk.Tk()
window.title("Basic MPM Simulation")
window.geometry(f"{WIN_X}x{WIN_Y}")
window.resizable(False, False)

# キャンバスの作成
canvas = tk.Canvas(window, width=WIN_X, height=WIN_Y, bg="#4D4D4D", highlightthickness=0)
canvas.pack()

# 初期化
particles_init()
grid_points_init()

# メインループ
main_loop()

# ウィンドウイベントループ
window.mainloop()
