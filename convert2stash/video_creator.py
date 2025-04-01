import os
import re

from moviepy import ImageSequenceClip, concatenate_videoclips


def create_slideshow(image_folder, output_file, duration_per_image=2, fps=24):
    """
    创建图片轮播视频
    参数：
    image_folder: 图片文件夹路径
    output_file: 输出视频文件名（建议.mp4结尾）
    duration_per_image: 单张图片显示时间（秒）
    fps: 视频帧率（推荐24/30）
    """

    def extract_number(filename):
        match = re.search(r'(\d+)(\.\w+)?$', filename)
        return int(match.group(1)) if match else float('inf')  # 如果没有匹配，返回无穷大

    # 获取并排序图片文件
    image_files = sorted([
        os.path.join(image_folder, img)
        for img in os.listdir(image_folder)
        if img.lower().endswith(('.png', '.jpg', '.jpeg'))
    ], key=lambda x: extract_number(os.path.basename(x)))  # 使用提取序号的函数进行降序排列

    if not image_files:
        raise ValueError("未找到支持的图片文件（.png/.jpg/.jpeg）")

    # 创建并拼接视频片段
    clips = [ImageSequenceClip([img], fps=1) for img in image_files]
    for clip in clips:
        clip.duration = duration_per_image
    video = concatenate_videoclips(clips, method="compose")

    # 导出视频文件
    video.write_videofile(
        output_file,
        fps=fps,
        codec='libx264',  # H.264 兼容性
        preset='medium',  # 平衡速度与质量
        ffmpeg_params=['-crf', '23']  # 视频质量参数（18-28，越小质量越高）
    )


if __name__ == "__main__":
    # 使用示例
    create_slideshow(
        image_folder='images',  # 替换为你的图片文件夹路径
        output_file='output.mp4',
        duration_per_image=2,  # 每张显示3秒
        fps=1  # 30帧/秒
    )
