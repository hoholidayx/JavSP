import os
import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from ultralytics import YOLO
import threading


# -------------------------- 全局变量与初始化 --------------------------
class PosterCropApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DVD海报人物裁切工具 v1.5（最终无错版）")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)

        # 核心参数
        self.params = {
            "input_dir": tk.StringVar(value="/Users/hoholiday/Downloads/input_posters"),
            "output_dir": tk.StringVar(value="/Users/hoholiday/Downloads/output_posters"),
            "conf_threshold": tk.DoubleVar(value=0.5),
            "body_complete_ratio": tk.DoubleVar(value=0.6),
            "expansion_ratio": tk.DoubleVar(value=0.2),
            "aspect_ratio_w": tk.IntVar(value=2),
            "aspect_ratio_h": tk.IntVar(value=3),
            "min_bbox_w": tk.IntVar(value=20),
            "min_bbox_h": tk.IntVar(value=50)
        }

        # 模型与状态变量
        self.model = None
        self.processed_files = []
        self.current_index = 0
        self.crop_rect = None
        self.crop_start_x = 0
        self.crop_start_y = 0
        self.original_img = None
        self.original_img_tk = None
        self.ori_img_tk = None
        self.crop_img_tk = None

        # 创建UI
        self.create_widgets()
        # 加载模型
        threading.Thread(target=self.load_model, daemon=True).start()

    def load_model(self):
        """子线程加载YOLO模型"""
        try:
            self.model = YOLO("yolov8n.pt")
            self.log_text.insert(tk.END, "✅ YOLOv8n模型加载完成\n")
            self.log_text.see(tk.END)
        except Exception as e:
            self.log_text.insert(tk.END, f"❌ 模型加载失败：{str(e)}\n")
            self.log_text.see(tk.END)
            messagebox.showerror("错误", f"模型加载失败：{str(e)}")

    def create_widgets(self):
        """创建UI组件（彻底修复所有tkinter参数错误）"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)
        main_frame.columnconfigure(0, weight=0)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=0)
        main_frame.rowconfigure(2, weight=1)

        # 1. 参数配置区（左侧）
        param_frame = ttk.LabelFrame(main_frame, text="参数配置", padding="10")
        param_frame.grid(row=0, column=0, rowspan=3, sticky="ns", padx=5, pady=5)
        for i in range(9):
            param_frame.rowconfigure(i, weight=1)
        param_frame.columnconfigure(1, weight=1)

        # 路径配置（仅使用grid支持的参数）
        ttk.Label(param_frame, text="输入目录：").grid(row=0, column=0, sticky="w", pady=2)
        ttk.Entry(param_frame, textvariable=self.params["input_dir"]).grid(row=0, column=1, sticky="ew", pady=2, padx=2)
        ttk.Button(param_frame, text="浏览", command=self.select_input_dir).grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(param_frame, text="输出目录：").grid(row=1, column=0, sticky="w", pady=2)
        ttk.Entry(param_frame, textvariable=self.params["output_dir"]).grid(row=1, column=1, sticky="ew", pady=2,
                                                                            padx=2)
        ttk.Button(param_frame, text="浏览", command=self.select_output_dir).grid(row=1, column=2, padx=5, pady=2)

        # 检测参数（仅使用合法的sticky值：w/ew）
        ttk.Label(param_frame, text="检测置信度阈值：").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Scale(param_frame, from_=0.1, to=0.9, variable=self.params["conf_threshold"],
                  orient="horizontal", command=lambda v: self.update_param_label("conf_label", v)).grid(row=2, column=1,
                                                                                                        sticky="ew",
                                                                                                        pady=2, padx=2)
        self.conf_label = ttk.Label(param_frame, text=f"{self.params['conf_threshold'].get():.1f}")
        self.conf_label.grid(row=2, column=2, padx=5, pady=2)

        ttk.Label(param_frame, text="人体完整性阈值：").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Scale(param_frame, from_=0.3, to=0.9, variable=self.params["body_complete_ratio"],
                  orient="horizontal", command=lambda v: self.update_param_label("body_label", v)).grid(row=3, column=1,
                                                                                                        sticky="ew",
                                                                                                        pady=2, padx=2)
        self.body_label = ttk.Label(param_frame, text=f"{self.params['body_complete_ratio'].get():.1f}")
        self.body_label.grid(row=3, column=2, padx=5, pady=2)

        # 裁切参数
        ttk.Label(param_frame, text="主体拓展比例：").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Scale(param_frame, from_=0.0, to=0.5, variable=self.params["expansion_ratio"],
                  orient="horizontal", command=lambda v: self.update_param_label("expand_label", v)).grid(row=4,
                                                                                                          column=1,
                                                                                                          sticky="ew",
                                                                                                          pady=2,
                                                                                                          padx=2)
        self.expand_label = ttk.Label(param_frame, text=f"{self.params['expansion_ratio'].get():.1f}")
        self.expand_label.grid(row=4, column=2, padx=5, pady=2)

        ttk.Label(param_frame, text="裁切宽高比（宽）：").grid(row=5, column=0, sticky="w", pady=2)
        ttk.Spinbox(param_frame, from_=1, to=10, textvariable=self.params["aspect_ratio_w"], width=5).grid(row=5,
                                                                                                           column=1,
                                                                                                           sticky="w",
                                                                                                           pady=2)

        ttk.Label(param_frame, text="裁切宽高比（高）：").grid(row=6, column=0, sticky="w", pady=2)
        ttk.Spinbox(param_frame, from_=1, to=10, textvariable=self.params["aspect_ratio_h"], width=5).grid(row=6,
                                                                                                           column=1,
                                                                                                           sticky="w",
                                                                                                           pady=2)

        # 最小检测框参数
        ttk.Label(param_frame, text="最小检测框宽度：").grid(row=7, column=0, sticky="w", pady=2)
        ttk.Spinbox(param_frame, from_=10, to=100, textvariable=self.params["min_bbox_w"], width=5).grid(row=7,
                                                                                                         column=1,
                                                                                                         sticky="w",
                                                                                                         pady=2)

        ttk.Label(param_frame, text="最小检测框高度：").grid(row=8, column=0, sticky="w", pady=2)
        ttk.Spinbox(param_frame, from_=30, to=200, textvariable=self.params["min_bbox_h"], width=5).grid(row=8,
                                                                                                         column=1,
                                                                                                         sticky="w",
                                                                                                         pady=2)

        # 2. 结果展示区（关键修复：anchor是Label的属性，不是grid的参数）
        result_frame = ttk.LabelFrame(main_frame, text="裁切结果预览（原图/自动裁切）", padding="10")
        result_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        result_frame.columnconfigure(0, weight=1)
        result_frame.columnconfigure(1, weight=1)
        result_frame.rowconfigure(1, weight=1)

        # 标题居中：anchor作为Label的参数，grid仅用合法参数
        self.original_label = ttk.Label(result_frame, text="原图", anchor="center")
        self.original_label.grid(row=0, column=0, pady=5)
        self.cropped_label = ttk.Label(result_frame, text="自动裁切结果", anchor="center")
        self.cropped_label.grid(row=0, column=1, pady=5)

        self.original_canvas = tk.Canvas(result_frame, bg="#f0f0f0", highlightthickness=1, highlightbackground="#ccc")
        self.original_canvas.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.cropped_canvas = tk.Canvas(result_frame, bg="#f0f0f0", highlightthickness=1, highlightbackground="#ccc")
        self.cropped_canvas.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        # 3. 操作按钮区
        btn_frame = ttk.Frame(main_frame, padding="10")
        btn_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        for i in range(6):
            btn_frame.columnconfigure(i, weight=1)

        ttk.Button(btn_frame, text="批量处理图片", command=self.batch_process).grid(row=0, column=0, padx=3, pady=3,
                                                                                    sticky="ew")
        ttk.Button(btn_frame, text="查看上一张", command=self.prev_image).grid(row=0, column=1, padx=3, pady=3,
                                                                               sticky="ew")
        ttk.Button(btn_frame, text="查看下一张", command=self.next_image).grid(row=0, column=2, padx=3, pady=3,
                                                                               sticky="ew")
        ttk.Button(btn_frame, text="标记为不合格", command=self.mark_unqualified).grid(row=0, column=3, padx=3, pady=3,
                                                                                       sticky="ew")
        ttk.Button(btn_frame, text="人工裁切当前图", command=self.open_manual_crop).grid(row=0, column=4, padx=3,
                                                                                         pady=3, sticky="ew")
        ttk.Button(btn_frame, text="查看使用说明", command=self.show_help).grid(row=0, column=5, padx=3, pady=3,
                                                                                sticky="ew")

        # 4. 日志区
        log_frame = ttk.LabelFrame(main_frame, text="处理日志（自动滚动）", padding="10")
        log_frame.grid(row=2, column=1, sticky="nsew", padx=5, pady=5)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap="word")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        self.log_text.config(height=8)

        # 5. 人工裁切窗口
        self.crop_window = tk.Toplevel(self.root)
        self.crop_window.title("人工裁切（鼠标绘制红框）")
        self.crop_window.geometry("800x700")
        self.crop_window.minsize(600, 500)
        self.crop_window.withdraw()

        crop_main = ttk.Frame(self.crop_window, padding="10")
        crop_main.pack(fill="both", expand=True)
        crop_main.rowconfigure(0, weight=1)
        crop_main.columnconfigure(0, weight=1)
        crop_main.rowconfigure(1, weight=0)

        self.crop_canvas = tk.Canvas(crop_main, bg="#f0f0f0", highlightthickness=1, highlightbackground="#ccc")
        self.crop_canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.crop_canvas.bind("<ButtonPress-1>", self.start_crop)
        self.crop_canvas.bind("<B1-Motion>", self.draw_crop_rect)
        self.crop_canvas.bind("<ButtonRelease-1>", self.end_crop)

        crop_btn_frame = ttk.Frame(crop_main)
        crop_btn_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        crop_btn_frame.columnconfigure(0, weight=1)
        crop_btn_frame.columnconfigure(1, weight=1)
        ttk.Button(crop_btn_frame, text="保存裁切结果", command=self.save_manual_crop).grid(row=0, column=0, padx=5,
                                                                                            pady=5, sticky="ew")
        ttk.Button(crop_btn_frame, text="取消", command=lambda: self.crop_window.withdraw()).grid(row=0, column=1,
                                                                                                  padx=5, pady=5,
                                                                                                  sticky="ew")

    def update_param_label(self, label_name, value):
        """更新参数标签"""
        value = round(float(value), 1)
        if label_name == "conf_label":
            self.conf_label.config(text=f"{value:.1f}")
        elif label_name == "body_label":
            self.body_label.config(text=f"{value:.1f}")
        elif label_name == "expand_label":
            self.expand_label.config(text=f"{value:.1f}")

    def select_input_dir(self):
        """选择输入目录"""
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.params["input_dir"].set(dir_path)

    def select_output_dir(self):
        """选择输出目录"""
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.params["output_dir"].set(dir_path)

    def resize_image(self, img, canvas):
        """等比例缩放图片"""
        canvas_w = canvas.winfo_width()
        canvas_h = canvas.winfo_height()
        if canvas_w <= 10 or canvas_h <= 10:
            canvas_w = 400
            canvas_h = 600

        img_ratio = img.width / img.height
        canvas_ratio = canvas_w / canvas_h

        if img_ratio > canvas_ratio:
            new_w = canvas_w
            new_h = int(new_w / img_ratio)
        else:
            new_h = canvas_h
            new_w = int(new_h * img_ratio)

        # 兼容新旧Pillow版本
        try:
            return img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        except AttributeError:
            return img.resize((new_w, new_h), Image.LANCZOS)

    # -------------------------- 核心业务逻辑 --------------------------
    def get_complete_largest_person_bbox(self, image, img_h, img_w):
        """检测完整人物"""
        if not self.model:
            return None
        conf_thresh = self.params["conf_threshold"].get()
        body_complete_ratio = self.params["body_complete_ratio"].get()
        min_bbox_w = self.params["min_bbox_w"].get()
        min_bbox_h = self.params["min_bbox_h"].get()

        results = self.model(image, conf=conf_thresh)
        valid_persons = []

        for r in results:
            boxes = r.boxes
            for box in boxes:
                # 只处理人物类别（YOLOv8中0代表person）
                if int(box.cls.item()) != 0:  # 修复：使用.item()获取标量
                    continue
                try:
                    # 修复核心：正确提取标量值
                    xyxy = box.xyxy[0].cpu().numpy()  # 获取bbox坐标数组
                    x1, y1, x2, y2 = map(int, xyxy)  # 直接转换数组中的4个值

                    # 使用.item()将1维置信度数组转为Python标量
                    conf = box.conf.cpu().numpy().item()
                except Exception:
                    # 兼容detach的情况
                    xyxy = box.xyxy[0].detach().cpu().numpy()
                    x1, y1, x2, y2 = map(int, xyxy)
                    conf = box.conf.detach().cpu().numpy().item()

                bbox_w = x2 - x1
                bbox_h = y2 - y1
                if bbox_w < min_bbox_w or bbox_h < min_bbox_h:
                    continue

                human_hw_ratio = bbox_h / bbox_w
                if 2 * body_complete_ratio <= human_hw_ratio <= 4 / body_complete_ratio:
                    bbox_area = bbox_w * bbox_h
                    valid_persons.append({
                        "bbox": (x1, y1, x2, y2),
                        "area": bbox_area,
                        "conf": conf,
                        "hw_ratio": human_hw_ratio
                    })

        if not valid_persons:
            return None
        valid_persons.sort(key=lambda x: x["area"], reverse=True)
        return valid_persons[0]["bbox"]

    def calculate_crop_box(self, image_shape, person_bbox):
        """计算裁切框"""
        img_h, img_w = image_shape
        p_x1, p_y1, p_x2, p_y2 = person_bbox
        expansion_ratio = self.params["expansion_ratio"].get()
        aspect_w = self.params["aspect_ratio_w"].get()
        aspect_h = self.params["aspect_ratio_h"].get()
        target_w_h = aspect_w / aspect_h

        p_center_x = (p_x1 + p_x2) / 2
        p_center_y = (p_y1 + p_y2) / 2
        p_w = p_x2 - p_x1
        p_h = p_y2 - p_y1

        expand_w = p_w * expansion_ratio
        expand_h = p_h * expansion_ratio
        exp_x1 = max(0, p_x1 - expand_w)
        exp_y1 = max(0, p_y1 - expand_h)
        exp_x2 = min(img_w, p_x2 + expand_w)
        exp_y2 = min(img_h, p_y2 + expand_h)
        exp_w = exp_x2 - exp_x1
        exp_h = exp_y2 - exp_y1

        if exp_w / exp_h < target_w_h:
            final_h = exp_h
            final_w = final_h * target_w_h
        else:
            final_w = exp_w
            final_h = final_w / target_w_h

        crop_x1 = p_center_x - final_w / 2
        crop_y1 = p_center_y - final_h / 2
        crop_x2 = p_center_x + final_w / 2
        crop_y2 = p_center_y + final_h / 2

        crop_x1 = max(0, int(crop_x1))
        crop_y1 = max(0, int(crop_y1))
        crop_x2 = min(img_w, int(crop_x2))
        crop_y2 = min(img_h, int(crop_y2))

        crop_x1 = min(crop_x1, p_x1)
        crop_y1 = min(crop_y1, p_y1)
        crop_x2 = max(crop_x2, p_x2)
        crop_y2 = max(crop_y2, p_y2)

        return (crop_x1, crop_y1, crop_x2, crop_y2)

    def process_single_image(self, input_path, output_path):
        """处理单张图片"""
        try:
            img_cv = cv2.imread(input_path)
            if img_cv is None:
                self.log_text.insert(tk.END, f"⚠️ 无法读取：{os.path.basename(input_path)}\n")
                self.log_text.see(tk.END)
                return None

            img_h, img_w = img_cv.shape[:2]
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)

            bbox = self.get_complete_largest_person_bbox(img_cv, img_h, img_w)
            if bbox is None:
                self.log_text.insert(tk.END, f"⚠️ 无完整人物：{os.path.basename(input_path)}\n")
                self.log_text.see(tk.END)
                return None

            crop_box = self.calculate_crop_box((img_h, img_w), bbox)
            cropped_img = img_pil.crop(crop_box)
            cropped_img.save(output_path, quality=95)

            self.log_text.insert(tk.END, f"✅ 处理完成：{os.path.basename(input_path)}\n")
            self.log_text.see(tk.END)
            return output_path

        except Exception as e:
            self.log_text.insert(tk.END, f"❌ 处理失败：{os.path.basename(input_path)} - {str(e)[:50]}...\n")
            self.log_text.see(tk.END)
            return None

    def batch_process(self):
        """批量处理"""
        input_dir = self.params["input_dir"].get()
        output_dir = self.params["output_dir"].get()

        if not os.path.exists(input_dir):
            messagebox.showerror("错误", "输入目录不存在！")
            return
        os.makedirs(output_dir, exist_ok=True)

        self.processed_files = []
        self.current_index = 0

        supported = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
        image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(supported)]

        if not image_files:
            messagebox.showwarning("提示", "输入目录无支持的图片！")
            return

        def process_thread():
            self.log_text.insert(tk.END, f"\n🚀 开始批量处理：共{len(image_files)}张图片\n")
            self.log_text.see(tk.END)

            for filename in image_files:
                input_path = os.path.join(input_dir, filename)
                output_path = os.path.join(output_dir, filename)
                crop_path = self.process_single_image(input_path, output_path)
                if crop_path:
                    self.processed_files.append((input_path, crop_path, True))

            self.log_text.insert(tk.END,
                                 f"\n📊 批量处理完成：成功{len(self.processed_files)}张 | 失败{len(image_files) - len(self.processed_files)}张\n")
            self.log_text.see(tk.END)

            if self.processed_files:
                self.show_image(0)

        threading.Thread(target=process_thread, daemon=True).start()

    # -------------------------- 结果展示与人工裁切 --------------------------
    def show_image(self, index):
        """展示图片"""
        if not self.processed_files or index < 0 or index >= len(self.processed_files):
            return

        self.current_index = index
        input_path, crop_path, _ = self.processed_files[index]

        # 显示原图
        try:
            self.original_canvas.delete("all")
            img_ori = Image.open(input_path)
            img_ori_resized = self.resize_image(img_ori, self.original_canvas)
            self.ori_img_tk = ImageTk.PhotoImage(img_ori_resized)

            x = (self.original_canvas.winfo_width() - img_ori_resized.width) / 2
            y = (self.original_canvas.winfo_height() - img_ori_resized.height) / 2
            self.original_canvas.create_image(x, y, anchor="nw", image=self.ori_img_tk)
        except Exception as e:
            self.original_canvas.delete("all")
            self.original_canvas.create_text(self.original_canvas.winfo_width() / 2,
                                             self.original_canvas.winfo_height() / 2,
                                             text=f"加载失败：{str(e)[:20]}...", fill="red")

        # 显示裁切图
        try:
            self.cropped_canvas.delete("all")
            img_crop = Image.open(crop_path)
            img_crop_resized = self.resize_image(img_crop, self.cropped_canvas)
            self.crop_img_tk = ImageTk.PhotoImage(img_crop_resized)

            x = (self.cropped_canvas.winfo_width() - img_crop_resized.width) / 2
            y = (self.cropped_canvas.winfo_height() - img_crop_resized.height) / 2
            self.cropped_canvas.create_image(x, y, anchor="nw", image=self.crop_img_tk)
        except Exception as e:
            self.cropped_canvas.delete("all")
            self.cropped_canvas.create_text(self.cropped_canvas.winfo_width() / 2,
                                            self.cropped_canvas.winfo_height() / 2,
                                            text=f"加载失败：{str(e)[:20]}...", fill="red")

    def prev_image(self):
        """上一张"""
        self.show_image(self.current_index - 1)

    def next_image(self):
        """下一张"""
        self.show_image(self.current_index + 1)

    def mark_unqualified(self):
        """标记不合格"""
        if not self.processed_files:
            return

        input_path, crop_path, _ = self.processed_files[self.current_index]
        self.processed_files[self.current_index] = (input_path, crop_path, False)

        self.log_text.insert(tk.END, f"⚠️ 标记为不合格：{os.path.basename(input_path)}\n")
        self.log_text.see(tk.END)
        messagebox.showinfo("提示", "已标记为不合格，可进行人工裁切！")

    def open_manual_crop(self):
        """打开人工裁切"""
        if not self.processed_files:
            messagebox.showwarning("提示", "暂无处理完成的图片！")
            return

        input_path, _, _ = self.processed_files[self.current_index]

        try:
            self.original_img = Image.open(input_path)
            self.crop_canvas.delete("all")

            img_resized = self.resize_image(self.original_img, self.crop_canvas)
            self.original_img_tk = ImageTk.PhotoImage(img_resized)

            x = (self.crop_canvas.winfo_width() - img_resized.width) / 2
            y = (self.crop_canvas.winfo_height() - img_resized.height) / 2
            self.crop_canvas.create_image(x, y, anchor="nw", image=self.original_img_tk)

            self.crop_rect = None
            self.crop_window.deiconify()
        except Exception as e:
            messagebox.showerror("错误", f"加载原图失败：{str(e)}")

    def start_crop(self, event):
        """开始裁切"""
        x = self.crop_canvas.canvasx(event.x)
        y = self.crop_canvas.canvasy(event.y)
        self.crop_start_x = x
        self.crop_start_y = y
        self.crop_rect = None

    def draw_crop_rect(self, event):
        """绘制裁切框"""
        if self.crop_rect:
            self.crop_canvas.delete(self.crop_rect)

        x = self.crop_canvas.canvasx(event.x)
        y = self.crop_canvas.canvasy(event.y)
        self.crop_rect = self.crop_canvas.create_rectangle(
            self.crop_start_x, self.crop_start_y, x, y,
            outline="red", width=2
        )

    def end_crop(self, event):
        """结束裁切"""
        pass

    def save_manual_crop(self):
        """保存人工裁切"""
        if not self.crop_rect or not self.original_img:
            messagebox.showwarning("提示", "请先绘制裁切框！")
            return

        x1, y1, x2, y2 = self.crop_canvas.coords(self.crop_rect)
        img_resized = self.resize_image(self.original_img, self.crop_canvas)

        canvas_w = self.crop_canvas.winfo_width()
        canvas_h = self.crop_canvas.winfo_height()

        offset_x = (canvas_w - img_resized.width) / 2
        offset_y = (canvas_h - img_resized.height) / 2

        x1 = max(0, x1 - offset_x)
        y1 = max(0, y1 - offset_y)
        x2 = min(img_resized.width, x2 - offset_x)
        y2 = min(img_resized.height, y2 - offset_y)

        scale_w = self.original_img.width / img_resized.width
        scale_h = self.original_img.height / img_resized.height

        x1 = int(x1 * scale_w)
        y1 = int(y1 * scale_h)
        x2 = int(x2 * scale_w)
        y2 = int(y2 * scale_h)

        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        if x2 - x1 < 10 or y2 - y1 < 10:
            messagebox.showwarning("提示", "裁切框过小，请重新绘制！")
            return

        try:
            cropped = self.original_img.crop((x1, y1, x2, y2))
            output_path = self.processed_files[self.current_index][1]
            cropped.save(output_path, quality=95)

            self.processed_files[self.current_index] = (self.processed_files[self.current_index][0], output_path, True)
            self.log_text.insert(tk.END, f"✅ 人工裁切保存：{os.path.basename(output_path)}\n")
            self.log_text.see(tk.END)

            self.crop_window.withdraw()
            self.show_image(self.current_index)
            messagebox.showinfo("提示", "人工裁切结果已保存并覆盖！")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{str(e)}")

    def show_help(self):
        """显示帮助"""
        help_text = """
        # DVD海报人物裁切工具 v1.5（最终无错版） 使用说明
        ## 核心功能
        1. 基于YOLOv8n模型检测海报中的完整主体人物（有头有身）
        2. 按自定义宽高比自动裁切，确保完整包含人物主体
        3. 支持人工复检+手动裁切，结果不满意可手动调整
        4. 全界面自适应屏幕，窗口拉伸/缩小后图片、日志自动适配

        ## 参数详细说明
        1. 检测置信度阈值（0.1~0.9）：值越高检测越严格，减少误检；值越低检测越灵敏，适合模糊海报
        2. 人体完整性阈值（0.3~0.9）：值越高越倾向于检测完整人物，过滤局部（仅头/仅身体）
        3. 主体拓展比例（0.0~0.5）：裁切后人物周边的背景范围，值越大背景越多，值越小越聚焦人物
        4. 裁切宽高比：自定义裁切的宽高比例，默认2:3（DVD海报常用比例）
        5. 最小检测框：过滤过小的误检框（如海报中的小图标、文字），避免误判

        ## 标准操作流程
        1. 配置参数：选择输入/输出目录，调节检测/裁切参数（建议先使用默认值）
        2. 批量处理：点击【批量处理图片】，等待日志提示处理完成
        3. 结果检查：左右分栏对比原图和裁切图，上下翻页查看所有结果
        4. 标记不合格：裁切结果不满意（人物截断/比例不对），点击【标记为不合格】
        5. 人工裁切：点击【人工裁切当前图】，鼠标绘制红框选择裁切区域，保存即可覆盖原结果

        ## 注意事项
        1. 首次运行会自动下载YOLOv8n模型（约6MB），需保证网络畅通
        2. 支持图片格式：jpg/jpeg/png/bmp/webp
        3. 人工裁切时，红框尽量完整包含人物，画布可随窗口拉伸
        4. 日志会自动滚动到底部，所有操作记录均可追溯
        5. 输出目录会自动创建，裁切结果会覆盖同名文件（人工裁切同理）

        ## 常见问题解决
        1. 检测不到人物：降低【检测置信度阈值】或【人体完整性阈值】
        2. 人物被截断：提高【主体拓展比例】，或直接使用人工裁切
        3. 误检较多：提高【检测置信度阈值】，增大【最小检测框】尺寸
        4. 图片显示不全：直接拉伸窗口，界面会自动适配，图片等比例缩放无拉伸
        """
        help_window = tk.Toplevel(self.root)
        help_window.title("使用说明")
        help_window.geometry("800x600")
        help_window.minsize(600, 400)
        help_window.resizable(True, True)

        help_main = ttk.Frame(help_window, padding="10")
        help_main.pack(fill="both", expand=True)
        help_main.rowconfigure(0, weight=1)
        help_main.columnconfigure(0, weight=1)

        help_text_widget = scrolledtext.ScrolledText(help_main, wrap="word")
        help_text_widget.pack(fill="both", expand=True)
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state="disabled")


# -------------------------- 程序入口 --------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = PosterCropApp(root)


    def on_window_resize(event):
        if event.widget == root and app.processed_files:
            app.show_image(app.current_index)


    root.bind("<Configure>", on_window_resize)
    root.mainloop()