import tkinter as tk
from tkinter import messagebox
import random

# --- 主题颜色和符号 ---
COLOR_BACKGROUND = "#1A1A2E"  # 深海军蓝/紫色
COLOR_CELL_COVERED = "#2D2D44" # 较深的格子颜色
COLOR_CELL_REVEALED = "#4A4A6A" # 揭开的空格子颜色
COLOR_MINE_EXPLODED = "#FF4136"  # 爆炸的地雷 (红色)
COLOR_MINE_REVEALED_END = "#FFA500" # 游戏结束时显示的地雷 (橙色)
COLOR_FLAG = "#FFD700"      # 旗帜颜色 (金色/黄色)
COLOR_TEXT_DEFAULT = "#E0E0E0" # 默认文字颜色 (浅灰色)
COLOR_BUTTON_NORMAL = "#3D3D5A"
COLOR_BUTTON_ACTIVE = "#505070"

NUMBER_COLORS = {
    0: COLOR_CELL_REVEALED, # 0 通常不显示数字，但背景色一致
    1: "#00FFFF",  # 青色 (Cyan)
    2: "#00FF00",  # 霓虹绿 (Neon Green)
    3: "#FF00FF",  # 品红 (Magenta)
    4: "#FFFF00",  # 黄色 (Yellow)
    5: "#FF8C00",  # 深橙色 (DarkOrange)
    6: "#40E0D0",  # 绿松石色 (Turquoise)
    7: "#8A2BE2",  # 蓝紫色 (BlueViolet)
    8: "#7FFF00",  # 黄绿色 (Chartreuse)
}

SYMBOL_MINE = "💥"
SYMBOL_FLAG = "👽"
SYMBOL_COVERED = ""
SYMBOL_WRONG_FLAG = "❌"


class MinesweeperGame:
    def __init__(self, rows, cols, num_mines):
        self.rows = rows
        self.cols = cols
        self.num_mines = num_mines
        self.first_click_done = False
        self.reset_game()

    def reset_game(self):
        self.board = [[' ' for _ in range(self.cols)] for _ in range(self.rows)]
        self.mines_locations = set()
        self.revealed = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.flagged = [[False for _ in range(self.cols)] for _ in range(self.rows)]
        self.game_over = False
        self.won = False
        self.first_click_done = False
        self.mines_flagged_count = 0
        self.cells_revealed_count = 0

    def place_mines(self, first_click_r, first_click_c):
        available_spots = []
        for r in range(self.rows):
            for c in range(self.cols):
                # 确保第一个点击的格子及其周围（可选，此处简化为仅第一个点击的格子）不是雷
                if abs(r - first_click_r) > 0 or abs(c - first_click_c) > 0: # 至少保证第一个点的格子不是雷
                     available_spots.append((r, c))

        if len(available_spots) < self.num_mines: # 检查是否有足够的位置放雷
            # 这通常发生在板子太小或雷太多的情况下
            # 为了简单起见，我们直接使用所有位置，并接受第一个点击可能是雷的风险
            # 或者，更好的做法是调整雷的数量或板子大小
            print("警告: 雷太多或板子太小，无法保证首次点击安全。")
            available_spots = []
            for r in range(self.rows):
                for c in range(self.cols):
                    if r != first_click_r or c != first_click_c:
                        available_spots.append((r,c))
            if not available_spots: # 如果连一个非首次点击位置都没有（比如1x1的板）
                 messagebox.showerror("错误", "板子太小，无法放置地雷。")
                 return


        random.shuffle(available_spots)
        for r, c in available_spots[:self.num_mines]:
            self.mines_locations.add((r, c))

        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) in self.mines_locations:
                    self.board[r][c] = SYMBOL_MINE
                else:
                    count = self.count_adjacent_mines(r, c)
                    self.board[r][c] = count
        self.first_click_done = True


    def count_adjacent_mines(self, r, c):
        count = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols and (nr, nc) in self.mines_locations:
                    count += 1
        return count

    def reveal_cell(self, r, c):
        if self.game_over or self.revealed[r][c] or self.flagged[r][c]:
            return False # 没有变化

        if not self.first_click_done:
            self.place_mines(r, c)
            # 如果place_mines后第一个点击的格子恰好是数字0，则place_mines后board[r][c]会是0
            # 如果place_mines后第一个点击的格子是数字，board[r][c]会是数字

        self.revealed[r][c] = True
        self.cells_revealed_count += 1

        if (r, c) in self.mines_locations:
            self.game_over = True
            self.won = False
            return True # 踩雷了

        if self.board[r][c] == 0:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        self.reveal_cell(nr, nc) # 递归揭开

        self.check_win()
        return True # 成功揭开

    def toggle_flag(self, r, c):
        if self.game_over or self.revealed[r][c]:
            return False

        if self.flagged[r][c]:
            self.flagged[r][c] = False
            self.mines_flagged_count -= 1
        else:
            self.flagged[r][c] = True
            self.mines_flagged_count += 1
        return True

    def check_win(self):
        if self.cells_revealed_count == (self.rows * self.cols) - self.num_mines:
            self.game_over = True
            self.won = True
            # 自动标记所有剩余的雷
            for r_mine, c_mine in self.mines_locations:
                if not self.flagged[r_mine][c_mine]:
                    self.flagged[r_mine][c_mine] = True
                    self.mines_flagged_count +=1


    def get_neighbors(self, r, c):
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append((nr, nc))
        return neighbors

