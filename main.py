import os
import random
import re
from typing import Tuple, List

import questionary
from PIL import Image, ImageEnhance
from rich.console import Console
from rich.panel import Panel


# 兼容 Pillow 高低版本的 RESAMPLING 方法
try:
    RESAMPLING = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLING = Image.ANTIALIAS


def resize_backgrounds(directory: str, target_size: Tuple[int, int]):
    """统一调整目录下所有背景图的尺寸，并覆盖保存"""
    print(f"--- 开始格式化背景图片，目标尺寸: {target_size[0]}x{target_size[1]} ---")
    for fname in os.listdir(directory):
        if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
            continue

        file_path = os.path.join(directory, fname)
        try:
            with Image.open(file_path) as img:
                if img.size != target_size:
                    print(f"正在调整尺寸: {fname} ...")
                    # 使用高质量的LANCZOS算法进行缩放
                    resized_img = img.resize(target_size, RESAMPLING)
                    # 保存时可以指定质量等参数
                    resized_img.save(file_path, quality=95)
                else:
                    print(f"尺寸符合，跳过: {fname}")
        except Exception as e:
            print(f"[!] 处理 {fname} 时出错，已跳过。原因: {e}")
    print("--- 背景图片格式化完成 ---\n")


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


def paste_images(
    background_path: str,
    overlays: List[dict],
    output_path: str,
    vertical_center: bool = True,
):
    """将多个贴图自适应缩放并垂直粘贴到背景图上"""
    bg = Image.open(background_path).convert("RGBA")
    bg_w, bg_h = bg.size

    if not overlays:
        bg.save(output_path)
        print(f"[!] 没有提供贴图，已跳过: {background_path}")
        return

    # --- 1. 设置初始参数和期望的缩放比例 ---
    initial_scale = 0.9  # [可调整] 期望贴图宽度占背景宽度的 60%
    padding = 0         # [可调整] 图片之间的垂直间距
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

    # --- 4. 计算起始Y坐标 ---
    if vertical_center:
        # 实现垂直居中
        current_y = (bg_h - total_required_h) // 2
    else:
        # 从顶部开始，并保留边距
        current_y = int(bg_h * vertical_margin_ratio)

    # --- 5. 依次粘贴图片 ---
    x = (bg_w - target_patch_width) // 2  # 水平居中
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


def batch_process(
    background_dir: str,
    output_dir: str,
    patch_dir: str,
    resize_bg_to: Tuple[int, int] | None = None,
    vertical_center: bool = True,
):
    """
    批量处理流程:
    1. (可选) 统一调整背景图尺寸
    2. 从贴图子目录中随机选择图片
    3. 将贴图合成到每张背景图上
    """
    # 步骤1: 如果指定了目标尺寸，则先格式化所有背景图
    if resize_bg_to:
        resize_backgrounds(background_dir, resize_bg_to)

    os.makedirs(output_dir, exist_ok=True)

    # 步骤2: 首先生成一次贴图列表，确保所有背景使用相同的贴图组合
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

        paste_images(
            background_path, overlays, output_path, vertical_center=vertical_center
        )


def run_interactive_mode():
    """运行交互式命令行界面来获取用户配置"""
    console = Console()
    console.print(
        Panel(
            "[bold cyan]🖼️  欢迎使用图片批量合成工具  🖼️[/bold cyan]",
            title="[yellow]Image Merger[/yellow]",
            subtitle="[dim]由 Gemini & Cursor 强力驱动[/dim]",
            expand=False,
        )
    )

    # --- 交互式获取路径 ---
    background_dir = questionary.text(
        "1. 请输入背景图文件夹路径:",
        default="./backgrounds",
        validate=lambda p: os.path.isdir(p) or "路径不存在或不是一个文件夹",
    ).ask()

    patch_dir = questionary.text(
        "2. 请输入贴图文件夹路径:",
        default="./patches",
        validate=lambda p: os.path.isdir(p) or "路径不存在或不是一个文件夹",
    ).ask()

    output_dir = questionary.text("3. 请输入合成图片的输出路径:", default="./outputs").ask()

    # --- 交互式获取处理选项 ---
    target_bg_size = None
    if questionary.confirm("4. 是否要将所有背景图统一到指定尺寸?", default=True).ask():
        size_str = questionary.text(
            "   请输入目标尺寸 (格式: 宽x高):",
            default="1080x1920",
            validate=lambda s: re.match(r"^\d+x\d+$", s) is not None
            or "格式错误, 请使用 '宽x高' 格式, 例如 '1080x1920'",
        ).ask()
        w, h = map(int, size_str.split("x"))
        target_bg_size = (w, h)

    center_vertically = questionary.confirm(
        "5. 是否让贴图组合在背景上垂直居中? (选择 '否' 将从顶部开始排列)", default=True
    ).ask()

    # --- 汇总信息并最终确认 ---
    summary = (
        f"[bold]配置确认[/bold]\n"
        f"------------------\n"
        f"背景路径: [cyan]{background_dir}[/cyan]\n"
        f"贴图路径: [cyan]{patch_dir}[/cyan]\n"
        f"输出路径: [cyan]{output_dir}[/cyan]\n"
        f"调整尺寸: [cyan]{f'{target_bg_size[0]}x{target_bg_size[1]}' if target_bg_size else '否'}[/cyan]\n"
        f"垂直居中: [cyan]{'是' if center_vertically else '否'}[/cyan]\n"
    )
    console.print(Panel(summary, padding=(1, 2)))

    if not questionary.confirm("准备就绪, 是否开始处理?", default=True).ask():
        console.print("[yellow]操作已取消。[/yellow]")
        return

    # --- 开始执行 ---
    console.print("\n[green]🚀 开始批量处理, 请稍候...[/green]")
    batch_process(
        background_dir,
        output_dir,
        patch_dir,
        resize_bg_to=target_bg_size,
        vertical_center=center_vertically,
    )
    console.print("[bold green]✨ 全部处理完成！[/bold green]")


if __name__ == "__main__":
    # background_dir = "./backgrounds"
    # output_dir = "./outputs"
    # patch_dir = "./patches"
    # # 在这里指定背景图的目标尺寸, 设为 None 可跳过此步骤
    # target_bg_size = (1080, 1920)
    # # 控制贴图是否垂直居中, 设为 False 则从顶部开始排列
    # center_vertically = False
    #
    # batch_process(
    #     background_dir,
    #     output_dir,
    #     patch_dir,
    #     resize_bg_to=target_bg_size,
    #     vertical_center=center_vertically,
    # )
    run_interactive_mode()
