# GIF转PNG转换工具

一个简单易用的Python脚本，用于将GIF文件转换为PNG格式。支持单文件转换和批量转换，可以选择只转换第一帧或提取所有帧。

## 功能特点

- ✅ 单个GIF文件转换
- ✅ 批量转换目录中的所有GIF文件
- ✅ 支持提取GIF的所有帧
- ✅ 保持透明度（RGBA模式）
- ✅ 自动创建输出目录
- ✅ 详细的进度显示和错误提示
- ✅ 友好的命令行界面

## 安装依赖

在使用脚本之前，需要安装Pillow库：

```bash
pip install Pillow
```

## 使用方法

### 1. 转换单个GIF文件

```bash
# 转换单个文件（只转换第一帧）
python gif_to_png_converter.py image.gif

# 转换单个文件并提取所有帧
python gif_to_png_converter.py image.gif --extract-frames

# 指定输出目录
python gif_to_png_converter.py image.gif --output /path/to/output
```

### 2. 批量转换

```bash
# 批量转换目录中的所有GIF文件
python gif_to_png_converter.py --batch /path/to/gif/folder

# 批量转换并指定输出目录
python gif_to_png_converter.py --batch /path/to/gif/folder --output /path/to/output

# 批量转换并提取所有帧
python gif_to_png_converter.py --batch /path/to/gif/folder --extract-frames
```

### 3. 查看帮助

```bash
python gif_to_png_converter.py --help
```

## 参数说明

| 参数 | 简写 | 说明 |
|------|------|------|
| `input` | - | 输入GIF文件路径 |
| `--batch DIR` | - | 批量转换模式，指定输入目录 |
| `--output DIR` | `-o` | 输出目录路径 |
| `--extract-frames` | `-f` | 提取GIF的所有帧，而不是只转换第一帧 |

## 输出说明

### 单帧模式（默认）
- 输入：`animation.gif`
- 输出：`animation.png`

### 多帧模式（--extract-frames）
- 输入：`animation.gif`
- 输出：
  - `animation_frame_000.png`
  - `animation_frame_001.png`
  - `animation_frame_002.png`
  - ...

### 批量转换
- 默认输出到 `输入目录/converted_png/` 文件夹
- 可以使用 `--output` 参数指定其他目录

## 使用示例

### 示例1：转换单个GIF的第一帧
```bash
python gif_to_png_converter.py my_animation.gif
```
输出：`my_animation.png`

### 示例2：提取GIF的所有帧
```bash
python gif_to_png_converter.py my_animation.gif --extract-frames
```
输出：
- `my_animation_frame_000.png`
- `my_animation_frame_001.png`
- `my_animation_frame_002.png`
- ...

### 示例3：批量转换文件夹中的所有GIF
```bash
python gif_to_png_converter.py --batch ./gif_folder --output ./png_folder
```

## 错误处理

脚本会自动处理以下情况：
- 文件不存在
- 文件格式不正确
- 输出目录创建失败
- PIL库未安装

所有错误都会显示友好的错误信息和建议解决方案。

## 技术细节

- 使用PIL（Pillow）库进行图像处理
- 转换为RGBA模式以保持透明度
- 支持大小写不敏感的文件扩展名（.gif, .GIF）
- 自动处理路径和目录创建

## 许可证

这个脚本是开源的，您可以自由使用、修改和分发。

## 常见问题

### Q: 为什么需要安装Pillow？
A: Pillow是Python的图像处理库，提供了GIF和PNG格式的读写支持。

### Q: 转换后的PNG文件很大怎么办？
A: PNG是无损格式，文件会比较大。如果需要压缩，可以考虑使用其他工具进一步优化。

### Q: 支持哪些Python版本？
A: 脚本使用了pathlib和argparse，建议使用Python 3.6+。

### Q: 可以转换动画GIF吗？
A: 可以，使用 `--extract-frames` 参数可以将动画GIF的每一帧都保存为独立的PNG文件。