class MinesweeperUI:
    def __init__(self, master, rows=10, cols=10, num_mines=15):
        self.master = master
        self.rows = rows
        self.cols = cols
        self.num_mines = num_mines

        self.game = MinesweeperGame(rows, cols, num_mines)

        master.title("外星扫雷 (Alien Minesweeper)")
        master.configure(bg=COLOR_BACKGROUND)

        # --- 控制面板 ---
        self.controls_frame = tk.Frame(master, bg=COLOR_BACKGROUND)
        self.controls_frame.pack(pady=10)

        self.reset_button = tk.Button(self.controls_frame, text="重置游戏", command=self.reset_game_ui,
                                      bg=COLOR_BUTTON_NORMAL, fg=COLOR_TEXT_DEFAULT, relief=tk.FLAT,
                                      activebackground=COLOR_BUTTON_ACTIVE, activeforeground=COLOR_TEXT_DEFAULT)
        self.reset_button.pack(side=tk.LEFT, padx=5)

        self.autosolve_button = tk.Button(self.controls_frame, text="自动清除一步", command=self.auto_solve_step,
                                           bg=COLOR_BUTTON_NORMAL, fg=COLOR_TEXT_DEFAULT, relief=tk.FLAT,
                                           activebackground=COLOR_BUTTON_ACTIVE, activeforeground=COLOR_TEXT_DEFAULT)
        self.autosolve_button.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(self.controls_frame, text="", font=("Arial", 12),
                                     bg=COLOR_BACKGROUND, fg=COLOR_TEXT_DEFAULT)
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.mines_remaining_label = tk.Label(self.controls_frame, text="", font=("Arial", 12),
                                             bg=COLOR_BACKGROUND, fg=COLOR_TEXT_DEFAULT)
        self.mines_remaining_label.pack(side=tk.LEFT, padx=10)


        # --- 游戏面板 ---
        self.board_frame = tk.Frame(master, bg=COLOR_BACKGROUND)
        self.board_frame.pack()

        self.buttons = [[None for _ in range(cols)] for _ in range(rows)]
        self.create_board_ui()
        self.update_status_labels()

    def create_board_ui(self):
        for r in range(self.rows):
            for c in range(self.cols):
                button = tk.Button(self.board_frame, text=SYMBOL_COVERED, width=2, height=1,
                                   font=("Arial", 14, "bold"),
                                   bg=COLOR_CELL_COVERED, fg=COLOR_TEXT_DEFAULT,
                                   activebackground=COLOR_CELL_REVEALED, # 点击时的背景色
                                   relief=tk.RAISED, bd=1)
                button.grid(row=r, column=c, padx=1, pady=1)
                button.bind("<Button-1>", lambda e, r=r, c=c: self.on_left_click(r, c)) # 左键点击
                button.bind("<Button-3>", lambda e, r=r, c=c: self.on_right_click(r, c)) # 右键点击 (Windows/Linux)
                button.bind("<Button-2>", lambda e, r=r, c=c: self.on_right_click(r, c)) # 右键点击 (MacOS)
                self.buttons[r][c] = button

    def reset_game_ui(self):
        self.game.reset_game()
        for r in range(self.rows):
            for c in range(self.cols):
                self.buttons[r][c].config(text=SYMBOL_COVERED, bg=COLOR_CELL_COVERED, relief=tk.RAISED, state=tk.NORMAL, fg=COLOR_TEXT_DEFAULT)
        self.autosolve_button.config(state=tk.NORMAL)
        self.update_status_labels()


    def on_left_click(self, r, c):
        if self.game.game_over or self.game.flagged[r][c] or self.game.revealed[r][c]:
            return

        cell_changed = self.game.reveal_cell(r, c)

        if cell_changed:
            self.update_board_ui() # 更新整个面板以反映递归揭开
            self.update_status_labels()

        if self.game.game_over:
            self.handle_game_over()

    def on_right_click(self, r, c):
        if self.game.game_over or self.game.revealed[r][c]:
            return

        flag_toggled = self.game.toggle_flag(r, c)
        if flag_toggled:
            self.update_cell_display(r,c)
            self.update_status_labels()


    def update_board_ui(self):
        for r_idx in range(self.rows):
            for c_idx in range(self.cols):
                self.update_cell_display(r_idx, c_idx)

    def update_cell_display(self, r, c):
        button = self.buttons[r][c]
        if self.game.flagged[r][c]:
            button.config(text=SYMBOL_FLAG, bg=COLOR_FLAG, fg="black")
        elif not self.game.revealed[r][c]:
            button.config(text=SYMBOL_COVERED, bg=COLOR_CELL_COVERED, fg=COLOR_TEXT_DEFAULT)
        else: # Revealed
            content = self.game.board[r][c]
            if content == SYMBOL_MINE: # 踩到雷了 (只在游戏结束时，或被揭开时显示)
                button.config(text=SYMBOL_MINE, bg=COLOR_MINE_EXPLODED, fg="white")
            elif isinstance(content, int):
                if content == 0:
                    button.config(text=" ", bg=COLOR_CELL_REVEALED, relief=tk.SUNKEN)
                else:
                    button.config(text=str(content), fg=NUMBER_COLORS.get(content, COLOR_TEXT_DEFAULT),
                                  bg=COLOR_CELL_REVEALED, relief=tk.SUNKEN)
            else: # 理论上不应该到这里，除非board内容设置错误
                 button.config(text="?", bg="gray")

        if self.game.game_over:
            button.config(state=tk.DISABLED)
            if (r,c) in self.game.mines_locations and not self.game.revealed[r][c] and not self.game.flagged[r][c]:
                # 游戏结束时，显示所有未标记的雷
                button.config(text=SYMBOL_MINE, bg=COLOR_MINE_REVEALED_END, fg="black", relief=tk.FLAT)
            if self.game.flagged[r][c] and (r,c) not in self.game.mines_locations:
                # 标记错误
                button.config(text=SYMBOL_WRONG_FLAG, bg=COLOR_CELL_REVEALED, fg="red", relief=tk.FLAT)


    def update_status_labels(self):
        mines_to_find = self.game.num_mines - self.game.mines_flagged_count
        self.mines_remaining_label.config(text=f"剩余地雷: {mines_to_find} {SYMBOL_FLAG}")

        if self.game.game_over:
            if self.game.won:
                self.status_label.config(text="胜利! 🎉", fg="#00FF00")
            else:
                self.status_label.config(text="游戏结束 💥", fg="#FF4136")
            self.autosolve_button.config(state=tk.DISABLED)
        else:
            self.status_label.config(text="游戏中...", fg=COLOR_TEXT_DEFAULT)


    def handle_game_over(self):
        self.update_board_ui() # 确保所有格子都更新到最终状态
        self.update_status_labels()
        if self.game.won:
            messagebox.showinfo("外星扫雷", "恭喜！你清除了所有地雷！👽👍")
        else:
            # 找到第一个被揭开的雷来高亮显示 (如果需要)
            exploded_mine_button = None
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.game.revealed[r][c] and (r,c) in self.game.mines_locations:
                        exploded_mine_button = self.buttons[r][c]
                        break
                if exploded_mine_button:
                    break
            if exploded_mine_button:
                 exploded_mine_button.config(bg=COLOR_MINE_EXPLODED) # 特别高亮爆炸的那个

            messagebox.showerror("外星扫雷", "啊哦！你踩到地雷了！👾")

    def auto_solve_step(self):
        if self.game.game_over:
            return

        if not self.game.first_click_done:
            # 自动解谜器需要一个起点，随机点一个安全的
            # 为简单起见，让用户先点一下
            messagebox.showinfo("提示", "请先手动点击一个格子作为起点。")
            return

        made_a_move = False

        # 规则1: 如果一个已揭开的数字N，其周围已标记的旗帜数F等于N，则其周围所有其他未揭开的格子都是安全的
        for r in range(self.rows):
            for c in range(self.cols):
                if self.game.revealed[r][c] and isinstance(self.game.board[r][c], int) and self.game.board[r][c] > 0:
                    cell_value = self.game.board[r][c]
                    flagged_neighbors = 0
                    unrevealed_unflagged_neighbors = []

                    for nr, nc in self.game.get_neighbors(r, c):
                        if self.game.flagged[nr][nc]:
                            flagged_neighbors += 1
                        elif not self.game.revealed[nr][nc]:
                            unrevealed_unflagged_neighbors.append((nr, nc))

                    if flagged_neighbors == cell_value and unrevealed_unflagged_neighbors:
                        for nr_safe, nc_safe in unrevealed_unflagged_neighbors:
                            if not self.game.revealed[nr_safe][nc_safe] and not self.game.flagged[nr_safe][nc_safe]:
                                self.game.reveal_cell(nr_safe, nc_safe)
                                made_a_move = True
                                if self.game.game_over: # 如果自动解谜踩雷 (不应该发生，但以防万一)
                                    self.handle_game_over()
                                    return
                        if made_a_move: break # 做了一个动作就重新评估
            if made_a_move:
                self.update_board_ui()
                self.update_status_labels()
                if self.game.game_over: return # 检查游戏是否因揭开而结束
                 # return # 一次只执行一个类型的动作，或者继续找下一个

        if made_a_move and not self.game.game_over :
            # 如果因为上面的规则1揭开了格子，这里可以先返回，让用户看到变化
            # 或者继续执行规则2
             pass # 继续执行规则2

        # 规则2: 如果一个已揭开的数字N，其周围（未揭开+未标记旗帜的格子数U）+（已标记旗帜数F）= N，
        # 且 (N - F) = U， 那么所有U个格子都是地雷
        made_a_flag_move = False
        for r in range(self.rows):
            for c in range(self.cols):
                if self.game.revealed[r][c] and isinstance(self.game.board[r][c], int) and self.game.board[r][c] > 0:
                    cell_value = self.game.board[r][c]
                    flagged_neighbors_count = 0
                    unrevealed_unflagged_neighbors = []

                    for nr, nc in self.game.get_neighbors(r, c):
                        if self.game.flagged[nr][nc]:
                            flagged_neighbors_count += 1
                        elif not self.game.revealed[nr][nc]:
                            unrevealed_unflagged_neighbors.append((nr, nc))

                    # 如果 (单元格数字 - 已标记的邻居数) == 未揭开且未标记的邻居数
                    # 那么这些未揭开且未标记的邻居都是雷
                    if (cell_value - flagged_neighbors_count) == len(unrevealed_unflagged_neighbors) and unrevealed_unflagged_neighbors:
                        for nr_mine, nc_mine in unrevealed_unflagged_neighbors:
                            if not self.game.flagged[nr_mine][nc_mine]: # 确保只标记一次
                                self.game.toggle_flag(nr_mine, nc_mine)
                                made_a_flag_move = True
                                self.update_cell_display(nr_mine, nc_mine) # 只更新被标记的格子
                        if made_a_flag_move: break
            if made_a_flag_move: break

        if made_a_flag_move:
            self.update_status_labels() # 更新剩余雷数
            made_a_move = True # 标记有动作发生

        if not made_a_move:
            messagebox.showinfo("自动清除", "没有找到明确的下一步。")
        else:
            if self.game.won: # 检查自动操作后是否胜利
                self.handle_game_over()


if __name__ == "__main__":
    root = tk.Tk()
    # 游戏参数: 行数, 列数, 地雷数
    # 你可以修改这些值来改变游戏难度
    game_app = MinesweeperUI(root, rows=12, cols=12, num_mines=20)
    root.mainloop()