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
  // #ifdef MP-WEIXIN
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
  // #endif
  
  // #ifndef MP-WEIXIN
  uni.chooseFile({
    count: 1,
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
  // #endif
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

  // #ifdef MP-WEIXIN
  // 使用微信原生的 requestTask 监听 chunk
  let hasReceivedData = false
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
      
      // 如果没有收到任何数据，可能是错误
      if (!hasReceivedData && !messages.value[aiMsgIndex].content) {
        messages.value[aiMsgIndex].content = "[未收到响应，请检查后端服务]"
      }
      
      scrollToBottom()
    },
    fail: (err) => {
      console.error('请求失败:', err)
      messages.value[aiMsgIndex].content = messages.value[aiMsgIndex].content || "[网络错误] " + (err.errMsg || JSON.stringify(err))
      messages.value[aiMsgIndex].loading = false
      isGenerating.value = false
      scrollToBottom()
    }
  })

  // 监听流式数据块
  requestTask.onChunkReceived((response) => {
    try {
      hasReceivedData = true
      
      // ArrayBuffer 转 String
      const arrayBuffer = response.data
      if (!arrayBuffer || arrayBuffer.byteLength === 0) {
        return // 跳过空数据块
      }
      
      // 使用 TextDecoder 解码（小程序基础库 2.11.0+）
      let textChunk = ''
      try {
        const decoder = new TextDecoder('utf-8')
        textChunk = decoder.decode(arrayBuffer, { stream: true })
      } catch(e) {
        // Fallback: 使用 Uint8Array 转 String
        const uint8Array = new Uint8Array(arrayBuffer)
        textChunk = String.fromCharCode.apply(null, uint8Array)
      }

      // 追加内容
      if (textChunk) {
        messages.value[aiMsgIndex].content += textChunk
        scrollToBottom()
      }
    } catch (error) {
      console.error('处理数据块时出错:', error)
    }
  })
  
  // 设置超时（30秒）
  setTimeout(() => {
    if (isGenerating.value) {
      requestTask.abort()
      messages.value[aiMsgIndex].content = messages.value[aiMsgIndex].content || "[请求超时，请重试]"
      messages.value[aiMsgIndex].loading = false
      isGenerating.value = false
      uni.showToast({ title: '请求超时', icon: 'none' })
    }
  }, 30000)
  // #endif
  
  // #ifndef MP-WEIXIN
  // 非微信小程序环境使用 uni.request (不支持流式，需要后续优化)
  uni.request({
    url: `${API_BASE}/chat`,
    method: 'POST',
    header: {
      'content-type': 'application/x-www-form-urlencoded'
    },
    data: {
      query: userQuery,
      session_id: sessionId.value
    },
    success: (res) => {
      messages.value[aiMsgIndex].content = res.data || '[响应为空]'
      messages.value[aiMsgIndex].loading = false
      isGenerating.value = false
      scrollToBottom()
    },
    fail: (err) => {
      messages.value[aiMsgIndex].content = "[网络错误] " + JSON.stringify(err)
      messages.value[aiMsgIndex].loading = false
      isGenerating.value = false
    }
  })
  // #endif
}
</script>

<style lang="scss">
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f7f7f7;
}

.header {
  padding: 20rpx;
  background-color: #fff;
  border-bottom: 1rpx solid #eaeaea;
  
  .file-tag {
    font-size: 24rpx;
    color: #666;
  }
}

.chat-area {
  flex: 1;
  padding: 20rpx;
  box-sizing: border-box;
  overflow-y: hidden; 
}

.msg-list {
  min-height: 100%;
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
  flex-shrink: 0;
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
  font-size: 28rpx;
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
    flex-shrink: 0;
}

.send-btn {
  height: 80rpx;
  line-height: 80rpx;
  background-color: #07c160;
  color: white;
  font-size: 28rpx;
  padding: 0 30rpx;
  border-radius: 10rpx;
  flex-shrink: 0;
}

.send-btn[disabled] {
  background-color: #ccc;
  color: #999;
}
</style>

