import tkinter as tk
import random
import time

# パラメータ
WIN_X, WIN_Y = 800, 800 # ウィンドウ
DT = 1e-4   # 極小時間
UPDATES_PER_FRAME = 10  # 1フレームごとの計算回数
PARTICLE_RADIUS_PX = 15 # 粒子の半径（ピクセル）
PARTICLE_RADIUS_NORM = PARTICLE_RADIUS_PX / WIN_X   # 粒子の半径（正規化座標）
NUM_PARTICLES = 30  # 粒子の数

# 物理状態変数
gravity = [0.0, -9.8]   # 重力
restitution = 0.8   #　反発係数
K_SPRING = 5000.0 # 粒子間の反発係数（バネ定数）

# グローバル変数
particles = []  # 粒子のリスト
# FPS計算用の変数
last_time, frame_count, fps = 0, 0, 0
sum_fps, update_count, average_fps = 0, 0, 0.0

class Particle:
    def __init__(self, x, y, vx, vy, radius, color, canvas):
        self.pos = [x, y]
        self.vel = [vx, vy]
        self.force = [0.0, 0.0] # 粒子に働く力の合計
        self.mass = 1.0 # 粒子の質量
        self.radius = radius
        self.color = color
        self.canvas = canvas
        self.id = None  # 描画用のID、最初はNoneにしておき、draw関数で作成

    def apply_force(self, f):
        """ 粒子に力を加える """
        self.force[0] += f[0]
        self.force[1] += f[1]

    def update_physics(self):
        """ 力の合計に基づいて物理状態を更新する """
        # 加速度を計算
        ax = self.force[0] / self.mass
        ay = self.force[1] / self.mass

        # 速度の更新
        self.vel[0] += ax * DT
        self.vel[1] += ay * DT

        # 位置の更新
        self.pos[0] += self.vel[0] * DT
        self.pos[1] += self.vel[1] * DT

        # 壁との衝突判定と処理
        # 右壁
        if self.pos[0] + self.radius > 1.0:
            self.pos[0] = 1.0 - self.radius
            self.vel[0] *= -restitution
        # 左壁
        if self.pos[0] - self.radius < 0:
            self.pos[0] = self.radius
            self.vel[0] *= -restitution
        # 天井
        if self.pos[1] + self.radius > 1.0:
            self.pos[1] = 1.0 - self.radius
            self.vel[1] *= -restitution
        # 床
        if self.pos[1] - self.radius < 0:
            self.pos[1] = self.radius
            self.vel[1] *= -restitution

    def draw(self):
        # 現在の粒子の位置をキャンバスに描画する(正規 -> ピクセル化)
        px = self.pos[0] * WIN_X
        py = (1 - self.pos[1]) * WIN_Y

        x0 = px - PARTICLE_RADIUS_PX
        y0 = py - PARTICLE_RADIUS_PX
        x1 = px + PARTICLE_RADIUS_PX
        y1 = py + PARTICLE_RADIUS_PX

        # もし初回描画なら図形を生成、そうでなければ移動
        if self.id is None:
            self.id = self.canvas.create_oval(x0, y0, x1, y1, fill=self.color, outline="")
        else:
            self.canvas.coords(self.id, x0, y0, x1, y1)

# 関数定義
# 粒子の初期化
def particles_init():
    global particles
    particles = []

    # 色の候補リスト
    color_palette = [
        "#FF6B6B", "#FFD166", "#06D6A0", "#118AB2", "#073B4C",
        "#F7B267", "#F79D65", "#F4845F", "#F27059", "#F25C54"
    ]

    for _ in range(NUM_PARTICLES):
        x = random.uniform(0.1, 0.9)
        y = random.uniform(0.1, 0.9)
        vx, vy = 0.0, 0.0
        color = random.choice(color_palette)

        p = Particle(x, y, vx, vy, PARTICLE_RADIUS_NORM, color, canvas)
        particles.append(p)

def handle_particle_collisions():
    """ すべての粒子ペアの衝突を処理する """
    for i in range(NUM_PARTICLES):
        for j in range(i + 1, NUM_PARTICLES):
            p1 = particles[i]
            p2 = particles[j]

            dist_x = p2.pos[0] - p1.pos[0]
            dist_y = p2.pos[1] - p1.pos[1]
            dist_sq = dist_x**2 + dist_y**2

            # 衝突判定（半径の合計の2乗と比較）
            sum_radii = p1.radius + p2.radius
            # 粒子同士が衝突している場合
            if dist_sq < sum_radii**2 and dist_sq > 0.0:
                dist = dist_sq**0.5
                overlap = sum_radii - dist

                # 反発力（バネ力）を計算（大きさ）
                force_magnitude = K_SPRING * overlap

                # 力の方向（p1からp2へ）（向き）
                norm_x = dist_x / dist
                norm_y = dist_y / dist

                # 両方の粒子に力を加える（作用・反作用）
                force_vec = [force_magnitude * norm_x, force_magnitude * norm_y]
                p1.apply_force([-force_vec[0], -force_vec[1]])    # force_vecの向きが p1 -> p2 故
                p2.apply_force(force_vec)

# メインループ
def main_loop():
    global last_time, frame_count, fps,sum_fps, update_count, average_fps

    # FPS計算ロジック
    current_time = time.time()
    frame_count += 1
    # 1秒以上経過したらFPSを計算して表示を更新
    if current_time - last_time > 1.0:
        fps = frame_count / (current_time - last_time)
        sum_fps += fps
        update_count += 1
        average_fps = sum_fps / update_count
        window.title(f"Basic MPM Simulator - FPS: {fps:.1f} - Ave-FPS: {average_fps:.1f}")
        frame_count = 0
        last_time = current_time

    # 物理計算
    for _ in range(UPDATES_PER_FRAME):
        # 全ての粒子の力をリセットし、重力を加える
        for p in particles:
            p.force = [0.0, 0.0]
            p.apply_force([p.mass * gravity[0], p.mass * gravity[1]])

        # 粒子間の衝突力を計算して加える
        handle_particle_collisions()

        # 計算された力に基づいて、全粒子の物理状態を更新
        for p in particles:
            p.update_physics()

    # 描画
    for p in particles:
        p.draw()

    # 1msごとにこの関数を呼び出し、可能な限り高速にループさせる
    window.after(1, main_loop)

# GUIセットアップと実行
window = tk.Tk()
window.title("Basic MPM Simulator")
window.geometry(f"{WIN_X}x{WIN_Y}")
window.resizable(False, False)

# キャンバスの作成
canvas = tk.Canvas(window, width=WIN_X, height=WIN_Y, bg="#4D4D4D", highlightthickness=0)
canvas.pack()

# 初期化
particles_init()

# メインループを開始
main_loop()

# ウィンドウイベントループを開始
window.mainloop()