  <template>
  <div class="debate-chat">


    <!-- 左侧智能体列表 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2>辩论参与者</h2>
        <p>{{ activeAgents.length }} 个智能体在线</p>
      </div>
      
      <div class="agents-list">
        <div 
          v-for="agent in agents" 
          :key="agent.id"
          :class="['agent-item', { active: activeAgents.includes(agent.id) }]"
        >
          <div class="agent-avatar">
            <div class="avatar" :style="{ backgroundColor: getAvatarColor(agent.id) }">
              {{ getAvatarText(agent.id) }}
            </div>
          </div>
          <div class="agent-info">
            <div class="agent-name">{{ agent.name }}</div>
            <div class="agent-role">{{ agent.role }}</div>
            <div class="agent-status" :class="agent.status">
              {{ agent.status === 'online' ? '在线' : '离线' }}
            </div>
          </div>
        </div>
      </div>
      
      <div class="sidebar-footer">
        <div class="debate-topic" v-if="currentTopic">
        <h4>当前话题</h4>
        <p>{{ currentTopic }}</p>
      </div>
      <div class="debate-phase">
        <h4>辩论阶段</h4>
        <div class="phase-indicator">
          <div :class="['phase-item', { active: debatePhase === 'idle' }]">
            <span class="phase-dot"></span>
            <span class="phase-label">准备</span>
          </div>
          <div :class="['phase-item', { active: debatePhase === 'opening' }]">
            <span class="phase-dot"></span>
            <span class="phase-label">陈词</span>
          </div>
          <div :class="['phase-item', { active: debatePhase === 'cross-examination' }]">
            <span class="phase-dot"></span>
            <span class="phase-label">质询</span>
          </div>
          <div :class="['phase-item', { active: debatePhase === 'voting' }]">
            <span class="phase-dot"></span>
            <span class="phase-label">投票</span>
          </div>
          <div :class="['phase-item', { active: debatePhase === 'summary' }]">
            <span class="phase-dot"></span>
            <span class="phase-label">总结</span>
          </div>
        </div>
        <div class="current-speaker" v-if="currentSpeaker">
          当前发言：{{ currentSpeaker }}
        </div>
      </div>
        <div class="debate-stats">
          <div class="stat">
            <span class="stat-value">{{ messages.length }}</span>
            <span class="stat-label">消息数</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ activeAgents.length }}</span>
            <span class="stat-label">参与者</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧主内容区域 -->
    <div class="main-content">
      <!-- 标题区域 -->
      <div class="header">
        <h1>AI辩论聊天室</h1>
        <p>多智能体围绕话题进行深度辩论，裁判实时评判</p>
      </div>

      <!-- 聊天消息区域 -->
      <div class="chat-container">
        <div class="messages" ref="messagesContainer" @scroll="handleScroll">
          <div 
            v-for="(message, index) in messages" 
            :key="index" 
            :class="['message', `message-${message.sender}`]"
          >
            <div class="message-avatar">
              <div class="avatar" :style="{ backgroundColor: getAvatarColor(message.sender) }">
                {{ getAvatarText(message.sender) }}
              </div>
            </div>
            <div class="message-content">
              <div class="message-header">
                <span class="sender-name">{{ getSenderName(message.sender) }}</span>
                <span class="message-time">{{ formatTime(message.timestamp) }}</span>
              </div>
              <div class="message-text">{{ message.text }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 用户输入区域 -->
      <div class="input-area">
        <div class="input-container">
          <textarea 
            v-model="userInput" 
            :placeholder="debatePhase === 'idle' ? '请输入辩论话题...' : '辩论进行中，请观察...'"
            @keydown.enter.prevent="startDebate"
            rows="3"
            :disabled="debatePhase !== 'idle'"
          ></textarea>
        </div>
        <div class="controls">
          <button @click="startDebate" class="primary" :disabled="!userInput.trim() || debatePhase !== 'idle'">开始辩论</button>
          <button @click="nextPhase" class="primary" :disabled="debatePhase === 'idle' || debatePhase === 'summary'">下一阶段</button>
          <button @click="resetChat" class="secondary">重置聊天</button>
          <button @click="downloadMemory" class="secondary">下载对话</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { debateApi, type DebaterRolesResponse } from '../api/Api'

// 消息类型定义
interface Message {
  sender: string
  text: string
  timestamp: Date
}

// 智能体类型定义
interface Agent {
  id: string
  name: string
  role: string
  status: 'online' | 'offline'
}

// 辩论阶段定义
type DebatePhase = 'idle' | 'opening' | 'cross-examination' | 'voting' | 'summary'

// 投票结果类型
interface VoteResult {
  voter: string
  target: string
  reason: string
}

// 响应式数据
const messages = ref<Message[]>([])
const userInput = ref('ai怎么样')
const messagesContainer = ref<HTMLElement | null>(null)
const currentTopic = ref('')
const debaterRoles = ref<DebaterRolesResponse>({ judge: '', debater: [] })
const debatePhase = ref<DebatePhase>('idle')
const currentSpeaker = ref('')
const voteResults = ref<VoteResult[]>([])

// 智能体列表
const agents = computed(() => {
  const judgeAgent = {
    id: 'judge',
    name: debaterRoles.value.judge || '裁判',
    role: '裁判',
    status: 'online' as const
  }
  
  const debaterAgents = debaterRoles.value.debater.map((debater, index) => ({
    id: `agent${index + 1}`,
    name: debater || `辩手${index + 1}`,
    role: '辩手',
    status: 'online' as const
  }))
  
  return [judgeAgent, ...debaterAgents]
})

// 计算活跃的智能体
const activeAgents = computed(() => {
  return agents.value
    .filter(agent => agent.status === 'online')
    .map(agent => agent.id)
})

// 初始化一些示例消息
const initMessages = () => {
  messages.value = [
    {
      sender: 'judge',
      text: '欢迎来到AI辩论聊天室！左侧可以看到所有参与者，请输入一个话题开始辩论。',
      timestamp: new Date()
    }
  ]
}

// 获取头像文本（从智能体name属性中取第一个字符）
const getAvatarText = (sender: string) => {
  // 特殊处理用户
  if (sender === 'user') {
    return '用'
  }
  
  // 从智能体列表中查找对应的name
  const agent = agents.value.find(a => a.id === sender)
  if (agent && agent.name) {
    return agent.name[agent.name.length - 1] || sender[sender.length - 1]
  }
  
  // 默认返回sender的最后一个字符
  return sender[sender.length - 1]
}

// 获取发送者显示名称
const getSenderName = (sender: string) => {
  // 特殊处理用户
  if (sender === 'user') {
    return '用户'
  }
  
  // 从智能体列表中查找对应的name
  const agent = agents.value.find(a => a.id === sender)
  if (agent && agent.name) {
    return agent.name
  }
  
  // 默认返回sender
  return sender
}

// 头像颜色列表
const avatarColors = [
  '#2196F3', '#FF5722', '#9C27B0', '#00BCD4',
  '#FF9800', '#E91E63', '#3F51B5', '#009688',
  '#FFEB3B', '#795548', '#607D8B', '#F44336'
]

// 根据sender获取头像颜色（保持同一sender颜色一致）
const getAvatarColor = (sender: string) => {
  // 用户固定绿色
  if (sender === 'user') {
    return '#4CAF50'
  }
  
  // 计算hash值来确定颜色
  let hash = 0
  for (let i = 0; i < sender.length; i++) {
    hash = sender.charCodeAt(i) + ((hash << 5) - hash)
  }
  
  // 使用hash值选择颜色，确保同一sender始终有相同颜色
  const index = Math.abs(hash) % avatarColors.length
  return avatarColors[index]
}

// 格式化时间
const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}



