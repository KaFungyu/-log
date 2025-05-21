import tkinter as tk
from tkinter import messagebox
import random
import time
from PIL import ImageGrab
import os
from datetime import datetime

# 名字列表
names = ["黄珂明", "黄少华", "甘国庆", "尹秋峰", 
         "冯所利", "欧阳志光", "孙顺清", "梁伦鹏", "赖秋平",
         "虞超", "廖泽雄", "于潼", "李秋生", "李煌山",
         "陈怡昆", "何绮霞", "余嘉峰", "罗文涛", "吴亚涛",
         "李庆刚"]

class LotteryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("抽奖系统")
        
        # 创建截图保存目录
        self.screenshot_dir = "抽奖结果截图"
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)
        
        # 设置窗口大小和位置
        window_width = 1200
        window_height = 800
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建左侧设置区域
        self.left_frame = tk.Frame(root, padx=10, pady=10)
        self.left_frame.pack(side="left", fill="y")
        
        # 奖项设置区域
        self.prize_frame = tk.LabelFrame(self.left_frame, text="奖项设置", padx=10, pady=5, font=('微软雅黑', 14))
        self.prize_frame.pack(fill="x", padx=5, pady=5)
        
        # 剩余人数显示
        self.remaining_label = tk.Label(self.prize_frame, text=f"剩余人数：{len(names)}", font=('微软雅黑', 16))
        self.remaining_label.pack(pady=5)
        
        # 特等奖设置
        self.special_frame = tk.Frame(self.prize_frame)
        self.special_frame.pack(fill="x", pady=2)
        tk.Label(self.special_frame, text="特等奖人数:", font=('微软雅黑', 14), width=10).grid(row=0, column=0, sticky="e")
        self.special_count = tk.Entry(self.special_frame, width=6, font=('微软雅黑', 14))
        self.special_count.grid(row=0, column=1, padx=(0,20))
        tk.Label(self.special_frame, text="奖品:", font=('微软雅黑', 14), width=5).grid(row=0, column=2)
        self.special_prize = tk.Entry(self.special_frame, width=10, font=('微软雅黑', 14))
        self.special_prize.grid(row=0, column=3)
        
        # 一等奖设置
        self.first_frame = tk.Frame(self.prize_frame)
        self.first_frame.pack(fill="x", pady=2)
        tk.Label(self.first_frame, text="一等奖人数:", font=('微软雅黑', 14), width=10).grid(row=0, column=0, sticky="e")
        self.first_count = tk.Entry(self.first_frame, width=6, font=('微软雅黑', 14))
        self.first_count.grid(row=0, column=1, padx=(0,20))
        tk.Label(self.first_frame, text="*", fg="red", font=('微软雅黑', 14)).grid(row=0, column=1, sticky="e")
        tk.Label(self.first_frame, text="奖品:", font=('微软雅黑', 14), width=5).grid(row=0, column=2)
        self.first_prize = tk.Entry(self.first_frame, width=10, font=('微软雅黑', 14))
        self.first_prize.grid(row=0, column=3)
        
        # 二等奖设置
        self.second_frame = tk.Frame(self.prize_frame)
        self.second_frame.pack(fill="x", pady=2)
        tk.Label(self.second_frame, text="二等奖人数:", font=('微软雅黑', 14), width=10).grid(row=0, column=0, sticky="e")
        self.second_count = tk.Entry(self.second_frame, width=6, font=('微软雅黑', 14))
        self.second_count.grid(row=0, column=1, padx=(0,20))
        tk.Label(self.second_frame, text="*", fg="red", font=('微软雅黑', 14)).grid(row=0, column=1, sticky="e")
        tk.Label(self.second_frame, text="奖品:", font=('微软雅黑', 14), width=5).grid(row=0, column=2)
        self.second_prize = tk.Entry(self.second_frame, width=10, font=('微软雅黑', 14))
        self.second_prize.grid(row=0, column=3)
        
        # 三等奖设置
        self.third_frame = tk.Frame(self.prize_frame)
        self.third_frame.pack(fill="x", pady=2)
        tk.Label(self.third_frame, text="三等奖人数:", font=('微软雅黑', 14), width=10).grid(row=0, column=0, sticky="e")
        self.third_count = tk.Entry(self.third_frame, width=6, font=('微软雅黑', 14))
        self.third_count.grid(row=0, column=1, padx=(0,20))
        tk.Label(self.third_frame, text="*", fg="red", font=('微软雅黑', 14)).grid(row=0, column=1, sticky="e")
        tk.Label(self.third_frame, text="奖品:", font=('微软雅黑', 14), width=5).grid(row=0, column=2)
        self.third_prize = tk.Entry(self.third_frame, width=10, font=('微软雅黑', 14))
        self.third_prize.grid(row=0, column=3)
        
        # 配置列宽
        for frame in [self.special_frame, self.first_frame, self.second_frame, self.third_frame]:
            frame.grid_columnconfigure(0, minsize=120)  # 奖项名称列
            frame.grid_columnconfigure(1, minsize=60)   # 人数输入框列
            frame.grid_columnconfigure(2, minsize=60)   # "奖品:"标签列
            frame.grid_columnconfigure(3, minsize=120)  # 奖品输入框列
        
        # 抽奖显示区域
        self.rolling_frame = tk.LabelFrame(self.left_frame, text="抽奖进行中", padx=10, pady=5, font=('微软雅黑', 16))
        self.rolling_frame.pack(fill="x", pady=5, padx=5)
        self.rolling_label = tk.Label(self.rolling_frame, text="", font=('微软雅黑', 60, 'bold'))
        self.rolling_label.pack(pady=30)
        
        # 按钮区域
        self.button_frame = tk.Frame(self.left_frame)
        self.button_frame.pack(pady=5)
        
        self.draw_button = tk.Button(self.button_frame, text="开始/停止", command=self.toggle_drawing, font=('微软雅黑', 14))
        self.draw_button.pack(side="left", padx=5)
        
        self.start_button = tk.Button(self.button_frame, text="开始抽奖", command=self.start_lottery, font=('微软雅黑', 14))
        self.start_button.pack(side="left", padx=5)
        
        # 创建右侧结果显示区域
        self.result_frame = tk.Frame(root, padx=10, pady=10)
        self.result_frame.pack(side="right", fill="both", expand=True)
        
        # 创建四列显示区域
        self.columns_frame = tk.Frame(self.result_frame)
        self.columns_frame.pack(fill="both", expand=True)
        
        # 创建四个结果列
        self.create_result_columns()
        
        # 初始化变量
        self.current_prize = None
        self.remaining_count = 0
        self.winners = {'特等奖': [], '一等奖': [], '二等奖': [], '三等奖': []}
        self.available_participants = names.copy()
        self.drawing_in_progress = False
        self.is_rolling = False
        self.rolling_job = None
        
        # 添加按钮悬停效果
        self.draw_button.bind("<Enter>", lambda e: e.widget.config(bg="#4a90e2", fg="white"))
        self.draw_button.bind("<Leave>", lambda e: e.widget.config(bg="SystemButtonFace", fg="black"))
        self.start_button.bind("<Enter>", lambda e: e.widget.config(bg="#4a90e2", fg="white"))
        self.start_button.bind("<Leave>", lambda e: e.widget.config(bg="SystemButtonFace", fg="black"))
        
        # 添加快捷键
        self.root.bind('<space>', lambda e: self.toggle_drawing())
        self.root.bind('<Return>', lambda e: self.start_lottery())
        self.root.bind('<Escape>', lambda e: self.finish_lottery())
        
    def create_result_columns(self):
        # 创建四列标签和文本框
        columns = ['三等奖', '二等奖', '一等奖', '特等奖']
        self.result_texts = {}
        
        for i, prize in enumerate(columns):
            frame = tk.Frame(self.columns_frame)
            frame.pack(side="left", fill="both", expand=True, padx=5)
            
            tk.Label(frame, text=prize, font=('微软雅黑', 16, 'bold')).pack()
            text = tk.Text(frame, height=20, width=12, font=('微软雅黑', 14))
            text.pack(fill="both", expand=True)
            self.result_texts[prize] = text

    def toggle_drawing(self):
        if not self.drawing_in_progress:
            return
            
        if self.is_rolling:
            self.stop_rolling()
        else:
            self.start_rolling()

    def start_rolling(self):
        self.is_rolling = True
        self.roll_names()

    def stop_rolling(self):
        if self.rolling_job:
            self.root.after_cancel(self.rolling_job)
        self.is_rolling = False
        self.draw_next()

    def roll_names(self):
        if not self.is_rolling:
            return
            
        # 使用列表索引而不是random.choice，提高性能
        idx = random.randint(0, len(self.available_participants) - 1)
        name = self.available_participants[idx]
        self.rolling_label.config(text=name)
        
        # 根据奖项设置不同的滚动速度
        base_delay = 50  # 基础延迟时间
        if self.current_prize == "三等奖":
            delay = base_delay
        elif self.current_prize == "二等奖":
            delay = int(base_delay * 0.8)  # 比三等奖快20%
        elif self.current_prize == "一等奖":
            delay = int(base_delay * 0.6)  # 比三等奖快40%
        else:  # 特等奖
            delay = int(base_delay * 0.4)  # 比三等奖快60%
        
        # 在即将结束时降低速度
        if len(self.available_participants) <= 5:
            delay *= 2
        
        self.rolling_job = self.root.after(delay, self.roll_names)

    def draw_next(self):
        if not self.drawing_in_progress or self.remaining_count <= 0:
            return
            
        # 使用当前显示的名字作为获奖者
        winner = self.rolling_label.cget("text")
        if winner in self.available_participants:
            self.available_participants.remove(winner)
            
            # 更新当前奖项的获奖者列表
            self.winners[self.current_prize].append(winner)
            
            # 更新显示
            self.update_result_display()
            self.remaining_count -= 1
            
            # 更新剩余人数显示
            self.update_remaining_label()
            
            # 检查是否需要切换奖项
            if self.remaining_count == 0:
                self.switch_to_next_prize()

    def update_result_display(self):
        for prize, winners in self.winners.items():
            if winners:
                text = self.result_texts[prize]
                text.config(state='normal')  # 允许修改
                text.delete("1.0", tk.END)
                
                # 获取对应的奖品
                prize_text = ""
                if prize == "特等奖":
                    prize_text = self.special_prize.get()
                elif prize == "一等奖":
                    prize_text = self.first_prize.get()
                elif prize == "二等奖":
                    prize_text = self.second_prize.get()
                elif prize == "三等奖":
                    prize_text = self.third_prize.get()
                
                # 如果有奖品说明，先显示奖品
                if prize_text:
                    text.insert(tk.END, f"[{prize_text}]\n")
                    text.insert(tk.END, "-" * 15 + "\n")
                
                # 显示所有获奖者
                for winner in winners:
                    text.insert(tk.END, f"{winner}\n")
                
                text.config(state='disabled')  # 禁止修改
                text.see(tk.END)  # 滚动到最新内容

    def switch_to_next_prize(self):
        if self.current_prize == "三等奖":
            self.current_prize = "二等奖"
            self.remaining_count = int(self.second_count.get())
            self.is_rolling = False
            self.rolling_label.config(text="准备抽取二等奖")
            self.rolling_frame.config(text=f"抽奖进行中 - 正在抽取{self.current_prize}")
        elif self.current_prize == "二等奖":
            self.current_prize = "一等奖"
            self.remaining_count = int(self.first_count.get())
            self.is_rolling = False
            self.rolling_label.config(text="准备抽取一等奖")
            self.rolling_frame.config(text=f"抽奖进行中 - 正在抽取{self.current_prize}")
        elif self.current_prize == "一等奖":
            # 检查特等奖人数
            special_text = self.special_count.get().strip()
            if special_text and int(special_text) > 0:  # 只有在特等奖有效时才抽取
                self.current_prize = "特等奖"
                self.remaining_count = int(special_text)
                self.is_rolling = False
                self.rolling_label.config(text="准备抽取特等奖")
                self.rolling_frame.config(text=f"抽奖进行中 - 正在抽取{self.current_prize}")
            else:
                self.finish_lottery()
        elif self.current_prize == "特等奖":
            self.finish_lottery()

    def validate_inputs(self):
        try:
            # 特等奖可以为空或0，不进行验证
            special_text = self.special_count.get().strip()
            special = int(special_text) if special_text else 0
            
            # 验证其他必填项
            first = int(self.first_count.get().strip())
            second = int(self.second_count.get().strip())
            third = int(self.third_count.get().strip())
            
            if first < 1:
                messagebox.showerror("错误", "一等奖人数必须大于0！")
                return False
            if second < 1:
                messagebox.showerror("错误", "二等奖人数必须大于0！")
                return False
            if third < 1:
                messagebox.showerror("错误", "三等奖人数必须大于0！")
                return False
            
            # 计算总人数时只计算有效的特等奖
            total = first + second + third
            if special > 0:  # 只有在特等奖大于0时才计入总数
                total += special
            
            if total > len(names):
                messagebox.showerror("错误", f"总中奖人数({total})超过参与人数({len(names)})！")
                return False
            
            return True
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字！")
            return False
            
    def start_lottery(self):
        if not self.validate_inputs():
            return
            
        # 获取各奖项人数，特等奖可以为空或0
        special_text = self.special_count.get().strip()
        special_count = int(special_text) if special_text else 0
        first_count = int(self.first_count.get())
        second_count = int(self.second_count.get())
        third_count = int(self.third_count.get())
        
        # 检查总人数时只计算大于0的特等奖
        total_winners = (special_count if special_count > 0 else 0) + first_count + second_count + third_count
        if total_winners > len(names):
            messagebox.showerror("错误", "中奖人数超过参与人数！")
            return
            
        # 清空右侧显示区域
        for text in self.result_texts.values():
            text.config(state='normal')
            text.delete("1.0", tk.END)
            text.config(state='disabled')
        
        # 重置获奖者列表和可用参与者
        self.winners = {'特等奖': [], '一等奖': [], '二等奖': [], '三等奖': []}
        self.available_participants = names.copy()
        
        # 重置抽奖显示区域
        self.rolling_label.config(text="")
        self.rolling_frame.config(text="抽奖进行中 - 正在抽取三等奖")
        
        # 开始抽三等奖
        self.current_prize = "三等奖"
        self.remaining_count = third_count
        self.drawing_in_progress = True
        self.draw_button.config(state="normal")
        self.start_button.config(state="disabled")  # 禁用开始按钮
        
        # 更新剩余人数显示
        self.update_remaining_label()

    def finish_lottery(self):
        self.drawing_in_progress = False
        self.draw_button.config(state="disabled")
        self.start_button.config(state="normal")  # 启用开始按钮
        self.rolling_label.config(text="抽奖结束！")
        self.rolling_frame.config(text="抽奖进行中")  # 重置标题
        
        # 在抽奖结束时自动截图
        self.take_screenshot()

    def take_screenshot(self):
        try:
            # 等待一小段时间让界面完全更新
            self.root.after(100, self._capture_screenshot)
        except Exception as e:
            messagebox.showerror("错误", f"截图失败：{str(e)}")
    
    def _capture_screenshot(self):
        try:
            # 获取窗口位置和大小
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            
            # 截取窗口区域
            screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
            
            # 生成文件名（使用当前时间）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.screenshot_dir, f"抽奖结果_{timestamp}.png")
            
            # 保存截图
            screenshot.save(filename)
            messagebox.showinfo("提示", f"截图已保存至：{filename}")
        except Exception as e:
            messagebox.showerror("错误", f"截图保存失败：{str(e)}")

    def update_remaining_label(self):
        remaining = len(self.available_participants)
        self.remaining_label.config(text=f"剩余人数：{remaining}")
        # 强制更新显示
        self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = LotteryApp(root)
    root.mainloop()
