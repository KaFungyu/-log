import os
from collections import Counter
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import statistics
import concurrent.futures
import threading
from queue import Queue
import time
import io
# 移除mmap导入，因为存在兼容性问题
import gc

# 配置选项
CHUNK_SIZE = 8192 * 1024  # 8MB 的块大小，用于分块读取文件
MAX_WORKERS = min(8, os.cpu_count() or 4)  # 根据CPU核心数动态设置工作线程数
UI_UPDATE_INTERVAL = 100  # 毫秒，UI更新间隔
LOG_BATCH_SIZE = 20000  # 日志行批处理大小

# 文件夹路径列表
directories = [
    # r"D:\SecureCRT_log\Serial-COM3",
    
    # r"D:\D026_#051_lp5\BQ201_#13_com54-A\.Amlogic_DDR_Test",
    # r"D:\D026_#051_lp5\BQ201_#17_com55-B\.Amlogic_DDR_Test",
    r"D:\D026_#051_lp5\BQ201_#23_com56-C\.Amlogic_DDR_Test",

    # r"D:\D026_#051_lp5\BQ201_#13_com49-A\.Amlogic_DDR_Test",
    # r"D:\D026_#051_lp5\BQ201_#17_com46-B\.Amlogic_DDR_Test",
    # r"D:\D026_#051_lp5\BQ201_#23_com47-C\.Amlogic_DDR_Test",
]

# 固定关键字列表
# keywords = ["compare fail", "adlau error", "miscompare", "kernel panic", "all config", "watchdog_reboot"]
keywords = ["SAR_CH0:"]
# keywords = ["SAR_CH2:"]

# 正则表达式模式
keyword_patterns = {keyword: re.compile(re.escape(keyword), re.IGNORECASE) for keyword in keywords}
timestamp_pattern = re.compile(r'(\d{4}[-/]\d{2}[-/]\d{2}[_ ]\d{2}:\d{2}:\d{2})')
hex_pattern_6434 = re.compile(r'(?:\[)?0xfc006434(?:\])?\s*=\s*(?:0x)?([0-9a-fA-F]+)')
hex_pattern_6344 = re.compile(r'(?:\[)?0xfc006344(?:\])?\s*=\s*(?:0x)?([0-9a-fA-F]+)')

# 全局变量
stats_data = []
log_contents = []
results_dict = {}
progress_var = None
progress_label = None
root = None
progress_window = None
main_window = None
total_files = 0
processed_files = 0

def parse_timestamp(timestamp_str):
    """解析不同格式的时间戳"""
    try:
        if '/' in timestamp_str:
            return datetime.strptime(timestamp_str, "%Y/%m/%d_%H:%M:%S")
        else:
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

def _process_line(line, keyword_counter, matching_lines, keyword_matches, values_6434, values_6344, count_6344, first_timestamp, last_timestamp):
    """处理单行日志，提取关键信息"""
    # 快速检查，避免不必要的正则匹配
    has_timestamp = '/' in line or '-' in line
    has_6434 = '6434' in line
    has_6344 = '6344' in line
    
    # 时间戳处理 - 只有当行包含可能的时间戳字符时才执行
    if has_timestamp:
        match = timestamp_pattern.search(line)
        if match:
            current_timestamp = match.group(1)
            if not first_timestamp[0]:
                first_timestamp[0] = current_timestamp
            last_timestamp[0] = current_timestamp
    
    # 6434寄存器处理 - 只有当行包含6434时才执行
    if has_6434:
        match_6434 = hex_pattern_6434.search(line)
        if match_6434:
            try:
                hex_value = match_6434.group(1)
                value = int(hex_value, 16)
                if value != 0:  # 只添加非零值
                    values_6434.append(value)
            except ValueError:
                pass
    
    # 6344寄存器处理 - 只有当行包含6344时才执行
    if has_6344:
        match_6344 = hex_pattern_6344.search(line)
        if match_6344:
            try:
                hex_value = match_6344.group(1)
                value = int(hex_value, 16)
                if value != 0:  # 只添加非零值
                    values_6344.append(value)
                    count_6344[0] += 1
            except ValueError:
                pass
    
    # 关键字匹配处理 - 使用更高效的方式
    # 先转换为小写，然后检查是否包含任何关键字
    line_lower = line.lower()
    for keyword, pattern in keyword_patterns.items():
        # 使用字符串包含检查作为快速过滤
        if keyword.lower() in line_lower and pattern.search(line):
            keyword_counter[keyword] += 1
            line_stripped = line.rstrip()
            matching_lines.append((line_stripped, keyword))
            keyword_matches[keyword].append(line_stripped)
            break  # 找到一个匹配就退出循环