// 更新或创建消息（用于实时显示流式内容）
const updateOrCreateMessage = (sender: string, text: string) => {
  // 查找该发送者的最后一条消息（正在进行的发言）
  const lastMessageIndex = messages.value.length - 1
  
  // 如果最后一条消息是该发送者的，并且内容还没有以[END]结尾，则更新它
  if (
    lastMessageIndex >= 0 &&
    messages.value[lastMessageIndex].sender === sender &&
    !messages.value[lastMessageIndex].text.includes('[END]')
  ) {
    messages.value[lastMessageIndex].text = text
  } else {
    // 创建新消息
    messages.value.push({
      sender: sender,
      text: text,
      timestamp: new Date()
    })
  }
  
  scrollToBottom()
}

// 开始辩论
const startDebate = async () => {
  if (!userInput.value.trim()) {
    messages.value.push({
      sender: 'judge',
      text: '请输入一个辩论话题后再开始辩论。',
      timestamp: new Date()
    })
    return
  }
  
  const topic = userInput.value.trim()
  currentTopic.value = topic
  userInput.value = ''
  
  // 更新辩论阶段，禁用开始辩论按钮
  debatePhase.value = 'opening'
  
  messages.value.push({
    sender: 'judge',
    text: `辩论正式开始！话题：${topic}`,
    timestamp: new Date()
  })
  
  // 开始陈词阶段
  await startOpeningPhase(topic)
}

