#!/usr/bin/env python3
"""测试Humor类型支持"""

import json
import os
import sys

def test_humor_in_styles():
    """测试styles.json是否包含Humor"""
    print("=" * 60)
    print("测试1: 检查data/styles.json文件")
    print("=" * 60)

    styles_path = 'data/styles.json'
    if not os.path.exists(styles_path):
        print(f"❌ 文件不存在: {styles_path}")
        return False

    with open(styles_path, 'r', encoding='utf-8') as f:
        styles = json.load(f)

    genres = list(styles.keys())
    print(f"✓ 文件存在: {styles_path}")
    print(f"✓ 类型总数: {len(genres)}")
    print(f"✓ 所有类型: {', '.join(genres)}")
    print(f"✓ Humor在文件中: {'Humor' in genres}")

    if 'Humor' not in genres:
        print("❌ Humor不在styles.json中！")
        return False

    print("\n")
    return True

def test_resource_manager():
    """测试ResourceManager是否加载Humor"""
    print("=" * 60)
    print("测试2: 检查ResourceManager加载")
    print("=" * 60)

    try:
        from resource_mgr import ResourceManager
        mgr = ResourceManager()
        genres = mgr.get_available_genres()

        print(f"✓ ResourceManager加载成功")
        print(f"✓ 加载的类型数: {len(genres)}")
        print(f"✓ 所有类型: {', '.join(genres)}")
        print(f"✓ Humor在列表中: {'Humor' in genres}")

        if 'Humor' not in genres:
            print("❌ ResourceManager没有加载Humor！")
            return False

        print("\n")
        return True
    except Exception as e:
        print(f"❌ ResourceManager加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_genre_extraction():
    """测试类型名称提取"""
    print("=" * 60)
    print("测试3: 检查类型名称提取函数")
    print("=" * 60)

    try:
        from utils import extract_genre_from_filename

        test_cases = [
            ('test_humor.txt', 'Humor'),
            ('test_Humor.txt', 'Humor'),
            ('test_HUMOR.txt', 'Humor'),
            ('MyBook_humor.txt', 'Humor'),
        ]

        all_passed = True
        for filename, expected in test_cases:
            result = extract_genre_from_filename(filename)
            if result == expected:
                print(f"✓ {filename} → {result}")
            else:
                print(f"❌ {filename} → {result} (期望: {expected})")
                all_passed = False

        print("\n")
        return all_passed
    except Exception as e:
        print(f"❌ 类型提取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_genre_validation():
    """测试类型验证"""
    print("=" * 60)
    print("测试4: 检查类型验证")
    print("=" * 60)

    try:
        from utils import validate_genre
        from resource_mgr import ResourceManager

        mgr = ResourceManager()
        available_genres = mgr.get_available_genres()

        # 测试Humor应该通过验证
        try:
            validate_genre('Humor', available_genres)
            print("✓ 'Humor' 验证通过")
        except ValueError as e:
            print(f"❌ 'Humor' 验证失败: {e}")
            return False

        # 测试无效类型应该失败
        try:
            validate_genre('InvalidGenre', available_genres)
            print("❌ 无效类型验证应该失败但通过了")
            return False
        except ValueError:
            print("✓ 无效类型正确被拒绝")

        print("\n")
        return True
    except Exception as e:
        print(f"❌ 验证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "=" * 60)
    print("Humor类型支持测试")
    print("=" * 60 + "\n")

    results = []

    # 运行所有测试
    results.append(("styles.json文件", test_humor_in_styles()))
    results.append(("ResourceManager加载", test_resource_manager()))
    results.append(("类型名称提取", test_genre_extraction()))
    results.append(("类型验证", test_genre_validation()))

    # 汇总结果
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ 通过" if passed else "❌ 失败"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✓✓✓ 所有测试通过！Humor类型支持正常")
        print("=" * 60)
        print("\n现在你可以:")
        print("1. 运行Python版本:")
        print("   python3 outline_generator.py")
        print("   - 导入 xxx_humor.txt 或 xxx_Humor.txt 都可以")
        print("\n2. 或者重新打包:")
        print("   python3 build_package.py --debug")
        print("   - 打包后的应用也会包含Humor支持")
        return 0
    else:
        print("❌❌❌ 有测试失败！请检查上述错误信息")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