def process_log_file(file_path, result_queue):
    """处理单个日志文件，使用内存映射和批处理优化内存使用和性能"""
    keyword_counter = Counter()
    matching_lines = []
    first_timestamp = [None]  # 使用列表以便在_process_line中可以修改
    last_timestamp = [None]  # 使用列表以便在_process_line中可以修改
    values_6434 = []
    values_6344 = []
    count_6344 = [0]  # 使用列表以便在_process_line中可以修改
    run_time = "N/A"
    
    # 获取完整路径信息用于显示
    display_path = os.path.dirname(file_path)
    display_path = display_path.replace('\\', '/')
    
    # 获取文件名
    file_name = os.path.basename(file_path)
    
    # 使用关键字匹配字典收集匹配行，预先编译所有正则表达式提高性能
    keyword_matches = {keyword: [] for keyword in keywords}
    
    try:
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        # 对所有文件使用统一的、可靠的读取方式
        try:
            with open(file_path, "r", encoding='utf-8', errors='ignore') as f:
                # 初始化变量
                line_count = 0
                lines_batch = []
                
                # 根据文件大小选择读取策略
                if file_size < 100 * 1024 * 1024:  # 小于100MB的文件
                    # 使用readlines一次性读取所有行，适合小文件
                    all_lines = f.readlines()
                    
                    # 批量处理行，减少函数调用开销
                    for i in range(0, len(all_lines), LOG_BATCH_SIZE):
                        batch = all_lines[i:i+LOG_BATCH_SIZE]
                        for line in batch:
                            line_count += 1
                            _process_line(line, keyword_counter, matching_lines, keyword_matches, 
                                        values_6434, values_6344, count_6344, 
                                        first_timestamp, last_timestamp)
                        # 强制垃圾回收
                        gc.collect()
                        
                    # 清除引用，帮助垃圾回收
                    del all_lines
                else:  # 大于等于100MB的文件
                    # 使用迭代器按行读取，避免一次性加载整个文件
                    for line in f:
                        lines_batch.append(line)
                        if len(lines_batch) >= LOG_BATCH_SIZE:
                            for batch_line in lines_batch:
                                line_count += 1
                                _process_line(batch_line, keyword_counter, matching_lines, keyword_matches, 
                                            values_6434, values_6344, count_6344, 
                                            first_timestamp, last_timestamp)
                            # 清空已处理的行
                            lines_batch = []
                            # 强制垃圾回收
                            gc.collect()
                    
                    # 处理剩余的行
                    for line in lines_batch:
                        line_count += 1
                        _process_line(line, keyword_counter, matching_lines, keyword_matches, 
                                    values_6434, values_6344, count_6344, 
                                    first_timestamp, last_timestamp)
        except Exception as file_error:
            print(f"读取文件出错 {file_path}: {str(file_error)}")
            result_queue.put((file_path, None))  # 发送错误信号
            return
        
        # 打印匹配结果
        has_matches = any(matches for matches in keyword_matches.values())
        if has_matches:
            print("\n" + "=" * 100)  # 添加醒目的等号分隔线
            print(f"路径: {display_path}")  # 单独一行显示路径
            print("=" * 100)  # 添加醒目的等号分隔线
            
            # 显示该路径下的所有关键字匹配
            for keyword, matches in keyword_matches.items():
                if matches:
                    print(f"\n[{keyword}] ({len(matches)}个)")
                    for line in matches:
                        print(f"  {line}")
            
            print("-" * 100)  # 添加普通分隔线结束
    
    except Exception as e:
        print(f"处理文件出错 {file_path}: {str(e)}")
        result_queue.put((file_path, None))  # 发送错误信号
        return
    
    # 计算运行时间
    if first_timestamp[0] and last_timestamp[0]:
        try:
            start_time = parse_timestamp(first_timestamp[0])
            end_time = parse_timestamp(last_timestamp[0])
            if start_time and end_time:
                duration = end_time - start_time
                run_time = f"{duration.total_seconds() / 3600:.2f}h"
        except Exception:
            run_time = "Error"
    
    # 计算统计数据
    stats_6434 = {'min': 0, 'max': 0, 'avg': 0}
    if values_6434:
        stats_6434 = {
            'min': min(values_6434),
            'max': max(values_6434),
            'avg': round(sum(values_6434) / len(values_6434))
        }
        diff_6434 = stats_6434['max'] - stats_6434['min']
    else:
        diff_6434 = 0
        
    stats_6344 = {'min': 0, 'max': 0, 'avg': 0}
    if values_6344:
        stats_6344 = {
            'min': min(values_6344),
            'max': max(values_6344),
            'avg': round(sum(values_6344) / len(values_6344))
        }
        diff_6344 = stats_6344['max'] - stats_6344['min']
    else:
        diff_6344 = 0
    
    # 将结果放入队列
    result = (keyword_counter, matching_lines, run_time, "", diff_6434, stats_6434, diff_6344, stats_6344, count_6344[0], file_name)
    result_queue.put((file_path, result))

