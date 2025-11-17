"""
系统测试脚本 - 测试预处理流程
"""
import os
import sys
from core.task_manager import TaskManager
from core.preprocessor import Preprocessor

def test_preprocessing():
    """测试预处理功能"""
    print("=" * 80)
    print("测试预处理系统")
    print("=" * 80)

    # 使用测试小说
    test_novel = "test_novel_Romance.txt"

    if not os.path.exists(test_novel):
        print(f"❌ 测试文件不存在: {test_novel}")
        return

    # 创建任务
    print("\n[1] 创建任务...")
    tm = TaskManager()
    task_id = tm.create_task(
        novel_path=test_novel,
        genre="Romance",
        style_index=0
    )
    print(f"✅ 任务创建成功: {task_id}")

    # 测试预处理
    print("\n[2] 测试预处理...")
    preprocessor = Preprocessor(
        names_file="data/names_windows1.json",
        styles_file="data/styles.json",
        base_prompt_file="config/base_prompt.txt"
    )

    try:
        final_prompt, novel_content, name_mapping = preprocessor.preprocess_task(
            task_id=task_id,
            novel_path=test_novel,
            genre="Romance",
            style_index=0
        )

        print("\n" + "=" * 80)
        print("预处理结果")
        print("=" * 80)
        print(f"✅ 小说内容长度: {len(novel_content)} 字符")
        print(f"✅ 最终prompt长度: {len(final_prompt)} 字符")
        print(f"✅ 人名映射数量: {len(name_mapping)} 个")

        if name_mapping:
            print("\n人名映射:")
            for cn, en in list(name_mapping.items())[:5]:
                print(f"  {cn} → {en}")
            if len(name_mapping) > 5:
                print(f"  ... 还有 {len(name_mapping) - 5} 个")

        # 显示prompt前500字符
        print("\n" + "=" * 80)
        print("最终Prompt预览（前500字符）:")
        print("=" * 80)
        print(final_prompt[:500])
        print("...")

        print("\n" + "=" * 80)
        print("✅ 预处理测试成功！")
        print("=" * 80)

        # 检查输出文件
        output_dir = f"outputs/{task_id}"
        print(f"\n输出目录: {output_dir}")
        print("文件列表:")
        for file in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file)
            size = os.path.getsize(file_path)
            print(f"  - {file} ({size} bytes)")

    except Exception as e:
        print(f"\n❌ 预处理失败: {str(e)}")
        import traceback
        traceback.print_exc()


def test_api_connection():
    """测试API连接"""
    print("\n" + "=" * 80)
    print("测试API连接")
    print("=" * 80)

    try:
        import json
        from openai import OpenAI

        with open("config/api_config.json", 'r', encoding='utf-8') as f:
            api_config = json.load(f)

        client = OpenAI(
            api_key=api_config["api_key"],
            base_url=api_config["base_url"]
        )

        print("🔗 发送测试请求...")
        response = client.chat.completions.create(
            model=api_config["model"],
            messages=[{"role": "user", "content": "Hello! Please respond with just 'OK'."}],
            max_tokens=50
        )

        result = response.choices[0].message.content
        print(f"✅ API连接成功！")
        print(f"回复: {result}")

    except Exception as e:
        print(f"❌ API连接失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🧪 Novel Translator - 系统测试\n")

    # 测试API连接
    test_api_connection()

    # 测试预处理
    test_preprocessing()

    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
    print("\n下一步：")
    print("1. 如果测试成功，可以使用 GUI: python run_gui.py")
    print("2. 或直接运行翻译器: python translators/translator_1.py windows1")
    print("=" * 80)