// 陈词阶段
const startOpeningPhase = async (topic: string) => {
  debatePhase.value = 'opening'
  
  // 获取所有活跃的辩论者（不包括用户）
  const debaters = agents.value.filter(agent => 
    agent.status === 'online' && agent.id !== 'user' && agent.id !== 'judge'
  )
  
  // 遍历所有辩论者，依次调用SSE接口
  for (let i = 0; i < debaters.length; i++) {
    const debater = debaters[i]
    currentSpeaker.value = debater.name
    
    // 构建请求文本
    let requestTexts: string[] = []
    
    if (i === 0) {
      // 第一个辩论者：包含辩题
      requestTexts = [
        `辩题是${topic}`,
        `请${debater.name}发表观点`
      ]
    } else {
      // 其他辩论者：只包含发言邀请
      requestTexts = [`请${debater.name}发表观点`]
    }
    
    // 显示法官的发言邀请
    messages.value.push({
      sender: 'judge',
      text: `${requestTexts[requestTexts.length - 1]}`,
      timestamp: new Date()
    })
    scrollToBottom()
    
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 构建流式请求（裁判向辩论者发送请求）
    const request = {
      from_name: '裁判',
      to_name: debater.name,
      text: requestTexts
    }
    
    let fullStatement = ''
    messages.value.push({
      sender: debater.id,
      text: fullStatement,
      timestamp: new Date()
    })
    // 使用Promise包装，确保发言完成后才继续
    await new Promise<void>((resolve) => {
      debateApi.sendDebateMessage(
        request,
        (chunk) => {
          fullStatement += chunk
          updateOrCreateMessage(debater.id, fullStatement)
        },
        () => {
          console.log(`${debater.name} 发言完成`)
          // 发言完成，继续下一个
          currentSpeaker.value = ''
          resolve()
        },
        (error) => {
          console.error(`${debater.name} 发言错误:`, error)
        }
      ).catch((error) => {
        // 捕获发送消息时的错误
        console.error(`${debater.name} 发送消息失败:`, error)
      })
    })
    
    // 等待一段时间再继续下一个辩论者
    await new Promise(resolve => setTimeout(resolve, 1500))
  }
  
  currentSpeaker.value = ''
  
  // 陈词阶段结束，显示提示信息
  messages.value.push({
    sender: 'judge',
    text: '陈词阶段结束，请点击"下一阶段"继续质询环节。',
    timestamp: new Date()
  })
  scrollToBottom()
}

