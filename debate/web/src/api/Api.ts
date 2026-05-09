import axios from 'axios';

// 创建axios实例
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
  timeout: 10000, // 10秒超时
});

// 定义API响应类型
export interface DebaterRolesResponse {
  judge: string;
  debater: string[];
}

// SSE流式消息接口参数
export interface StreamingMessageRequest {
  from_name: string;
  to_name: string;
  text: string[];
}

// SSE流式消息响应
export interface StreamingMessageResponse {
  id?: string;
  event?: string;
  data: string;
  timestamp?: number;
}

// API调用函数
export const debateApi = {
  /**
   * 获取辩手角色列表
   * @returns 包含裁判和辩手列表的响应
   */
  async listDebaterRoles(): Promise<DebaterRolesResponse> {
    try {
      const response = await apiClient.get<DebaterRolesResponse>('/listDebaterRoles');
      return response.data;
    } catch (error) {
      console.error('获取辩手角色列表失败:', error);
      throw new Error('获取辩手角色列表失败，请检查网络连接或服务器状态');
    }
  },

  /**
   * 创建POST流式连接
   * @param request 流式消息请求参数
   * @param onMessage 消息回调函数
   * @param onError 错误回调函数
   * @returns 关闭连接的函数
   */
  createStreamingConnection(
    request: StreamingMessageRequest,
    onMessage: (data: StreamingMessageResponse) => void,
    onError: (error: Error) => void
  ): () => void {
    let isClosed = false;
    let controller: AbortController | null = null;

    const startStreaming = async () => {
      try {
        controller = new AbortController();

        const response = await fetch('http://localhost:8000/api/streaming', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
          },
          body: JSON.stringify(request),
          signal: controller.signal
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        if (!response.body) {
          throw new Error('Response body is null');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (!isClosed) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });

          // 解析SSE格式的消息
          const messages = buffer.split('\n\n');
          buffer = messages.pop() || '';

          for (const message of messages) {
            if (!message.trim()) continue;

            try {
              // 尝试解析为JSON
              const dataMatch = message.match(/^data:\s*(.+)$/ms);
              if (dataMatch) {
                const jsonData = JSON.parse(dataMatch[1]) as StreamingMessageResponse;
                onMessage(jsonData);
              } else {
                // 直接作为文本数据
                onMessage({
                  data: message,
                  timestamp: Date.now()
                });
              }
            } catch (parseError) {
              console.error('解析SSE消息失败:', parseError);
              onMessage({
                data: message,
                timestamp: Date.now()
              });
            }
          }
        }

        reader.releaseLock();
      } catch (error) {
        if (!isClosed) {
          console.error('流式连接错误:', error);
          onError(error as Error);
        }
      }
    };

    // 立即启动流式连接
    startStreaming();

    // 返回关闭函数
    return () => {
      isClosed = true;
      if (controller) {
        controller.abort();
      }
      console.log('流式连接已关闭');
    };
  },

  /**
   * 发送辩论消息并获取流式响应
   * @param request 消息请求参数
   * @param onChunk 流式数据块回调
   * @param onComplete 完成回调
   * @param onError 错误回调
   */
  async sendDebateMessage(
    request: StreamingMessageRequest,
    onChunk: (chunk: string) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): Promise<void> {
    return new Promise((resolve) => {
      const closeConnection = this.createStreamingConnection(
        request,
        (data) => {
          // 检查是否结束（根据事件类型或特定标记）
          if (data === 'end') {
            onComplete();
            closeConnection();
            resolve();
          }else if (data) {
            onChunk(data);
          }
          
        },
        (error) => {
          onError(error);
          resolve();
        }
      );
    });
  },

  /**
   * 重置对话记忆
   * @returns 响应结果
   */
  async resetMemory(): Promise<{ status: string; message: string }> {
    try {
      const response = await apiClient.get('http://localhost:8000/api/resetMemory');
      return response.data;
    } catch (error) {
      console.error('重置对话记忆失败:', error);
      throw new Error('重置对话记忆失败，请检查网络连接或服务器状态');
    }
  },

  /**
   * 保存对话记忆并下载
   * @returns Blob 文件内容
   */
  async saveMemory(): Promise<Blob> {
    try {
      const response = await apiClient.get('http://localhost:8000/api/saveMemory', {
        responseType: 'blob'
      });
      return response.data;
    } catch (error) {
      console.error('保存对话记忆失败:', error);
      throw new Error('保存对话记忆失败，请检查网络连接或服务器状态');
    }
  }
};

export default debateApi;