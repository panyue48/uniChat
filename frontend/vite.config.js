import { defineConfig } from 'vite'
import uniPluginModule from '@dcloudio/vite-plugin-uni'

// 处理 default 导出
const uniPlugin = uniPluginModule.default || uniPluginModule

export default defineConfig({
  plugins: [
    typeof uniPlugin === 'function' ? uniPlugin() : uniPlugin.default()
  ]
})
