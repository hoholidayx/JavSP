import os
import cv2
import numpy as np
from PIL import Image, ImageTk
from glob import glob
from ultralytics import YOLO
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
from datetime import datetime

# ---------------------- 全局变量 ----------------------
CURRENT_INDEX = 0  # 当前显示的图片索引
IMAGE_PATHS = []  # 所有处理后的图片路径（原路径+裁切后路径）
ERROR_LOG_PATH = "crop_error_log.txt"  # 错误标注日志文件
# 新增：保存图片对象引用，防止垃圾回收
GLOBAL_PHOTO_REFS = {"original": None, "cropped": None}


# ---------------------- 工具函数：计算IOU（交并比） ----------------------
def calculate_iou(box1, box2):
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2

    inter_x1 = max(x1_1, x1_2)
    inter_y1 = max(y1_1, y1_2)
    inter_x2 = min(x2_1, x2_2)
    inter_y2 = min(y2_1, y2_2)

    if inter_x2 <= inter_x1 or inter_y2 <= inter_y1:
        return 0.0

    inter_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    iou = inter_area / (area1 + area2 - inter_area)
    return iou


# ---------------------- Chambara 中缝检测 ----------------------
def detect_cover_border(img_cv, border_threshold=20):
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, border_threshold, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return 0, 0, 50, 50

    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)
    return x, y, x + w, y + h


def chambara_midline_detection(img_cv, valid_region, edge_threshold=50):
    x1, y1, x2, y2 = valid_region
    valid_img = img_cv[y1:y2, x1:x2]
    gray = cv2.cvtColor(valid_img, cv2.COLOR_BGR2GRAY)

    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_x_abs = np.abs(grad_x)
    col_grad = np.mean(grad_x_abs, axis=0)

    if len(col_grad) == 0:
        return -1

    mid_col = np.argmin(col_grad)
    if col_grad[mid_col] > edge_threshold:
        return -1

    midline_x = x1 + mid_col
    return midline_x


def get_cover_midline(image_path):
    try:
        img_cv = cv2.imread(image_path)
        if img_cv is None:
            return -1, (0, 0, 0, 0)

        valid_region = detect_cover_border(img_cv)
        vx1, vy1, vx2, vy2 = valid_region
        if vx2 - vx1 < 200 or vy2 - vy1 < 200:
            return -1, (0, 0, 0, 0)

        midline_x = chambara_midline_detection(img_cv, valid_region)

        if midline_x == 0:
            img_w = img_cv.shape[1]
            midline_x = img_w // 2
        elif midline_x < 0:
            return -1, (0, 0, 0, 0)

        return midline_x, valid_region

    except Exception as e:
        return -1, (0, 0, 0, 0)


