import os
import random
import subprocess
import shutil
import time
import threading
import tempfile
from pathlib import Path
from tkinter import *
from tkinter import filedialog, messagebox, ttk
import platform

try:
    from PIL import Image as PILImage
    from PIL import ImageTk
except ImportError:
    print("请安装Pillow：pip install pillow")
    exit(1)

DEFAULT_CONFIG = {
    "screenshot_count": 10,
    "recapture_count": 10,
    "min_interval_sec": 3,
    "max_random_skip_sec": 120,
    "ffmpeg": "ffmpeg",
    "video_exts": [".mp4", ".mkv", ".avi", ".mov", ".m4v", ".flv", ".wmv"],
    "poster_ratio": (2, 3),
    "disc_ratio": (1, 1),
    "landscape_ratio": (3, 2),
}

SYSTEM = platform.system()
COLORS = {
    "bg_main": "#202124", "bg_panel": "#2d2e32", "bg_card": "#38393d",
    "bg_selected": "#4a6fa5", "bg_button_primary": "#3a7bd5",
    "bg_button_success": "#28a745", "bg_button_warning": "#ffc107",
    "bg_button_default": "#44464a", "fg_text_primary": "#e8eaed",
    "fg_text_secondary": "#9aa0a6", "fg_text_highlight": "#8ab4f8",
    "fg_text_selected": "#ffffff", "fg_text_button_white": "#ffffff",
}

class JellyfinScreenshotTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Jellyfin 智能截图 · 最终完整版")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        self.temp_dir = Path(tempfile.mkdtemp())
        self.screenshots = {}
        self.processed_videos = []
        self.current_page = 0
        self.selected_video = None
        self.selected_img_key = None
        self.config = DEFAULT_CONFIG.copy()
        self.image_cache = {}

        self._init_ui()

    def _init_ui(self):
        main_paned = ttk.PanedWindow(self.root, orient=HORIZONTAL)
        main_paned.pack(fill=BOTH, expand=True, padx=5, pady=5)

        left_frame = Frame(main_paned, width=260, bg=COLORS["bg_panel"], relief=GROOVE, bd=1)
        main_paned.add(left_frame, weight=0)

        Label(left_frame, text="⚙️ 核心参数", font=("Arial",12,"bold"),
              bg=COLORS["bg_panel"], fg=COLORS["fg_text_primary"]).pack(pady=5)

        self.var_count = StringVar(value="10")
        self.var_recount = StringVar(value="10")
        self.var_interval = StringVar(value="3")
        self.var_skip = StringVar(value="120")
        self.var_ffmpeg = StringVar(value="ffmpeg")

        self._item(left_frame, "预览截图数", self.var_count)
        self._item(left_frame, "重截备选数", self.var_recount)
        self._item(left_frame, "最小间隔秒", self.var_interval)
        self._item(left_frame, "最大随机跳跃", self.var_skip)
        self._item(left_frame, "FFmpeg路径", self.var_ffmpeg)

        Button(left_frame, text="✅ 应用参数", command=self._apply_config,
               bg=COLORS["bg_button_success"], fg="white").pack(pady=5, fill=X, padx=10)
        Button(left_frame, text="📂 选择视频目录", command=self._start_process,
               bg=COLORS["bg_button_primary"], fg="white").pack(pady=5, fill=X, padx=10)
        Button(left_frame, text="🔄 重截当前（10张备选）", command=self._recapture_10,
               bg=COLORS["bg_button_warning"], fg="black").pack(pady=5, fill=X, padx=10)
        Button(left_frame, text="✅ 替换为这张备选图", command=self._replace_selected,
               bg=COLORS["bg_button_success"], fg="white").pack(pady=5, fill=X, padx=10)

        self.var_progress = StringVar(value="等待处理")
        Label(left_frame, textvariable=self.var_progress, fg=COLORS["fg_text_highlight"],
              bg=COLORS["bg_panel"]).pack(pady=10)

        right_frame = Frame(main_paned, bg=COLORS["bg_main"])
        main_paned.add(right_frame, weight=1)

        top_bar = Frame(right_frame, bg=COLORS["bg_main"])
        top_bar.pack(fill=X, padx=10, pady=5)
        self.var_page_info = StringVar(value="0/0")
        Label(top_bar, textvariable=self.var_page_info, bg=COLORS["bg_main"], fg=COLORS["fg_text_primary"]).pack(side=LEFT)
        Button(top_bar, text="上一页", command=self._prev_page).pack(side=LEFT, padx=5)
        Button(top_bar, text="下一页", command=self._next_page).pack(side=LEFT)
        self.var_selected_info = StringVar(value="未选中")
        Label(top_bar, textvariable=self.var_selected_info, bg=COLORS["bg_main"], fg=COLORS["fg_text_highlight"]).pack(side=RIGHT)

        preview_container = Frame(right_frame, bg=COLORS["bg_main"])
        preview_container.pack(fill=BOTH, expand=True, padx=10, pady=5)
        scroll_y = Scrollbar(preview_container, orient=VERTICAL)
        scroll_y.pack(side=RIGHT, fill=Y)
        self.preview_canvas = Canvas(preview_container, bg=COLORS["bg_main"], yscrollcommand=scroll_y.set)
        self.preview_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.config(command=self.preview_canvas.yview)
        self.preview_content = Frame(self.preview_canvas, bg=COLORS["bg_main"])
        self.preview_canvas.create_window((0, 0), window=self.preview_content, anchor=NW)
        self.preview_content.bind("<Configure>", lambda e: self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all")))

        save_frame = Frame(right_frame, bg=COLORS["bg_main"])
        save_frame.pack(fill=X, pady=10)
        Button(save_frame, text="💾 保存当前视频", command=self._save_current_video,
               bg=COLORS["bg_button_success"], fg="white").pack(side=LEFT, padx=10)
        Button(save_frame, text="📦 批量保存全部", command=self._save_all_videos,
               bg=COLORS["bg_button_warning"], fg="black").pack(side=LEFT)

    def _item(self, parent, txt, var):
        f = Frame(parent, bg=COLORS["bg_panel"])
        f.pack(fill=X, padx=10, pady=2)
        Label(f, text=txt, width=12, anchor=W, bg=COLORS["bg_panel"], fg=COLORS["fg_text_primary"]).pack(side=LEFT)
        Entry(f, textvariable=var, width=10).pack(side=LEFT)

    def _apply_config(self):
        try:
            self.config["screenshot_count"] = int(self.var_count.get())
            self.config["recapture_count"] = int(self.var_recount.get())
            self.config["min_interval_sec"] = int(self.var_interval.get())
            self.config["max_random_skip_sec"] = int(self.var_skip.get())
            self.config["ffmpeg"] = self.var_ffmpeg.get().strip()
            messagebox.showinfo("成功", "参数已应用")
        except:
            messagebox.showerror("错误", "参数格式不正确")

    def _get_duration(self, path):
        try:
            r = subprocess.run([self.config["ffmpeg"], "-i", str(path), "-hide_banner"], capture_output=True, text=True)
            for line in (r.stdout + r.stderr).split("\n"):
                if "Duration" in line:
                    h, m, s = line.split("Duration: ")[1].split(",")[0].split(":")
                    return int(float(h)*3600 + float(m)*60 + float(s))
        except:
            return 60

    def _rand_times(self, path, n):
        dur = self._get_duration(path)
        s, e = int(dur*0.05), int(dur*0.9)
        if s >= e:
            s, e = 10, max(dur-10, 20)
        used = set()
        res = []
        gap = self.config["min_interval_sec"]
        for _ in range(n*4):
            if len(res)>=n: break
            t = random.randint(s,e)
            if any(abs(t-x)<gap for x in used): continue
            used.add(t)
            res.append(t)
        while len(res)<n:
            t = random.randint(s,e)
            if not any(abs(t-x)<gap for x in used):
                used.add(t)
                res.append(t)
        random.shuffle(res)
        return res[:n]

    def _cap(self, vid, out, ratio=None, t=None):
        dur = self._get_duration(vid)
        if t is None or t < 0 or t >= dur:
            t = random.uniform(max(5, dur*0.05), min(dur*0.9, dur-5))
        cmd = [self.config["ffmpeg"], "-ss", str(t), "-i", str(vid), "-vframes", "1", "-q:v", "2", "-y"]
        if ratio:
            w, h = ratio
            cmd += ["-filter:v", f"crop=ih*{w}/{h}:ih"]
        cmd.append(str(out))
        for retry in range(3):
            try:
                subprocess.run(cmd, capture_output=True, check=True)
                if Path(out).exists() and Path(out).stat().st_size > 1024:
                    return True
            except:
                time.sleep(0.1)
        return False

    def _process_single_video(self, video_path):
        vp = Path(video_path)
        tmp = self.temp_dir / vp.stem
        tmp.mkdir(exist_ok=True)
        fan = tmp / "extrafanart"
        fan.mkdir(exist_ok=True)
        ss = {}

        ts = self._rand_times(video_path, self.config["screenshot_count"])
        for i, t in enumerate(ts, 1):
            p = fan / f"{vp.stem}-{i}.jpg"
            self._cap(video_path, p, t=t)
            ss[f"preview-{i}"] = p

        # ========== 强制生成 3张图：poster / landscape / disc ==========
        p_poster = tmp / "poster.jpg"
        self._cap(video_path, p_poster, self.config["poster_ratio"])
        ss["poster"] = p_poster

        p_land = tmp / "landscape.jpg"
        self._cap(video_path, p_land, self.config["landscape_ratio"])
        ss["landscape"] = p_land

        p_disc = tmp / "disc.jpg"
        self._cap(video_path, p_disc, self.config["disc_ratio"])
        ss["disc"] = p_disc

        self.screenshots[video_path] = ss
        self.processed_videos.append(video_path)

    def _start_process(self):
        d = filedialog.askdirectory()
        if not d: return
        self.screenshots.clear()
        self.processed_videos.clear()
        self.current_page = 0
        self.selected_img_key = None
        paths = []
        for f in Path(d).rglob("*"):
            if f.suffix.lower() in self.config["video_exts"]:
                paths.append(str(f))
        if not paths:
            messagebox.showinfo("提示", "未找到视频")
            return
        self.var_progress.set(f"处理中：0/{len(paths)}")
        total = len(paths)
        def run():
            for i, p in enumerate(paths, 1):
                self._process_single_video(p)
                self.root.after(0, lambda: self.var_progress.set(f"处理中：{i}/{total}"))
                time.sleep(0.02)
            self.var_progress.set("处理完成")
            self.root.after(0, self._show_current_page)
        threading.Thread(target=run, daemon=True).start()

    def _show_current_page(self):
        for w in self.preview_content.winfo_children(): w.destroy()
        self.image_cache.clear()
        if not self.processed_videos:
            Label(self.preview_content, text="暂无视频", bg=COLORS["bg_main"], fg=COLORS["fg_text_primary"]).pack()
            return
        total = len(self.processed_videos)
        self.var_page_info.set(f"{self.current_page+1}/{total}")
        self.selected_video = self.processed_videos[self.current_page]
        name = Path(self.selected_video).stem
        Label(self.preview_content, text=f"🎬 {name}", font=("Arial",14,"bold"),
              bg=COLORS["bg_main"], fg=COLORS["fg_text_primary"]).pack(pady=10)
        items = list(self.screenshots[self.selected_video].items())
        row, col, max_col = None, 0, 5
        for key, path in items:
            if not Path(path).exists(): continue
            try:
                im = PILImage.open(path)
                im.thumbnail((170,220))
                tk = ImageTk.PhotoImage(im)
                self.image_cache[key] = tk
            except:
                continue
            if col == 0:
                row = Frame(self.preview_content, bg=COLORS["bg_main"])
                row.pack(fill=X, pady=5)
            card = Frame(row, bg=COLORS["bg_card"], bd=2, relief=SOLID, padx=4, pady=4)
            card.pack(side=LEFT, padx=6)
            Label(card, image=tk, bg=COLORS["bg_card"]).pack()
            Label(card, text=self._nice_name(key), bg=COLORS["bg_card"], fg=COLORS["fg_text_primary"]).pack()
            card.bind("<Button-1>", lambda e,k=key: self._select_screenshot(k))
            col +=1
            if col >= max_col: col=0

    def _nice_name(self, k):
        if k.startswith("preview-"): return f"预览{k[8:]}"
        if k == "poster": return "海报"
        if k == "landscape": return "横向"
        if k == "disc": return "方形"
        if "_recap_" in k:
            b,i = k.split("_recap_")
            return f"{self._nice_name(b)}·备选{i}"
        return k

    def _select_screenshot(self, key):
        self.selected_img_key = key
        self.var_selected_info.set(f"已选：{self._nice_name(key)}")
        for rf in self.preview_content.winfo_children():
            for card in rf.winfo_children():
                if isinstance(card, Frame):
                    card.config(bg=COLORS["bg_card"])
                    for ch in card.winfo_children():
                        if isinstance(ch, Label):
                            ch.config(bg=COLORS["bg_card"], fg=COLORS["fg_text_primary"])
        for rf in self.preview_content.winfo_children():
            for card in rf.winfo_children():
                if isinstance(card, Frame) and key in str(card.bindtags()):
                    card.config(bg=COLORS["bg_selected"])
                    for ch in card.winfo_children():
                        if isinstance(ch, Label):
                            ch.config(bg=COLORS["bg_selected"], fg="white")

    def _recapture_10(self):
        if not self.selected_video or not self.selected_img_key:
            messagebox.showinfo("提示","先选中一张图")
            return
        base = self.selected_img_key.split("_recap_")[0]
        vid = self.selected_video
        ori = self.screenshots[vid][base]
        ratio = None
        if base == "poster": ratio = self.config["poster_ratio"]
        if base == "landscape": ratio = self.config["landscape_ratio"]
        if base == "disc": ratio = self.config["disc_ratio"]
        ts = self._rand_times(vid, self.config["recapture_count"])
        for i,t in enumerate(ts,1):
            k = f"{base}_recap_{i}"
            out = ori.parent / f"{ori.stem}_recap_{i}{ori.suffix}"
            self._cap(vid, out, ratio, t)
            self.screenshots[vid][k] = out
        self._show_current_page()

    def _replace_selected(self):
        if not self.selected_video or not self.selected_img_key:
            messagebox.showinfo("提示","未选中")
            return
        if "_recap_" not in self.selected_img_key:
            messagebox.showinfo("提示","请选备选图")
            return
        vid = self.selected_video
        base, _ = self.selected_img_key.split("_recap_")
        src = self.screenshots[vid][self.selected_img_key]
        dst = self.screenshots[vid][base]
        try:
            shutil.copy2(src, dst)
            for k in list(self.screenshots[vid].keys()):
                if "_recap_" in k:
                    del self.screenshots[vid][k]
            self.selected_img_key = base
            self._show_current_page()
            messagebox.showinfo("成功","已替换原图")
        except Exception as e:
            messagebox.showerror("失败", str(e))

    def _prev_page(self):
        if self.current_page>0:
            self.current_page -= 1
            self._show_current_page()

    def _next_page(self):
        if self.current_page < len(self.processed_videos)-1:
            self.current_page += 1
            self._show_current_page()

    # ========== 核心：保存 + 移动视频到文件夹 ==========
    def _save_video_screenshots(self, video_path):
        src = Path(video_path)
        movie_dir = src.parent / src.stem
        movie_dir.mkdir(exist_ok=True)

        # 移动视频（不存在才移动）
        dest_video = movie_dir / src.name
        if not dest_video.exists():
            try:
                shutil.move(str(src), str(dest_video))
            except:
                pass

        # 保存所有图（强制3张）
        for key, path in self.screenshots[video_path].items():
            if "_recap_" in key:
                continue
            if not Path(path).exists():
                continue
            if key.startswith("preview"):
                fan = movie_dir / "extrafanart"
                fan.mkdir(exist_ok=True)
                shutil.copy2(path, fan / Path(path).name)
            else:
                target = movie_dir / f"{key}.jpg"
                shutil.copy2(path, target)

    def _save_current_video(self):
        if not self.selected_video:
            return
        self._save_video_screenshots(self.selected_video)
        messagebox.showinfo("成功","已保存并整理完成")

    def _save_all_videos(self):
        if not self.processed_videos:
            messagebox.showinfo("提示","无视频")
            return
        for v in self.processed_videos:
            self._save_video_screenshots(v)
        messagebox.showinfo("成功","全部保存并移动完成")

if __name__ == "__main__":
    root = Tk()
    JellyfinScreenshotTool(root)
    root.mainloop()