def update_progress():
    """更新进度条，优化UI更新"""
    global processed_files, progress_var, progress_label, progress_window
    
    try:
        # 增加更严格的检查，确保progress_window存在且有效
        if (progress_var and progress_label and progress_window and 
            hasattr(progress_window, 'winfo_exists') and progress_window.winfo_exists()):
            # 设置进度变量
            progress_var.set(processed_files)
            # 计算百分比
            percentage = int((processed_files / max(total_files, 1)) * 100)
            # 更新标签文本
            progress_label.config(text=f"处理进度: {processed_files}/{total_files} ({percentage}%)")
            # 只更新必要的组件，减少UI开销
            progress_window.update_idletasks()
    except tk.TclError:
        # 忽略可能的Tcl错误，窗口可能已被销毁
        pass
    except Exception as e:
        # 捕获其他可能的异常
        print(f"更新进度时出错: {str(e)}")
        pass

def show_progress_window():
    """显示进度窗口"""
    global progress_var, progress_label, progress_window, total_files, main_window
    
    # 初始化进度窗口变量，确保在函数开始时就设置为None
    progress_window = None
    progress_var = None
    progress_label = None
    
    # 检查main_window是否存在且有效
    if not main_window or not hasattr(main_window, 'winfo_exists') or not main_window.winfo_exists():
        # 如果主窗口不存在或已销毁，创建一个新的主窗口
        main_window = tk.Tk()
        main_window.withdraw()  # 隐藏主窗口
    
    try:
        # 使用main_window作为父窗口创建Toplevel
        progress_window = tk.Toplevel(main_window)
        progress_window.title("处理进度")
        progress_window.geometry("400x150")
        progress_window.resizable(False, False)
        
        # 居中窗口
        x = (progress_window.winfo_screenwidth() - 400) // 2
        y = (progress_window.winfo_screenheight() - 150) // 2
        progress_window.geometry(f"400x150+{x}+{y}")
        
        # 创建进度条框架
        frame = ttk.Frame(progress_window, padding="20 20 20 20")
        frame.pack(fill='both', expand=True)
        
        # 创建标签
        progress_label = ttk.Label(frame, text=f"处理进度: 0/{total_files} (0%)")
        progress_label.pack(pady=(0, 10))
        
        # 创建进度条
        progress_var = tk.IntVar(value=0)
        progress_bar = ttk.Progressbar(frame, orient="horizontal", length=360, mode="determinate", 
                                     maximum=total_files, variable=progress_var)
        progress_bar.pack(fill='x', pady=10)
        
        # 设置窗口置顶
        progress_window.attributes('-topmost', True)
        
        # 添加窗口关闭事件处理
        def on_closing():
            global processed_files, progress_window
            # 设置处理文件数为总文件数，强制结束处理
            processed_files = total_files
            # 安全地销毁窗口
            try:
                if progress_window and hasattr(progress_window, 'winfo_exists') and progress_window.winfo_exists():
                    progress_window.destroy()
                    progress_window = None
            except tk.TclError:
                pass  # 忽略可能的Tcl错误
            
            # 不要在这里退出主窗口，让程序继续运行
            # 只有在用户明确关闭主窗口时才退出
        
        # 绑定窗口关闭事件
        progress_window.protocol("WM_DELETE_WINDOW", on_closing)
        
        # 安全地更新窗口
        try:
            if progress_window and hasattr(progress_window, 'winfo_exists') and progress_window.winfo_exists():
                progress_window.update()
        except tk.TclError:
            pass  # 忽略可能的Tcl错误
    except tk.TclError as e:
        print(f"创建进度窗口时出错: {str(e)}")
        progress_window = None  # 确保变量被设置为None

