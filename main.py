import os
import random
from typing import Tuple, List
from PIL import Image, ImageEnhance

# 兼容 Pillow 高低版本的 RESAMPLING 方法
try:
    RESAMPLING = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING = Image.ANTIALIAS


def generate_overlays_from_subdirs(patch_dir: str) -> List[dict]:
    """从 patches 目录下的每个子文件夹中各随机抽取一张图片"""
    overlays = []
    # 确保子文件夹按名称排序，保证合成顺序基本固定
    try:
        subdirs = sorted([d for d in os.listdir(patch_dir) if os.path.isdir(os.path.join(patch_dir, d))])
    except FileNotFoundError:
        print(f"[!] 错误: 贴图目录 '{patch_dir}' 不存在。")
        return []

    for subdir_name in subdirs:
        subdir_path = os.path.join(patch_dir, subdir_name)
        try:
            files = [
                f
                for f in os.listdir(subdir_path)
                if f.lower().endswith((".png", ".jpg", ".jpeg"))
            ]
            if not files:
                print(f"[!] 警告: 贴图子目录 '{subdir_path}' 为空，已跳过。")
                continue

            selected_file = random.choice(files)
            path = os.path.join(subdir_path, selected_file)
            overlays.append({"image_path": path})

        except FileNotFoundError:
            print(f"[!] 警告: 贴图子目录 '{subdir_path}' 不存在，已跳过。")
            continue

    return overlays


def paste_images(background_path: str, overlays: List[dict], output_path: str):
    """将多个贴图自适应缩放并垂直居中粘贴到背景图上"""
    bg = Image.open(background_path).convert("RGBA")
    bg_w, bg_h = bg.size

    if not overlays:
        bg.save(output_path)
        print(f"[!] 没有提供贴图，已跳过: {background_path}")
        return

    # --- 1. 设置初始参数和期望的缩放比例 ---
    initial_scale = 0.6  # [可调整] 期望贴图宽度占背景宽度的 60%
    padding = 20         # [可调整] 图片之间的垂直间距
    vertical_margin_ratio = 0.05 # [可调整] 上下留白占背景高度的比例

    target_patch_width = int(bg_w * initial_scale)

    # --- 2. 预计算总高度，以判断是否需要二次缩放 ---
    total_content_h = 0
    scaled_heights = []
    for overlay in overlays:
        # 使用 try-except 避免损坏的图片文件导致程序中断
        try:
            img = Image.open(overlay["image_path"])
            ow, oh = img.size
            if ow == 0: continue
            target_h = int(oh * (target_patch_width / ow))
            scaled_heights.append(target_h)
            total_content_h += target_h
        except Exception as e:
            print(f"[!] 错误: 无法读取贴图 {overlay['image_path']}, 已跳过。原因: {e}")
            # 添加一个0高度占位符，保持列表长度一致
            scaled_heights.append(0)


    total_padding_h = padding * (len(overlays) - 1) if len(overlays) > 1 else 0
    total_required_h = total_content_h + total_padding_h

    # --- 3. 如果总高度超出可用空间，计算修正系数并重新调整尺寸 ---
    available_h = bg_h * (1 - 2 * vertical_margin_ratio) # 上下各留5%边距
    if total_required_h > available_h:
        scale_correction = available_h / total_required_h
        target_patch_width = int(target_patch_width * scale_correction)
        # 需要用修正后的宽度重新计算所有尺寸
        scaled_heights = []
        total_content_h = 0
        for overlay in overlays:
            try:
                img = Image.open(overlay["image_path"])
                ow, oh = img.size
                if ow == 0: continue
                target_h = int(oh * (target_patch_width / ow))
                scaled_heights.append(target_h)
                total_content_h += target_h
            except Exception:
                scaled_heights.append(0) # 保持占位

        total_padding_h = padding * (len(overlays) - 1) if len(overlays) > 1 else 0
        total_required_h = total_content_h + total_padding_h

    # --- 4. 计算起始Y坐标，实现垂直居中 ---
    current_y = (bg_h - total_required_h) // 2

    # --- 5. 依次粘贴图片 ---
    x = (bg_w - target_patch_width) // 2 # 水平居中
    for i, overlay in enumerate(overlays):
        # 跳过加载失败的图片
        if scaled_heights[i] == 0:
            continue
        try:
            img = Image.open(overlay["image_path"]).convert("RGBA")
            target_h = scaled_heights[i]
            img = img.resize((target_patch_width, target_h), RESAMPLING)

            bg.paste(img, (x, current_y), img)
            current_y += target_h + padding
        except Exception as e:
            print(f"[!] 错误: 粘贴图片 {overlay['image_path']} 时失败, 已跳过。原因: {e}")


    bg.save(output_path)
    print(f"[✔] 合成图像保存到: {output_path}")


def batch_process(background_dir: str, output_dir: str, patch_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    # 首先生成一次贴图列表，确保所有背景使用相同的贴图组合
    overlays = generate_overlays_from_subdirs(patch_dir)
    if not overlays:
        print(f"[!] 在 '{patch_dir}' 中没有找到任何可用的贴图，处理中断。")
        return

    for fname in os.listdir(background_dir):
        if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        background_path = os.path.join(background_dir, fname)
        name, ext = os.path.splitext(fname)
        output_path = os.path.join(output_dir, f"{name}_merged{ext}")

        paste_images(background_path, overlays, output_path)


# ====== 示例入口 ======
if __name__ == "__main__":
    background_dir = "./backgrounds"
    output_dir = "./outputs"
    patch_dir = "./patches"

    batch_process(background_dir, output_dir, patch_dir)
