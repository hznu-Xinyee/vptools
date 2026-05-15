<template>
  <div class="min-h-screen bg-white w-screen h-screen overflow-hidden relative">

    <!-- Floating User Info Card (Bottom Left) -->
    <div class="fixed bottom-4 left-4 z-50">
      <div v-if="!authStore.isAuthenticated" class="bg-white rounded-xl border border-gray-200 shadow-lg p-4 min-w-[200px]">
        <button @click="showLoginModal = true" class="w-full py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition">
          登录
        </button>
      </div>
      <div v-else class="bg-white rounded-xl border border-gray-200 shadow-lg p-4 min-w-[200px]">
        <div class="mb-3">
          <p class="text-xs text-gray-500 mb-1">账号</p>
          <p class="text-sm font-medium text-gray-900 truncate">{{ authStore.user?.username || '用户' }}</p>
        </div>
        <div class="mb-3">
          <p class="text-xs text-gray-500 mb-1">积分</p>
          <p class="text-sm font-medium text-gray-900">{{ userPoints || 0 }}</p>
        </div>
        <button @click="handleLogout" class="w-full py-2 bg-gray-100 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-200 transition">
          退出登录
        </button>
      </div>
    </div>

    <!-- Floating Continue Button (Bottom Center) - Only show during auto translation processing steps 1 or 2 -->
    <div v-if="autoIsProcessing && autoProgress.value && (autoProgress.value.step === 1 || autoProgress.value.step === 2)" class="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50">
      <button @click="clearAutoTranslationState" class="px-6 py-3 bg-indigo-600 text-white rounded-full shadow-lg hover:bg-indigo-700 transition flex items-center space-x-2">
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        <span class="text-sm font-medium">继续翻译其他视频</span>
      </button>
    </div>

    <!-- Main Content full-viewport -->
    <main class="w-screen h-screen">
      <!-- Subtitle Erase Feature (Four-column) -->
      <div v-if="currentFeature === 'subtitle-erase'" class="flex min-h-screen">
        <!-- Far Left Wider Nav -->
        <aside class="hidden lg:flex w-44 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-1.5">
          <div class="text-xs text-gray-500 px-1 mb-1">导航</div>
          <button @click="navigateToFeature('auto-video-translate')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">视频翻译（自动版）</button>
          <button @click="navigateToFeature('subtitle-erase')" class="w-full text-left px-3 py-2 rounded-md text-sm bg-indigo-100 text-indigo-700">字幕擦除</button>
          <button @click="navigateToFeature('subtitle-extract')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">字幕提取</button>
          <button @click="navigateToFeature('subtitle-embed')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">视频翻译（手动）</button>
          <button @click="navigateToFeature('image-translate')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">图片翻译</button>
        </aside>

        <!-- Left Process Config Column -->
        <aside class="hidden lg:flex w-72 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-3">
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">已选择的处理方式</h3>
            </div>
            <div class="p-4 space-y-3">
              <div class="space-y-2">
                <div class="flex items-center">
                  <span class="w-4 h-4 inline-flex items-center justify-center rounded-full mr-2 text-[10px] bg-indigo-600 text-white">1</span>
                  <div class="text-xs text-gray-800">字幕擦除</div>
                </div>
              </div>
              <button @click="uploadVideo" :disabled="fileList.length === 0 || isUploading" class="w-full py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
                {{ isUploading ? '处理中...' : '提交 (消耗5积分/视频)' }}
              </button>
            </div>
          </div>
        </aside>

        <!-- Center Workspace -->
        <section class="flex-1 flex items-center justify-center bg-white">
          <div class="w-full h-full flex items-center justify-center p-6">
            <video v-if="currentVideoUrl" :src="currentVideoUrl" controls autoplay class="max-w-[80%] max-h-[80vh] rounded-lg shadow"></video>
            <div v-else class="text-center text-gray-400 select-none">
              <p class="text-sm">在右侧上传视频后，结果将在此处显示</p>
            </div>
          </div>
        </section>

        <!-- Right Sidebar: Upload + History -->
        <aside class="w-full lg:w-80 border-l border-gray-200 bg-gray-50 p-3 space-y-3">
          <!-- Upload Card -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">待擦除字幕视频</h3>
            </div>
            <div class="p-4">
              <div class="relative">
                <el-upload
                  ref="uploadRef"
                  :auto-upload="false"
                  :on-change="handleFileSelect"
                  :on-remove="handleFileRemove"
                  :file-list="fileList"
                  multiple
                  accept="video/*"
                  :disabled="isUploading"
                  drag
                  class="w-full"
                >
                  <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                  <div class="el-upload__text">将视频拖拽到此处，或<em>点击上传</em></div>
                  <template #tip>
                    <div class="el-upload__tip">支持 mp4, avi, mov 等（可多选）</div>
                  </template>
                </el-upload>
                
                <!-- Loading Overlay -->
                <div v-if="isUploading" class="absolute inset-0 bg-white/80 flex flex-col items-center justify-center rounded-lg z-10">
                  <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-2"></div>
                  <p class="text-sm text-gray-600">处理中... {{ uploadProgress }}%</p>
                </div>
              </div>
            </div>
          </div>

          <!-- History Card -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">擦除记录</h3>
              <button @click="refreshHistory" class="p-1.5 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-md transition" title="刷新">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              </button>
            </div>
            <div class="p-3">
              <div v-if="taskHistory.length === 0" class="text-center py-6 text-gray-400 text-xs">暂无历史记录</div>
              <div v-else class="space-y-2.5 max-h-[calc(100vh-400px)] overflow-y-auto">
                <div v-for="task in taskHistory" :key="task.id" @click="selectHistoryTask(task)" class="bg-white rounded-lg p-2.5 border border-gray-200 cursor-pointer hover:border-indigo-400 transition" :class="{ 'border-indigo-400 bg-indigo-50/30': selectedHistoryTask?.id === task.id }">
                  <div class="flex justify-between items-start">
                    <div class="flex-1 min-w-0">
                      <p v-if="editingTaskId !== task.id" class="text-gray-900 text-xs font-medium truncate">{{ task.original_filename }}</p>
                      <input v-else v-model="editingTaskName" @click.stop @blur="saveTaskName" @keyup.enter="saveTaskName" @keyup.esc="cancelEditTaskName" ref="editInput" class="text-gray-900 text-xs font-medium w-full border border-indigo-400 rounded px-1 py-0.5 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                      <p class="text-gray-500 text-[11px] mt-1">{{ formatDate(task.created_at) }}</p>
                    </div>
                    <div class="flex flex-col items-end gap-1">
                      <button @click.stop="startEditTaskName(task)" class="px-2 py-0.5 text-[10px] text-gray-400 hover:text-indigo-600 hover:bg-gray-100 rounded transition" title="编辑名称">
                        编辑
                      </button>
                      <span class="px-2 py-0.5 rounded-full text-[11px] font-medium" :class="getStatusClass(task.status)">{{ getStatusText(task.status) }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="totalPages > 1" class="flex justify-between items-center mt-3 pt-2 border-t border-gray-100">
                <button @click="changePage(currentPage - 1)" :disabled="currentPage === 1" class="px-2.5 py-1 text-[11px] border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">上一页</button>
                <div class="flex items-center space-x-1 text-[11px] text-gray-600"><span>第</span><span class="font-medium">{{ currentPage }}</span><span>页 / 共</span><span class="font-medium">{{ totalPages }}</span><span>页</span></div>
                <button @click="changePage(currentPage + 1)" :disabled="currentPage === totalPages" class="px-2.5 py-1 text-[11px] border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">下一页</button>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <!-- Subtitle Extract Feature (Four-column) -->
      <div v-else-if="currentFeature === 'subtitle-extract'" class="flex min-h-screen">
        <!-- Far Left Wider Nav -->
        <aside class="hidden lg:flex w-44 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-1.5">
          <div class="text-xs text-gray-500 px-1 mb-1">导航</div>
          <button @click="navigateToFeature('auto-video-translate')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">视频翻译（自动版）</button>
          <button @click="navigateToFeature('subtitle-erase')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">字幕擦除</button>
          <button @click="navigateToFeature('subtitle-extract')" class="w-full text-left px-3 py-2 rounded-md text-sm bg-indigo-100 text-indigo-700">字幕提取</button>
          <button @click="navigateToFeature('subtitle-embed')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">视频翻译（手动）</button>
          <button @click="navigateToFeature('image-translate')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">图片翻译</button>
        </aside>

        <!-- Left Process Config Column -->
        <aside class="hidden lg:flex w-72 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-3">
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">已选择的处理方式</h3>
            </div>
            <div class="p-4 space-y-3">
              <div class="space-y-2">
                <div class="flex items-center">
                  <span class="w-4 h-4 inline-flex items-center justify-center rounded-full mr-2 text-[10px] bg-indigo-600 text-white">1</span>
                  <div class="text-xs text-gray-800">字幕提取</div>
                </div>
              </div>
              <button @click="uploadExtractFile" :disabled="!extractFile || extractIsUploading" class="w-full py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
                {{ extractIsUploading ? '处理中...' : '提交' }}
              </button>
            </div>
          </div>
        </aside>

        <!-- Center Workspace -->
        <section class="flex-1 flex items-center justify-center bg-white">
          <div class="w-full h-full flex items-center justify-center p-6">
            <video v-if="extractFile && extractFileObjectUrl && extractFile.type.startsWith('video/')" :src="extractFileObjectUrl" controls class="max-w-[80%] max-h-[80vh] rounded-lg shadow"></video>
            <audio v-else-if="extractFile && extractFileObjectUrl && extractFile.type.startsWith('audio/')" :src="extractFileObjectUrl" controls class="max-w-[80%] rounded-lg shadow"></audio>
            <div v-else class="text-center text-gray-400 select-none">
              <div @click="() => !extractIsUploading && document.getElementById('extractFileInput').click()" class="mx-auto mb-4 w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center cursor-pointer hover:bg-gray-200 transition">
                <svg class="w-10 h-10 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M4 6h8m-8 4h8m-8 4h5"/></svg>
              </div>
              <p class="text-sm">将视频或音频拖拽到右侧"上传文件"卡片，或点击上传</p>
            </div>
          </div>
        </section>

        <!-- Right Sidebar: Upload + Select from Erasure + Extract Records -->
        <aside class="w-full lg:w-80 border-l border-gray-200 bg-gray-50 p-3 space-y-3">
          <!-- Upload Card -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">待提取字幕文件</h3>
              <span class="text-[11px] px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700">ata音频版</span>
            </div>
            <div class="p-4">
              <div @click="() => !extractIsUploading && document.getElementById('extractFileInput').click()" class="border-2 border-dashed rounded-lg p-6 text-center transition-colors duration-200 relative" :class="extractIsUploading ? 'border-gray-300 bg-gray-50 cursor-not-allowed' : 'border-gray-300 hover:border-indigo-400 hover:bg-indigo-50/30 cursor-pointer'">
                <input type="file" id="extractFileInput" @change="handleExtractFileSelect" accept="video/*,audio/*" class="hidden" :disabled="extractIsUploading" />
                
                <!-- Loading Overlay -->
                <div v-if="extractIsUploading" class="absolute inset-0 bg-white/80 flex flex-col items-center justify-center rounded-lg z-10">
                  <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-2"></div>
                  <p class="text-sm text-gray-600">处理中...</p>
                </div>
                
                <template v-if="!extractFile">
                  <p class="text-gray-700 text-sm font-medium">点击上传视频或音频</p>
                  <p class="text-gray-400 text-xs mt-1">支持 mp4, avi, mov, mp3 等</p>
                </template>
                <div v-else class="flex flex-col items-center">
                  <img v-if="extractFileThumbnail" :src="extractFileThumbnail" class="max-w-full h-auto max-h-36 object-contain rounded-lg mb-3" alt="Video thumbnail" />
                  <p class="text-gray-900 text-xs font-medium">{{ extractFile.name }}</p>
                  <p class="text-gray-500 text-[11px] mt-1">{{ formatFileSize(extractFile.size) }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Select from Erasure History Card -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">从字幕擦除历史中选择</h3>
              <button @click="refreshExtractErasureHistory" class="p-1.5 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-md transition" :class="{ 'animate-spin': extractIsRefreshing }" title="刷新">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              </button>
            </div>
            <div class="p-3">
              <div v-if="extractErasureHistory.length === 0" class="text-center py-6 text-gray-400 text-xs">暂无已完成的历史记录</div>
              <div v-else class="space-y-2.5 max-h-72 overflow-y-auto">
                <div v-for="task in extractErasureHistory" :key="task.id" @click="extractSelectedErasureTask = task" class="bg-white rounded-lg p-2.5 border border-gray-200 cursor-pointer hover:border-indigo-400 transition" :class="{ 'border-indigo-400 bg-indigo-50/30': extractSelectedErasureTask?.id === task.id }">
                  <p class="text-gray-900 text-xs font-medium truncate">{{ task.original_filename }}</p>
                  <p class="text-gray-500 text-[11px] mt-1">{{ formatDate(task.created_at) }}</p>
                </div>
              </div>
              <div v-if="extractErasureTotalPages > 1" class="flex justify-between items-center mt-3 pt-2 border-t border-gray-100">
                <button @click="changeExtractErasurePage(extractErasureCurrentPage - 1)" :disabled="extractErasureCurrentPage === 1" class="px-2.5 py-1 text-[11px] border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">上一页</button>
                <div class="flex items-center space-x-1 text-[11px] text-gray-600"><span>第</span><span class="font-medium">{{ extractErasureCurrentPage }}</span><span>页 / 共</span><span class="font-medium">{{ extractErasureTotalPages }}</span><span>页</span></div>
                <button @click="changeExtractErasurePage(extractErasureCurrentPage + 1)" :disabled="extractErasureCurrentPage === extractErasureTotalPages" class="px-2.5 py-1 text-[11px] border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">下一页</button>
              </div>
              <button @click="submitExtractFromHistory" :disabled="!extractSelectedErasureTask || extractIsSubmitting" class="w-full mt-3 py-2 bg-neutral-900 text-white rounded-md text-sm font-medium hover:bg-neutral-800 transition disabled:opacity-50">{{ extractIsSubmitting ? '提交中...' : '开始提取' }}</button>
            </div>
          </div>

          <!-- Extract Records Card -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">提取记录</h3>
              <button @click="refreshExtractHistory" class="p-1.5 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-md transition" title="刷新">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              </button>
            </div>
            <div class="p-3">
              <div v-if="extractTaskHistory.length === 0" class="text-center py-6 text-gray-400 text-xs">暂无提取记录</div>
              <div v-else class="space-y-2.5 max-h-[calc(100vh-400px)] overflow-y-auto">
                <div v-for="task in extractTaskHistory" :key="task.id" @click="viewSubtitleResult(task)" class="bg-white rounded-lg p-2.5 border border-gray-200 cursor-pointer hover:border-indigo-400 transition">
                  <div class="flex justify-between items-start">
                    <div class="flex-1 min-w-0">
                      <p class="text-gray-900 text-xs font-medium truncate">{{ task.original_filename }}</p>
                      <p class="text-gray-500 text-[11px] mt-1">{{ formatDate(task.created_at) }}</p>
                    </div>
                    <span class="px-2 py-0.5 rounded-full text-[11px] font-medium" :class="getStatusClass(task.status)">{{ getStatusText(task.status) }}</span>
                  </div>
                </div>
              </div>
              <div v-if="extractTotalPages > 1" class="flex justify-between items-center mt-3 pt-2 border-t border-gray-100">
                <button @click="changeExtractPage(extractCurrentPage - 1)" :disabled="extractCurrentPage === 1" class="px-2.5 py-1 text-[11px] border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">上一页</button>
                <div class="flex items-center space-x-1 text-[11px] text-gray-600"><span>第</span><span class="font-medium">{{ extractCurrentPage }}</span><span>页 / 共</span><span class="font-medium">{{ extractTotalPages }}</span><span>页</span></div>
                <button @click="changeExtractPage(extractCurrentPage + 1)" :disabled="extractCurrentPage === extractTotalPages" class="px-2.5 py-1 text-[11px] border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">下一页</button>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <!-- Video Translation Feature (Four-column) -->
      <div v-else-if="currentFeature === 'subtitle-embed'" class="flex min-h-screen">
        <!-- Far Left Wider Nav -->
        <aside class="hidden lg:flex w-44 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-1.5">
          <div class="text-xs text-gray-500 px-1 mb-1">导航</div>
          <button @click="navigateToFeature('auto-video-translate')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">视频翻译（自动版）</button>
          <button @click="navigateToFeature('subtitle-erase')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">字幕擦除</button>
          <button @click="navigateToFeature('subtitle-extract')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">字幕提取</button>
          <button @click="navigateToFeature('subtitle-embed')" class="w-full text-left px-3 py-2 rounded-md text-sm bg-indigo-100 text-indigo-700">视频翻译（手动）</button>
          <button @click="navigateToFeature('image-translate')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">图片翻译</button>
        </aside>

        <!-- Left Process Config Column -->
        <aside class="hidden lg:flex w-72 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-3">
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">已选择的处理方式</h3>
            </div>
            <div class="p-4 space-y-3">
              <div class="space-y-2">
                <div class="flex items-center">
                  <span class="w-4 h-4 inline-flex items-center justify-center rounded-full mr-2 text-[10px]" :class="translationProgress.step >= 1 ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-600'">1</span>
                  <div class="text-xs text-gray-800">字幕嵌入</div>
                </div>
              </div>

              <div class="pt-1">
                <label class="block text-[11px] text-gray-500 mb-1">目标语言</label>
                <select v-model="translationTargetLanguage" class="w-full px-2.5 py-2 border border-gray-300 rounded-md bg-white text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600">
                  <option v-for="language in LANGUAGE_OPTIONS" :key="language.code" :value="language.code">{{ language.name }}</option>
                </select>
              </div>

              <div>
                <label class="block text-[11px] text-gray-500 mb-1">字体大小</label>
                <input type="number" v-model="translationSubtitleParams.font_size" class="w-full px-2 py-1 border border-gray-300 rounded-md text-xs" min="20" max="80" />
              </div>

              <div>
                <label class="block text-[11px] text-gray-500 mb-1">字体颜色</label>
                <input type="color" v-model="translationSubtitleParams.font_color" class="w-full h-8 border border-gray-300 rounded-md" />
              </div>

              <div>
                <label class="block text-[11px] text-gray-500 mb-1">描边宽度</label>
                <input type="number" v-model="translationSubtitleParams.outline" class="w-full px-2 py-1 border border-gray-300 rounded-md text-xs" min="0" max="10" />
              </div>

              <div>
                <label class="block text-[11px] text-gray-500 mb-1">描边颜色</label>
                <input type="color" v-model="translationSubtitleParams.outline_colour" class="w-full h-8 border border-gray-300 rounded-md" />
              </div>

              <div>
                <label class="block text-[11px] text-gray-500 mb-1">对齐方式</label>
                <select v-model="translationSubtitleParams.alignment" class="w-full px-2 py-1 border border-gray-300 rounded-md text-xs">
                  <option value="BottomCenter">底部居中</option>
                  <option value="BottomLeft">底部左侧</option>
                  <option value="BottomRight">底部右侧</option>
                  <option value="TopCenter">顶部居中</option>
                  <option value="TopLeft">顶部左侧</option>
                  <option value="TopRight">顶部右侧</option>
                  <option value="Center">居中</option>
                </select>
              </div>

              <button @click="submitVideoTranslation" :disabled="translationIsSubmitting || !translationVideoFile || (translationSubtitleMode === 'upload' ? !translationSubtitleJson : !translationSelectedExtractTask)" class="w-full py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
                {{ translationIsSubmitting ? '处理中...' : '提交 (消耗5积分)' }}
              </button>
            </div>
          </div>
        </aside>

        <!-- Center Workspace -->
        <section class="flex-1 flex items-center justify-center bg-white">
          <div class="w-full h-full flex items-center justify-center p-6">
            <video v-if="currentVideoUrl" :src="currentVideoUrl" controls autoplay class="max-w-[80%] max-h-[80vh] rounded-lg shadow"></video>
            <video v-else-if="translationVideoFile && translationVideoObjectUrl" :src="translationVideoObjectUrl" controls class="max-w-[80%] max-h-[80vh] rounded-lg shadow"></video>
            <div v-else class="text-center text-gray-400 select-none">
              <div @click="() => !translationIsSubmitting && translationVideoInputRef.click()" class="mx-auto mb-4 w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center cursor-pointer hover:bg-gray-200 transition">
                <svg class="w-10 h-10 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M4 6h8m-8 4h8m-8 4h5"/></svg>
              </div>
              <p class="text-sm">将视频拖拽到右侧"上传视频"卡片，或点击上传</p>
            </div>
          </div>
        </section>

        <!-- Right Sidebar: Upload + Subtitle Source + History -->
        <aside class="w-full lg:w-80 border-l border-gray-200 bg-gray-50 p-3 space-y-3">
          <!-- Upload Video Card -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">待翻译视频</h3>
            </div>
            <div class="p-4">
              <div @click="() => !translationIsSubmitting && translationVideoInputRef?.click()" class="border-2 border-dashed rounded-lg p-6 text-center transition-colors duration-200 relative" :class="translationIsSubmitting ? 'border-gray-300 bg-gray-50 cursor-not-allowed' : 'border-gray-300 hover:border-indigo-400 hover:bg-indigo-50/30 cursor-pointer'">
                <input type="file" ref="translationVideoInputRef" @change="handleTranslationVideoSelect" accept="video/*" class="hidden" :disabled="translationIsSubmitting" />
                
                <!-- Loading Overlay -->
                <div v-if="translationIsSubmitting" class="absolute inset-0 bg-white/80 flex flex-col items-center justify-center rounded-lg z-10">
                  <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-2"></div>
                  <p class="text-sm text-gray-600">处理中...</p>
                </div>
                
                <template v-if="!translationVideoFile">
                  <p class="text-gray-700 text-sm font-medium">点击上传视频</p>
                  <p class="text-gray-400 text-xs mt-1">支持 mp4, avi, mov 等</p>
                </template>
                <div v-else class="flex flex-col items-center">
                  <img v-if="translationVideoThumbnail" :src="translationVideoThumbnail" class="max-w-full h-auto max-h-36 object-contain rounded-lg mb-3" alt="Video thumbnail" />
                  <p class="text-gray-900 text-xs font-medium">{{ translationVideoFile.name }}</p>
                  <p class="text-gray-500 text-[11px] mt-1">{{ formatFileSize(translationVideoFile.size) }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Subtitle Source Card -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100"><h3 class="text-sm font-medium text-gray-900">字幕来源</h3></div>
            <div class="p-4">
              <div class="flex space-x-2 mb-3">
                <button @click="translationSubtitleMode = 'upload'" class="flex-1 px-2 py-1 rounded-md text-xs transition-colors" :class="translationSubtitleMode === 'upload' ? 'bg-neutral-900 text-white' : 'bg-gray-200 text-gray-700'">上传JSON</button>
                <button @click="translationSubtitleMode = 'history'" class="flex-1 px-2 py-1 rounded-md text-xs transition-colors" :class="translationSubtitleMode === 'history' ? 'bg-neutral-900 text-white' : 'bg-gray-200 text-gray-700'">提取记录</button>
              </div>
              <div v-if="translationSubtitleMode === 'upload'">
                <input type="file" accept="application/json,.json" @change="handleTranslationSubtitleFile" class="block w-full text-xs text-gray-700 file:mr-2 file:py-1 file:px-2 file:rounded-md file:border-0 file:bg-neutral-900 file:text-white file:cursor-pointer" />
                <p v-if="translationSubtitleFileName" class="mt-1 text-xs text-gray-600">{{ translationSubtitleFileName }}</p>
              </div>
              <div v-else class="space-y-2 max-h-40 overflow-y-auto">
                <div v-for="task in extractTaskHistory.filter(item => item.status === 'completed' && item.subtitle_result)" :key="task.id" @click="translationSelectedExtractTask = task" class="bg-white rounded-lg p-2 border border-gray-200 cursor-pointer hover:border-indigo-400 transition" :class="{ 'border-indigo-400 bg-indigo-50/30': translationSelectedExtractTask?.id === task.id }">
                  <p class="text-gray-900 text-xs font-medium truncate">{{ task.original_filename }}</p>
                  <p class="text-gray-500 text-[11px] mt-1">{{ formatDate(task.created_at) }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- History Card -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">嵌入记录</h3>
              <button @click="loadTranslationHistory" class="p-1.5 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-md transition" title="刷新">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              </button>
            </div>
            <div class="p-3">
              <div v-if="translationTaskHistory.length === 0" class="text-center py-6 text-gray-400 text-xs">暂无翻译记录</div>
              <div v-else class="space-y-2.5 max-h-[calc(100vh-400px)] overflow-y-auto">
                <div v-for="task in translationTaskHistory" :key="task.id" @click="playTranslationVideo(task)" class="bg-white rounded-lg p-2.5 border border-gray-200 cursor-pointer hover:border-indigo-400 transition">
                  <p class="text-gray-900 text-xs font-medium truncate">{{ task.original_filename }}</p>
                  <div class="flex justify-between items-center mt-1">
                    <p class="text-gray-500 text-[11px]">{{ getLanguageName(task.target_language) }}</p>
                    <span class="px-2 py-0.5 rounded-full text-[11px] font-medium" :class="getStatusClass(task.status)">{{ getStatusText(task.status) }}</span>
                  </div>
                </div>
              </div>
              <div class="flex justify-between items-center mt-3 pt-2 border-t border-gray-100">
                <button @click="changeTranslationPage(translationCurrentPage - 1)" :disabled="translationCurrentPage === 1" class="px-2.5 py-1 text-[11px] border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">上一页</button>
                <div class="flex items-center space-x-1 text-[11px] text-gray-600"><span>第</span><span class="font-medium">{{ translationCurrentPage }}</span><span>页 / 共</span><span class="font-medium">{{ translationTotalPages }}</span><span>页</span></div>
                <button @click="changeTranslationPage(translationCurrentPage + 1)" :disabled="translationCurrentPage === translationTotalPages" class="px-2.5 py-1 text-[11px] border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">下一页</button>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <!-- Automatic Video Translation Feature -->
      <div v-else-if="currentFeature === 'auto-video-translate'" class="flex min-h-screen">
        <!-- Far Left Wider Nav -->
        <aside class="hidden lg:flex w-44 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-1.5">
          <div class="text-xs text-gray-500 px-1 mb-1">导航</div>
          <button @click="navigateToFeature('auto-video-translate')" class="w-full text-left px-3 py-2 rounded-md text-sm transition-colors"
                  :class="currentFeature === 'auto-video-translate' ? 'bg-indigo-100 text-indigo-700' : 'text-gray-700 hover:bg-gray-100'">视频翻译（自动版）</button>
          <button @click="navigateToFeature('subtitle-erase')" class="w-full text-left px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-gray-100">字幕擦除</button>
          <button @click="navigateToFeature('subtitle-extract')" class="w-full text-left px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-gray-100">字幕提取</button>
          <button @click="navigateToFeature('subtitle-embed')" class="w-full text-left px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-gray-100">视频翻译（手动）</button>
          <button @click="navigateToFeature('image-translate')" class="w-full text-left px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-gray-100">图片翻译</button>
        </aside>

        <!-- Left Process Config Column -->
        <aside class="hidden lg:flex w-72 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-3">
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">已选择的处理方式</h3>
            </div>
            <div class="p-4 space-y-3">
              <div class="space-y-2">
                <div class="flex items-center">
                  <span class="w-4 h-4 inline-flex items-center justify-center rounded-full mr-2 text-[10px]" :class="autoProgress.step >= 1 ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-600'">1</span>
                  <div class="text-xs text-gray-800">字幕提取</div>
                </div>
                <div class="flex items-center">
                  <span class="w-4 h-4 inline-flex items-center justify-center rounded-full mr-2 text-[10px]" :class="autoProgress.step >= 2 ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-600'">2</span>
                  <div class="text-xs text-gray-800">字幕擦除<span v-if="autoSkipSubtitleErasure" class="ml-1 text-gray-400">已跳过</span></div>
                </div>
                <div class="flex items-center">
                  <span class="w-4 h-4 inline-flex items-center justify-center rounded-full mr-2 text-[10px]" :class="autoProgress.step >= 3 ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-600'">3</span>
                  <div class="text-xs text-gray-800">视频翻译</div>
                </div>
              </div>

              <label class="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-3 py-2">
                <div>
                  <div class="text-xs font-medium text-gray-800">跳过字幕擦除</div>
                  <div class="text-[10px] text-gray-400">开启后直接使用原视频进行翻译</div>
                </div>
                <input
                  v-model="autoSkipSubtitleErasure"
                  type="checkbox"
                  :disabled="autoIsProcessing"
                  class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
              </label>

              <div class="pt-1">
                <div class="flex items-center justify-between mb-2">
                  <label class="block text-[11px] text-gray-500">目标语言</label>
                  <span class="text-[11px] text-indigo-600">已选 {{ autoTargetLanguages.length }} 门</span>
                </div>
                <div class="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-1">
                  <button
                    v-for="language in LANGUAGE_OPTIONS"
                    :key="language.code"
                    type="button"
                    @click="toggleAutoTargetLanguage(language.code)"
                    class="px-2.5 py-2 rounded-lg border text-left text-xs transition"
                    :class="autoTargetLanguages.includes(language.code) ? 'border-indigo-500 bg-indigo-50 text-indigo-700 shadow-sm' : 'border-gray-200 bg-white text-gray-700 hover:border-indigo-300'"
                  >
                    <span class="font-medium">{{ language.name }}</span>
                    <span class="block text-[10px] opacity-70">{{ language.code }}</span>
                  </button>
                </div>
              </div>

              <div class="pt-1">
                <label class="block text-[11px] text-gray-500 mb-2">字幕花字样式</label>
                <div class="rounded-xl border border-gray-200 bg-white p-2 shadow-sm">
                  <div class="flex h-24 items-center justify-center overflow-hidden rounded-lg bg-gray-900">
                    <img
                      v-if="selectedAutoSubtitleStyle.imageUrl"
                      :src="selectedAutoSubtitleStyle.imageUrl"
                      :alt="selectedAutoSubtitleStyle.label"
                      class="h-full w-full object-contain [image-rendering:auto]"
                    />
                    <div v-else class="px-3 py-2 text-center text-lg font-bold text-white" style="text-shadow: 0 2px 0 #000, 0 0 6px #000;">
                      字幕样式
                    </div>
                  </div>
                  <button
                    type="button"
                    @click="openAutoSubtitleStyleModal"
                    :disabled="autoIsProcessing"
                    class="mt-2 w-full rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-xs font-medium text-indigo-700 transition hover:border-indigo-300 hover:bg-indigo-100 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    更换字幕样式
                  </button>
                </div>
              </div>

              <button @click="startAutoTranslation" :disabled="autoIsProcessing || autoUploadedVideos.length === 0 || autoTargetLanguages.length === 0" :title="autoUploadedVideos.length === 0 ? '请先确认上传视频' : autoTargetLanguages.length === 0 ? '请至少选择一种目标语言' : ''" class="w-full py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
                {{ autoIsProcessing ? '处理中...' : `提交 (消耗${autoTranslationPointCost}积分)` }}
              </button>
            </div>
          </div>
        </aside>

        <!-- Center Workspace -->
        <section class="flex-1 flex items-center justify-center bg-white relative">
          <div class="w-full h-full flex flex-col items-center justify-center p-6">
            <div class="relative">
              <video v-if="currentVideoUrl" :src="currentVideoUrl" controls autoplay class="max-w-[80%] max-h-[70vh] rounded-lg shadow"></video>
              <video v-else-if="autoVideoObjectUrl" :src="autoVideoObjectUrl" controls class="max-w-[80%] max-h-[70vh] rounded-lg shadow"></video>
              <div v-else-if="autoSelectedHistoryTask" class="w-full max-w-md rounded-xl border border-gray-200 bg-gray-50 px-6 py-8 text-center">
                <div class="mb-3 text-sm font-medium text-gray-800">{{ autoSelectedHistoryTask.original_filename }}</div>
                <div class="mb-2 text-xs text-gray-500">当前状态：{{ getAutoStatusText(autoSelectedHistoryTask.status, autoSelectedHistoryTask) }}</div>
                <div class="text-sm" :class="autoSelectedHistoryTask.status === 'failed' ? 'text-red-600' : 'text-indigo-600'">
                  {{ autoSelectedHistoryTask.status === 'failed' ? '视频生成失败，请检查任务状态或重新提交' : '视频还在生成中，请继续耐心等待' }}
                </div>
              </div>
              <div v-else class="text-gray-400 text-sm">暂无视频</div>
            </div>
            <div v-if="!currentVideoUrl && autoVideoFiles.length > 0" class="mt-4 w-full max-w-[80%]">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-700">待上传视频</span>
                <span class="text-xs text-indigo-600">{{ autoPreviewVideoIndex + 1 }} / {{ autoVideoFiles.length }}</span>
              </div>
              <div class="flex flex-wrap gap-2 justify-center">
                <div
                  v-for="(file, index) in autoVideoFiles"
                  :key="`${file.name}-${index}`"
                  class="relative max-w-44"
                >
                  <button
                    type="button"
                    @click="switchAutoPreviewVideo(index)"
                    class="w-full max-w-44 truncate px-3 py-1.5 pr-6 rounded-md text-xs transition-colors"
                    :class="getAutoVideoFileButtonClass(file, index)"
                    :title="file.name"
                  >
                    {{ file.name }}
                  </button>
                  <button
                    type="button"
                    @click.stop="removeAutoVideoFile(index)"
                    class="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] leading-none text-white hover:bg-red-600"
                    title="删除"
                  >
                    ×
                  </button>
                </div>
              </div>
              <button
                type="button"
                @click="confirmAutoVideoUpload"
                :disabled="autoIsUploading || autoPendingVideoFiles.length === 0"
                class="mt-3 w-full rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {{ autoIsUploading ? `上传中... ${autoUploadProgress}%` : autoUploadedVideos.length > 0 ? '继续上传' : '确认上传' }}
              </button>
              <div v-if="autoUploadedVideos.length > 0" class="mt-2 text-center text-xs text-green-600">
                已上传 {{ autoUploadedVideos.length }} 个视频，待上传 {{ autoPendingVideoFiles.length }} 个视频
              </div>
            </div>
            <!-- Language Switcher for Multi-language Videos -->
            <div v-if="currentPlayingTask && getCompletedLanguageResults(currentPlayingTask).length > 1" class="mt-4 pt-4 border-t border-gray-200 w-full max-w-[80%]">
              <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-gray-700">切换语言版本</span>
                <span v-if="currentPlayingLanguage" class="text-xs text-indigo-600">{{ getLanguageName(currentPlayingLanguage) }}</span>
              </div>
              <div class="flex flex-wrap gap-2 justify-center">
                <button
                  v-for="result in getCompletedLanguageResults(currentPlayingTask)"
                  :key="result.code"
                  @click="switchVideoLanguage(result.code)"
                  class="px-3 py-1.5 rounded-md text-sm transition-colors"
                  :class="currentPlayingLanguage === result.code ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
                >
                  {{ getLanguageName(result.code) }}
                </button>
              </div>
            </div>
            
            <!-- Flying animation element from center video to history -->
            <div v-if="showSubmitAnimation && autoVideoObjectUrl" class="absolute top-1/2 left-1/2 w-[40%] h-[50vh] bg-black rounded-lg shadow animate-video-fly-to-history overflow-hidden">
              <video :src="autoVideoObjectUrl" class="w-full h-full object-cover"></video>
            </div>
            
            <!-- Success card -->
            <div v-if="showSubmitSuccessCard" class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 z-50 animate-fade-in-out">
              <div class="flex flex-col items-center">
                <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-3">
                  <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                </div>
                <p class="text-gray-900 font-medium text-center">已经提交任务</p>
                <p class="text-gray-500 text-sm text-center mt-1">请稍后在历史记录中查看</p>
              </div>
            </div>
          </div>
        </section>

        <!-- Right Sidebar Cards -->
        <aside class="w-full lg:w-80 border-l border-gray-200 bg-gray-50 p-3 space-y-3">
          <!-- Upload Card -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">待翻译视频</h3>
            </div>
            <div class="p-4">
              <div
                @click="() => !autoIsProcessing && autoVideoInputRef?.click()"
                class="border-2 border-dashed rounded-lg p-6 text-center transition-colors duration-200 relative"
                :class="autoIsProcessing || autoIsUploading ? 'border-gray-300 bg-gray-50 cursor-not-allowed' : 'border-gray-300 hover:border-indigo-400 hover:bg-indigo-50/30 cursor-pointer'"
              >
                <input type="file" ref="autoVideoInputRef" @change="handleAutoVideoSelect" accept="video/*" multiple class="hidden" :disabled="autoIsProcessing || autoIsUploading" />
                
                <!-- Upload Progress Overlay -->
                <div v-if="autoIsUploading" class="absolute inset-0 bg-white/90 flex flex-col items-center justify-center rounded-lg z-10">
                  <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-2"></div>
                  <p class="text-sm text-gray-600 mb-2">上传中... {{ autoUploadProgress }}%</p>
                  <div class="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div class="h-full bg-indigo-600 transition-all duration-300" :style="{ width: autoUploadProgress + '%' }"></div>
                  </div>
                </div>
                
                <!-- Processing Overlay -->
                <div v-if="autoIsProcessing" class="absolute inset-0 bg-white/80 flex flex-col items-center justify-center rounded-lg z-10">
                  <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-2"></div>
                  <p class="text-sm text-gray-600">处理中...</p>
                </div>
                
                <template v-if="autoVideoFiles.length === 0">
                  <p class="text-gray-700 text-sm font-medium">点击上传视频</p>
                  <p class="text-gray-400 text-xs mt-1">支持 mp4, avi, mov 等（可多选）</p>
                </template>
                <div v-else class="w-full">
                  <img v-if="autoVideoThumbnail && autoVideoFiles.length === 1" :src="autoVideoThumbnail" class="max-w-full h-auto max-h-36 object-contain rounded-lg mb-3 mx-auto" alt="Video thumbnail" />
                  <p class="text-gray-900 text-xs font-medium text-center mb-2">待上传 {{ autoVideoFiles.length }} 个视频</p>
                  <div class="max-h-32 overflow-y-auto space-y-1">
                    <div v-for="(file, index) in autoVideoFiles" :key="index" class="flex items-center justify-between bg-gray-50 rounded px-2 py-1">
                      <p class="text-gray-900 text-[11px] font-medium truncate flex-1">{{ file.name }}</p>
                      <p class="text-gray-500 text-[10px] ml-2">{{ formatFileSize(file.size) }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- History Card -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">自动翻译记录</h3>
              <button @click="refreshAutoTranslationHistory" class="p-1.5 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-md transition" :class="{ 'animate-spin': autoIsRefreshing }" title="刷新">
                <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              </button>
            </div>
            <div class="p-3">
              <div v-if="autoTaskHistory.length === 0" class="text-center py-6 text-gray-400 text-xs">暂无自动翻译记录</div>
              <div v-else class="space-y-2.5 max-h-[calc(100vh-400px)] overflow-y-auto">
                <div v-for="task in autoTaskHistory" :key="task.id" @click="playAutoTranslationVideo(task)" class="bg-white rounded-lg p-2.5 border border-gray-200 cursor-pointer hover:border-indigo-400 transition">
                  <div class="flex justify-between items-start gap-2">
                    <div class="flex-1 min-w-0">
                      <p v-if="editingAutoTaskId !== task.id" class="text-gray-900 text-xs font-medium truncate">{{ task.original_filename }}</p>
                      <input v-else v-model="editingAutoTaskName" @click.stop @blur="saveAutoTaskName" @keyup.enter="saveAutoTaskName" @keyup.esc="cancelEditAutoTaskName" ref="autoEditInput" class="text-gray-900 text-xs font-medium w-full border border-indigo-400 rounded px-1 py-0.5 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                      <p class="text-gray-500 text-[11px] mt-1">{{ formatDate(task.created_at) }}</p>
                    </div>
                    <div class="flex flex-col items-end gap-1 shrink-0">
                      <button @click.stop="startEditAutoTaskName(task)" class="px-2 py-0.5 text-[10px] text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded transition" title="编辑名称">
                        编辑
                      </button>
                      <span class="px-2 py-0.5 rounded-full text-[11px] font-medium shrink-0" :class="getAutoStatusClass(task.status, task)">{{ getAutoStatusText(task.status, task) }}</span>
                    </div>
                  </div>
                  <div class="flex justify-between items-center mt-1 gap-2">
                    <p class="text-gray-500 text-[11px] truncate">{{ getTaskLanguageNames(task) }}</p>
                  </div>
                  <div v-if="getCompletedLanguageResults(task).length > 1" class="flex flex-wrap gap-1 mt-2">
                    <button
                      v-for="result in getCompletedLanguageResults(task)"
                      :key="`${task.id}-${result.code}`"
                      type="button"
                      @click.stop="playAutoTranslationVideo(task, result.code)"
                      class="px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-[10px] hover:bg-indigo-100"
                    >
                      {{ getLanguageName(result.code) }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- Pagination Controls for Auto Translation History -->
              <div class="flex justify-between items-center mt-3 pt-2 border-t border-gray-100">
                <button @click="changeAutoPage(autoCurrentPage - 1)" :disabled="autoCurrentPage === 1" class="px-2.5 py-1 text-[11px] border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">上一页</button>
                <div class="flex items-center space-x-1 text-[11px] text-gray-600">
                  <span>第</span><span class="font-medium">{{ autoCurrentPage }}</span><span>页 / 共</span><span class="font-medium">{{ autoTotalPages }}</span><span>页</span>
                </div>
                <button @click="changeAutoPage(autoCurrentPage + 1)" :disabled="autoCurrentPage === autoTotalPages" class="px-2.5 py-1 text-[11px] border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">下一页</button>
              </div>
            </div>
          </div>
        </aside>
      </div>

      <!-- Image Translate Feature (Four-column) -->
      <div v-else-if="currentFeature === 'image-translate'" class="flex min-h-screen">
        <!-- Far Left Wider Nav -->
        <aside class="hidden lg:flex w-44 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-1.5">
          <div class="text-xs text-gray-500 px-1 mb-1">导航</div>
          <button @click="navigateToFeature('auto-video-translate')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">视频翻译（自动版）</button>
          <button @click="navigateToFeature('subtitle-erase')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">字幕擦除</button>
          <button @click="navigateToFeature('subtitle-extract')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">字幕提取</button>
          <button @click="navigateToFeature('subtitle-embed')" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-gray-100">视频翻译（手动）</button>
          <button @click="navigateToFeature('image-translate')" class="w-full text-left px-3 py-2 rounded-md text-sm bg-indigo-100 text-indigo-700">图片翻译</button>
        </aside>

        <!-- Left Process Config Column -->
        <aside class="hidden lg:flex w-72 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-3">
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">已选择的处理方式</h3>
            </div>
            <div class="p-4 space-y-3">
              <div class="space-y-2">
                <div class="flex items-center">
                  <span class="w-4 h-4 inline-flex items-center justify-center rounded-full mr-2 text-[10px] bg-indigo-600 text-white">1</span>
                  <div class="text-xs text-gray-800">图片翻译</div>
                </div>
              </div>

              <div class="pt-1">
                <label class="block text-[11px] text-gray-500 mb-1">目标语言（暂未提供）</label>
                <select disabled class="w-full px-2.5 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-500 text-sm cursor-not-allowed">
                  <option>待实现</option>
                </select>
              </div>

              <button disabled class="w-full py-2 bg-gray-300 text-gray-500 rounded-md text-sm font-medium cursor-not-allowed">
                提交（暂未实现）
              </button>
            </div>
          </div>
        </aside>

        <!-- Center Workspace -->
        <section class="flex-1 flex items-center justify-center bg-white">
          <div class="w-full h-full flex items-center justify-center p-6">
            <div class="text-center text-gray-400 select-none">
              <div class="mx-auto mb-4 w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center">
                <svg class="w-10 h-10 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>
              </div>
              <p class="text-sm">图片翻译功能正在开发中</p>
            </div>
          </div>
        </section>

        <!-- Right Sidebar: Upload + History Placeholder -->
        <aside class="w-full lg:w-80 border-l border-gray-200 bg-gray-50 p-3 space-y-3">
          <!-- Upload Card Placeholder -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">待翻译图片</h3>
            </div>
            <div class="p-4">
              <div class="border-2 border-dashed rounded-lg p-6 text-center cursor-not-allowed transition-colors duration-200 border-gray-300 bg-gray-50">
                <p class="text-gray-500 text-sm font-medium">点击上传图片（暂未实现）</p>
                <p class="text-gray-400 text-xs mt-1">支持 jpg, png 等</p>
              </div>
            </div>
          </div>

          <!-- History Card Placeholder -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">翻译记录</h3>
            </div>
            <div class="p-4">
              <div class="text-center py-6 text-gray-400 text-xs">暂无翻译记录</div>
            </div>
          </div>
        </aside>
      </div>

      <!-- Other Features Placeholder -->
      <div v-else class="text-center">
        <div class="bg-gray-50 rounded-lg p-16">
          <h2 class="text-3xl font-medium text-neutral-900 mb-4">
            {{ getFeatureTitle() }}
          </h2>
          <p class="text-lg text-gray-500 mb-8">
            {{ getFeatureDescription() }}
          </p>
          <div class="inline-flex items-center px-6 py-3 bg-gray-100 rounded-lg">
            <span class="text-gray-600 font-medium">🚧 正在开发中</span>
          </div>
        </div>
      </div>
    </main>

    <!-- Auto Subtitle Style Modal -->
    <div v-if="showAutoSubtitleStyleModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" @click="closeAutoSubtitleStyleModal">
      <div class="mx-4 flex max-h-[86vh] w-full max-w-5xl flex-col overflow-hidden rounded-xl bg-white shadow-xl" @click.stop>
        <div class="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 class="text-lg font-semibold text-gray-900">选择字幕花字样式</h2>
          <button @click="closeAutoSubtitleStyleModal" class="text-gray-400 hover:text-gray-600">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-6 space-y-6">
          <div v-for="group in AUTO_SUBTITLE_STYLE_GROUPS" :key="group.label">
            <h3 class="mb-3 text-sm font-medium text-gray-700">{{ group.label }}</h3>
            <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
              <button
                v-for="style in group.options"
                :key="style.id"
                type="button"
                @click="selectAutoSubtitleStyle(style.id)"
                :aria-label="`选择字幕样式 ${style.label}`"
                class="relative flex h-24 items-center justify-center overflow-hidden rounded-xl border bg-gray-900 p-2 transition hover:border-indigo-400 hover:shadow-sm"
                :class="style.id === autoSubtitleStyleId ? 'border-indigo-500 ring-2 ring-indigo-200' : 'border-gray-200'"
              >
                <img
                  v-if="style.imageUrl"
                  :src="style.imageUrl"
                  :alt="style.label"
                  class="h-full w-full object-contain [image-rendering:auto]"
                  loading="lazy"
                />
                <span v-else class="text-center text-base font-bold text-white" style="text-shadow: 0 2px 0 #000, 0 0 6px #000;">字幕样式</span>
                <span v-if="style.id === autoSubtitleStyleId" class="absolute right-2 top-2 h-3 w-3 rounded-full bg-indigo-500 ring-2 ring-white"></span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Result Modal -->
    <div v-if="showResultModal && selectedHistoryTask" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div class="bg-white rounded-lg p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-6">
          <h2 class="text-2xl font-medium text-neutral-900">处理结果</h2>
          <button @click="closeResultModal" class="text-gray-500 hover:text-gray-700">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="space-y-4">
          <div class="flex justify-between items-center">
            <span class="text-gray-600">文件名:</span>
            <span class="text-gray-900 font-medium">{{ selectedHistoryTask.original_filename }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-gray-600">状态:</span>
            <span 
              class="px-3 py-1 rounded-full text-sm font-medium"
              :class="getStatusClass(selectedHistoryTask.status)"
            >
              {{ getStatusText(selectedHistoryTask.status) }}
            </span>
          </div>
          
          <div v-if="selectedHistoryTask.status === 'processing'" class="text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <p class="text-gray-600 mt-4">正在处理中，请稍候...</p>
          </div>

          <div v-if="selectedHistoryTask.status === 'completed' && selectedHistoryTask.result_video_url">
            <div class="mt-4">
              <video 
                :src="selectedHistoryTask.result_video_url" 
                controls 
                class="w-3/4 mx-auto rounded-lg"
              ></video>
            </div>
            <div class="text-center mt-4">
              <a 
                :href="selectedHistoryTask.result_video_url" 
                download
                class="inline-block px-6 py-2 bg-blue-500 text-white rounded-md font-medium hover:bg-blue-600 transition-colors duration-200"
              >
                下载处理后的视频
              </a>
            </div>
          </div>

          <div v-if="selectedHistoryTask.status === 'failed'" class="text-red-600">
            <p class="font-medium">处理失败</p>
            <p class="text-sm mt-2">{{ selectedHistoryTask.error_message || '未知错误' }}</p>
          </div>
        </div>
      </div>
    </div>
  <!-- Subtitle Display Modal -->
    <div v-if="showSubtitleModal && selectedExtractTask" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="closeSubtitleModal">
      <div class="bg-white rounded-lg shadow-xl w-4/5 max-w-5xl max-h-[80vh] overflow-hidden flex flex-col" @click.stop>
        <div class="p-6 border-b border-gray-200 flex justify-between items-center">
          <h2 class="text-xl font-semibold text-gray-900">{{ selectedExtractTask.original_filename }}</h2>
          <button @click="closeSubtitleModal" class="text-gray-400 hover:text-gray-600">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="p-6 overflow-y-auto flex-1">
          <div v-if="selectedExtractTask.subtitle_result">
            <div v-for="(item, index) in parseSubtitles(selectedExtractTask.subtitle_result)" :key="index" class="mb-4 p-3 bg-gray-50 rounded-lg">
              <div class="flex items-center text-sm text-gray-500 mb-2">
                <span class="font-mono">{{ formatTime(item.start_time) }}</span>
                <span class="mx-2">→</span>
                <span class="font-mono">{{ formatTime(item.end_time) }}</span>
              </div>
              <p class="text-gray-900 text-base leading-relaxed">{{ item.text }}</p>
            </div>
          </div>
          <div v-else class="text-center py-8 text-gray-400">
            <p>暂无字幕数据</p>
          </div>
        </div>

        <div class="p-4 border-t border-gray-200 flex justify-end">
          <button 
            @click="downloadSubtitleJson"
            :disabled="!selectedExtractTask.subtitle_result"
            class="px-6 py-2 bg-neutral-900 text-white rounded-md font-medium hover:bg-neutral-800 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            下载字幕 JSON
          </button>
        </div>
      </div>
    </div>

    <!-- Video Player Modal -->
    <div v-if="showVideoModal" class="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50" @click="showVideoModal = false">
      <div class="bg-white rounded-lg max-w-2xl w-full mx-4 overflow-hidden" @click.stop>
        <div class="flex justify-between items-center p-4 border-b">
          <h2 class="text-xl font-semibold text-gray-900">视频播放</h2>
          <button @click="showVideoModal = false" class="text-gray-400 hover:text-gray-600">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-4">
          <video :src="currentVideoUrl" controls class="w-full rounded-lg" autoplay></video>
        </div>
      </div>
    </div>

    <!-- Login Modal -->
    <div v-if="showLoginModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="showLoginModal = false">
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 overflow-hidden" @click.stop>
        <div class="p-6 border-b border-gray-200 flex justify-between items-center">
          <h2 class="text-xl font-semibold text-gray-900">登录</h2>
          <button @click="showLoginModal = false" class="text-gray-400 hover:text-gray-600">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-6">
          <form @submit.prevent="handleLoginSubmit">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">用户名</label>
              <input v-model="loginForm.username" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-600" placeholder="请输入用户名" />
            </div>
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">密码</label>
              <input v-model="loginForm.password" type="password" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-600" placeholder="请输入密码" />
            </div>
            <div v-if="loginError" class="mb-4 text-sm text-red-600">{{ loginError }}</div>
            <button type="submit" :disabled="isLoggingIn" class="w-full py-2 bg-indigo-600 text-white rounded-md font-medium hover:bg-indigo-700 transition disabled:opacity-50">
              {{ isLoggingIn ? '登录中...' : '登录' }}
            </button>
          </form>
          <div class="mt-4 text-center text-sm text-gray-600">
            还没有账号？<a href="/register" class="text-indigo-600 hover:text-indigo-700">注册</a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import OSS from 'ali-oss'
import { useAuthStore } from '@/stores/auth'
import { UploadFilled } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const LANGUAGE_OPTIONS = [
  { code: 'zh', name: '中文' },
  { code: 'en', name: '英语' },
  { code: 'ja', name: '日语' },
  { code: 'ko', name: '韩语' },
  { code: 'th', name: '泰语' },
  { code: 'vi', name: '越南语' },
  { code: 'es', name: '西班牙语' },
  { code: 'fr', name: '法语' },
  { code: 'de', name: '德语' },
  { code: 'id', name: '印尼语' },
  { code: 'ms', name: '马来语' },
  { code: 'fil', name: '菲律宾语' },
  { code: 'ru', name: '俄语' },
  { code: 'it', name: '意大利语' },
  { code: 'yue', name: '粤语' }
]

const DEFAULT_AUTO_SUBTITLE_PARAMS = {
  alignment: 'TopCenter',
  font: 'Alibaba PuHuiTi',
  font_size: 84,
  font_color: '#ffffff',
  outline: 2,
  outline_colour: '#000000',
  y: 0.75
}

const SUBTITLE_STYLE_PLACEHOLDER_IMAGE = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='

const AUTO_SUBTITLE_STYLE_IMAGES = {
  'CS0001-000001': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712522.png',
  'CS0001-000002': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712523.png',
  'CS0001-000003': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712525.png',
  'CS0001-000004': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712526.png',
  'CS0001-000005': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712528.png',
  'CS0001-000006': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712529.png',
  'CS0001-000007': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712530.png',
  'CS0001-000008': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712531.png',
  'CS0001-000009': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712532.png',
  'CS0001-000010': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712533.png',
  'CS0001-000011': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712534.png',
  'CS0001-000012': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712535.png',
  'CS0001-000013': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712536.png',
  'CS0001-000014': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712537.png',
  'CS0001-000015': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712538.png',
  'CS0001-000016': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712539.png',
  'CS0002-000001': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712540.png',
  'CS0002-000002': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712541.png',
  'CS0002-000003': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712542.png',
  'CS0002-000004': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712543.png',
  'CS0002-000005': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712544.png',
  'CS0002-000006': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712545.png',
  'CS0002-000007': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712546.png',
  'CS0002-000008': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712547.png',
  'CS0002-000009': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712548.png',
  'CS0002-000010': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712549.png',
  'CS0002-000011': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712550.png',
  'CS0002-000012': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712551.png',
  'CS0002-000013': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712552.png',
  'CS0002-000014': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712553.png',
  'CS0002-000015': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712554.png',
  'CS0002-000016': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712555.png',
  'CS0003-000001': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712556.png',
  'CS0003-000002': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712557.png',
  'CS0003-000003': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712558.png',
  'CS0003-000004': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712559.png',
  'CS0003-000005': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712560.png',
  'CS0003-000006': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712561.png',
  'CS0003-000007': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712562.png',
  'CS0003-000008': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712563.png',
  'CS0003-000009': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712564.png',
  'CS0003-000010': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712565.png',
  'CS0003-000011': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712566.png',
  'CS0003-000012': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712567.png',
  'CS0003-000013': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712568.png',
  'CS0003-000014': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712569.png',
  'CS0003-000015': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712570.png',
  'CS0003-000016': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712571.png',
  'CS0003-000017': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712572.png',
  'CS0003-000018': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712573.png',
  'CS0003-000019': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712574.png',
  'CS0003-000020': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712575.png',
  'CS0003-000021': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712576.png',
  'CS0003-000022': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712577.png',
  'CS0003-000023': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712578.png',
  'CS0003-000024': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712579.png',
  'CS0003-000025': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712580.png',
  'CS0004-000001': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712581.png',
  'CS0004-000002': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712582.png',
  'CS0004-000003': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712583.png',
  'CS0004-000004': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712584.png',
  'CS0004-000005': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712585.png',
  'CS0004-000006': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712586.png',
  'CS0004-000007': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712587.png',
  'CS0004-000008': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712588.png',
  'CS0004-000009': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712589.png',
  'CS0004-000010': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712590.png',
  'CS0004-000011': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712591.png',
  'CS0004-000012': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712592.png',
  'CS0004-000013': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712593.png',
  'CS0004-000014': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712594.png',
  'CS0004-000015': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712595.png',
  'CS0004-000016': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712596.png',
  'CS0004-000017': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712597.png',
  'CS0004-000018': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712598.png',
  'CS0004-000019': 'https://help-static-aliyun-doc.aliyuncs.com/assets/img/zh-CN/1263923961/p712599.png'
}

const getAutoSubtitleStyleImage = (id) => AUTO_SUBTITLE_STYLE_IMAGES[id] || SUBTITLE_STYLE_PLACEHOLDER_IMAGE

const createCsSubtitleStyleOptions = (series, count) => Array.from({ length: count }, (_, index) => {
  const id = `${series}-${String(index + 1).padStart(6, '0')}`
  return {
    id,
    label: id,
    params: {
      effect_color_style: id,
      outline: 0
    },
    imageUrl: getAutoSubtitleStyleImage(id),
    swatches: [
      { label: '花字', color: '#6366f1' }
    ]
  }
})

const createNamedSubtitleStyleOption = (id, outlineColour, backColour) => ({
  id,
  label: id,
  params: {
    effect_color_style: id,
    outline_colour: outlineColour,
    back_colour: backColour,
    outline: 2
  },
  imageUrl: getAutoSubtitleStyleImage(id),
  swatches: [
    { label: '描边', color: outlineColour },
    { label: '背景', color: backColour }
  ]
})

const AUTO_SUBTITLE_STYLE_GROUPS = [
  {
    label: '默认',
    options: [
      {
        id: 'default',
        label: '默认白字黑边',
        params: {},
        imageUrl: '',
        swatches: [
          { label: '文字', color: '#ffffff' },
          { label: '描边', color: '#000000' }
        ]
      }
    ]
  },
  {
    label: '花字一（推荐）',
    options: [
      ...createCsSubtitleStyleOptions('CS0001', 16),
      ...createCsSubtitleStyleOptions('CS0002', 16),
      ...createCsSubtitleStyleOptions('CS0003', 3)
    ]
  }
]

const AUTO_SUBTITLE_STYLE_OPTIONS = AUTO_SUBTITLE_STYLE_GROUPS.flatMap(group => group.options)

const showLoginModal = ref(false)
const userPoints = ref(0)
const loginForm = ref({ username: '', password: '' })
const loginError = ref('')
const isLoggingIn = ref(false)

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const fetchUserPoints = async () => {
  if (authStore.isAuthenticated) {
    try {
      const response = await axios.get(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${authStore.token}` }
      })
      userPoints.value = response.data.points || 0
      authStore.user = response.data
    } catch (error) {
      console.error('Failed to fetch user points:', error)
    }
  }
}

const handleLoginSubmit = async () => {
  isLoggingIn.value = true
  loginError.value = ''
  
  try {
    const result = await authStore.login(loginForm.value.username, loginForm.value.password)
    if (result.success) {
      showLoginModal.value = false
      loginForm.value = { username: '', password: '' }
      await fetchUserPoints()
    } else {
      loginError.value = result.error
    }
  } catch (error) {
    loginError.value = '登录失败，请稍后重试'
  } finally {
    isLoggingIn.value = false
  }
}

const currentFeature = ref('auto-video-translate')
const fileList = ref([])
const isUploading = ref(false)
const uploadProgress = ref(0)
const currentTask = ref(null)
const taskHistory = ref([])
const uploadRef = ref(null)
const pollingInterval = ref(null)
const selectedHistoryTask = ref(null)
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = ref(8)
const isSubmitting = ref(false)
const showResultModal = ref(false)
const editingTaskId = ref(null)
const editingTaskName = ref('')
const editInput = ref(null)

// Subtitle extraction states
const extractFile = ref(null)
const extractFileObjectUrl = ref('')
const extractFileThumbnail = ref('')
const extractIsUploading = ref(false)
const extractIsSubmitting = ref(false)
const extractUploadProgress = ref(0)
const extractTaskHistory = ref([])
const extractSelectedHistoryTask = ref(null)
const extractCurrentPage = ref(1)
const extractTotalPages = ref(1)
const extractPageSize = ref(8)
const extractSourceMode = ref('upload') // 'upload' or 'history'
const extractErasureHistory = ref([])
const extractSelectedErasureTask = ref(null)
const extractErasureCurrentPage = ref(1)
const extractErasureTotalPages = ref(1)
const extractErasurePageSize = ref(8)
const extractIsRefreshing = ref(false)
const showSubtitleModal = ref(false)
const selectedExtractTask = ref(null)

// Video translation states
const translationVideoFile = ref(null)
const translationVideoObjectUrl = ref('')
const translationVideoThumbnail = ref('')
const translationProgress = ref({ step: 0, status: '' })
const translationSubtitleMode = ref('upload')
const translationSubtitleJson = ref(null)
const translationSubtitleFileName = ref('')
const translationSelectedExtractTask = ref(null)
const translationTargetLanguage = ref('en')
const translationSubtitleParams = ref({
  alignment: 'BottomCenter',
  font_size: 42,
  font_color: '#ffffff',
  outline: 2,
  outline_colour: '#000000',
  adapt_mode: 'Auto'
})
const translationIsSubmitting = ref(false)
const translationUploadProgress = ref(0)
const translationTaskHistory = ref([])
const translationVideoInputRef = ref(null)
const showVideoModal = ref(false)
const currentVideoUrl = ref('')
const currentPlayingTask = ref(null)
const currentPlayingLanguage = ref(null)
const autoSelectedHistoryTask = ref(null)
const translationCurrentPage = ref(1)
const translationTotalPages = ref(1)
const translationPageSize = ref(8)

// Automatic video translation states
const autoVideoFiles = ref([])
const autoVideoThumbnail = ref('')
const autoVideoObjectUrl = ref('')
const autoPreviewVideoIndex = ref(0)
const autoUploadedVideos = ref([])
const autoUploadProgress = ref(0)
const autoIsUploading = ref(false)
const autoTargetLanguages = ref(['en'])
const autoSkipSubtitleErasure = ref(false)
const autoSubtitleStyleId = ref('default')
const selectedAutoSubtitleStyle = computed(() => AUTO_SUBTITLE_STYLE_OPTIONS.find(style => style.id === autoSubtitleStyleId.value) || AUTO_SUBTITLE_STYLE_OPTIONS[0])
const autoTranslationPointCost = computed(() => (10 + Math.max(0, autoTargetLanguages.value.length - 1) * 5) * Math.max(1, autoUploadedVideos.value.length))
const autoPendingVideoFiles = computed(() => autoVideoFiles.value.filter(file => !autoUploadedVideos.value.some(item => item.file === file)))
const autoIsProcessing = ref(false)
const autoProgress = ref({ step: 0, status: '' })
const autoTaskHistory = ref([])
const autoVideoInputRef = ref(null)
const autoCurrentPage = ref(1)
const autoTotalPages = ref(1)
const autoPageSize = ref(8)
const autoIsRefreshing = ref(false)
const showSubmitAnimation = ref(false)
const showSubmitSuccessCard = ref(false)
const showAutoSubtitleStyleModal = ref(false)
const editingAutoTaskId = ref(null)
const editingAutoTaskName = ref('')
const autoEditInput = ref(null)

const API_BASE = '/api'

// Generate video thumbnail
const generateVideoThumbnail = (file) => {
  return new Promise((resolve) => {
    const video = document.createElement('video')
    video.src = URL.createObjectURL(file)
    video.currentTime = 1 // Capture frame at 1 second

    video.addEventListener('loadeddata', () => {
      const canvas = document.createElement('canvas')
      const maxWidth = 640
      const maxHeight = 360

      // Calculate aspect ratio
      const aspectRatio = video.videoWidth / video.videoHeight

      let canvasWidth = maxWidth
      let canvasHeight = canvasWidth / aspectRatio

      if (canvasHeight > maxHeight) {
        canvasHeight = maxHeight
        canvasWidth = canvasHeight * aspectRatio
      }

      canvas.width = canvasWidth
      canvas.height = canvasHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
      const thumbnail = canvas.toDataURL('image/jpeg', 0.85)
      URL.revokeObjectURL(video.src)
      resolve(thumbnail)
    })

    video.addEventListener('error', () => {
      URL.revokeObjectURL(video.src)
      resolve('')
    })
  })
}

// Handle translation video selection
const handleTranslationVideoSelect = async (e) => {
  const file = e.target.files[0]
  if (file) {
    translationVideoFile.value = file
    translationVideoObjectUrl.value = URL.createObjectURL(file)
    translationVideoThumbnail.value = await generateVideoThumbnail(file)
  }
}

// OSS client for direct upload
let ossClient = null

const initOSSClient = async () => {
  try {
    const response = await axios.get(
      `${API_BASE}/video-translation/oss-config`,
      { headers: { 'Authorization': `Bearer ${authStore.token}` } }
    )
    const config = response.data
    ossClient = new OSS({
      region: config.region,
      accessKeyId: config.accessKeyId,
      accessKeySecret: config.accessKeySecret,
      bucket: config.bucket
    })
    return ossClient
  } catch (error) {
    console.error('Failed to init OSS client:', error)
    return null
  }
}

const navigateToFeature = (feature) => {
  currentFeature.value = feature
  if (feature === 'subtitle-erase') {
    loadTaskHistory()
  } else if (feature === 'subtitle-extract') {
    loadExtractHistory()
    loadErasureHistory()
  } else if (feature === 'subtitle-embed') {
    loadExtractHistory()
    loadTranslationHistory()
  } else if (feature === 'auto-video-translate') {
    loadAutoTranslationHistory()
  }
}

const getFeatureTitle = () => {
  const titles = {
    'subtitle-erase': '字幕擦除',
    'subtitle-extract': '字幕提取',
    'subtitle-embed': '视频翻译',
    'image-translate': '图片翻译',
    'auto-video-translate': '视频翻译（自动版）'
  }
  return titles[currentFeature.value] || 'VP智能视频翻译'
}

const getFeatureDescription = () => {
  const descriptions = {
    'subtitle-erase': '智能识别并移除视频中的字幕，保持画面完整性',
    'subtitle-extract': '从视频中准确提取字幕内容，支持多种格式输出',
    'subtitle-embed': '上传视频和字幕时间戳，翻译并合成目标语言音频',
    'image-translate': '智能翻译图片中的文字内容，保持原始排版',
    'auto-video-translate': '一键完成字幕提取、字幕擦除、视频翻译全流程'
  }
  return descriptions[currentFeature.value] || '选择功能开始处理'
}

const getLanguageName = (langCode) => {
  return LANGUAGE_OPTIONS.find(language => language.code === langCode)?.name || langCode
}

const getTaskTargetLanguages = (task) => {
  if (Array.isArray(task.target_languages) && task.target_languages.length > 0) {
    return task.target_languages
  }
  return task.target_language ? [task.target_language] : []
}

const getTaskLanguageNames = (task) => {
  const languageNames = getTaskTargetLanguages(task).map(getLanguageName)
  return languageNames.length > 0 ? languageNames.join('、') : '未选择语言'
}

const getCompletedLanguageResults = (task) => {
  const results = task.language_results || {}
  return Object.entries(results)
    .filter(([, result]) => result?.result_video_url)
    .map(([code, result]) => ({ code, ...result }))
}

const toggleAutoTargetLanguage = (languageCode) => {
  if (autoTargetLanguages.value.includes(languageCode)) {
    autoTargetLanguages.value = autoTargetLanguages.value.filter(code => code !== languageCode)
  } else {
    autoTargetLanguages.value = [...autoTargetLanguages.value, languageCode]
  }
}

const buildAutoSubtitleParams = () => ({
  ...DEFAULT_AUTO_SUBTITLE_PARAMS,
  ...selectedAutoSubtitleStyle.value.params
})

const openAutoSubtitleStyleModal = () => {
  showAutoSubtitleStyleModal.value = true
}

const closeAutoSubtitleStyleModal = () => {
  showAutoSubtitleStyleModal.value = false
}

const selectAutoSubtitleStyle = (styleId) => {
  autoSubtitleStyleId.value = styleId
  closeAutoSubtitleStyleModal()
}

const handleFileSelect = (file) => {
  if (file.raw && file.raw.type.startsWith('video/')) {
    // Element Plus的Upload组件会自动管理fileList
  }
}

const handleFileRemove = (file) => {
  // Element Plus的Upload组件会自动管理fileList
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const uploadVideo = async () => {
  if (!fileList.value || fileList.value.length === 0) return

  isUploading.value = true
  uploadProgress.value = 0
  const totalFiles = fileList.value.length
  let completedFiles = 0

  try {
    // Initialize OSS client
    if (!ossClient) {
      await initOSSClient()
    }

    // Upload each file
    for (const fileItem of fileList.value) {
      const file = fileItem.raw
      // Generate OSS key
      const timestamp = new Date().toISOString().replace(/[:.]/g, '').slice(0, 15)
      const randomStr = Math.random().toString(36).substring(2, 10)
      const ext = file.name.split('.').pop()
      const ossKey = `subtitle_erase/1/${timestamp}_${randomStr}.${ext}`

      // Upload directly using OSS SDK multipart
      const result = await ossClient.multipartUpload(ossKey, file, {
        progress: (p) => {
          const overallProgress = Math.round((completedFiles + p) / totalFiles * 100)
          uploadProgress.value = overallProgress
        },
        partSize: 30 * 1024 * 1024, // 30MB per part
        parallel: 5
      })

      // Get file URL
      const fileUrl = ossClient.signatureUrl(ossKey, { expires: 604800 })

      // Submit task to backend
      const submitResponse = await axios.post(
        `${API_BASE}/subtitle/submit`,
        {
          video_url: fileUrl,
          oss_key: ossKey,
          original_filename: file.name,
          mode: 'Subtitle'
        },
        {
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        }
      )

      completedFiles++
      uploadProgress.value = Math.round(completedFiles / totalFiles * 100)
    }

    // Upload complete
    isUploading.value = false
    
    // Reload history
    await loadTaskHistory()
    
    // Reset file selection
    fileList.value = []
    uploadProgress.value = 0
    
  } catch (error) {
    console.error('Upload failed:', error)
    alert('上传失败: ' + (error.response?.data?.detail || error.message))
    isUploading.value = false
  }
}

const startPolling = (taskId) => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
  }
  
  pollingInterval.value = setInterval(async () => {
    try {
      const response = await axios.get(
        `${API_BASE}/subtitle/tasks/${taskId}`,
        {
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        }
      )
      
      currentTask.value = response.data
      
      if (response.data.status === 'completed' || response.data.status === 'failed') {
        clearInterval(pollingInterval.value)
        pollingInterval.value = null
        await loadTaskHistory()
      }
    } catch (error) {
      console.error('Polling failed:', error)
    }
  }, 10000) // Poll every 10 seconds
}

const loadTaskHistory = async () => {
  try {
    const response = await axios.get(
      `${API_BASE}/subtitle/tasks`,
      {
        params: {
          page: currentPage.value,
          page_size: pageSize.value
        },
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    )
    taskHistory.value = response.data.items
    totalPages.value = response.data.total_pages
  } catch (error) {
    console.error('Failed to load task history:', error)
  }
}

const refreshHistory = async () => {
  try {
    // Get task IDs from current page
    const taskIds = taskHistory.value.map(task => task.id)
    
    if (taskIds.length > 0) {
      // Refresh statuses from VolcEngine
      await axios.post(
        `${API_BASE}/subtitle/tasks/refresh-status`,
        taskIds,
        {
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        }
      )
    }
    
    // Reload history to get updated data
    await loadTaskHistory()
  } catch (error) {
    console.error('Failed to refresh task statuses:', error)
  }
}

const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadTaskHistory()
}

const startEditTaskName = (task) => {
  editingTaskId.value = task.id
  editingTaskName.value = task.original_filename
  // Focus the input in the next tick
  setTimeout(() => {
    editInput.value?.focus()
  }, 0)
}

const saveTaskName = async () => {
  if (!editingTaskId.value || !editingTaskName.value.trim()) {
    cancelEditTaskName()
    return
  }

  try {
    await axios.patch(
      `${API_BASE}/subtitle/tasks/${editingTaskId.value}`,
      {
        original_filename: editingTaskName.value.trim()
      },
      {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    )

    // Update local task data
    const task = taskHistory.value.find(t => t.id === editingTaskId.value)
    if (task) {
      task.original_filename = editingTaskName.value.trim()
    }

    cancelEditTaskName()
  } catch (error) {
    console.error('Failed to update task name:', error)
    alert('更新失败: ' + (error.response?.data?.detail || error.message))
    cancelEditTaskName()
  }
}

const cancelEditTaskName = () => {
  editingTaskId.value = null
  editingTaskName.value = ''
}

const selectHistoryTask = (task) => {
  selectedHistoryTask.value = task
  showResultModal.value = true
  if (task.status === 'processing') {
    startPolling(task.id)
  }
}

const closeResultModal = () => {
  showResultModal.value = false
}

// Subtitle extraction functions
const loadExtractHistory = async () => {
  try {
    const response = await axios.get(
      `${API_BASE}/subtitle-extract/tasks`,
      {
        params: {
          page: extractCurrentPage.value,
          page_size: extractPageSize.value
        },
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    )
    extractTaskHistory.value = response.data.items
    extractTotalPages.value = response.data.total_pages
  } catch (error) {
    console.error('Failed to load extract history:', error)
  }
}

const loadErasureHistory = async () => {
  try {
    const response = await axios.get(
      `${API_BASE}/subtitle/tasks`,
      {
        params: {
          page: extractErasureCurrentPage.value,
          page_size: extractErasurePageSize.value
        },
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    )
    extractErasureHistory.value = response.data.items.filter(task => task.status === 'completed')
    extractErasureTotalPages.value = response.data.total_pages
  } catch (error) {
    console.error('Failed to load erasure history:', error)
  }
}

const handleExtractFileSelect = (event) => {
  const file = event.target.files[0]
  if (file && (file.type.startsWith('video/') || file.type.startsWith('audio/'))) {
    extractFile.value = file
    extractFileObjectUrl.value = URL.createObjectURL(file)
    if (file.type.startsWith('video/')) {
      generateVideoThumbnail(file).then(thumbnail => {
        extractFileThumbnail.value = thumbnail
      })
    }
  }
}

const uploadExtractFile = async () => {
  if (!extractFile.value) return

  extractIsUploading.value = true

  try {
    // Initialize OSS client
    if (!ossClient) {
      await initOSSClient()
    }

    // Generate OSS key
    const timestamp = new Date().toISOString().replace(/[:.]/g, '').slice(0, 15)
    const randomStr = Math.random().toString(36).substring(2, 10)
    const ext = extractFile.value.name.split('.').pop()
    const ossKey = `subtitle_extract/1/${timestamp}_${randomStr}.${ext}`

    // Upload directly using OSS SDK multipart
    const result = await ossClient.multipartUpload(ossKey, extractFile.value, {
      progress: (p) => {
        extractUploadProgress.value = Math.round(p * 100)
      },
      partSize: 30 * 1024 * 1024,
      parallel: 5
    })

    // Get file URL
    const fileUrl = ossClient.signatureUrl(ossKey, { expires: 604800 })

    extractIsUploading.value = false
    extractIsSubmitting.value = true

    // Submit task to backend
    const submitResponse = await axios.post(
      `${API_BASE}/subtitle-extract/submit`,
      {
        oss_key: ossKey,
        original_filename: extractFile.value.name,
        source_type: extractFile.value.type.startsWith('audio') ? 'audio' : 'video'
      },
      {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    )
    
    extractFile.value = null
    extractIsSubmitting.value = false
    await loadExtractHistory()
  } catch (error) {
    console.error('Extract upload failed:', error)
    alert('上传失败: ' + (error.response?.data?.detail || error.message))
    extractIsUploading.value = false
    extractIsSubmitting.value = false
  }
}

const submitExtractFromHistory = async () => {
  if (!extractSelectedErasureTask.value) return
  
  extractIsSubmitting.value = true
  
  try {
    const submitResponse = await axios.post(
      `${API_BASE}/subtitle-extract/submit`,
      {
        oss_key: extractSelectedErasureTask.value.oss_key,
        original_filename: extractSelectedErasureTask.value.original_filename,
        source_type: 'history_video',
        history_task_id: extractSelectedErasureTask.value.id
      },
      {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    )
    
    extractIsSubmitting.value = false
    await loadExtractHistory()
  } catch (error) {
    console.error('Extract from history failed:', error)
    alert('提交失败: ' + (error.response?.data?.detail || error.message))
    extractIsSubmitting.value = false
  }
}

const selectExtractTask = (task) => {
  extractSelectedHistoryTask.value = task
}

const viewSubtitleResult = (task) => {
  selectedExtractTask.value = task
  showSubtitleModal.value = true
}

const closeSubtitleModal = () => {
  showSubtitleModal.value = false
  selectedExtractTask.value = null
}

const formatTime = (milliseconds) => {
  const seconds = Math.floor(milliseconds / 1000)
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const parseSubtitles = (subtitleResult) => {
  try {
    const data = JSON.parse(subtitleResult)
    return data.utterances || []
  } catch {
    return []
  }
}

const downloadSubtitleJson = () => {
  if (!selectedExtractTask.value || !selectedExtractTask.value.subtitle_result) return
  
  const subtitles = parseSubtitles(selectedExtractTask.value.subtitle_result)
  const jsonContent = JSON.stringify(subtitles, null, 2)
  const blob = new Blob([jsonContent], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = `${selectedExtractTask.value.original_filename}_subtitles.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

const changeExtractErasurePage = (page) => {
  extractErasureCurrentPage.value = page
  loadErasureHistory()
}

const refreshExtractErasureHistory = async () => {
  extractIsRefreshing.value = true
  await loadErasureHistory()
  extractIsRefreshing.value = false
}

const changeExtractPage = (page) => {
  extractCurrentPage.value = page
  loadExtractHistory()
}

const refreshExtractHistory = async () => {
  extractIsRefreshing.value = true
  try {
    // First refresh statuses from ATA
    const response = await axios.post(
      `${API_BASE}/subtitle-extract/tasks/refresh-status`,
      extractTaskHistory.value.map(task => task.id),
      {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    )
    // Then reload the history
    await loadExtractHistory()
  } catch (error) {
    console.error('Failed to refresh extract history:', error)
  } finally {
    extractIsRefreshing.value = false
  }
}

const handleTranslationSubtitleFile = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  try {
    const text = await file.text()
    translationSubtitleJson.value = JSON.parse(text)
    translationSubtitleFileName.value = file.name
  } catch (error) {
    translationSubtitleJson.value = null
    translationSubtitleFileName.value = ''
    alert('字幕 JSON 文件格式错误')
  }
}

const loadTranslationHistory = async () => {
  try {
    const response = await axios.get(
      `${API_BASE}/video-translation/tasks`,
      {
        params: {
          is_auto: false,
          page: translationCurrentPage.value,
          page_size: translationPageSize.value
        },
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    )
    translationTaskHistory.value = response.data.items
    translationTotalPages.value = response.data.total_pages
  } catch (error) {
    console.error('Failed to load translation history:', error)
  }
}

const changeTranslationPage = (page) => {
  if (page < 1 || page > translationTotalPages.value) return
  translationCurrentPage.value = page
  loadTranslationHistory()
}

const playTranslationVideo = (task) => {
  if (task.result_video_url) {
    currentVideoUrl.value = task.result_video_url
    showVideoModal.value = true
  } else {
    alert('视频还未生成或生成失败')
  }
}

const submitVideoTranslation = async () => {
  if (!translationVideoFile.value) return

  translationIsSubmitting.value = true
  try {
    // Initialize OSS client
    if (!ossClient) {
      await initOSSClient()
    }

    // Generate OSS key
    const timestamp = new Date().toISOString().replace(/[:.]/g, '').slice(0, 15)
    const randomStr = Math.random().toString(36).substring(2, 10)
    const ext = translationVideoFile.value.name.split('.').pop()
    const ossKey = `video_translation/1/${timestamp}_${randomStr}.${ext}`

    // Upload directly using OSS SDK multipart
    const result = await ossClient.multipartUpload(ossKey, translationVideoFile.value, {
      progress: (p) => {
        translationUploadProgress.value = Math.round(p * 100)
      },
      partSize: 30 * 1024 * 1024,
      parallel: 5
    })

    // Get file URL
    const fileUrl = ossClient.signatureUrl(ossKey, { expires: 604800 })

    // Register media with ICE via backend
    const registerResponse = await axios.post(
      `${API_BASE}/video-translation/register-media`,
      {
        oss_key: ossKey,
        file_url: fileUrl
      },
      {
        headers: { 'Authorization': `Bearer ${authStore.token}` }
      }
    )

    const subtitlePayload = translationSubtitleMode.value === 'upload'
      ? translationSubtitleJson.value
      : null

    await axios.post(
      `${API_BASE}/video-translation/submit`,
      {
        video_oss_key: ossKey,
        media_id: registerResponse.data.media_id,
        video_url: fileUrl,
        original_filename: translationVideoFile.value.name,
        target_language: translationTargetLanguage.value,
        subtitle_source_type: translationSubtitleMode.value === 'upload' ? 'upload' : 'extract_history',
        subtitle_json: subtitlePayload,
        subtitle_extract_task_id: translationSelectedExtractTask.value?.id || null,
        subtitle_params: translationSubtitleParams.value
      },
      {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    )

    translationVideoFile.value = null
    translationSubtitleJson.value = null
    translationSubtitleFileName.value = ''
    translationSelectedExtractTask.value = null
    await loadTranslationHistory()
  } catch (error) {
    console.error('Video translation submit failed:', error)
    alert('视频翻译提交失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    translationIsSubmitting.value = false
  }
}

const viewTask = (task) => {
  currentTask.value = task
  if (task.status === 'processing') {
    startPolling(task.id)
  }
}

const getStatusClass = (status) => {
  const classes = {
    'pending': 'bg-gray-100 text-gray-700',
    'uploading': 'bg-blue-100 text-blue-700',
    'processing': 'bg-yellow-100 text-yellow-700',
    'completed': 'bg-green-100 text-green-700',
    'failed': 'bg-red-100 text-red-700'
  }
  return classes[status] || 'bg-gray-100 text-gray-700'
}

const getStatusText = (status) => {
  const texts = {
    'pending': '等待中',
    'uploading': '上传中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return texts[status] || status
}

const getAutoStatusText = (status, task = null) => {
  // If task has current_stage information, use it
  if (task && task.current_stage) {
    const stageTexts = {
      'queued': '排队中',
      'subtitle_extraction': '字幕提取中',
      'subtitle_erasure': '字幕擦除中',
      'video_translation': '视频翻译中',
      'completed': '已完成'
    }
    return stageTexts[task.current_stage] || '处理中'
  }
  
  // If it's the currently processing task, show the specific stage
  if (status === 'processing' && autoIsProcessing.value) {
    const stepTexts = {
      0: '处理中',
      1: '字幕提取中',
      2: '字幕擦除中',
      3: '视频翻译中',
      4: '已完成'
    }
    return stepTexts[autoProgress.value.step] || '处理中'
  }
  
  // For history records, show the status from backend
  const texts = {
    'pending': '等待中',
    'uploading': '上传中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return texts[status] || status
}

const getAutoStatusClass = (status, task = null) => {
  // If task has current_stage information, use it for color
  if (task && task.current_stage) {
    const stageClasses = {
      'queued': 'bg-gray-100 text-gray-700',
      'subtitle_extraction': 'bg-blue-100 text-blue-700',
      'subtitle_erasure': 'bg-yellow-100 text-yellow-700',
      'video_translation': 'bg-purple-100 text-purple-700',
      'completed': 'bg-green-100 text-green-700'
    }
    return stageClasses[task.current_stage] || getStatusClass(status)
  }
  
  // Otherwise use the standard status class
  return getStatusClass(status)
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Automatic video translation functions
const handleAutoVideoSelect = async (e) => {
  const files = Array.from(e.target.files || []).filter(file => file.type.startsWith('video/'))
  if (files.length > 0) {
    autoVideoFiles.value = [...autoVideoFiles.value, ...files]
    autoPreviewVideoIndex.value = 0
    autoVideoThumbnail.value = await generateVideoThumbnail(autoVideoFiles.value[0])
    // Manage object URL for center preview
    if (autoVideoObjectUrl.value) {
      URL.revokeObjectURL(autoVideoObjectUrl.value)
    }
    autoVideoObjectUrl.value = URL.createObjectURL(autoVideoFiles.value[0])
    e.target.value = ''
  }
}

const confirmAutoVideoUpload = async () => {
  if (autoPendingVideoFiles.value.length === 0) return
  
  try {
    autoIsUploading.value = true
    autoUploadProgress.value = 0
    
    // Initialize OSS client
    if (!ossClient) {
      await initOSSClient()
    }
    
    const filesToUpload = [...autoPendingVideoFiles.value]
    const totalFiles = filesToUpload.length
    let completedFiles = 0

    for (const file of filesToUpload) {
      // Generate OSS key
      const timestamp = new Date().toISOString().replace(/[:.]/g, '').slice(0, 15)
      const randomStr = Math.random().toString(36).substring(2, 10)
      const ext = file.name.split('.').pop()
      const ossKey = `auto_translate/1/${timestamp}_${randomStr}.${ext}`
      
      // Upload video to OSS with progress tracking
      await ossClient.multipartUpload(ossKey, file, {
        progress: (p) => {
          autoUploadProgress.value = Math.round((completedFiles + p) / totalFiles * 100)
        },
        partSize: 30 * 1024 * 1024,
        parallel: 5
      })

      autoUploadedVideos.value.push({ file, ossKey })
      completedFiles++
      autoUploadProgress.value = Math.round(completedFiles / totalFiles * 100)
    }
    
    console.log('Videos uploaded successfully:', autoUploadedVideos.value.map(item => item.ossKey))
    autoIsUploading.value = false
  } catch (error) {
    console.error('Failed to upload video:', error)
    alert('视频上传失败: ' + error.message)
    autoIsUploading.value = false
  }
}

const isAutoVideoFileUploaded = (file) => {
  return autoUploadedVideos.value.some(item => item.file === file)
}

const getAutoVideoFileButtonClass = (file, index) => {
  const isActive = autoPreviewVideoIndex.value === index
  const isUploaded = isAutoVideoFileUploaded(file)

  if (isUploaded) {
    return isActive ? 'bg-indigo-600 text-white' : 'bg-indigo-500 text-white hover:bg-indigo-600'
  }

  return isActive ? 'bg-sky-200 text-sky-900' : 'bg-sky-50 text-sky-700 hover:bg-sky-100'
}

const switchAutoPreviewVideo = async (index) => {
  const file = autoVideoFiles.value[index]
  if (!file) return

  autoPreviewVideoIndex.value = index
  autoVideoThumbnail.value = await generateVideoThumbnail(file)
  if (autoVideoObjectUrl.value) {
    URL.revokeObjectURL(autoVideoObjectUrl.value)
  }
  autoVideoObjectUrl.value = URL.createObjectURL(file)
}

const removeAutoVideoFile = async (index) => {
  const file = autoVideoFiles.value[index]
  autoVideoFiles.value.splice(index, 1)
  autoUploadedVideos.value = autoUploadedVideos.value.filter(item => item.file !== file)

  if (autoVideoFiles.value.length === 0) {
    autoPreviewVideoIndex.value = 0
    autoVideoThumbnail.value = ''
    if (autoVideoObjectUrl.value) {
      URL.revokeObjectURL(autoVideoObjectUrl.value)
    }
    autoVideoObjectUrl.value = ''
    return
  }

  const nextIndex = Math.min(index, autoVideoFiles.value.length - 1)
  await switchAutoPreviewVideo(nextIndex)
}

const clearAutoTranslationState = () => {
  autoVideoFiles.value = []
  autoVideoThumbnail.value = ''
  autoVideoObjectUrl.value = ''
  autoPreviewVideoIndex.value = 0
  autoUploadedVideos.value = []
  autoIsProcessing.value = false
  autoProgress.value = { step: 0, status: '' }
  autoUploadProgress.value = 0
  autoIsUploading.value = false
  autoSubtitleStyleId.value = 'default'
}

const getAutoStepStatus = (step) => {
  const statusMap = {
    0: { 1: '等待中', 2: '等待中', 3: '等待中' },
    1: { 1: '处理中...', 2: '等待中', 3: '等待中' },
    2: { 1: '已完成', 2: '处理中...', 3: '等待中' },
    3: { 1: '已完成', 2: '已完成', 3: '处理中...' },
    4: { 1: '已完成', 2: '已完成', 3: '已完成' }
  }
  return statusMap[autoProgress.value.step]?.[step] || '等待中'
}

const startAutoTranslation = async () => {
  if (autoUploadedVideos.value.length === 0 || autoTargetLanguages.value.length === 0) return

  autoIsProcessing.value = true

  // Show success card immediately
  showSubmitSuccessCard.value = true
  setTimeout(() => {
    showSubmitSuccessCard.value = false
  }, 3000)

  try {
    for (const uploadedVideo of autoUploadedVideos.value) {
      const fileUrl = ossClient.signatureUrl(uploadedVideo.ossKey, { expires: 604800 })

      // Submit auto translation task (will be processed in background)
      await axios.post(
        `${API_BASE}/video-translation/submit-auto`,
        {
          original_filename: uploadedVideo.file.name,
          target_language: autoTargetLanguages.value[0],
          target_languages: autoTargetLanguages.value,
          oss_key: uploadedVideo.ossKey,
          file_url: fileUrl,
          skip_subtitle_erasure: autoSkipSubtitleErasure.value,
          subtitle_params: buildAutoSubtitleParams()
        },
        {
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        }
      )
    }
    
    // Show animation
    showSubmitAnimation.value = true
    
    // Reset form immediately - task will be processed in background
    autoVideoFiles.value = []
    autoVideoThumbnail.value = ''
    autoVideoObjectUrl.value = ''
    autoPreviewVideoIndex.value = 0
    autoUploadedVideos.value = []
    autoProgress.value = { step: 0, status: '' }
    autoUploadProgress.value = 0
    autoTargetLanguages.value = ['en']
    autoSkipSubtitleErasure.value = false
    autoSubtitleStyleId.value = 'default'
    
    // Reload history to show the new task after animation
    setTimeout(async () => {
      await loadAutoTranslationHistory()
      showSubmitAnimation.value = false
    }, 1000)
  } catch (error) {
    console.error('Auto translation failed:', error)
    alert('提交失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    autoIsProcessing.value = false
  }
}

const pollExtractTaskCompletion = async (taskId) => {
  const maxAttempts = 60 // 10 minutes (60 * 10 seconds)
  let attempts = 0

  while (attempts < maxAttempts) {
    try {
      const response = await axios.post(
        `${API_BASE}/subtitle-extract/tasks/refresh-status`,
        [taskId],
        {
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        }
      )

      const task = response.data[0]
      if (task.status === 'completed') {
        return true
      } else if (task.status === 'failed') {
        throw new Error('字幕提取失败: ' + (task.error_message || '未知错误'))
      }

      await new Promise(resolve => setTimeout(resolve, 10000))
      attempts++
    } catch (error) {
      if (attempts >= maxAttempts - 1) throw error
      await new Promise(resolve => setTimeout(resolve, 10000))
      attempts++
    }
  }

  throw new Error('字幕提取超时')
}

const pollEraseTaskCompletion = async (taskId) => {
  const maxAttempts = 60 // 10 minutes
  let attempts = 0

  while (attempts < maxAttempts) {
    try {
      const response = await axios.post(
        `${API_BASE}/subtitle/tasks/refresh-status`,
        [taskId],
        {
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        }
      )

      const task = response.data[0]
      if (task.status === 'completed') {
        return true
      } else if (task.status === 'failed') {
        throw new Error('字幕擦除失败: ' + (task.error_message || '未知错误'))
      }

      await new Promise(resolve => setTimeout(resolve, 10000))
      attempts++
    } catch (error) {
      if (attempts >= maxAttempts - 1) throw error
      await new Promise(resolve => setTimeout(resolve, 10000))
      attempts++
    }
  }

  throw new Error('字幕擦除超时')
}

const loadAutoTranslationHistory = async () => {
  try {
    const response = await axios.get(
      `${API_BASE}/video-translation/tasks`,
      {
        params: {
          is_auto: true,
          page: autoCurrentPage.value,
          page_size: autoPageSize.value
        },
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    )
    autoTaskHistory.value = response.data.items
    autoTotalPages.value = response.data.total_pages
  } catch (error) {
    console.error('Failed to load auto translation history:', error)
  }
}

const playAutoTranslationVideo = (task, languageCode = null) => {
  const playableResult = languageCode
    ? task.language_results?.[languageCode]
    : getCompletedLanguageResults(task)[0]
  const videoUrl = playableResult?.result_video_url || task.result_video_url
  if (videoUrl) {
    currentVideoUrl.value = videoUrl
    currentPlayingTask.value = task
    currentPlayingLanguage.value = playableResult?.code || languageCode
    autoSelectedHistoryTask.value = null
    // 不再使用弹窗，直接在中间预览区域播放
  } else {
    currentVideoUrl.value = ''
    currentPlayingTask.value = null
    currentPlayingLanguage.value = null
    autoSelectedHistoryTask.value = task
  }
}

const switchVideoLanguage = (languageCode) => {
  if (!currentPlayingTask.value) return
  const result = currentPlayingTask.value.language_results?.[languageCode]
  if (result?.result_video_url) {
    currentVideoUrl.value = result.result_video_url
    currentPlayingLanguage.value = languageCode
  }
}

const changeAutoPage = (page) => {
  if (page < 1 || page > autoTotalPages.value) return
  autoCurrentPage.value = page
  loadAutoTranslationHistory()
}

const startEditAutoTaskName = (task) => {
  editingAutoTaskId.value = task.id
  editingAutoTaskName.value = task.original_filename
  setTimeout(() => {
    autoEditInput.value?.focus()
  }, 0)
}

const saveAutoTaskName = async () => {
  if (!editingAutoTaskId.value || !editingAutoTaskName.value.trim()) {
    cancelEditAutoTaskName()
    return
  }

  try {
    await axios.patch(
      `${API_BASE}/video-translation/tasks/${editingAutoTaskId.value}`,
      {
        original_filename: editingAutoTaskName.value.trim()
      },
      {
        headers: {
          'Authorization': `Bearer ${authStore.token}`
        }
      }
    )

    const task = autoTaskHistory.value.find(t => t.id === editingAutoTaskId.value)
    if (task) {
      task.original_filename = editingAutoTaskName.value.trim()
    }

    cancelEditAutoTaskName()
  } catch (error) {
    console.error('Failed to update auto task name:', error)
    alert('更新失败: ' + (error.response?.data?.detail || error.message))
    cancelEditAutoTaskName()
  }
}

const cancelEditAutoTaskName = () => {
  editingAutoTaskId.value = null
  editingAutoTaskName.value = ''
}

const refreshAutoTranslationHistory = async () => {
  autoIsRefreshing.value = true
  try {
    // First refresh statuses from backend
    const taskIds = autoTaskHistory.value.map(task => task.id)
    
    if (taskIds.length > 0) {
      await axios.post(
        `${API_BASE}/video-translation/tasks/refresh-status`,
        taskIds,
        {
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        }
      )
    }
    
    // Reload history to get updated data
    await loadAutoTranslationHistory()
  } catch (error) {
    console.error('Failed to refresh auto translation history:', error)
  } finally {
    autoIsRefreshing.value = false
  }
}

onMounted(() => {
  loadAutoTranslationHistory()
  fetchUserPoints()
})
</script>
