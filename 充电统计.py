import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import pickle  # 导入pickle模块

class ChargingCostCalculator:
    def __init__(self, master):
        self.master = master
        master.title("充电费用计算器")

        # 创建左右框架
        self.left_frame = tk.Frame(master)
        self.left_frame.pack(side=tk.LEFT, padx=20, pady=20)

        self.right_frame = tk.Frame(master)
        self.right_frame.pack(side=tk.RIGHT, padx=20, pady=20)

        # 初始化累计变量和记录列表
        self.total_kWh = 0.0
        self.total_cost = 0.0
        self.total_distance = 0.0  # 累计行驶里程
        self.records = []
        self.platforms = {}  # 用于存储每个平台的累计数据
        self.purchase_date = None  # 提车日期
        self.current_platform = None  # 当前充电平台

        # 左侧输入框
        self.date_label = tk.Label(self.left_frame, text="请输入提车日期（YYYY.MM.DD）:", font=("微软雅黑", 14))
        self.date_label.pack(pady=10)

        self.date_entry = tk.Entry(self.left_frame, font=("微软雅黑", 14))
        self.date_entry.pack(pady=10)

        self.set_date_button = tk.Button(self.left_frame, text="设置提车日期", font=("微软雅黑", 14), command=self.set_purchase_date)
        self.set_date_button.pack(pady=10)

        self.distance_label = tk.Label(self.left_frame, text="请输入行驶里程（km）:", font=("微软雅黑", 14))
        self.distance_label.pack(pady=10)

        self.distance_entry = tk.Entry(self.left_frame, font=("微软雅黑", 14))
        self.distance_entry.pack(pady=10)

        self.set_distance_button = tk.Button(self.left_frame, text="设置行驶里程", font=("微软雅黑", 14), command=self.set_distance)
        self.set_distance_button.pack(pady=10)

        self.platform_label = tk.Label(self.left_frame, text="充电平台:", font=("微软雅黑", 14))
        self.platform_label.pack(pady=10)

        self.platform_display = tk.Label(self.left_frame, text="未设置充电平台", font=("微软雅黑", 14))
        self.platform_display.pack(pady=10)

        self.platform_entry = tk.Entry(self.left_frame, font=("微软雅黑", 14))
        self.platform_entry.pack(pady=10)

        self.set_platform_button = tk.Button(self.left_frame, text="设置充电平台", font=("微软雅黑", 14), command=self.set_platform)
        self.set_platform_button.pack(pady=10)

        self.kWh_label = tk.Label(self.left_frame, text="请输入充电电量（kWh）:", font=("微软雅黑", 14))
        self.kWh_label.pack(pady=10)

        self.kWh_entry = tk.Entry(self.left_frame, font=("微软雅黑", 14))
        self.kWh_entry.pack(pady=10)

        self.cost_label = tk.Label(self.left_frame, text="请输入充电费用（元）:", font=("微软雅黑", 14))
        self.cost_label.pack(pady=10)

        self.cost_entry = tk.Entry(self.left_frame, font=("微软雅黑", 14))
        self.cost_entry.pack(pady=10)

        self.apply_button = tk.Button(self.left_frame, text="提交", font=("微软雅黑", 14), command=self.submit)
        self.apply_button.pack(pady=10)

        self.load_button = tk.Button(self.left_frame, text="加载数据", font=("微软雅黑", 14), command=self.load_data)
        self.load_button.pack(pady=10)

        # 右侧结果和操作
        self.result_label = tk.Label(self.right_frame, text="", font=("微软雅黑", 14))
        self.result_label.pack(pady=10)

        self.days_label = tk.Label(self.right_frame, text="", font=("微软雅黑", 14))
        self.days_label.pack(pady=10)

        self.records_listbox = tk.Listbox(self.right_frame, font=("微软雅黑", 14), width=50, selectmode=tk.MULTIPLE)
        self.records_listbox.pack(pady=10)

        self.delete_button = tk.Button(self.right_frame, text="删除选中记录", font=("微软雅黑", 14), command=self.delete_selected_records)
        self.delete_button.pack(pady=10)

        self.delete_all_button = tk.Button(self.right_frame, text="删除所有记录", font=("微软雅黑", 14), command=self.delete_all_records)
        self.delete_all_button.pack(pady=10)

        self.modify_button = tk.Button(self.right_frame, text="修改选中记录", font=("微软雅黑", 14), command=self.modify_record)
        self.modify_button.pack(pady=10)

        self.select_all_button = tk.Button(self.right_frame, text="全选/取消全选", font=("微软雅黑", 14), command=self.toggle_select_all)
        self.select_all_button.pack(pady=10)

        self.platform_summary_label = tk.Label(self.right_frame, text="", font=("微软雅黑", 14))
        self.platform_summary_label.pack(pady=10)

    def set_purchase_date(self):
        try:
            purchase_date_str = self.date_entry.get().strip()
            self.purchase_date = datetime.strptime(purchase_date_str, "%Y.%m.%d")
            self.update_days_label()
            messagebox.showinfo("成功", "提车日期已设置！")
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的日期（格式：YYYY.MM.DD）")

    def set_distance(self):
        try:
            distance_str = self.distance_entry.get().strip()
            self.total_distance = float(distance_str)
            messagebox.showinfo("成功", "行驶里程已设置！")
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的行驶里程（数字）")

    def set_platform(self):
        platform = self.platform_entry.get().strip()
        if platform:
            self.current_platform = platform  # 设置当前充电平台
            self.platform_display.config(text=f"当前充电平台: {platform}")  # 更新显示的充电平台
            messagebox.showinfo("成功", f"充电平台已设置为: {platform}")
        else:
            messagebox.showerror("输入错误", "请输入有效的充电平台")

    def update_days_label(self):
        if self.purchase_date:
            current_date = datetime.now()
            days_difference = (current_date - self.purchase_date).days
            self.days_label.config(text=f"提车至今共 {days_difference} 天")

    def submit(self):
        if not self.purchase_date:
            messagebox.showerror("错误", "请先设置提车日期")
            return

        if not self.current_platform:
            messagebox.showerror("错误", "请先设置充电平台")
            return

        try:
            kWh = float(self.kWh_entry.get())
            cost = float(self.cost_entry.get())

            # 累加充电度数和费用
            self.total_kWh += kWh
            self.total_cost += cost

            # 添加记录
            self.records.append((self.current_platform, kWh, cost, self.total_distance))
            self.update_records_listbox()

            # 更新平台统计
            if self.current_platform in self.platforms:
                self.platforms[self.current_platform]['kWh'] += kWh
                self.platforms[self.current_platform]['cost'] += cost
            else:
                self.platforms[self.current_platform] = {'kWh': kWh, 'cost': cost}

            self.update_platform_summary()

            # 计算每公里的费用
            cost_per_km = self.total_cost / self.total_distance if self.total_distance > 0 else 0

            # 更新结果标签
            today_date = datetime.now().strftime("%Y.%m.%d")
            self.result_label.config(text=f"累计充电度数: {self.total_kWh:.2f} kWh\n"
                                           f"累计充电费用: {self.total_cost:.2f} 元\n"
                                           f"每公里费用: {cost_per_km:.2f} 元/km\n"
                                           f"今天日期: {today_date}\n"
                                           f"提车日期: {self.purchase_date.strftime('%Y.%m.%d')}")
            self.update_days_label()  # 更新天数显示

            # 清空输入框
            self.kWh_entry.delete(0, tk.END)
            self.cost_entry.delete(0, tk.END)

            # 自动保存数据
            self.save_data()

        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字")

    def save_data(self):
        data = {
            'purchase_date': self.purchase_date,
            'total_kWh': self.total_kWh,
            'total_cost': self.total_cost,
            'total_distance': self.total_distance,
            'records': self.records,
            'platforms': self.platforms,
            'current_platform': self.current_platform  # 保存当前充电平台
        }
        with open('charging_data.pkl', 'wb') as f:
            pickle.dump(data, f)
        messagebox.showinfo("成功", "数据已保存！")

    def load_data(self):
        try:
            with open('charging_data.pkl', 'rb') as f:
                data = pickle.load(f)
                self.purchase_date = data['purchase_date']
                self.total_kWh = data['total_kWh']
                self.total_cost = data['total_cost']
                self.total_distance = data['total_distance']
                self.records = data['records']
                self.platforms = data['platforms']
                self.current_platform = data['current_platform']  # 加载当前充电平台

                # 更新界面
                self.date_entry.delete(0, tk.END)
                self.date_entry.insert(0, self.purchase_date.strftime('%Y.%m.%d'))
                self.distance_entry.delete(0, tk.END)
                self.distance_entry.insert(0, str(self.total_distance))
                self.update_records_listbox()
                self.update_platform_summary()
                self.update_days_label()

                # 更新显示的充电平台
                self.platform_display.config(text=f"当前充电平台: {self.current_platform}")

                # 计算今天日期和每公里费用
                today_date = datetime.now().strftime("%Y.%m.%d")
                cost_per_km = self.total_cost / self.total_distance if self.total_distance > 0 else 0

                # 更新结果标签
                self.result_label.config(text=f"累计充电度数: {self.total_kWh:.2f} kWh\n"
                                               f"累计充电费用: {self.total_cost:.2f} 元\n"
                                               f"每公里费用: {cost_per_km:.2f} 元/km\n"
                                               f"今天日期: {today_date}\n"
                                               f"提车日期: {self.purchase_date.strftime('%Y.%m.%d')}")
                messagebox.showinfo("成功", "数据已加载！")
                
                # 自动保存加载后的数据
                self.save_data()
        except FileNotFoundError:
            messagebox.showerror("错误", "未找到保存的数据文件！")
        except Exception as e:
            messagebox.showerror("错误", f"加载数据时发生错误: {e}")

    def update_records_listbox(self):
        self.records_listbox.delete(0, tk.END)  # 清空列表框
        for platform, kWh, cost, distance in self.records:
            self.records_listbox.insert(tk.END, f"平台: {platform}, 充电度数: {kWh:.2f} kWh, 费用: {cost:.2f} 元, 行驶里程: {distance:.2f} km")

    def update_platform_summary(self):
        summary = "各平台统计:\n"
        for platform, data in self.platforms.items():
            summary += f"{platform}: 充电度数: {data['kWh']:.2f} kWh, 费用: {data['cost']:.2f} 元\n"
        self.platform_summary_label.config(text=summary)

    def delete_selected_records(self):
        selected_indices = self.records_listbox.curselection()
        if not selected_indices:
            messagebox.showerror("删除错误", "请先选择一条记录")
            return

        for index in reversed(selected_indices):
            platform, kWh, cost, distance = self.records[index]
            self.total_kWh -= kWh
            self.total_cost -= cost
            self.total_distance -= distance  # 减去行驶里程
            del self.records[index]

            # 更新平台统计
            self.platforms[platform]['kWh'] -= kWh
            self.platforms[platform]['cost'] -= cost
            if self.platforms[platform]['kWh'] <= 0:  # 如果某个平台的累计度数为0，删除该平台
                del self.platforms[platform]

        self.update_records_listbox()
        self.update_platform_summary()
        self.save_data()  # 自动保存数据

    def delete_all_records(self):
        confirm = messagebox.askyesno("确认", "您确定要删除所有记录吗？")
        if confirm:
            self.records.clear()
            self.total_kWh = 0.0
            self.total_cost = 0.0
            self.total_distance = 0.0
            self.platforms.clear()
            self.update_records_listbox()
            self.update_platform_summary()
            self.result_label.config(text="")
            self.save_data()  # 自动保存数据

    def toggle_select_all(self):
        if self.records_listbox.curselection():
            self.records_listbox.selection_clear(0, tk.END)  # 取消全选
        else:
            self.records_listbox.select_set(0, tk.END)  # 全选

    def modify_record(self):
        try:
            selected_index = self.records_listbox.curselection()[0]
            platform, kWh, cost, distance = self.records[selected_index]

            new_platform = simpledialog.askstring("修改平台", "请输入新的充电平台:", initialvalue=platform)
            new_kWh = simpledialog.askfloat("修改充电度数", "请输入新的充电度数（kWh）:", initialvalue=kWh)
            new_cost = simpledialog.askfloat("修改充电费用", "请输入新的充电费用（元）:", initialvalue=cost)
            new_distance = simpledialog.askfloat("修改行驶里程", "请输入新的行驶里程（km）:", initialvalue=distance)

            if new_platform is not None and new_kWh is not None and new_cost is not None and new_distance is not None:
                # 更新累计数据
                self.total_kWh += (new_kWh - kWh)
                self.total_cost += (new_cost - cost)
                self.total_distance += (new_distance - distance)  # 更新行驶里程

                # 更新平台统计
                if platform in self.platforms:
                    self.platforms[platform]['kWh'] -= kWh
                    self.platforms[platform]['cost'] -= cost
                    if self.platforms[platform]['kWh'] <= 0:
                        del self.platforms[platform]

                if new_platform in self.platforms:
                    self.platforms[new_platform]['kWh'] += new_kWh
                    self.platforms[new_platform]['cost'] += new_cost
                else:
                    self.platforms[new_platform] = {'kWh': new_kWh, 'cost': new_cost}

                # 更新记录
                self.records[selected_index] = (new_platform, new_kWh, new_cost, new_distance)
                self.update_records_listbox()
                self.update_platform_summary()
                today_date = datetime.now().strftime("%Y.%m.%d")
                cost_per_km = self.total_cost / self.total_distance if self.total_distance > 0 else 0
                self.result_label.config(text=f"累计充电度数: {self.total_kWh:.2f} kWh\n"
                                               f"累计充电费用: {self.total_cost:.2f} 元\n"
                                               f"每公里费用: {cost_per_km:.2f} 元/km\n"
                                               f"今天日期: {today_date}\n"
                                               f"提车日期: {self.purchase_date.strftime('%Y.%m.%d')}")
                self.save_data()  # 自动保存数据
        except IndexError:
            messagebox.showerror("修改错误", "请先选择一条记录")

if __name__ == "__main__":
    root = tk.Tk()
    calculator = ChargingCostCalculator(root)
    root.mainloop()