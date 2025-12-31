<template>
  <view class="container">
    <!-- 顶部状态栏 (可选) -->
    <view class="header" v-if="fileName">
      <text class="file-tag">当前文件: {{ fileName }}</text>
    </view>

    <!-- 聊天滚动区域 -->
    <scroll-view 
      class="chat-area" 
      scroll-y 
      :scroll-top="scrollTop" 
      :scroll-with-animation="true"
    >
      <view class="msg-list">
        <view v-for="(msg, index) in messages" :key="index" :class="['msg-item', msg.role]">
          <view class="avatar">{{ msg.role === 'user' ? '我' : 'AI' }}</view>
          <view class="content">
            <text user-select>{{ msg.content }}</text>
            <view v-if="msg.loading" class="cursor-blink">|</view>
          </view>
        </view>
      </view>
    </scroll-view>

    <!-- 底部输入区 -->
    <view class="footer safe-area">
      <view class="tool-btn" @click="handleUpload">
        <text class="icon">+</text>
      </view>
      <input 
        class="input-box" 
        v-model="inputVal" 
        :disabled="isGenerating"
        placeholder="上传PDF后提问..." 
        confirm-type="send"
        @confirm="sendMessage"
      />
      <button 
        class="send-btn" 
        :disabled="!inputVal || isGenerating" 
        @click="sendMessage"
      >发送</button>
    </view>
  </view>
</template>

<script setup>
import { ref, nextTick } from 'vue'

// --- 状态管理 ---
const messages = ref([
  { role: 'ai', content: '你好！请先点击左下角 "+" 号上传一个 PDF 文档，然后我们可以开始对话。' }
])
const inputVal = ref('')
const fileName = ref('')
const isGenerating = ref(false)
const scrollTop = ref(0)
// 生成唯一 Session ID
const sessionId = ref('sess_' + Math.random().toString(36).substr(2, 9))

// 你的本机 IP (真机调试需要换成局域网IP，如 192.168.1.5)
const API_BASE = 'http://127.0.0.1:8000'

// --- 核心逻辑：滚动到底部 ---
const scrollToBottom = () => {
  nextTick(() => {
    scrollTop.value += 10000 // 强制滚到底
  })
}

// --- 核心逻辑 1：上传 PDF ---
const handleUpload = () => {
  wx.chooseMessageFile({
    count: 1,
    type: 'file',
    extension: ['pdf'],
    success(res) {
      const tempFile = res.tempFiles[0]
      fileName.value = tempFile.name
      
      uni.showLoading({ title: '解析文档中...' })
      
      uni.uploadFile({
        url: `${API_BASE}/upload`,
        filePath: tempFile.path,
        name: 'file',
        formData: {
          'session_id': sessionId.value
        },
        success: (uploadRes) => {
          uni.hideLoading()
          const data = JSON.parse(uploadRes.data)
          if (data.status === 'success') {
            messages.value.push({ role: 'system', content: `文档《${tempFile.name}》解析成功，共 ${data.count} 个片段。请提问！` })
            scrollToBottom()
          }
        },
        fail: (err) => {
          uni.hideLoading()
          uni.showToast({ title: '上传失败', icon: 'none' })
          console.error(err)
        }
      })
    }
  })
}

// --- 核心逻辑 2：流式问答 ---
const sendMessage = () => {
  if (!inputVal.value.trim() || isGenerating.value) return
  
  const userQuery = inputVal.value
  messages.value.push({ role: 'user', content: userQuery })
  inputVal.value = ''
  
  // 预先占位 AI 的回复
  const aiMsgIndex = messages.value.push({ role: 'ai', content: '', loading: true }) - 1
  isGenerating.value = true
  scrollToBottom()

  // 使用微信原生的 requestTask 监听 chunk
  const requestTask = wx.request({
    url: `${API_BASE}/chat`,
    method: 'POST',
    responseType: 'text', // 必须设为 text
    enableChunked: true,  // 开启分块传输关键参数
    header: {
      'content-type': 'application/x-www-form-urlencoded'
    },
    data: {
      query: userQuery,
      session_id: sessionId.value
    },
    success: (res) => {
      // 请求完成
      messages.value[aiMsgIndex].loading = false
      isGenerating.value = false
    },
    fail: (err) => {
      messages.value[aiMsgIndex].content = "[网络错误] " + JSON.stringify(err)
      isGenerating.value = false
    }
  })

  // 监听流式数据块
  requestTask.onChunkReceived((response) => {
    // ArrayBuffer 转 String
    const arrayBuffer = response.data
    const uint8Array = new Uint8Array(arrayBuffer)
    // 微信小程序兼容处理
    let textChunk = String.fromCharCode.apply(null, uint8Array) 
    
    // 如果包含中文，简单的 String.fromCharCode 可能会乱码
    // 更稳健的方式是使用 TextDecoder (小程序基础库 2.11.0+)
    try {
        const decoder = new TextDecoder('utf-8');
        textChunk = decoder.decode(arrayBuffer, { stream: true });
    } catch(e) {
        // Fallback for older libraries
        textChunk = decodeURIComponent(escape(textChunk)); 
    }

    // 追加内容
    messages.value[aiMsgIndex].content += textChunk
    scrollToBottom()
  })
}
</script>

<style lang="scss">
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f7f7f7;
}

.chat-area {
  flex: 1;
  padding: 20rpx;
  box-sizing: border-box;
  overflow-y: hidden; 
}

.msg-item {
  display: flex;
  margin-bottom: 30rpx;
  
  &.user {
    flex-direction: row-reverse;
    .content {
      background-color: #95ec69;
      color: #000;
    }
    .avatar {
        background-color: #ddd;
    }
  }
  
  &.ai {
    flex-direction: row;
    .content {
      background-color: #fff;
      color: #333;
    }
    .avatar {
        background-color: #4080ff;
        color: white;
    }
  }

  &.system {
      justify-content: center;
      .content {
          background: none;
          color: #999;
          font-size: 24rpx;
          padding: 0;
      }
      .avatar { display: none; }
  }
}

.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 10rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  margin: 0 20rpx;
}

.content {
  max-width: 65%;
  padding: 20rpx;
  border-radius: 10rpx;
  font-size: 30rpx;
  line-height: 1.5;
  word-break: break-all;
  position: relative;
}

.cursor-blink {
  display: inline-block;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.footer {
  background-color: #f7f7f7;
  padding: 20rpx;
  display: flex;
  align-items: center;
  border-top: 1rpx solid #eaeaea;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
}

.input-box {
  flex: 1;
  background-color: #fff;
  height: 80rpx;
  border-radius: 10rpx;
  padding: 0 20rpx;
  margin: 0 20rpx;
}

.tool-btn {
    width: 60rpx;
    height: 60rpx;
    border: 1px solid #999;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 40rpx;
    color: #666;
}

.send-btn {
  height: 80rpx;
  line-height: 80rpx;
  background-color: #07c160;
  color: white;
  font-size: 28rpx;
  padding: 0 30rpx;
}
</style>