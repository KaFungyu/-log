import pygame, random
from collections import deque
import os, json
import time

# 初始化pygame
pygame.init()

# 游戏常量
screen_info = pygame.display.Info()
W, H = screen_info.current_w, screen_info.current_h
C = min(W, H) // 40  # 调整格子大小以更好地适应屏幕
GRID_W, GRID_H = W // C, H // C
WHITE = (255,) * 3
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)

# 游戏状态管理
_current_high_score = 0

def load_high_score():
    global _current_high_score
    return _current_high_score

def save_high_score(score):
    global _current_high_score
    _current_high_score = score

# 游戏核心逻辑
def get_wrapped_distance(pos1, pos2):
    x1, y1 = pos1
    x2, y2 = pos2
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    if dx > GRID_W // 2: dx = GRID_W - dx
    if dy > GRID_H // 2: dy = GRID_H - dy
    return dx + dy

def count_reachable_cells(start, snake):
    visited = {start}
    queue = deque([(start, 0)])
    snake_set = set(snake[:-1])
    
    # 动态调整搜索深度，根据蛇的长度和网格大小
    snake_ratio = len(snake) / (GRID_W * GRID_H)
    if snake_ratio > 0.8:
        # 当蛇很长时，进行更彻底的搜索
        max_depth = GRID_W * GRID_H
        max_visited = GRID_W * GRID_H
    else:
        # 正常情况下的搜索深度限制
        max_depth = min(len(snake) * 6, GRID_W * GRID_H // 4)
        max_visited = GRID_W * GRID_H // 3
    
    while queue:
        pos, depth = queue.popleft()
        if depth >= max_depth or len(visited) >= max_visited: break
        
        # 按照曼哈顿距离排序方向，优先探索更开阔的区域
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dx, dy in directions:
            next_pos = ((pos[0] + dx) % GRID_W, (pos[1] + dy) % GRID_H)
            if next_pos not in visited and next_pos not in snake_set:
                visited.add(next_pos)
                queue.append((next_pos, depth + 1))
    
    return len(visited)

def find_shortest_path(start, target, snake_set):
    """使用BFS查找从起点到目标的最短路径，考虑环绕边界"""
    if start == target:
        return [start]
    
    # 使用优先队列，优先考虑距离目标更近的路径
    visited = {start}
    queue = deque([(start, [])])
    
    # 计算启发式距离的函数
    def heuristic(pos):
        return get_wrapped_distance(pos, target)
    
    while queue:
        pos, path = queue.popleft()
        path = path + [pos]
        
        # 按照启发式距离排序方向，优先考虑朝向食物的方向
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        directions.sort(key=lambda d: heuristic(((pos[0] + d[0]) % GRID_W, (pos[1] + d[1]) % GRID_H)))
        
        for dx, dy in directions:
            next_pos = ((pos[0] + dx) % GRID_W, (pos[1] + dy) % GRID_H)
            
            if next_pos == target:
                return path + [next_pos]
            
            if next_pos not in visited and next_pos not in snake_set:
                visited.add(next_pos)
                queue.append((next_pos, path))
                
                # 动态调整搜索范围，根据蛇的长度和网格大小
                max_search_area = min(GRID_W * GRID_H // 2, len(snake_set) * 10)
                if len(visited) > max_search_area:
                    return None
    
    return None

def get_next_move(snake, food, fps=30):
    head = snake[0]
    snake_set = set(snake[:-1])
    current_food_dist = get_wrapped_distance(head, food)
    best_move = None
    best_score = float('-inf')
    
    # 计算蛇占据屏幕的比例
    snake_ratio = len(snake) / (GRID_W * GRID_H)
    
    # 动态调整食物权重 - 更加智能地平衡贪吃与安全
    base_food_weight = 35 if fps <= 30 else 25  # 增加基础食物权重
    
    # 根据蛇的长度动态调整策略
    if snake_ratio >= 0.9:  # 当蛇占据屏幕90%以上时
        food_weight = base_food_weight * 0.3  # 更多关注安全
        safety_factor = 5.0  # 显著提高安全因子
        space_weight = 7.0  # 更重视空间
        path_weight = 0.5  # 降低路径权重
    elif snake_ratio >= 0.75:  # 当蛇占据屏幕75%以上时
        t = (snake_ratio - 0.75) / 0.15  # 0.75到0.9之间的比例
        food_weight = base_food_weight * (0.5 - 0.2 * t)  # 逐渐降低食物权重
        safety_factor = 3.0 + 2.0 * t  # 逐渐提高安全因子
        space_weight = 5.0 + 2.0 * t  # 逐渐提高空间权重
        path_weight = 0.7  # 中等路径权重
    elif snake_ratio >= 0.5:  # 当蛇占据屏幕50%以上时
        t = (snake_ratio - 0.5) / 0.25  # 0.5到0.75之间的比例
        food_weight = base_food_weight * (0.8 - 0.3 * t)  # 逐渐降低食物权重
        safety_factor = 1.5 + 1.5 * t  # 逐渐提高安全因子
        space_weight = 3.5 + 1.5 * t  # 逐渐提高空间权重
        path_weight = 0.9  # 较高路径权重
    elif snake_ratio >= 0.25:  # 当蛇占据屏幕25%以上时
        t = (snake_ratio - 0.25) / 0.25  # 0.25到0.5之间的比例
        food_weight = base_food_weight * (1.0 - 0.2 * t)  # 轻微降低食物权重
        safety_factor = 1.0 + 0.5 * t  # 轻微提高安全因子
        space_weight = 2.5 + 1.0 * t  # 轻微提高空间权重
        path_weight = 1.0  # 高路径权重
    else:
        food_weight = base_food_weight  # 保持高贪吃权重
        safety_factor = 1.0
        space_weight = 2.5
        path_weight = 1.0  # 高路径权重
    
    # 尝试使用BFS查找最短路径
    shortest_path = None
    # 当蛇不太长或者食物距离较远时，尝试使用BFS
    if snake_ratio < 0.8 or current_food_dist > 5:
        shortest_path = find_shortest_path(head, food, snake_set)
    
    # 如果找到了最短路径，直接使用它的下一步
    if shortest_path and len(shortest_path) > 1:
        next_move = shortest_path[1]
        # 验证这一步是否安全
        space = count_reachable_cells(next_move, [next_move] + snake[:-1])
        if space >= len(snake) + 1:
            # 额外检查：确保这一步不会导致蛇陷入死胡同
            if snake_ratio < 0.7 or space >= len(snake) * 1.2:
                return next_move
    
    # 如果BFS失败或路径不安全，使用改进的评分系统
    # 记录最短路径选项
    shortest_path_move = None
    min_food_dist = float('inf')
    
    # 检测是否有紧急情况（可能陷入死胡同）
    emergency_mode = False
    available_moves = []
    
    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        next_pos = ((head[0] + dx) % GRID_W, (head[1] + dy) % GRID_H)
        if next_pos not in snake_set:
            available_moves.append(next_pos)
            
            food_dist = get_wrapped_distance(next_pos, food)
            
            # 记录最短路径选项
            if food_dist < min_food_dist:
                min_food_dist = food_dist
                shortest_path_move = next_pos
            
            # 计算可达空间
            space = count_reachable_cells(next_pos, [next_pos] + snake[:-1])
            
            # 紧急情况检测：如果可达空间小于蛇长度，标记为紧急模式
            if space < len(snake) + 1:
                if len(available_moves) <= 2:  # 如果可用移动很少，进入紧急模式
                    emergency_mode = True
                continue
            
            # 优化评分系统 - 更强调最短路径吃食物
            # 调整空间评分的权重
            space_score = space * space_weight * safety_factor
            
            # 显著增加食物距离评分的权重
            food_score = (current_food_dist - food_dist) * food_weight
            
            # 如果是最短路径选项，给予额外奖励
            shortest_path_bonus = 400 if food_dist == min_food_dist else 0
            
            # 如果下一步就是食物，给予更高额外奖励
            direct_food_bonus = 1000 if next_pos == food else 0
            
            # 总分
            score = space_score + food_score + direct_food_bonus + shortest_path_bonus
            
            # 优化避让策略 - 更智能地避开自己的身体
            for i, segment in enumerate(snake[1:8]):  # 检查前8个身体段
                dist = get_wrapped_distance(next_pos, segment)
                if dist < 2:
                    # 距离越近的身体段惩罚越重
                    penalty = 200 * safety_factor / (i + 1)
                    score -= penalty
            
            # 额外考虑：避免走入死胡同
            if space < len(snake) * 1.5 and snake_ratio > 0.4:
                score -= (len(snake) * 1.5 - space) * 15 * safety_factor
            
            # 额外考虑：当蛇很长时，更倾向于选择能看到尾巴的路径
            if snake_ratio > 0.7 and len(snake) > 20:
                tail_dist = get_wrapped_distance(next_pos, snake[-1])
                if tail_dist < GRID_W // 4 or tail_dist < GRID_H // 4:
                    score += 300 * safety_factor
            
            if score > best_score:
                best_score = score
                best_move = next_pos
    
    # 紧急情况处理
    if emergency_mode or best_move is None:
        # 如果有最短路径选项，尝试使用它
        if shortest_path_move is not None:
            space = count_reachable_cells(shortest_path_move, [shortest_path_move] + snake[:-1])
            if space >= len(snake):
                best_move = shortest_path_move
        
        # 如果仍然没有找到移动，选择可用移动中空间最大的
        if best_move is None and available_moves:
            best_space = -1
            for move in available_moves:
                space = count_reachable_cells(move, [move] + snake[:-1])
                if space > best_space:
                    best_space = space
                    best_move = move
    
    return best_move

# 绘图函数
def get_rainbow_color(index, total):
    if total < 2: return GREEN
    colors = [
        (255, 0, 0), (255, 127, 0), (255, 255, 0),
        (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)
    ]
    t = (index / total) * (len(colors) - 1)
    i = int(t)
    f = t - i
    c1 = colors[i]
    c2 = colors[min(i + 1, len(colors) - 1)]
    return tuple(int(c1[j] + (c2[j] - c1[j]) * f) for j in range(3))

def draw_segment(surface, pos, color, is_head=False):
    x, y = pos[0] * C, pos[1] * C
    pygame.draw.rect(surface, (*color, 120), (x-3, y-3, C+6, C+6), border_radius=5)
    pygame.draw.rect(surface, (*color, 230 if is_head else 180), (x, y, C, C), border_radius=3)
    if is_head:
        pygame.draw.circle(surface, (50, 50, 50, 255), (x + C//3, y + C//3), 4)
        pygame.draw.circle(surface, (50, 50, 50, 255), (x + 2*C//3, y + C//3), 4)

def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
    pygame.display.set_caption("智能贪吃蛇")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Microsoft YaHei', int(H/35))
    transparent = pygame.Surface((W, H), pygame.SRCALPHA)
    
    # 合并显示消息函数
    def display_message(text, color, y_offset=0, center_x=W//2):
        msg = font.render(text, True, color)
        msg_rect = msg.get_rect(center=(center_x, H//2 + y_offset))
        bg_rect = msg_rect.inflate(20, 10)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surface, (0, 0, 0, 128), bg_surface.get_rect(), border_radius=5)
        screen.blit(bg_surface, bg_rect)
        screen.blit(msg, msg_rect)
    
    # 简化游戏速度设置
    speed_settings = {0.5: 120, 1.0: 90, 2.0: 65, 4.0: 45, 8.0: 30}
    
    def game(speed_multiplier=1):
        snake = [(GRID_W//2, GRID_H//2)]
        food = (random.randrange(GRID_W), random.randrange(GRID_H))
        high_score = load_high_score()
        score = 0
        direction = None
        game_mode = 'auto'
        current_move_interval = speed_settings[speed_multiplier]
        current_fps = 60
        last_move = pygame.time.get_ticks()
        start_time = time.time()
        
        # 游戏控制键映射
        dir_keys = {
            pygame.K_LEFT: (-1, 0), pygame.K_RIGHT: (1, 0),
            pygame.K_UP: (0, -1), pygame.K_DOWN: (0, 1)
        }
        
        # 游戏模式切换映射
        mode_cycle = {'auto': 'manual', 'manual': 'hybrid', 'hybrid': 'auto'}
        mode_text_map = {'auto': '自动模式', 'manual': '手动模式', 'hybrid': '混合模式'}
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        game_mode = mode_cycle[game_mode]
                        direction = None if game_mode == 'manual' else direction
                    elif game_mode in ['manual', 'hybrid'] and event.key in dir_keys:
                        new_dir = dir_keys[event.key]
                        # 检查是否是反方向，如果是则忽略这个按键
                        if not direction or (new_dir[0], new_dir[1]) != (-direction[0], -direction[1]):
                            direction = new_dir
            
            if pygame.time.get_ticks() - last_move >= current_move_interval:
                # 确定下一个位置
                next_pos = None
                if game_mode == 'manual' and direction:
                    x, y = snake[0]
                    next_pos = ((x + direction[0]) % GRID_W, (y + direction[1]) % GRID_H)
                elif game_mode == 'hybrid':
                    if direction and any(pygame.key.get_pressed()[k] for k in dir_keys):
                        x, y = snake[0]
                        next_pos = ((x + direction[0]) % GRID_W, (y + direction[1]) % GRID_H)
                    if not next_pos or next_pos in snake[:-1]:
                        next_pos = get_next_move(snake, food, speed_multiplier)
                else:
                    next_pos = get_next_move(snake, food, speed_multiplier)
                
                if not next_pos or next_pos in snake[:-1]: break
                
                # 更新蛇的位置
                snake.insert(0, next_pos)
                if next_pos == food:
                    score += 1
                    if score > high_score:
                        high_score = score
                        save_high_score(score)
                    # 生成新食物
                    while True:
                        food = (random.randrange(GRID_W), random.randrange(GRID_H))
                        if food not in snake and get_wrapped_distance(food, snake[0]) > 3:
                            break
                else:
                    snake.pop()
                
                last_move = pygame.time.get_ticks()
            
            # 绘制游戏界面
            screen.fill(BLACK)
            
            # 绘制网格线
            for x in range(0, W + 1, C): pygame.draw.line(screen, GRAY, (x, 0), (x, H), 2)
            for y in range(0, H + 1, C): pygame.draw.line(screen, GRAY, (0, y), (W, y), 2)
            pygame.draw.line(screen, GRAY, (0, H-1), (W, H-1), 3)
            
            # 显示游戏信息
            padding = 20
            screen.blit(font.render(mode_text_map[game_mode], True, WHITE), (padding, padding))
            screen.blit(font.render('按空格切换模式', True, WHITE), (padding, padding + 40))
            
            score_text = font.render(f'得分: {score}', True, WHITE)
            high_score_text = font.render(f'最高分: {high_score}', True, WHITE)
            screen.blit(score_text, (W - score_text.get_width() - padding, padding))
            screen.blit(high_score_text, (W - high_score_text.get_width() - padding, padding + 40))
            
            # 绘制食物和蛇
            transparent.fill((0, 0, 0, 0))
            food_glow = pygame.Surface((C*2, C*2), pygame.SRCALPHA)
            pygame.draw.circle(food_glow, (*RED, 100), (C, C), C)
            transparent.blit(food_glow, (food[0]*C - C//2, food[1]*C - C//2))
            pygame.draw.rect(transparent, (*RED, 200), (food[0]*C, food[1]*C, C, C))
            
            for i, segment in enumerate(snake):
                draw_segment(transparent, segment, WHITE if i == 0 else get_rainbow_color(i-1, len(snake)-1), i == 0)
            
            screen.blit(transparent, (0, 0))
            pygame.display.flip()
            clock.tick(current_fps)
        
        # 游戏结束
        game_time = time.time() - start_time
        display_message('游戏结束!', RED)
        display_message(f'最终得分: {score}', WHITE, 40)
        display_message(f'存活时间: {game_time:.1f}秒', WHITE, 80)
        display_message('按任意键返回主菜单', WHITE, 120)
        pygame.display.flip()
        
        # 等待任意键返回
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in [pygame.QUIT, pygame.KEYDOWN]:
                    return
    
    # 主菜单
    menu = ["慢速", "正常", "快速", "极速", "疯狂"]
    speed_values = [0.5, 1, 2, 4, 8]
    selected = 1
    
    while True:
        screen.fill(BLACK)
        display_message("智能贪吃蛇", GREEN, -H//3)
        
        menu_start_y = -H//4
        menu_spacing = int(H/10)
        for i, option in enumerate(menu):
            display_message(option, BLUE if i == selected else WHITE, menu_start_y + i * menu_spacing)
        
        hint_start_y = H//3
        display_message("空格键: 开始游戏", WHITE, hint_start_y)
        display_message("方向键: 手动控制", WHITE, hint_start_y + int(H/15))
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: selected = (selected - 1) % len(menu)
                elif event.key == pygame.K_DOWN: selected = (selected + 1) % len(menu)
                elif event.key == pygame.K_SPACE:
                    game(speed_values[selected])
                    screen.fill(BLACK)
                    pygame.event.wait()

if __name__ == '__main__':
    main()