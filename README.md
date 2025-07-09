# 🖼️ 图片批量合成工具 (Image Merger)

这是一个功能强大的 Python 脚本，旨在自动化地将多张贴图（overlays）以各种方式批量合成到背景图片上。脚本配备了现代化的交互式命令行界面，并且可以通过 GitHub Actions 自动打包成独立的 `.exe` 可执行文件。

---

## ✨ 核心功能

- **🎨 批量处理**: 自动处理指定文件夹下的所有背景图片。
- **📐 统一尺寸**: 可选地将所有背景图预处理为统一的指定尺寸 (例如 `1080x1920`)。
- **🗂️ 分层贴图**: 从 `patches` 目录下的每个子文件夹中各随机抽取一张图片进行合成。
- **🤸‍♂️ 自适应缩放**: 智能计算贴图尺寸，使其既能最大化显示，又不会超出背景边界。
- **↔️ 灵活对齐**: 支持将贴图组合在背景上垂直居中或从顶部开始排列。
- **💬 交互式界面**: 无需修改代码，通过美观的命令行向导即可完成所有配置。
- **📦 自动打包**: 集成 GitHub Actions，每次提交代码到 `main` 分支后，会自动打包生成独立的 Windows `.exe` 文件。

---

## 📁 文件夹结构

在使用前，请确保按以下结构组织你的文件夹：

```
/
├── backgrounds/      # 存放你的背景图片
│   ├── bg1.jpg
│   └── bg2.png
├── patches/          # 存放你的贴图，每个子文件夹代表一个图层
│   ├── layer1/
│   │   ├── patch1_1.png
│   │   └── patch1_2.png
│   └── layer2/
│       ├── patch2_1.png
│       └── patch2_2.png
├── outputs/          # (会自动创建) 用于存放最终合成的图片
└── main.py           # 主脚本
```

---

## 🚀 如何使用

### 1. 在本地运行 (需要 Python 环境)

**a. 准备环境**

- 克隆或下载本仓库代码。
- 确保你已安装 Python 3.7+。
- 在项目根目录下打开终端，安装所有必要的库：
  ```bash
  pip install -r requirements.txt
  ```

**b. 运行脚本**

- 在终端中运行主脚本：
  ```bash
  python main.py
  ```
- 脚本会启动一个交互式向导，根据提示输入或确认你的配置即可。

### 2. 使用独立的 .exe 文件 (无需 Python)

**a. 获取 .exe 文件**

- 访问本仓库的 [**Actions**](https://github.com/YOUR_USERNAME/YOUR_REPONAME/actions) 页面 (请将 `YOUR_USERNAME/YOUR_REPONAME` 替换为你的 GitHub 用户名和仓库名)。
- 点击列表里最新的一个名为 "Build Windows Executable" 的工作流。
- 在该工作流的 "Artifacts" (产物) 部分，下载 `ImageMerger-windows-build` 文件。

**b. 运行程序**

- 解压下载的 `.zip` 文件，你会得到一个 `ImageMerger.exe` 文件。
- 在 `ImageMerger.exe` **相同的目录下**，创建 `backgrounds` 和 `patches` 文件夹，并放入你的图片。
- 双击运行 `ImageMerger.exe`，之后的操作和本地运行完全一样。

---

## 🤖 关于 GitHub Actions

本仓库已配置好 GitHub Actions 工作流 (`.github/workflows/build.yml`)。

- **触发**: 每当有新的代码被 `push` 到 `main` 分支时，该工作流会自动触发。
- **过程**: 它会在一个虚拟的 Windows 环境中，安装依赖、运行 `PyInstaller` 命令进行打包。
- **结果**: 成功后，会将生成的 `.exe` 文件上传为可供下载的 "Artifact" (产物)。 