# ---------------------- YOLOv8 人脸+人体IOU精准匹配 ----------------------
def detect_human_full_body_iou(image_path, conf_threshold=0.5, iou_threshold=0.3):
    model = YOLO('yolov8n.pt')
    results = model(image_path, conf=conf_threshold)
    if not results or len(results[0].boxes) == 0:
        return 0, (0, 0), "left", (0, 0, 0, 0)

    img_w = results[0].orig_shape[1]
    mid_x = img_w // 2
    max_total_area = 0
    main_center = (0, 0)
    main_region = "left"
    best_box = (0, 0, 0, 0)

    person_boxes = []
    face_boxes = []
    for box in results[0].boxes:
        cls = int(box.cls.cpu().numpy()[0])
        x1, y1, x2, y2 = box.xyxy.cpu().numpy()[0].astype(int)
        area = (x2 - x1) * (y2 - y1)
        if cls == 0:
            person_boxes.append((x1, y1, x2, y2, area))
        elif cls == 1:
            face_boxes.append((x1, y1, x2, y2, area))

    matched_persons = []
    used_faces = set()

    for person in person_boxes:
        p_x1, p_y1, p_x2, p_y2, p_area = person
        best_iou = 0.0
        best_face = None

        for idx, face in enumerate(face_boxes):
            if idx in used_faces:
                continue
            f_x1, f_y1, f_x2, f_y2, f_area = face
            iou = calculate_iou((p_x1, p_y1, p_x2, p_y2), (f_x1, f_y1, f_x2, f_y2))
            if iou > best_iou and iou >= iou_threshold:
                best_iou = iou
                best_face = face

        if best_face is not None:
            f_x1, f_y1, f_x2, f_y2, f_area = best_face
            merge_x1 = min(p_x1, f_x1)
            merge_y1 = min(p_y1, f_y1)
            merge_x2 = max(p_x2, f_x2)
            merge_y2 = max(p_y2, f_y2)
            merge_area = (merge_x2 - merge_x1) * (merge_y2 - merge_y1)
            matched_persons.append(((merge_x1, merge_y1, merge_x2, merge_y2), merge_area))
            used_faces.add(idx)

    unmatched_persons = []
    for p in person_boxes:
        p_box = (p[0], p[1], p[2], p[3])
        p_area = p[4]
        is_matched = False
        for m in matched_persons:
            if p_box == m[0]:
                is_matched = True
                break
        if not is_matched:
            unmatched_persons.append((p_box, p_area))

    unmatched_faces = []
    for idx, f in enumerate(face_boxes):
        if idx not in used_faces:
            f_box = (f[0], f[1], f[2], f[3])
            f_area = f[4]
            unmatched_faces.append((f_box, f_area))

    all_candidates = matched_persons + unmatched_persons + unmatched_faces
    if not all_candidates:
        return 0, (0, 0), "left", (0, 0, 0, 0)

    best_candidate = max(all_candidates, key=lambda x: x[1])
    best_box, best_area = best_candidate
    bx1, by1, bx2, by2 = best_box

    cx = (bx1 + bx2) // 2
    cy = (by1 + by2) // 2
    main_center = (cx, cy)
    main_region = "left" if cx < mid_x else "right"
    max_total_area = best_area

    return max_total_area, main_center, main_region, best_box


