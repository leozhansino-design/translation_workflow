"""
简单的API测试脚本
测试Gemini和GPT模型的API连接
"""
import http.client
import json

# 配置信息
API_BASE_URL = "https://yunwuapi.com"  # 替换为你的中转服务商提供的域名
API_KEY = "sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln"  # 替换为你的API Key

# 测试的模型列表
MODELS = [
    "gemini-2.5-pro",
    "gpt-5-mini",
    "gpt-4-turbo-preview"
]


def test_model(model_name):
    """测试单个模型"""
    print(f"\n{'='*60}")
    print(f"测试模型: {model_name}")
    print(f"{'='*60}")

    # 设置连接
    conn = http.client.HTTPSConnection(API_BASE_URL.replace("https://", ""))

    # 准备请求数据
    payload = json.dumps({
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": "你好，请用一句话介绍你自己。"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 100,
        "stream": False
    })

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}'
    }

    # 发送请求
    try:
        conn.request("POST", "/v1/chat/completions", payload, headers)
        response = conn.getresponse()
        data = response.read().decode('utf-8')

        # 解析并打印结果
        if response.status == 200:
            response_data = json.loads(data)
            assistant_reply = response_data['choices'][0]['message']['content']
            usage = response_data.get('usage', {})

            print(f"✅ 成功")
            print(f"模型回复: {assistant_reply}")
            print(f"Token使用: {usage.get('total_tokens', 'N/A')}")
        else:
            print(f"❌ 请求失败，状态码：{response.status}")
            print(f"错误信息：{data}")

    except Exception as e:
        print(f"❌ 发生错误：{e}")

    finally:
        conn.close()


if __name__ == '__main__':
    print("API连接测试工具")
    print("="*60)

    for model in MODELS:
        test_model(model)

    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}")