def scan_directory(directory):
    """扫描单个目录并返回最新的日志文件"""
    try:
        # 使用列表推导式一次性获取所有日志文件，提高性能
        log_files = [f for f in os.scandir(directory) if f.name.lower().endswith('.log')]
        if log_files:
            # 直接使用max函数获取最新文件
            latest_file = max(log_files, key=lambda x: x.stat().st_mtime)
            return (directory, latest_file)
    except Exception as e:
        print(f"扫描目录出错 {directory}: {str(e)}")
    return None

def process_single_directory(directory, index, latest_file, result_queue):
    """处理单个目录的函数"""
    try:
        # 启动文件处理
        process_log_file(latest_file.path, result_queue)
    except Exception as e:
        print(f"处理目录出错 {directory}: {str(e)}")
        result_queue.put((latest_file.path, None))  # 发送错误信号

def process_results(directory, index, result):
    """处理从队列接收到的结果"""
    global processed_files, results_dict, log_contents
    
    if result is None:
        # 处理失败
        return
    
    keyword_counter, matching_lines, run_time, empty_diff, diff_6434, stats_6434, diff_6344, stats_6344, count_6344, file_name = result
    
    # 使用basename显示路径
    row = [os.path.basename(directory)]
    total = 0
    for keyword in keywords:
        count = keyword_counter[keyword]
        row.append(count)
        total += count
    
    row.append(total)
    row.append(run_time)
    # 添加6434和6344的统计数据
    row.extend([diff_6434, stats_6434['min'], stats_6434['max'], stats_6434['avg']])
    row.extend([diff_6344, stats_6344['min'], stats_6344['max'], stats_6344['avg']])
    row.append(count_6344)
    # 添加文件名
    row.append(file_name)
    
    # 保存匹配行
    if matching_lines:
        log_contents.append((directory, matching_lines))
    
    # 将结果存入字典，使用索引作为键以保持顺序
    results_dict[index] = row