// 质询阶段
const startCrossExaminationPhase = async (topic: string) => {
  debatePhase.value = 'cross-examination'
  
  // 1. 裁判通知进入质询环节
  messages.value.push({
    sender: 'judge',
    text: '陈词阶段结束，现在进入质询阶段。请各方依次选择对手进行质询。',
    timestamp: new Date()
  })
  scrollToBottom()
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  // 2. 获取所有辩论者（不包括裁判）
  const debaters = agents.value.filter(agent => 
    agent.status === 'online' && agent.id !== 'user' && agent.id !== 'judge'
  )
  
  // 3. 遍历所有辩论者进行质询
  for (const debater of debaters) {
    currentSpeaker.value = debater.name
    
    // 4. 裁判通知辩论者选择质询对象
    messages.value.push({
      sender: 'judge',
      text: `请${debater.name}选择一位辩手进行质询。`,
      timestamp: new Date()
    })
    scrollToBottom()
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 5. 构建请求：让辩论者选择质询对象并提问
    const requestTexts = [
      `质询阶段，请选择一位其他辩手进行质询，输出格式：[被质询者名字] 你的质询问题`
    ]
    
    const questionRequest = {
      from_name: '裁判',
      to_name: debater.name,
      text: requestTexts
    }
    
    let questionResponse = ''
    
    // 6. 发送请求获取质询内容
    await new Promise<void>((resolve) => {
      debateApi.sendDebateMessage(
        questionRequest,
        (chunk) => {
          questionResponse += chunk
          updateOrCreateMessage(debater.id, questionResponse)
        },
        () => {
          console.log(`${debater.name} 质询完成`)
          resolve()
        },
        (error) => {
          console.error(`${debater.name} 质询错误:`, error)
          scrollToBottom()
          resolve()
        }
      ).catch((error) => {
        console.error(`${debater.name} 发送质询失败:`, error)
        questionResponse = `我想质询小儒，请问你对${topic}有什么看法？`
        scrollToBottom()
        resolve()
      })
    })
    
    // 7. 解析回复中的被质询者名字
    const targetName = parseTargetName(questionResponse)
    const targetAgent = debaters.find(d => d.name === targetName)
    let targetDebater = targetAgent
    
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 8. 如果找到被质询者，发送回复请求
    if (targetDebater) {
      currentSpeaker.value = targetDebater.name
      
      scrollToBottom()
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // 构建回复请求
      const responseRequest = {
        from_name: debater.name,
        to_name: targetDebater.name,
        text: [
          `请回应${debater.name}的质询：${questionResponse}`
        ]
      }
      
      let responseText = ''
      messages.value.push({
        sender: targetDebater.id,
        text: responseText,
        timestamp: new Date()
      })
      await new Promise<void>((resolve) => {
        debateApi.sendDebateMessage(
          responseRequest,
          (chunk) => {
            responseText += chunk
            updateOrCreateMessage(targetDebater.id, responseText)
          },
          () => {
            console.log(`${targetDebater.name} 回复完成`)
            resolve()
          },
          (error) => {
            console.error(`${targetDebater.name} 回复错误:`, error)
            scrollToBottom()
            resolve()
          }
        ).catch((error) => {
          console.error(`${targetDebater.name} 发送回复失败:`, error)
          scrollToBottom()
          resolve()
        })
      })
    }
    
    await new Promise(resolve => setTimeout(resolve, 1500))
  }
  
  currentSpeaker.value = ''
  
  // 质询阶段结束
  messages.value.push({
    sender: 'judge',
    text: '质询阶段结束，请点击"下一阶段"继续投票环节。',
    timestamp: new Date()
  })
  scrollToBottom()
}

// 解析回复中的被质询者名字
const parseTargetName = (text: string): string => {
  // 尝试从文本中提取名字
  // 模式1: [名字] 问题
  const bracketMatch = text.match(/[【\[]([^】\]]+)[】\]]/)
  if (bracketMatch) {
    return bracketMatch[1].trim()
  }
  
  // 模式2: @名字 问题
  const atMatch = text.match(/@([\u4e00-\u9fa5]+)/)
  if (atMatch) {
    return atMatch[1].trim()
  }
  
  // 模式3: 质询名字，问题
  const questionMatch = text.match(/质询\s*([\u4e00-\u9fa5]+)/)
  if (questionMatch) {
    return questionMatch[1].trim()
  }
  
  // 模式4: 问名字
  const askMatch = text.match(/问\s*([\u4e00-\u9fa5]+)/)
  if (askMatch) {
    return askMatch[1].trim()
  }
  
  return ''
}

// 解析投票结果
const parseVoteResult = (voter: string, response: string): VoteResult | null => {
  // 尝试解析投票响应
  // 格式：[被投票者名字] 投票理由
  const match = response.match(/【(.*?)】|\[(.*?)\]|(\S+)\s+(.+)/)
  if (match) {
    const target = match[1] || match[2] || match[3]
    const reason = match[4] || ''
    if (target) {
      return {
        voter,
        target: target.trim(),
        reason: reason.trim()
      }
    }
  }
  return null
}

