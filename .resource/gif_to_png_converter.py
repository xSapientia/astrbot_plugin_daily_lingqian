#!/usr/bin/env python3
"""
GIF转PNG转换脚本
支持单个文件转换和批量转换
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image

def convert_gif_to_png(gif_path, output_dir=None, extract_frames=False):
    """
    将GIF文件转换为PNG
    
    Args:
        gif_path (str): GIF文件路径
        output_dir (str): 输出目录，如果为None则使用GIF文件所在目录
        extract_frames (bool): 是否提取所有帧，False则只转换第一帧
    
    Returns:
        list: 成功转换的PNG文件路径列表
    """
    try:
        gif_path = Path(gif_path)
        if not gif_path.exists():
            print(f"❌ 文件不存在: {gif_path}")
            return []
        
        if gif_path.suffix.lower() != '.gif':
            print(f"❌ 文件不是GIF格式: {gif_path}")
            return []
        
        # 确定输出目录
        if output_dir is None:
            output_dir = gif_path.parent
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        
        # 打开GIF文件
        with Image.open(gif_path) as gif_img:
            converted_files = []
            
            if extract_frames:
                # 提取所有帧
                frame_count = 0
                try:
                    while True:
                        # 转换为RGBA模式以保持透明度
                        frame = gif_img.convert('RGBA')
                        
                        # 生成输出文件名
                        output_filename = f"{gif_path.stem}_frame_{frame_count:03d}.png"
                        output_path = output_dir / output_filename
                        
                        # 保存PNG文件
                        frame.save(output_path, 'PNG')
                        converted_files.append(str(output_path))
                        print(f"✅ 已保存帧 {frame_count}: {output_path}")
                        
                        frame_count += 1
                        gif_img.seek(frame_count)
                        
                except EOFError:
                    # 所有帧都已处理完毕
                    pass
                
                print(f"🎯 总共提取了 {frame_count} 帧")
                
            else:
                # 只转换第一帧
                frame = gif_img.convert('RGBA')
                output_filename = f"{gif_path.stem}.png"
                output_path = output_dir / output_filename
                
                frame.save(output_path, 'PNG')
                converted_files.append(str(output_path))
                print(f"✅ 已转换: {gif_path} -> {output_path}")
            
            return converted_files
            
    except Exception as e:
        print(f"❌ 转换失败 {gif_path}: {e}")
        return []

def batch_convert_gif_to_png(input_dir, output_dir=None, extract_frames=False):
    """
    批量转换目录中的所有GIF文件
    
    Args:
        input_dir (str): 输入目录路径
        output_dir (str): 输出目录路径
        extract_frames (bool): 是否提取所有帧
    
    Returns:
        dict: 转换结果统计
    """
    input_dir = Path(input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"❌ 输入目录不存在或不是目录: {input_dir}")
        return {'success': 0, 'failed': 0, 'files': []}
    
    # 查找所有GIF文件
    gif_files = list(input_dir.glob('*.gif')) + list(input_dir.glob('*.GIF'))
    
    if not gif_files:
        print(f"📭 在目录 {input_dir} 中没有找到GIF文件")
        return {'success': 0, 'failed': 0, 'files': []}
    
    print(f"🔍 找到 {len(gif_files)} 个GIF文件")
    
    # 设置输出目录
    if output_dir is None:
        output_dir = input_dir / 'converted_png'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 批量转换
    success_count = 0
    failed_count = 0
    all_converted_files = []
    
    for gif_file in gif_files:
        print(f"\n🔄 正在处理: {gif_file.name}")
        converted_files = convert_gif_to_png(gif_file, output_dir, extract_frames)
        
        if converted_files:
            success_count += 1
            all_converted_files.extend(converted_files)
        else:
            failed_count += 1
    
    return {
        'success': success_count,
        'failed': failed_count,
        'files': all_converted_files
    }

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='GIF转PNG转换工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 转换单个GIF文件
  python gif_to_png_converter.py image.gif
  
  # 转换单个GIF并提取所有帧
  python gif_to_png_converter.py image.gif --extract-frames
  
  # 批量转换目录中的所有GIF文件
  python gif_to_png_converter.py --batch input_folder
  
  # 批量转换并指定输出目录
  python gif_to_png_converter.py --batch input_folder --output output_folder
  
  # 批量转换并提取所有帧
  python gif_to_png_converter.py --batch input_folder --extract-frames
        '''
    )
    
    parser.add_argument('input', nargs='?', help='输入GIF文件路径或目录路径')
    parser.add_argument('--batch', metavar='DIR', help='批量转换模式，指定输入目录')
    parser.add_argument('--output', '-o', metavar='DIR', help='输出目录路径')
    parser.add_argument('--extract-frames', '-f', action='store_true', 
                       help='提取GIF的所有帧，而不是只转换第一帧')
    
    args = parser.parse_args()
    
    # 检查PIL库是否可用
    try:
        from PIL import Image
    except ImportError:
        print("❌ 错误: 缺少PIL库，请安装Pillow:")
        print("pip install Pillow")
        sys.exit(1)
    
    # 处理命令行参数
    if args.batch:
        # 批量转换模式
        print("🚀 开始批量转换...")
        result = batch_convert_gif_to_png(args.batch, args.output, args.extract_frames)
        
        print(f"\n📊 转换完成!")
        print(f"✅ 成功: {result['success']} 个文件")
        print(f"❌ 失败: {result['failed']} 个文件")
        print(f"📁 总共生成: {len(result['files'])} 个PNG文件")
        
        if result['files']:
            print(f"\n📋 生成的文件:")
            for file_path in result['files'][:10]:  # 只显示前10个
                print(f"  {file_path}")
            if len(result['files']) > 10:
                print(f"  ... 还有 {len(result['files']) - 10} 个文件")
        
    elif args.input:
        # 单文件转换模式
        print("🚀 开始单文件转换...")
        converted_files = convert_gif_to_png(args.input, args.output, args.extract_frames)
        
        if converted_files:
            print(f"\n🎉 转换成功! 生成了 {len(converted_files)} 个PNG文件")
            for file_path in converted_files:
                print(f"  {file_path}")
        else:
            print("\n❌ 转换失败")
            sys.exit(1)
    
    else:
        # 没有提供输入参数
        parser.print_help()
        print("\n❌ 错误: 请提供输入文件或使用 --batch 指定目录")
        sys.exit(1)

if __name__ == '__main__':
    main()