def process_all_directories():
    """使用多线程处理所有目录，优化性能"""
    global stats_data, results_dict, total_files, processed_files, main_window, progress_window, progress_var, progress_label
    stats_data = []
    results_dict = {}
    processed_files = 0
    
    # 计算总文件数，优化目录扫描
    valid_directories = []
    
    # 使用线程池并行扫描目录
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as scan_executor:
        # 创建扫描任务
        scan_futures = []
        for directory in directories:
            if os.path.exists(directory):
                scan_futures.append(scan_executor.submit(scan_directory, directory))
        
        # 收集扫描结果
        for future in concurrent.futures.as_completed(scan_futures):
            result = future.result()
            if result:
                valid_directories.append(result)
    
    total_files = len(valid_directories)
    
    if total_files == 0:
        messagebox.showinfo("提示", "没有找到有效的日志文件")
        return
    
    # 显示进度窗口
    show_progress_window()
    
    # 创建结果队列
    result_queue = Queue()
    
    # 创建文件路径到目录和索引的映射，避免每次都循环查找
    # 使用原始目录列表的索引，而不是处理顺序的索引
    file_path_map = {}
    dir_to_original_idx = {dir_path: idx for idx, dir_path in enumerate(directories) if os.path.exists(dir_path)}
    for dir_path, latest_file in valid_directories:
        # 使用原始目录列表中的索引
        original_idx = dir_to_original_idx.get(dir_path)
        if original_idx is not None:
            file_path_map[latest_file.path] = (dir_path, original_idx)
    
    # 创建线程池
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        for directory, latest_file in valid_directories:
            # 获取原始索引
            original_idx = dir_to_original_idx.get(directory)
            if original_idx is not None:
                executor.submit(process_single_directory, directory, original_idx, latest_file, result_queue)
        
        # 设置UI更新定时器
        def update_ui():
            try:
                # 检查窗口是否存在且有效，以及处理是否完成
                if progress_window and progress_window.winfo_exists() and processed_files < total_files:
                    update_progress()
                    # 安全地设置下一次更新
                    try:
                        progress_window.after(UI_UPDATE_INTERVAL, update_ui)
                    except tk.TclError:
                        pass  # 忽略可能的Tcl错误
            except tk.TclError:
                pass  # 忽略可能的Tcl错误，窗口可能已被销毁
        
        # 安全地启动UI更新定时器
        try:
            if progress_window and hasattr(progress_window, 'winfo_exists') and progress_window.winfo_exists():
                progress_window.after(UI_UPDATE_INTERVAL, update_ui)
        except tk.TclError:
            pass  # 忽略可能的Tcl错误
        except Exception as e:
            print(f"设置UI更新定时器时出错: {str(e)}")
        
        # 处理结果
        while processed_files < total_files:
            try:
                file_path, result = result_queue.get(timeout=0.1)
                # 使用映射直接查找对应的目录和索引
                if file_path in file_path_map:
                    directory, index = file_path_map[file_path]
                    if result is not None:
                        process_results(directory, index, result)
                
                processed_files += 1
                
            except Exception as e:
                # 队列可能为空，继续等待
                continue
    
    # 安全地关闭进度窗口
    try:
        if progress_window and hasattr(progress_window, 'winfo_exists') and progress_window.winfo_exists():
            progress_window.destroy()
    except tk.TclError:
        # 窗口可能已经被销毁，忽略此错误
        pass
    except Exception as e:
        print(f"关闭进度窗口时出错: {str(e)}")
    
    # 重置进度窗口变量
    progress_window = None
    progress_var = None
    progress_label = None
    
    # 按原始目录顺序收集结果
    for i in range(len(directories)):
        if i in results_dict:
            stats_data.append(results_dict[i])
    
    # 显示统计窗口
    if stats_data:
        create_table_window()
    else:
        messagebox.showinfo("提示", "没有找到有效数据")