// 投票阶段
const startVotingPhase = async (topic: string) => {
  debatePhase.value = 'voting'
  voteResults.value = [] // 清空之前的投票结果
  
  // 1. 裁判通知进入投票环节
  messages.value.push({
    sender: 'judge',
    text: '质询阶段结束，现在进入投票阶段。请各位辩手投票给你认为表现最佳的辩手（不能投给自己）。',
    timestamp: new Date()
  })
  scrollToBottom()
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  // 2. 获取所有辩论者（不包括裁判）
  const debaters = agents.value.filter(agent => 
    agent.status === 'online' && agent.id !== 'user' && agent.id !== 'judge'
  )
  
  // 3. 遍历所有辩论者进行投票
  for (const debater of debaters) {
    currentSpeaker.value = debater.name
    
    // 4. 裁判通知辩论者进行投票
    messages.value.push({
      sender: 'judge',
      text: `请${debater.name}进行投票（不能投给自己）。`,
      timestamp: new Date()
    })
    scrollToBottom()
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 5. 构建投票请求
    // 获取可投票的辩手列表（排除自己）
    const otherDebaters = debaters.filter(d => d.id !== debater.id)
    const otherNames = otherDebaters.map(d => d.name).join('、')
    
    const voteRequest = {
      from_name: '裁判',
      to_name: debater.name,
      text: [
        `投票阶段，你是${debater.name}，请从以下辩手中选择一位投票：${otherNames}，不能投给自己。输出格式：【被投票者名字】你的投票理由`
      ]
    }
    
    let voteResponse = ''
    
    // 6. 发送SSE请求获取投票结果
    await new Promise<void>((resolve) => {
      debateApi.sendDebateMessage(
        voteRequest,
        (chunk) => {
          voteResponse += chunk
          updateOrCreateMessage(debater.id, voteResponse)
        },
        () => {
          console.log(`${debater.name} 投票完成`)
          // 解析并存储投票结果
          const result = parseVoteResult(debater.name, voteResponse)
          if (result) {
            voteResults.value.push(result)
          }
          resolve()
        },
        (error) => {
          console.error(`${debater.name} 投票错误:`, error)
          scrollToBottom()
          resolve()
        }
      ).catch((error) => {
        console.error(`${debater.name} 发送投票失败:`, error)
        scrollToBottom()
        resolve()
      })
    })
    
    await new Promise(resolve => setTimeout(resolve, 1500))
  }
  
  currentSpeaker.value = ''
  
  // 投票阶段结束
  messages.value.push({
    sender: 'judge',
    text: '投票阶段结束，请点击"下一阶段"进入总结环节。',
    timestamp: new Date()
  })
  scrollToBottom()
}

// 统计投票结果
const countVotes = (): { winner: string; voteCount: { [key: string]: number }; details: string } => {
  const voteCount: { [key: string]: number } = {}
  
  voteResults.value.forEach(vote => {
    const target = vote.target
    voteCount[target] = (voteCount[target] || 0) + 1
  })
  
  // 找出得票最多的获胜者
  let winner = ''
  let maxVotes = 0
  for (const [name, count] of Object.entries(voteCount)) {
    if (count > maxVotes) {
      maxVotes = count
      winner = name
    }
  }
  
  // 生成详细的投票结果文本
  let details = '投票详情：\n'
  voteResults.value.forEach(vote => {
    details += `${vote.voter} 投票给 ${vote.target}（理由：${vote.reason || '无'}）\n`
  })
  
  return { winner, voteCount, details }
}

