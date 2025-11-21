#!/usr/bin/env python3
"""
测试Horror类型识别 - 验证修复是否有效
"""
import sys
from resource_mgr import ResourceManager
from utils import extract_genre_from_filename, validate_genre

def test_horror():
    print("=" * 70)
    print("  Horror类型识别测试")
    print("=" * 70)
    
    # 测试文件名
    test_files = [
        '34骨肉汤_Horror.txt',
        '测试_horror.txt',
        '测试_HORROR.txt',
    ]
    
    print("\n1. 测试文件名解析:")
    print("-" * 70)
    for filename in test_files:
        try:
            genre = extract_genre_from_filename(filename)
            print(f"✓ {filename:30} -> {genre}")
        except Exception as e:
            print(f"✗ {filename:30} -> 错误: {e}")
            return False
    
    print("\n2. 测试资源加载:")
    print("-" * 70)
    try:
        rm = ResourceManager()
        genres = rm.get_available_genres()
        print(f"✓ 成功加载 {len(genres)} 个类型")
        
        if 'Horror' not in genres:
            print(f"✗ Horror类型不在列表中！")
            print(f"   可用类型: {', '.join(genres)}")
            return False
        
        print(f"✓ Horror类型存在")
        
        # 检查Horror的详细信息
        if 'Horror' in rm.styles:
            authors = rm.styles['Horror'].get('authors', [])
            styles_count = len(rm.styles['Horror'].get('styles', []))
            print(f"✓ Horror作者: {', '.join(authors)}")
            print(f"✓ Horror风格数: {styles_count}")
        
    except Exception as e:
        print(f"✗ 资源加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n3. 测试类型验证:")
    print("-" * 70)
    try:
        validate_genre('Horror', genres)
        print(f"✓ validate_genre('Horror') 通过")
    except Exception as e:
        print(f"✗ validate_genre('Horror') 失败: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("  ✅ 所有测试通过！Horror类型识别正常")
    print("=" * 70)
    return True

if __name__ == '__main__':
    success = test_horror()
    sys.exit(0 if success else 1)