def create_table_window():
    global root, main_window
    # 使用已经创建的主窗口而不是创建新窗口
    root = main_window
    root.deiconify()  # 显示主窗口
    root.title("关键字统计")
    
    # 创建主框架
    main_frame = ttk.Frame(root, padding="0")
    main_frame.pack(expand=True, fill='both')
    
    # 创建表格
    base_headers = ["路径"] + keywords + ["总计", "运行时间"]
    hex_headers = [
        "6434_diff", "6434_min", "6434_max", "6434_ave",
        "6344_diff", "6344_min", "6344_max", "6344_ave",
        "6344_count"
    ]
    # 添加文件名列
    file_header = ["文件名"]
    headers = base_headers + hex_headers + file_header
    
    # 设置样式 - 只设置一次，避免重复创建样式对象
    style = ttk.Style()
    if not style.theme_names() or 'optimized_theme' not in style.theme_names():
        style.configure("Treeview", 
                      font=('Microsoft YaHei', 10),
                      rowheight=25,
                      borderwidth=1,
                      relief="solid",
                      fieldbackground="white",
                      background="white")
        style.configure("Treeview.Heading", font=('Microsoft YaHei', 10))
        style.map("Treeview",
                background=[("selected", "#CCE8FF")],
                foreground=[("selected", "black")])
    
    # 创建表格框架
    table_frame = ttk.Frame(main_frame)
    table_frame.pack(expand=True, fill='both')
    
    # 创建滚动条
    vsb = ttk.Scrollbar(table_frame, orient="vertical")
    hsb = ttk.Scrollbar(table_frame, orient="horizontal")
    
    # 创建Treeview，启用多选功能
    tree = ttk.Treeview(table_frame, columns=headers, show='headings', 
                       height=min(len(stats_data), 20), # 限制高度，避免窗口过大
                       selectmode='extended',
                       yscrollcommand=vsb.set,
                       xscrollcommand=hsb.set)
    
    # 配置滚动条
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)
    
    # 放置组件
    vsb.pack(side='right', fill='y')
    hsb.pack(side='bottom', fill='x')
    tree.pack(expand=True, fill='both')
    
    # 配置红色标签
    tree.tag_configure('red', foreground='red')
    
    # 添加提示标签
    tip_label = ttk.Label(table_frame, text="提示：可以选择一行或多行，然后点击\"删除目录\"按钮进行删除", font=('Microsoft YaHei', 9))
    tip_label.pack(pady=(5, 0))
    
    # 优化列宽计算 - 使用估算而不是精确计算
    max_widths = {}
    char_width = 8  # 估计每个字符的平均宽度（像素）
    
    for i, header in enumerate(headers):
        # 获取该列所有数据
        column_data = [str(row[i]) for row in stats_data]
        
        # 找出最长的内容和标题
        longest_content = max([header] + column_data, key=len, default='')
        
        # 估算宽度
        estimated_width = len(longest_content) * char_width + 20  # 添加padding
        max_widths[header] = max(estimated_width, 45)  # 最小宽度
    
    # 设置列宽和标题，并添加排序功能
    for header in headers:
        tree.column(header, width=max_widths[header], anchor='center', stretch=False)
        tree.heading(header, text=header, command=lambda h=header: sort_treeview(tree, h, False))
    
    # 批量插入数据 - 使用批处理提高性能
    batch_size = 100  # 每批处理的行数
    for i in range(0, len(stats_data), batch_size):
        batch = stats_data[i:i+batch_size]
        for row in batch:
            # 创建标签列表
            tags = []
            # 检查关键字列的非零值
            keyword_values = row[1:len(keywords)+1]  # 获取所有关键字列的值
            if any(str(val) != '0' for val in keyword_values):
                tags.append('red')
            
            # 插入数据并设置标签
            tree.insert('', 'end', values=row, tags=tags if tags else ())
        
        # 每批次后更新UI
        if i + batch_size < len(stats_data):
            root.update_idletasks()
    
    # 创建按钮框架
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(pady=5)
    
    # 一键复制功能 - 优化大数据集处理
    def copy_all():
        # 使用StringIO提高字符串拼接性能
        import io
        buffer = io.StringIO()
        
        # 写入标题行
        buffer.write('\t'.join(headers) + '\n')
        
        # 分批处理数据行，避免一次性处理过多数据
        items = tree.get_children()
        batch_size = 500  # 每批处理的行数
        
        for i in range(0, len(items), batch_size):
            batch_items = items[i:i+batch_size]
            for item in batch_items:
                values = tree.item(item)['values']
                row_text = '\t'.join(str(x) if x is not None else "" for x in values)
                buffer.write(row_text + '\n')
        
        # 获取完整文本并复制到剪贴板
        text = buffer.getvalue()
        buffer.close()
        
        root.clipboard_clear()
        root.clipboard_append(text)
        messagebox.showinfo("提示", "已复制到剪贴板")
    
    # 添加目录功能 - 优化用户体验
    def add_directory():
        directory = filedialog.askdirectory(title="选择日志文件目录")
        if directory:
            # 检查目录是否已存在
            if directory in directories:
                messagebox.showinfo("提示", "该目录已在列表中")
                return
                
            # 将目录添加到列表
            directories.append(directory)
            # 关闭当前窗口
            root.destroy()
            # 重新处理所有目录并刷新数据
            process_all_directories()
            
    # 删除目录功能
    def delete_directory():
        global progress_window, progress_var, progress_label
        # 获取表格中选中的行
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请在表格中选择要删除的目录行")
            return
        
        # 获取选中行的路径值（第一列）
        selected_paths = []
        for item in selected_items:
            # 获取行的值
            values = tree.item(item, 'values')
            if values:
                # 找到对应的完整路径
                for i, dir_path in enumerate(directories):
                    if os.path.basename(dir_path) == values[0]:
                        selected_paths.append((i, dir_path))
                        break
        
        if not selected_paths:
            messagebox.showinfo("提示", "无法找到对应的目录路径")
            return
        
        # 确认删除
        paths_str = "\n".join([path for _, path in selected_paths])
        confirm = messagebox.askyesno("确认删除", f"确定要删除以下目录吗？\n{paths_str}")
        if not confirm:
            return
        
        # 从后往前删除，避免索引变化
        indices = [idx for idx, _ in sorted(selected_paths, key=lambda x: x[0], reverse=True)]
        for index in indices:
            del directories[index]
        
        # 安全地关闭当前窗口
        try:
            # 保存对main_window的引用
            global main_window
            main_window_ref = main_window
            
            # 关闭当前窗口
            if root and root.winfo_exists():
                root.destroy()
            
            # 确保全局变量被正确重置
            global progress_window, progress_var, progress_label
            progress_window = None
            progress_var = None
            progress_label = None
            
            # 重新处理所有目录并刷新数据
            # 使用after方法安排处理，避免在回调中直接调用
            if main_window_ref and main_window_ref.winfo_exists():
                main_window_ref.after(100, process_all_directories)
            else:
                # 如果主窗口已销毁，创建新窗口
                main_window = tk.Tk()
                main_window.withdraw()
                main_window.after(100, process_all_directories)
        except tk.TclError as e:
            print(f"关闭窗口时出错: {str(e)}")
            # 创建新的主窗口并继续处理
            main_window = tk.Tk()
            main_window.withdraw()
            main_window.after(100, process_all_directories)
    
    # 创建按钮
    copy_button = ttk.Button(button_frame, text="一键复制", command=copy_all)
    copy_button.pack(side=tk.LEFT, padx=5)
    
    add_dir_button = ttk.Button(button_frame, text="添加目录", command=add_directory)
    add_dir_button.pack(side=tk.LEFT, padx=5)
    
    delete_dir_button = ttk.Button(button_frame, text="删除选中目录", command=delete_directory)
    delete_dir_button.pack(side=tk.LEFT, padx=5)
    
    # 添加键盘快捷键提示
    shortcut_label = ttk.Label(button_frame, text="快捷键: Ctrl+点击可多选行", font=('Microsoft YaHei', 9))
    shortcut_label.pack(side=tk.LEFT, padx=15)
    
    # 刷新数据功能
    def refresh_data():
        # 保存当前目录列表
        current_directories = directories.copy()
        # 关闭当前窗口
        root.destroy()
        # 重新处理所有目录并刷新数据
        process_all_directories()
    
    refresh_button = ttk.Button(button_frame, text="刷新数据", command=refresh_data)
    refresh_button.pack(side=tk.LEFT, padx=5)
    
    # 计算窗口大小
    window_width = sum(max_widths.values()) + 30
    window_height = (len(stats_data) + 1) * 25 + 80
    
    # 居中窗口
    x = (root.winfo_screenwidth() - window_width) // 2
    y = (root.winfo_screenheight() - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # 添加快捷键关闭功能
    def close_window(event=None):
        root.destroy()
    
    root.bind('<space>', close_window)
    root.bind('<Escape>', close_window)
    
    root.mainloop()

def sort_treeview(tree, col, reverse):
    """排序表格 - 优化排序性能"""
    # 获取所有数据
    items = tree.get_children('')
    data = []
    
    # 预先检查列类型
    is_numeric = col in ["总计", "6434_diff", "6434_min", "6434_max", "6434_ave", "6344_diff", "6344_min", "6344_max", "6344_ave", "6344_count"]
    
    # 批量获取数据，减少树视图访问次数
    for item in items:
        value = tree.set(item, col)
        # 预处理数值
        if is_numeric:
            try:
                if value.isdigit():
                    value = int(value)
                elif value.replace('.', '', 1).isdigit():
                    value = float(value)
                else:
                    value = 0
            except (ValueError, AttributeError):
                value = 0
        data.append((value, item))
    
    # 排序
    data.sort(reverse=reverse)
    
    # 批量重新排列数据
    for idx, (_, item) in enumerate(data):
        tree.move(item, '', idx)
    
    # 切换排序方向
    tree.heading(col, command=lambda: sort_treeview(tree, col, not reverse))

def main():
    """程序主入口函数，优化性能和刷新机制"""
    global main_window
    
    # 循环处理，允许用户添加或删除目录后重新处理
    while True:
        # 创建隐藏的主窗口
        main_window = tk.Tk()
        main_window.withdraw()  # 隐藏主窗口，防止显示空白窗口
        
        # 设置图标和标题（即使窗口隐藏，这些属性也会被子窗口继承）
        main_window.title("日志搜索工具")
        
        # 添加窗口关闭事件处理，确保点击右上角X按钮时能够完全退出程序
        def on_main_window_close():
            # 设置标志，表示用户希望完全退出程序
            main_window.quit()
            main_window.destroy()
            # 使用SystemExit异常跳出主循环
            raise SystemExit
            
        main_window.protocol("WM_DELETE_WINDOW", on_main_window_close)
        
        # 优化窗口性能
        main_window.update_idletasks()
        
        try:
            # 处理所有目录
            process_all_directories()
            
            # 进入主循环，等待用户操作
            main_window.mainloop()
            
            # 检查是否需要继续循环
            # 如果程序执行到这里，说明用户点击了添加、删除目录按钮或刷新按钮
            # 需要确保旧窗口被正确销毁
            try:
                if main_window and main_window.winfo_exists():
                    main_window.destroy()
            except tk.TclError:
                # 窗口可能已经被销毁，忽略此错误
                pass
                
        except Exception as e:
            # 捕获并显示详细错误信息
            import traceback
            error_msg = f"程序运行出错：\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            messagebox.showerror("错误", error_msg)
            break
        except KeyboardInterrupt:
            print("程序被用户中断")
            break
        except SystemExit:
            break
    
    # 最终确保窗口被销毁
    try:
        if main_window and main_window.winfo_exists():
            main_window.destroy()
    except tk.TclError:
        # 窗口可能已经被销毁，忽略此错误
        pass

if __name__ == "__main__":
    main()
