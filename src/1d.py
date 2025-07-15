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
PARTICLE_RADIUS = 10 # ピクセルで半径
PARTICLE_RADIUS_NORM = PARTICLE_RADIUS / WIN_X  # 半径を正規化座標に変換
N_PARTICLES = 100    # 粒子の数
PARTICLE_MASS = 1.0

# グローバル変数
particles = []
grid_points = []
# 計算用のグリッドデータ (NumPy配列)
grid_mass = np.zeros((N_GRID_SIDE, N_GRID_SIDE))
grid_vel = np.zeros((N_GRID_SIDE, N_GRID_SIDE, 2))

class Particle:
    def __init__(self, x, y, vx, vy, mass, radius, color, canvas):
        self.pos = np.array([x, y], dtype=float)
        self.vel = np.array([vx, vy], dtype=float)
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

# 描画用のグリッドクラス
class GridPoints:
    def __init__(self, x, y, radius, color, canvas):
        self.pos = [x, y]
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

    for i in range(N_GRID_SIDE):
        for j in range(N_GRID_SIDE):
            # グリッド点はセルの中心にある
            x = (j + 0.5) * DX
            y = (i + 0.5) * DX
            color = "#FFFFFF"
            g = GridPoints(x, y, GRID_POINT_RADIUS_NORM, color, canvas)
            grid_points.append(g)

def main_loop():
    # グリッドのリセット
    grid_mass.fill(0)
    grid_vel.fill(0)

    # ステップ1: P2G
    for p in particles:
        # 粒子の座標から、どのグリッドセルの間にいるか計算
        grid_pos = p.pos / DX
        # 左下のノードのインデックス（intにキャスト）
        base_node = grid_pos.astype(int)

        # 1Dシミュレーションなので、X方向は一番近い列を使う
        base_node_x = base_node[0]
        base_node_y = base_node[1]

        # 粒子から base_node_y と base_node_y+1 までの距離（重み）を計算
        fx_y = grid_pos[1] - base_node_y
        w_y = np.array([1.0 - fx_y, fx_y])

        # Xインデックス(base_node_x)を指定して、Y方向の2点に分配
        for i in range(2):  # y と y+1 の2点についてループ
            weight = w_y[i]
            # 質量を分配
            grid_mass[base_node_y + i, base_node_x] += weight * p.mass
            # Y方向の運動量を分配（p.velはベクトルなのでp.vel[1]でY成分を取得
            grid_vel[base_node_y + i, base_node_x, 1] += weight * p.mass * p.vel[1]

    # ステップ2: グリッド上での計算
    # 運動量を質量で割り、速度に変換
    # 質量が0のままの速度は0のまま
    mass_filter = grid_mass > 1e-10 # ごくわずかな質量も考慮
    grid_vel[mass_filter, 1] /= grid_mass[mass_filter]

    # 重力を加える（質量があるすべての点に）
    grid_vel[mass_filter, 1] += DT * GRAVITY

    # 境界条件（床と天井で跳ね返る、または止まる）
    # Y=0（床）と Y=N_GRID_SIDE-1（天井）での処理
    grid_vel[0, :, 1][grid_vel[0, :, 1] < 0] = 0    # 床より下に行こうとしたら止める
    grid_vel[N_GRID_SIDE - 1, :, 1][grid_vel[N_GRID_SIDE - 1, :, 1] > 0] = 0    # 天井より上に行こうとしたらとめる

    # ステップ3: G2P
    for p in particles:
        # 同様に、近傍グリッドとその重みを計算
        grid_pos = p.pos / DX
        base_node = grid_pos.astype(int)
        base_node_x = base_node[0]
        base_node_y = base_node[1]

        fx_y = grid_pos[1] - base_node_y
        w_y = np.array([1.0 - fx_y, fx_y])

        # グリッドから補間して新しい速度を計算
        new_vel_y = 0.0
        for i in range(2):
            weight = w_y[i]
            new_vel_y += weight * grid_vel[base_node_y + i, base_node_x, 1]

        # 速度を代入する
        p.vel[1] = new_vel_y

        # 新しい速度で位置を更新
        p.pos += DT * p.vel

        # X方向は今は動かさない
        # p.pos[0] += DT * p.vel[0]

    # ステップ4: 描画
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