// 总结阶段
const startSummaryPhase = async (topic: string) => {
  debatePhase.value = 'summary'
  
  // 1. 宣布投票结果
  const { winner, voteCount, details } = countVotes()
  
  messages.value.push({
    sender: 'judge',
    text: '投票阶段结束，现在进入总结阶段。',
    timestamp: new Date()
  })
  scrollToBottom()
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // 2. 宣布投票结果
  messages.value.push({
    sender: 'judge',
    text: '=== 投票结果 ===',
    timestamp: new Date()
  })
  scrollToBottom()
  await new Promise(resolve => setTimeout(resolve, 500))
  
  // 显示每位辩手的得票数
  for (const [name, count] of Object.entries(voteCount)) {
    messages.value.push({
      sender: 'judge',
      text: `${name}：${count} 票`,
      timestamp: new Date()
    })
    scrollToBottom()
    await new Promise(resolve => setTimeout(resolve, 500))
  }
  
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  // 3. 宣布获胜者
  messages.value.push({
    sender: 'judge',
    text: `🎉 经过投票，本次辩论的获胜者是：${winner}！`,
    timestamp: new Date()
  })
  scrollToBottom()
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  // 4. 获胜者发表终结观点
  if (winner) {
    currentSpeaker.value = winner
    messages.value.push({
      sender: 'judge',
      text: `请${winner}发表终结观点。`,
      timestamp: new Date()
    })
    scrollToBottom()
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 获取获胜者的agent信息
    const winnerAgent = agents.value.find(a => a.name === winner)
    if (winnerAgent) {
      const finalStatementRequest = {
        to_name: winner,
        from_name: debaterRoles.value.judge || '裁判',
        text: [
          topic,
          '总结阶段',
          `你在本次辩论中获胜，请发表终结观点，总结你的核心论点并回应对手的质疑。`
        ]
      }
      
      let finalStatement = ''
      
      try {
        await debateApi.sendDebateMessage(
          finalStatementRequest,
          (chunk) => {
            finalStatement += chunk
            updateOrCreateMessage(winnerAgent.id, finalStatement)
          },
          () => {
            console.log(`${winner} 终结观点完成`)
          },
          (error) => {
            console.error(`${winner} 终结观点错误:`, error)
          }
        )
      } catch (error) {
        console.error(`${winner} 发送终结观点失败:`, error)
      }
      
      await new Promise(resolve => setTimeout(resolve, 1500))
    }
  }
  
  // 5. 裁判总结
  currentSpeaker.value = 'judge'
  messages.value.push({
    sender: 'judge',
    text: '=== 裁判总结 ===',
    timestamp: new Date()
  })
  scrollToBottom()
  await new Promise(resolve => setTimeout(resolve, 500))
  
  const summaryRequest = {
    to_name: '裁判',
    from_name: debaterRoles.value.judge || '裁判',
    text: [topic, '总结阶段', `投票结果：${JSON.stringify(voteCount)}，获胜者：${winner}。请对本次辩论进行全面总结，评价各方表现。`]
  }
  
  let summaryText = ''
  
  try {
    await debateApi.sendDebateMessage(
      summaryRequest,
      (chunk) => {
        summaryText += chunk
        updateOrCreateMessage('judge', summaryText)
      },
      () => {
        console.log('裁判总结完成')
      },
      (error) => {
        console.error('裁判总结错误:', error)
        messages.value.push({
          sender: 'judge',
          text: `本次辩论到此结束，感谢各方的精彩表现。`,
          timestamp: new Date()
        })
        scrollToBottom()
      }
    )
  } catch (error) {
    await new Promise(resolve => setTimeout(resolve, 2000))
    messages.value.push({
      sender: 'judge',
      text: `本次辩论到此结束，感谢各方的精彩表现。`,
      timestamp: new Date()
    })
    scrollToBottom()
  }
  
  currentSpeaker.value = ''
}

// 下一阶段
const nextPhase = async () => {
  const topic = currentTopic.value
  if (!topic) return
  
  switch (debatePhase.value) {
    case 'opening':
      await startCrossExaminationPhase(topic)
      break
    case 'cross-examination':
      await startVotingPhase(topic)
      break
    case 'voting':
      await startSummaryPhase(topic)
      break
    default:
      break
  }
}

// 重置聊天
const resetChat = async () => {
  try {
    await debateApi.resetMemory()
    messages.value = []
    userInput.value = ''
    currentTopic.value = ''
    debatePhase.value = 'idle'
    currentSpeaker.value = ''
    voteResults.value = []
    initMessages()
    messages.value.push({
      sender: 'judge',
      text: '对话记忆已重置，可以开始新的辩论。',
      timestamp: new Date()
    })
    scrollToBottom()
  } catch (error) {
    console.error('重置聊天失败:', error)
    // 即使API调用失败，也清空本地状态
    messages.value = []
    userInput.value = ''
    currentTopic.value = ''
    debatePhase.value = 'idle'
    currentSpeaker.value = ''
    voteResults.value = []
    initMessages()
  }
}

