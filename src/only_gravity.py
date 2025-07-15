import tkinter as tk
import numpy as np
import random
import time

# パラメータ
WIN_X, WIN_Y = 800, 800
# 物理パラメータ
DT = 1e-4 * 5
GRAVITY = -9.81
# グリッドのパラメータ
N_GRID_SIDE = 32 # 各軸の格子点
DX = 1.0 / N_GRID_SIDE   # 格子点の間隔
GRID_POINT_RADIUS = 1 # ピクセルで半径
GRID_POINT_RADIUS_NORM = GRID_POINT_RADIUS / WIN_X  # 半径を正規化座標に変換
# 粒子のパラメータ
PARTICLE_RADIUS = 5 # ピクセルで半径
PARTICLE_RADIUS_NORM = PARTICLE_RADIUS / WIN_X  # 半径を正規化座標に変換
N_PARTICLES = 100    # 粒子の数
PARTICLE_MASS = 1.0

# グローバル変数
particles = []
grid_points = []
# 計算用のグリッドデータ (NumPy配列)
grid_mass = np.zeros((N_GRID_SIDE, N_GRID_SIDE))
grid_vel = np.zeros((N_GRID_SIDE, N_GRID_SIDE, 2))
# FPS計算用の変数
last_time, frame_count, fps = 0, 0, 0

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
        px = random.uniform(-0.2, 0.2)
        py = random.uniform(-0.2, 0.2)
        if px**2 + py**2 < 0.2**2:
            x = 0.5 + px
            y = 0.7 + py
            p = Particle(x, y, 0.0, 0.0, PARTICLE_MASS, PARTICLE_RADIUS_NORM, "#06D6A0", canvas)
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
    global last_time, frame_count, fps
    # FPS計算用のロジック
    current_time = time.time()
    frame_count += 1
    if current_time - last_time > 1.0:
        fps = frame_count / (current_time - last_time)
        window.title(f"Basic MPM Simulation - fps: {fps:.1f}")
        frame_count = 0
        last_time = current_time

    # グリッドのリセット
    grid_mass.fill(0)
    grid_vel.fill(0)

    # ステップ1: P2G
    for p in particles:
        # 粒子の座標から、どのグリッドセルの間にいるか計算
        grid_pos = p.pos / DX
        # 左下のノード（格子点）のインデックス（intにキャスト）
        base_node = grid_pos.astype(int)
        # 左下のノード（格子点）からの相対距離
        fx = grid_pos - base_node

        # バイリニア補間の重みを計算
        w = [
            (1 - fx[0]) * (1 - fx[1]),  # 左下(w00)
            fx[0] * (1 - fx[1]),        # 右下(w10)
            (1 - fx[0]) * fx[1],        # 左上(w01)
            fx[0] * fx[1]               # 右上(w11)
        ]

        # 周囲4点のグリッドに質量と運動量を分配
        for i in range(2):  # Y方向 (0 or 1)
            for j in range(2):  # X方向 (0 or 1)
                # グリッドインデックスが範囲内かチェック
                node_idx_y = base_node[1] + i
                node_idx_x = base_node[0] + j
                if 0 <= node_idx_x < N_GRID_SIDE and 0 <= node_idx_y < N_GRID_SIDE:
                    weight_index = i * 2 + j
                    weight = w[weight_index]
                    node_idx = (base_node[1] + i, base_node[0] + j)
                    # 質量を送信
                    grid_mass[node_idx] += weight * p.mass
                    # 運動量を送信
                    grid_vel[node_idx] += weight * p.mass * p.vel

    # ステップ2: グリッド上での計算
    # 運動量を質量で割り、速度に変換
    # 質量が0のままの速度は0のまま
    mass_filter = grid_mass > 1e-10 # ごくわずかな質量も考慮
    # 運動量を質量で割り、速度ベクトルに変換
    grid_vel[mass_filter] /= grid_mass[mass_filter, np.newaxis]

    # 重力を加える（質量があるすべての点に）
    grid_vel[mass_filter, 1] += DT * GRAVITY

    # 境界条件（4方の壁）
    # X方向の壁
    grid_vel[:, 0, 0][grid_vel[:, 0, 0] < 0] = 0    # 左壁
    grid_vel[:, N_GRID_SIDE - 1, 0][grid_vel[:, N_GRID_SIDE - 1, 0] > 0] = 0    # 右壁
    # Y方向の壁
    grid_vel[0, :, 1][grid_vel[0, :, 1] < 0] = 0    # 床より下に行こうとしたら止める
    grid_vel[N_GRID_SIDE - 1, :, 1][grid_vel[N_GRID_SIDE - 1, :, 1] > 0] = 0    # 天井より上に行こうとしたらとめる

    # ステップ3: G2P
    for p in particles:
        # 同様に、近傍グリッドとその重みを計算
        grid_pos = p.pos / DX
        base_node = grid_pos.astype(int)
        fx = grid_pos - base_node

        w = [
            (1.0 - fx[0]) * (1.0 - fx[1]),
            fx[0] * (1.0 - fx[1]),
            (1.0 - fx[0]) * fx[1],
            fx[0] * fx[1]
        ]

        # グリッドから補間して新しい速度を計算
        new_vel = np.zeros(2)
        for i in range(2):  # Y軸
            for j in range(2):  # X軸
                # グリッドインデックスが範囲内かチェック
                node_idx_y = base_node[1] + i
                node_idx_x = base_node[0] + j
                if 0 <= node_idx_x < N_GRID_SIDE and 0 <= node_idx_y < N_GRID_SIDE:
                    weight_index = i * 2 + j
                    weight = w[weight_index]
                    node_idx = (base_node[1] + i, base_node[0] + j)
                    new_vel += weight * grid_vel[node_idx]

        p.vel = new_vel
        p.pos += DT * p.vel

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