# ---------------------- 核心裁切逻辑：跨中线优先保主体完整 ----------------------
def crop_by_full_body_iou_9_16(image_path, output_path, midline_x, valid_region,
                               conf_threshold=0.5, iou_threshold=0.3,
                               target_aspect=9 / 16, midline_overlap_thresh=0.3,
                               expand_ratio=0.1):
    """
    跨中线裁切策略：优先保证人物完整 > 满足9:16比例
    :param target_aspect: 目标宽高比
    :param midline_overlap_thresh: 跨中线判定阈值
    :param expand_ratio: 主体外安全拓展比例
    """
    img = Image.open(image_path)
    img_w, img_h = img.size

    # 检测主体：返回中心、区域、主体框
    _, body_center, body_region, body_box = detect_human_full_body_iou(image_path, conf_threshold, iou_threshold)
    bx1, by1, bx2, by2 = body_box
    body_width = bx2 - bx1
    body_height = by2 - by1

    # 1. 判定主体是否跨中线
    is_cross_midline = False
    overlap_width = max(0, min(bx2, midline_x) - max(bx1, midline_x))
    if body_width > 0 and (overlap_width / body_width) > midline_overlap_thresh:
        is_cross_midline = True

    if is_cross_midline:
        # 2. 跨中线：优先保证主体完整，再适配比例
        # 第一步：确保主体完全包含（基础安全框）
        safe_bx1 = max(0, bx1 - int(body_width * expand_ratio))
        safe_bx2 = min(img_w, bx2 + int(body_width * expand_ratio))
        safe_by1 = max(0, by1 - int(body_height * expand_ratio))
        safe_by2 = min(img_h, by2 + int(body_height * expand_ratio))

        # 第二步：计算目标宽度（9:16）
        target_crop_width = img_h * target_aspect

        # 第三步：基于安全框调整，优先保证主体在裁切框内
        if (safe_bx2 - safe_bx1) >= target_crop_width:
            # 安全框已满足比例，居中裁切
            center_x = (safe_bx1 + safe_bx2) // 2
            init_x1 = max(0, center_x - int(target_crop_width // 2))
            init_x2 = min(img_w, center_x + int(target_crop_width // 2))
        else:
            # 安全框不足，向两侧拓展（优先保证主体在裁切框内）
            need_expand = target_crop_width - (safe_bx2 - safe_bx1)
            expand_left = int(need_expand * 0.5)
            expand_right = int(need_expand - expand_left)

            init_x1 = max(0, safe_bx1 - expand_left)
            init_x2 = min(img_w, safe_bx2 + expand_right)

            # 仍不足则强制按比例，确保主体完整
            if (init_x2 - init_x1) < target_crop_width:
                # 计算主体在图片中的位置，优先保留主体侧
                if (safe_bx1 + safe_bx2) / 2 < img_w / 2:
                    init_x2 = min(img_w, init_x1 + target_crop_width)
                else:
                    init_x1 = max(0, init_x2 - target_crop_width)
    else:
        # 3. 不跨中线：按原逻辑，优先主体+比例
        cx, cy = body_center
        if body_region == "left":
            init_x2 = midline_x
            init_x1 = max(0, cx - (init_x2 - cx))
        else:
            init_x1 = midline_x
            init_x2 = min(img_w, cx + (cx - init_x1))

        # 调整至目标比例，保证主体完整
        current_width = init_x2 - init_x1
        target_width = img_h * target_aspect
        if current_width < target_width:
            expand = target_width - current_width
            init_x1 = max(0, init_x1 - expand // 2)
            init_x2 = min(img_w, init_x2 + (expand - expand // 2))

    # 最终裁切框（高度始终为完整高度）
    init_y1, init_y2 = 0, img_h
    crop_box = (int(init_x1), init_y1, int(init_x2), init_y2)

    # 二次校验：确保主体完全在裁切框内（最终兜底）
    if not (bx1 >= crop_box[0] and bx2 <= crop_box[2]):
        new_x1 = min(crop_box[0], bx1)
        new_x2 = max(crop_box[2], bx2)
        # 若超出图片则调整，优先保证主体
        if new_x2 - new_x1 > img_w:
            new_x1 = max(0, bx1 - (img_w - (bx2 - bx1)) // 2)
            new_x2 = min(img_w, new_x1 + img_w)
        crop_box = (new_x1, init_y1, new_x2, init_y2)

    # 裁切并保存
    cropped_img = img.crop(crop_box)
    ext = os.path.splitext(output_path)[1].lower()
    if ext in ['.jpg', '.jpeg']:
        cropped_img.save(output_path, quality=100, subsampling=0, optimize=False)
    else:
        cropped_img.save(output_path, optimize=True)

    return True


# ---------------------- 批量处理函数 ----------------------
def batch_process_dvd_covers(source_dir, output_dir,
                             conf_threshold=0.5, iou_threshold=0.3,
                             target_aspect=9 / 16, midline_overlap_thresh=0.3,
                             expand_ratio=0.1):
    global IMAGE_PATHS
    os.makedirs(output_dir, exist_ok=True)
    img_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']
    img_paths = []
    for ext in img_extensions:
        img_paths.extend(glob(os.path.join(source_dir, ext)))

    if not img_paths:
        messagebox.showerror("错误", f"源目录 {source_dir} 中未找到任何图片")
        return

    IMAGE_PATHS = []
    success_count = 0
    for img_path in img_paths:
        midline_x, valid_region = get_cover_midline(img_path)
        if midline_x < 0:
            continue

        img_name = os.path.basename(img_path)
        base_name, ext = os.path.splitext(img_name)
        output_path = os.path.join(output_dir, img_name)
        counter = 1
        while os.path.exists(output_path):
            output_path = os.path.join(output_dir, f"{base_name}_{counter}{ext}")
            counter += 1

        try:
            crop_by_full_body_iou_9_16(
                img_path, output_path, midline_x, valid_region,
                conf_threshold, iou_threshold,
                target_aspect, midline_overlap_thresh,
                expand_ratio
            )
            IMAGE_PATHS.append({
                "original": img_path,
                "cropped": output_path
            })
            success_count += 1
        except Exception as e:
            print(f"处理失败 {img_path}: {str(e)}")
            continue

    if success_count == 0:
        messagebox.showwarning("警告", "未成功处理任何图片")
        return

    # 启动对比界面
    show_compare_gui()


# ---------------------- 对比界面相关函数 ----------------------
def resize_image(image_path, max_size=(800, 600)):
    try:
        img = Image.open(image_path)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        blank_img = Image.new('RGB', max_size, color='gray')
        return blank_img


def update_image_display(orig_label, crop_label, page_label):
    global CURRENT_INDEX, IMAGE_PATHS, GLOBAL_PHOTO_REFS

    if not IMAGE_PATHS:
        return

    CURRENT_INDEX = CURRENT_INDEX % len(IMAGE_PATHS)

    current_data = IMAGE_PATHS[CURRENT_INDEX]
    orig_path = current_data["original"]
    crop_path = current_data["cropped"]

    orig_img = resize_image(orig_path)
    crop_img = resize_image(crop_path)

    GLOBAL_PHOTO_REFS["original"] = ImageTk.PhotoImage(orig_img)
    GLOBAL_PHOTO_REFS["cropped"] = ImageTk.PhotoImage(crop_img)

    orig_label.config(image=GLOBAL_PHOTO_REFS["original"])
    crop_label.config(image=GLOBAL_PHOTO_REFS["cropped"])

    page_label.config(text=f"第 {CURRENT_INDEX + 1}/{len(IMAGE_PATHS)} 张")


def prev_image(orig_label, crop_label, page_label):
    global CURRENT_INDEX
    CURRENT_INDEX -= 1
    update_image_display(orig_label, crop_label, page_label)


def next_image(orig_label, crop_label, page_label):
    global CURRENT_INDEX
    CURRENT_INDEX += 1
    update_image_display(orig_label, crop_label, page_label)


def mark_correct(orig_label, crop_label, page_label):
    next_image(orig_label, crop_label, page_label)


def mark_error(orig_label, crop_label, page_label):
    """优化：错误按钮静默记录日志，无弹窗（仅系统错误提示）"""
    global CURRENT_INDEX, IMAGE_PATHS

    if not IMAGE_PATHS:
        messagebox.showerror("系统错误", "无图片可标记！")
        return

    current_data = IMAGE_PATHS[CURRENT_INDEX]
    orig_path = current_data["original"]
    crop_path = current_data["cropped"]

    # 静默写入日志（无弹窗）
    try:
        with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n【标记时间】: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"【原始路径】: {orig_path}\n")
            f.write(f"【裁切路径】: {crop_path}\n")
            f.write("-" * 80 + "\n")
    except Exception as e:
        messagebox.showerror("系统错误", f"日志写入失败：{str(e)}")
        return

    next_image(orig_label, crop_label, page_label)


def show_compare_gui():
    compare_root = tk.Toplevel()
    compare_root.title("图片裁切前后对比")
    compare_root.geometry("1700x800")
    compare_root.resizable(True, True)
    compare_root.attributes('-topmost', True)

    page_label = ttk.Label(compare_root, text="", font=("Arial", 14))
    page_label.pack(pady=10)

    img_frame = ttk.Frame(compare_root)
    img_frame.pack(pady=10, fill=tk.BOTH, expand=True)

    orig_frame = ttk.Frame(img_frame)
    orig_frame.grid(row=0, column=0, padx=20)
    ttk.Label(orig_frame, text="裁切前", font=("Arial", 12, "bold")).pack(pady=5)
    orig_label = ttk.Label(orig_frame, relief=tk.SUNKEN)
    orig_label.pack()

    crop_frame = ttk.Frame(img_frame)
    crop_frame.grid(row=0, column=1, padx=20)
    ttk.Label(crop_frame, text="裁切后", font=("Arial", 12, "bold")).pack(pady=5)
    crop_label = ttk.Label(crop_frame, relief=tk.SUNKEN)
    crop_label.pack()

    btn_frame = ttk.Frame(compare_root)
    btn_frame.pack(pady=20)

    prev_btn = ttk.Button(btn_frame, text="上一页",
                          command=lambda: prev_image(orig_label, crop_label, page_label),
                          width=12)
    prev_btn.grid(row=0, column=0, padx=15)

    next_btn = ttk.Button(btn_frame, text="下一页",
                          command=lambda: next_image(orig_label, crop_label, page_label),
                          width=12)
    next_btn.grid(row=0, column=1, padx=15)

    correct_btn = ttk.Button(btn_frame, text="正确",
                             command=lambda: mark_correct(orig_label, crop_label, page_label),
                             width=12, style="Success.TButton")
    correct_btn.grid(row=0, column=2, padx=15)

    error_btn = ttk.Button(btn_frame, text="错误",
                           command=lambda: mark_error(orig_label, crop_label, page_label),
                           width=12, style="Error.TButton")
    error_btn.grid(row=0, column=3, padx=15)

    style = ttk.Style()
    style.configure("Success.TButton", foreground="green", font=("Arial", 10))
    style.configure("Error.TButton", foreground="red", font=("Arial", 10))

    update_image_display(orig_label, crop_label, page_label)

    def on_close():
        global GLOBAL_PHOTO_REFS
        GLOBAL_PHOTO_REFS = {"original": None, "cropped": None}
        compare_root.destroy()

    compare_root.protocol("WM_DELETE_WINDOW", on_close)


# ---------------------- 说明页面函数 ----------------------
def show_help_window():
    """创建详细说明窗口"""
    help_root = tk.Toplevel()
    help_root.title("工具使用说明")
    help_root.geometry("800x600")
    help_root.resizable(True, True)
    help_root.attributes('-topmost', True)

    # 创建滚动文本框
    help_text = scrolledtext.ScrolledText(help_root, wrap=tk.WORD, font=("Arial", 10), padx=15, pady=15)
    help_text.pack(fill=tk.BOTH, expand=True)

    # 说明内容
    help_content = """
# DVD封面智能裁切工具 详细说明
## 一、工具作用
本工具基于YOLOv8目标检测算法，实现DVD/影视海报的**智能主体裁切**，核心功能：
1. 自动识别海报中的人物主体（人脸+人体匹配）
2. 判定主体是否横跨图片中线，采用差异化裁切策略
3. 优先保证人物主体完整，再适配目标宽高比（默认9:16）
4. 提供可视化对比界面，支持人工审核与错误标记

## 二、核心算法原理
### 1. 中缝检测（Chambara Midline Detection）
- 基于图像边缘梯度，计算图片的视觉中线位置
- 用于区分主体位于左侧、右侧或横跨中线
- 解决传统对半裁切导致主体截断的问题

### 2. YOLOv8 人脸+人体IOU匹配
- 使用YOLOv8n轻量级模型，同时检测人体（class 0）和人脸（class 1）
- 计算人体框与人脸框的IOU（交并比），匹配属于同一人的检测框
- 选择面积最大的匹配框作为核心主体，确保裁切焦点准确

### 3. 跨中线判定逻辑
- 计算主体框与中线的重叠宽度占主体总宽度的比例
- 当比例超过设定阈值（默认0.3），判定为主体跨中线
- 跨中线时采用「主体优先」裁切策略，非跨中线时采用「中线+主体」策略

## 三、裁切策略详解
### 1. 跨中线裁切策略（优先级：主体完整 > 比例适配）
步骤1： 为主体添加安全拓展区（比例可配置），确保主体不被截断
步骤2： 计算目标宽度（基于目标宽高比和图片高度）
步骤3： 若安全框宽度 ≥ 目标宽度 → 安全框内居中裁切
步骤4： 若安全框宽度 < 目标宽度 → 向安全框两侧均匀拓展
步骤5： 拓展后仍不足 → 向主体所在侧优先延伸，强制满足比例

### 2. 非跨中线裁切策略
步骤1： 以中线为界，确定主体所在侧（左/右）
步骤2： 以主体中心为基准，向中线方向扩展
步骤3： 调整宽度至目标比例，确保主体完整

## 四、参数说明（主界面可配置）
### 1. 路径配置
- 源图片目录：待裁切的海报图片所在文件夹
- 输出目录：裁切后的图片保存路径

### 2. 检测参数
- 检测置信度（0-1）：YOLO模型检测阈值，越高检测越严格，漏检率上升；越低检测越宽松，误检率上升。默认0.5
- IOU匹配阈值（0-1）：人脸与人体的匹配阈值，越高匹配越精准，默认0.3

### 3. 裁切参数
- 目标宽高比：裁切后的图片比例，默认9/16（竖版海报常用），可根据需求修改（如16/9横版）
- 跨中线判定阈值（0-1）：判定主体跨中线的灵敏度，值越低越易判定为跨中线，默认0.3
- 主体拓展比例（0-0.5）：主体框外的安全区域比例，防止主体边缘被截断，默认0.1

## 五、使用步骤
1. 配置源目录、输出目录及各项参数
2. 点击「开始裁切并对比」按钮，工具自动处理所有图片
3. 对比界面弹出后，查看裁切前后效果
4. 点击「正确」→ 自动跳至下一张；点击「错误」→ 静默记录路径到日志文件
5. 审核完成后关闭对比窗口即可

## 六、日志说明
- 错误日志文件：crop_error_log.txt
- 日志内容：标记时间、原始图片路径、裁切图片路径
- 日志位置：脚本运行目录下
    """

    # 插入内容并设置只读
    help_text.insert(tk.END, help_content)
    help_text.config(state=tk.DISABLED)

    # 关闭按钮
    close_btn = ttk.Button(help_root, text="关闭", command=help_root.destroy, width=15)
    close_btn.pack(pady=10)


# ---------------------- 主界面：所有可调参数可视化 + 说明按钮 ----------------------
def create_main_gui():
    root = tk.Tk()
    root.title("DVD封面智能裁切工具")
    root.geometry("750x650")
    root.resizable(False, False)

    # 标题
    title_label = ttk.Label(root, text="DVD封面智能裁切工具", font=("Arial", 16, "bold"))
    title_label.pack(pady=20)

    # 说明按钮（新增）
    help_btn = ttk.Button(root, text="使用说明", command=show_help_window, width=15)
    help_btn.pack(pady=5)

    # 第一组：路径配置
    path_frame = ttk.LabelFrame(root, text="路径配置", padding=10)
    path_frame.pack(fill=tk.X, padx=30, pady=10)

    ttk.Label(path_frame, text="源图片目录:", font=("Arial", 11)).grid(row=0, column=0, sticky=tk.W, pady=5)
    source_entry = ttk.Entry(path_frame, width=60, font=("Arial", 10))
    source_entry.grid(row=0, column=1, padx=10, pady=5)
    source_entry.insert(0, os.path.expanduser("~/Downloads/outputs_posters"))

    ttk.Label(path_frame, text="输出目录:", font=("Arial", 11)).grid(row=1, column=0, sticky=tk.W, pady=5)
    output_entry = ttk.Entry(path_frame, width=60, font=("Arial", 10))
    output_entry.grid(row=1, column=1, padx=10, pady=5)
    output_entry.insert(0, os.path.expanduser("~/Downloads/outputs_posters2"))

    # 第二组：检测参数
    detect_frame = ttk.LabelFrame(root, text="检测参数", padding=10)
    detect_frame.pack(fill=tk.X, padx=30, pady=10)

    ttk.Label(detect_frame, text="检测置信度:", font=("Arial", 11)).grid(row=0, column=0, sticky=tk.W, pady=5)
    conf_var = tk.DoubleVar(value=0.5)
    conf_entry = ttk.Entry(detect_frame, textvariable=conf_var, width=15, font=("Arial", 10))
    conf_entry.grid(row=0, column=1, padx=10, pady=5)
    ttk.Label(detect_frame, text="(0-1，越高越严格)", font=("Arial", 9)).grid(row=0, column=2, sticky=tk.W)

    ttk.Label(detect_frame, text="IOU匹配阈值:", font=("Arial", 11)).grid(row=1, column=0, sticky=tk.W, pady=5)
    iou_var = tk.DoubleVar(value=0.3)
    iou_entry = ttk.Entry(detect_frame, textvariable=iou_var, width=15, font=("Arial", 10))
    iou_entry.grid(row=1, column=1, padx=10, pady=5)
    ttk.Label(detect_frame, text="(0-1，越高匹配越准)", font=("Arial", 9)).grid(row=1, column=2, sticky=tk.W)

    # 第三组：裁切参数
    crop_frame = ttk.LabelFrame(root, text="裁切参数", padding=10)
    crop_frame.pack(fill=tk.X, padx=30, pady=10)

    ttk.Label(crop_frame, text="目标宽高比:", font=("Arial", 11)).grid(row=0, column=0, sticky=tk.W, pady=5)
    aspect_var = tk.DoubleVar(value=9 / 16)
    aspect_entry = ttk.Entry(crop_frame, textvariable=aspect_var, width=15, font=("Arial", 10))
    aspect_entry.grid(row=0, column=1, padx=10, pady=5)
    ttk.Label(crop_frame, text="(默认9/16=0.5625)", font=("Arial", 9)).grid(row=0, column=2, sticky=tk.W)

    ttk.Label(crop_frame, text="跨中线判定阈值:", font=("Arial", 11)).grid(row=1, column=0, sticky=tk.W, pady=5)
    overlap_var = tk.DoubleVar(value=0.3)
    overlap_entry = ttk.Entry(crop_frame, textvariable=overlap_var, width=15, font=("Arial", 10))
    overlap_entry.grid(row=1, column=1, padx=10, pady=5)
    ttk.Label(crop_frame, text="(0-1，越低越易判定跨中线)", font=("Arial", 9)).grid(row=1, column=2, sticky=tk.W)

    ttk.Label(crop_frame, text="主体拓展比例:", font=("Arial", 11)).grid(row=2, column=0, sticky=tk.W, pady=5)
    expand_var = tk.DoubleVar(value=0.1)
    expand_entry = ttk.Entry(crop_frame, textvariable=expand_var, width=15, font=("Arial", 10))
    expand_entry.grid(row=2, column=1, padx=10, pady=5)
    ttk.Label(crop_frame, text="(0-0.5，主体外安全区)", font=("Arial", 9)).grid(row=2, column=2, sticky=tk.W)

    # 开始处理按钮
    def start_process():
        # 获取所有参数
        source_dir = source_entry.get().strip()
        output_dir = output_entry.get().strip()
        conf = conf_var.get()
        iou = iou_var.get()
        target_aspect = aspect_var.get()
        midline_overlap_thresh = overlap_var.get()
        expand_ratio = expand_var.get()

        # 参数校验
        if not os.path.exists(source_dir):
            messagebox.showerror("错误", "源目录不存在！")
            return
        if not (0 <= conf <= 1):
            messagebox.showerror("错误", "检测置信度需在0-1之间！")
            return
        if not (0 <= iou <= 1):
            messagebox.showerror("错误", "IOU阈值需在0-1之间！")
            return
        if target_aspect <= 0:
            messagebox.showerror("错误", "目标宽高比必须大于0！")
            return
        if not (0 <= midline_overlap_thresh <= 1):
            messagebox.showerror("错误", "跨中线判定阈值需在0-1之间！")
            return
        if not (0 <= expand_ratio <= 0.5):
            messagebox.showerror("错误", "主体拓展比例需在0-0.5之间！")
            return

        # 执行处理
        root.update()
        batch_process_dvd_covers(
            source_dir, output_dir,
            conf, iou,
            target_aspect, midline_overlap_thresh,
            expand_ratio
        )

    start_btn = ttk.Button(root, text="开始裁切并对比", command=start_process,
                           style="Accent.TButton", width=25)
    start_btn.pack(pady=30)

    root.mainloop()


# ---------------------- 执行入口 ----------------------
if __name__ == "__main__":
    # 兼容macOS PIL缩放
    if sys.platform == "darwin":
        try:
            from PIL import Image

            Image.ANTIALIAS = Image.Resampling.LANCZOS
        except:
            pass

    # 初始化错误日志
    if not os.path.exists(ERROR_LOG_PATH):
        with open(ERROR_LOG_PATH, "w", encoding="utf-8") as f:
            f.write("图片裁切错误日志\n")
            f.write("=" * 80 + "\n")
            f.write(f"日志创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 80 + "\n")

    # 启动主界面
    create_main_gui()