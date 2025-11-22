"""
通用API调用模块
使用http.client方式调用各种LLM API，兼容GPT和Gemini等模型
基于用户验证成功的代码实现
"""
import http.client
import json
import time


class UniversalAPIClient:
    """通用API客户端 - 使用http.client方式"""

    def __init__(self, api_key, base_url="https://yunwuapi.com"):
        """
        初始化API客户端

        Args:
            api_key: API密钥
            base_url: API基础URL（不包含/v1/）
        """
        self.api_key = api_key
        # 移除协议头和尾部斜杠
        self.base_url = base_url.replace("https://", "").replace("http://", "").rstrip("/")
        print(f"✅ UniversalAPIClient 初始化")
        print(f"   Base URL: {self.base_url}")

    def chat_completion(self, model, messages, temperature=0.7, max_tokens=25000, stream=False):
        """
        调用聊天完成API

        Args:
            model: 模型名称（如 gemini-3-pro-preview, gpt-5.1等）
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出

        Returns:
            dict: API响应，包含 choices、usage 等字段

        Raises:
            Exception: API调用失败时抛出异常
        """
        start_time = time.time()

        # 准备请求数据（完全按照用户成功的代码）
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        })

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        try:
            # 建立HTTPS连接（不设置timeout，完全按照成功代码）
            conn = http.client.HTTPSConnection(self.base_url)

            # 发送请求
            conn.request("POST", "/v1/chat/completions", payload, headers)

            # 获取响应
            response = conn.getresponse()
            data = response.read().decode('utf-8')

            conn.close()

            elapsed = time.time() - start_time

            # 检查响应状态
            if response.status == 200:
                response_data = json.loads(data)

                # 验证响应格式
                if 'choices' not in response_data or len(response_data['choices']) == 0:
                    raise ValueError(f"API响应格式异常: {data[:200]}")

                # 添加额外信息
                if 'elapsed_time' not in response_data:
                    response_data['elapsed_time'] = elapsed

                return response_data
            else:
                # 请求失败
                raise Exception(f"API返回状态码 {response.status}: {data[:500]}")

        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")

    def get_message_content(self, response):
        """
        从API响应中提取消息内容

        Args:
            response: chat_completion()返回的响应

        Returns:
            str: 助手回复的内容
        """
        return response['choices'][0]['message']['content']

    def get_usage(self, response):
        """
        从API响应中提取使用统计

        Args:
            response: chat_completion()返回的响应

        Returns:
            dict: 包含 prompt_tokens, completion_tokens, total_tokens
        """
        return response.get('usage', {
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'total_tokens': 0
        })


def test_api():
    """测试API调用"""
    print("=" * 70)
    print("测试UniversalAPIClient")
    print("=" * 70)

    # 使用测试API Key
    api_key = "sk-4FqZoOFgSYHP6Vfk9HGqhGyrPJjNTVwnaB6zVAbLp8UdlCln"

    # 初始化客户端
    client = UniversalAPIClient(api_key=api_key)

    # 测试Gemini模型
    print("\n🧪 测试 Gemini 模型...")
    try:
        response = client.chat_completion(
            model="gemini-3-pro-preview",
            messages=[
                {"role": "user", "content": "你好，请用一句话介绍你自己。"}
            ],
            temperature=0.7,
            max_tokens=100
        )

        content = client.get_message_content(response)
        usage = client.get_usage(response)

        print(f"✅ Gemini 测试成功")
        print(f"   回复: {content}")
        print(f"   Token使用: {usage.get('total_tokens', 'N/A')}")

    except Exception as e:
        print(f"❌ Gemini 测试失败: {e}")

    # 测试GPT模型
    print("\n🧪 测试 GPT 模型...")
    try:
        response = client.chat_completion(
            model="gpt-5.1",
            messages=[
                {"role": "user", "content": "Hello, introduce yourself in one sentence."}
            ],
            temperature=0.7,
            max_tokens=50
        )

        content = client.get_message_content(response)
        usage = client.get_usage(response)

        print(f"✅ GPT 测试成功")
        print(f"   回复: {content}")
        print(f"   Token使用: {usage.get('total_tokens', 'N/A')}")

    except Exception as e:
        print(f"❌ GPT 测试失败: {e}")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    test_api()