// 下载对话内容
const downloadMemory = async () => {
  try {
    const blob = await debateApi.saveMemory()
    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    // 获取文件名（从响应头或使用默认名）
    const dateStr = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
    a.download = `debate_memory_${dateStr}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载对话失败:', error)
    alert('下载对话失败，请稍后重试')
  }
}

// 响应式变量：用户是否正在查看历史消息（手动滚动后）
const isScrolledUp = ref(false)

// 滚动到最新消息（仅在用户没有手动滚动时执行）
const scrollToBottom = () => {
  // 如果用户手动滚动到了历史消息，不自动滚动
  if (isScrolledUp.value) {
    return
  }
  
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 处理滚动事件
const handleScroll = () => {
  if (!messagesContainer.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  const distanceToBottom = scrollHeight - scrollTop - clientHeight
  
  // 如果距离底部超过50px，认为用户正在查看历史消息
  isScrolledUp.value = distanceToBottom > 50
}

// 获取角色列表
const fetchRoles = async () => {
  try {
    const roles = await debateApi.listDebaterRoles()
    debaterRoles.value = roles
  } catch (error) {
    console.error('获取角色失败:', error)
  }
}

// 组件挂载时初始化
onMounted(() => {
  initMessages()
  // 自动获取角色列表
  fetchRoles()
})
</script>

<style scoped>
.debate-chat {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90vw;
  max-width: 1200px;
  height: 85vh;
  max-height: 800px;
  display: flex;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15), 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  z-index: 1000;
}

/* 左侧边栏样式 */
.sidebar {
  width: 280px;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e1e5e9;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.sidebar-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 1.3rem;
}

.sidebar-header p {
  margin: 0;
  opacity: 0.9;
  font-size: 0.9rem;
}

.agents-list {
  flex: 1;
  padding: 1rem 0;
  overflow-y: auto;
}

.agent-item {
  display: flex;
  align-items: center;
  padding: 1rem 1.5rem;
  border-left: 4px solid transparent;
  transition: all 0.3s ease;
  cursor: pointer;
}

.agent-item:hover {
  background: #f8f9fa;
}

.agent-item.active {
  border-left-color: #667eea;
  background: #f0f4ff;
}

.agent-avatar {
  margin-right: 1rem;
}

.agent-info {
  flex: 1;
}

.agent-name {
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 0.25rem;
}

.agent-role {
  font-size: 0.85rem;
  color: #718096;
  margin-bottom: 0.25rem;
}

.agent-status {
  font-size: 0.75rem;
  padding: 0.1rem 0.5rem;
  border-radius: 1rem;
  display: inline-block;
}

.agent-status.online {
  background: #c6f6d5;
  color: #276749;
}

.agent-status.offline {
  background: #fed7d7;
  color: #c53030;
}

.sidebar-footer {
  padding: 1.5rem;
  border-top: 1px solid #e1e5e9;
  background: #f8f9fa;
}

.debate-topic {
  margin-bottom: 1rem;
}

.debate-topic h4 {
  margin: 0 0 0.5rem 0;
  color: #4a5568;
  font-size: 0.9rem;
}

.debate-topic p {
  margin: 0;
  font-size: 0.85rem;
  color: #718096;
  line-height: 1.4;
}

.debate-stats {
  display: flex;
  justify-content: space-around;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: bold;
  color: #667eea;
}

.stat-label {
  font-size: 0.75rem;
  color: #718096;
}

.debate-phase {
  margin-top: 1rem;
}

.debate-phase h4 {
  margin: 0 0 0.5rem 0;
  color: #4a5568;
  font-size: 0.9rem;
}

.phase-indicator {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.phase-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  opacity: 0.5;
  transition: all 0.3s ease;
}

.phase-item.active {
  opacity: 1;
}

.phase-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
  margin-bottom: 0.25rem;
  transition: all 0.3s ease;
}

.phase-item.active .phase-dot {
  background: #667eea;
  transform: scale(1.2);
}

.phase-label {
  font-size: 0.7rem;
  color: #718096;
  text-align: center;
}

.phase-item.active .phase-label {
  color: #667eea;
  font-weight: 500;
}

.current-speaker {
  font-size: 0.8rem;
  color: #667eea;
  font-weight: 500;
  text-align: center;
  padding: 0.25rem;
  background: #f0f4ff;
  border-radius: 4px;
  margin-top: 0.5rem;
}

/* 右侧主内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

.header {
  background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
  padding: 1.5rem 2rem;
  text-align: center;
  border-bottom: 1px solid #e2e8f0;
}

.header h1 {
  margin: 0;
  color: #2d3748;
  font-size: 1.8rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.header p {
  margin: 0.5rem 0 0 0;
  color: #718096;
  font-size: 1rem;
}

.chat-container {
  flex: 1;
  overflow: hidden;
  padding: 1.5rem;
  background: #fafbfc;
}

.messages {
  height: 100%;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-right: 0.5rem;
}

.message {
  display: flex;
  gap: 0.75rem;
  max-width: 80%;
  animation: fadeIn 0.3s ease-in;
}

.message-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-agent1, .message-agent2, .message-agent3, .message-judge {
  align-self: flex-start;
}

.message-avatar {
  flex-shrink: 0;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: white;
  font-size: 0.9rem;
}

.avatar-user { background: #4CAF50; }

.message-content {
  background: white;
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  min-width: 200px;
}

.message-user .message-content {
  background: #E3F2FD;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.sender-name {
  font-weight: bold;
  font-size: 0.9rem;
}

.message-agent1 .sender-name { color: #2196F3; }
.message-agent2 .sender-name { color: #FF5722; }
.message-agent3 .sender-name { color: #9C27B0; }
.message-judge .sender-name { color: #FFC107; }

.message-time {
  font-size: 0.8rem;
  color: #999;
}

.message-text {
  line-height: 1.4;
  word-wrap: break-word;
}

.input-area {
  background: #f8fafc;
  padding: 1.5rem 2rem;
  border-top: 1px solid #e2e8f0;
}

.input-container {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  align-items: flex-end;
}

.input-container textarea {
  flex: 1;
  padding: 0.875rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  resize: vertical;
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.5;
  background: white;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.input-container textarea::placeholder {
  color: #94a3b8;
  font-size: 0.9rem;
}

.input-container textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.15);
  transform: translateY(-1px);
}

.input-container textarea:hover {
  border-color: #cbd5e1;
}

.input-container button {
  padding: 0.875rem 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25);
  min-width: 80px;
}

.input-container button:disabled {
  background: #cbd5e1;
  box-shadow: none;
  cursor: not-allowed;
  transform: none;
}

.input-container button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.35);
}

.controls {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
}

.controls button {
  padding: 0.7rem 1.4rem;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.controls .primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.controls .primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
}

.controls .secondary {
  background: white;
  color: #475569;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.controls .secondary:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 滚动条样式 */
.messages::-webkit-scrollbar {
  width: 6px;
}

.messages::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.messages::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.messages::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.agents-list::-webkit-scrollbar {
  width: 4px;
}

.agents-list::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.agents-list::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 2px;
}

.agents-list::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 角色管理弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.3s ease;
}

.modal-content {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: hidden;
  animation: slideUp 0.3s ease;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.3rem;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.modal-body {
  padding: 1.5rem;
  max-height: 60vh;
  overflow-y: auto;
}

.role-section {
  margin-bottom: 1.5rem;
}

.role-section h4 {
  margin: 0 0 1rem 0;
  color: #2d3748;
  font-size: 1.1rem;
  border-bottom: 2px solid #667eea;
  padding-bottom: 0.5rem;
}

.role-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.role-name {
  font-weight: 600;
  color: #2d3748;
}

.role-badge {
  background: #667eea;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
}

.refresh-btn {
  padding: 0.6rem 1.2rem;
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.refresh-btn:disabled {
  background: #cbd5e1;
  cursor: not-allowed;
  opacity: 0.7;
}

.refresh-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(72, 187, 120, 0.3);
}

.close-modal-btn {
  padding: 0.6rem 1.2rem;
  background: #e2e8f0;
  color: #4a5568;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.close-modal-btn:hover {
  background: #cbd5e1;
  transform: translateY(-1px);
}

.role-manager-btn {
  margin-top: 0.5rem;
  padding: 0.4rem 0.8rem;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.3s ease;
}

.role-manager-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 拟态框背景遮罩 */
body::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  z-index: 999;
}
</style>