<template>
  <div class="min-h-screen bg-white w-screen h-screen overflow-hidden relative">

    <!-- Mobile Header -->
    <MobileHeader
      v-if="!isDesktop"
      :title="getFeatureTitle()"
      @toggle-menu="layoutStore.toggleMobileMenu"
      @toggle-config="layoutStore.toggleConfigSidebar"
    />

    <!-- Mobile Navigation Drawer -->
    <MobileDrawer
      :is-open="layoutStore.isMobileMenuOpen"
      title="导航"
      position="left"
      width="narrow"
      @close="layoutStore.closeAllSidebars"
    >
      <div class="space-y-1.5">
        <button @click="navigateToFeature('auto-video-translate'); layoutStore.closeAllSidebars()" :class="['w-full text-left px-3 py-2 rounded-md text-sm', currentFeature === 'auto-video-translate' ? 'bg-indigo-100 text-indigo-700' : 'hover:bg-gray-100']">视频翻译（自动版）</button>
        <button @click="navigateToFeature('subtitle-erase'); layoutStore.closeAllSidebars()" :class="['w-full text-left px-3 py-2 rounded-md text-sm', currentFeature === 'subtitle-erase' ? 'bg-indigo-100 text-indigo-700' : 'hover:bg-gray-100']">字幕擦除</button>
        <button @click="navigateToFeature('subtitle-extract'); layoutStore.closeAllSidebars()" :class="['w-full text-left px-3 py-2 rounded-md text-sm', currentFeature === 'subtitle-extract' ? 'bg-indigo-100 text-indigo-700' : 'hover:bg-gray-100']">字幕提取</button>
        <button @click="navigateToFeature('subtitle-embed'); layoutStore.closeAllSidebars()" :class="['w-full text-left px-3 py-2 rounded-md text-sm', currentFeature === 'subtitle-embed' ? 'bg-indigo-100 text-indigo-700' : 'hover:bg-gray-100']">视频翻译（手动）</button>
        <button @click="navigateToFeature('image-translate'); layoutStore.closeAllSidebars()" :class="['w-full text-left px-3 py-2 rounded-md text-sm', currentFeature === 'image-translate' ? 'bg-indigo-100 text-indigo-700' : 'hover:bg-gray-100']">图片翻译</button>
      </div>
    </MobileDrawer>

    <!-- Floating User Info Card (Bottom Left) -->
    <div class="fixed bottom-4 left-4 z-50">
      <!-- Collapsed Circle -->
      <div v-if="!isUserCardExpanded" @click="isUserCardExpanded = true" class="w-14 h-14 bg-indigo-600 rounded-full shadow-lg flex items-center justify-center cursor-pointer hover:bg-indigo-700 transition">
        <span class="text-white text-lg font-semibold">{{ authStore.isAuthenticated ? (authStore.user?.username?.[0]?.toUpperCase() || 'U') : 'L' }}</span>
      </div>

      <!-- Expanded Card -->
      <div v-else class="relative">
        <div v-if="!authStore.isAuthenticated" class="bg-white rounded-xl border border-gray-200 shadow-lg p-4 min-w-[200px]">
          <button @click="isUserCardExpanded = false" class="absolute top-2 right-2 w-6 h-6 flex items-center justify-center text-gray-400 hover:text-gray-600 transition">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <button @click="showLoginModal = true" class="w-full py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition">
            登录
          </button>
        </div>
        <div v-else class="bg-white rounded-xl border border-gray-200 shadow-lg p-4 min-w-[200px]">
          <button @click="isUserCardExpanded = false" class="absolute top-2 right-2 w-6 h-6 flex items-center justify-center text-gray-400 hover:text-gray-600 transition">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1">账号</p>
            <p class="text-sm font-medium text-gray-900 truncate">{{ authStore.user?.username || '用户' }}</p>
          </div>
          <div class="mb-3">
            <p class="text-xs text-gray-500 mb-1">积分</p>
            <p class="text-sm font-medium text-gray-900">{{ userPoints || 0 }}</p>
          </div>
          <button @click="showGiftCardModal = true" class="w-full py-2 mb-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition">
            点卡兑换
          </button>
          <button @click="handleLogout" class="w-full py-2 bg-gray-100 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-200 transition">
            退出登录
          </button>
        </div>
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
    <main :class="['w-screen h-screen', !isDesktop ? 'pt-14' : '']">
      <!-- Subtitle Erase Feature (Four-column) -->
      <div v-if="currentFeature === 'subtitle-erase'" class="flex min-h-screen">
        <!-- Left Process Config Column -->
        <aside v-if="isDesktop" class="w-72 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-3 flex">
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
        <aside :class="['border-l border-gray-200 bg-gray-50 p-3 space-y-3', isDesktop ? 'w-80' : 'w-full']">
          <!-- Upload Card -->
          <div class="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
              <h3 class="text-sm font-medium text-gray-900">待擦除字幕视频</h3>
            </div>
            <div class="p-4">
              <div class="relative">
                <el-upload
                  ref="uploadRef"
                  v-model:file-list="fileList"
                  :auto-upload="false"
                  :on-change="handleFileSelect"
                  :on-remove="handleFileRemove"
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
        <!-- Left Process Config Column -->
        <aside v-if="isDesktop" class="w-72 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-3 flex">
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
        <!-- Left Process Config Column -->
        <aside v-if="isDesktop" class="w-72 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-3 flex">
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
                  <option v-for="language in LANGUAGE_OPTIONS" :key="language.code" :value="language.code">{{ language.name }}（{{ language.voice }} · {{ language.gender }}）</option>
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
      <div v-else-if="currentFeature === 'auto-video-translate'" class="flex h-full overflow-hidden">
        <!-- Left Process Config Column -->
        <aside v-if="isDesktop" class="w-96 2xl:w-[420px] flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-3 overflow-y-auto max-h-screen flex">
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

              <label class="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-3 py-2">
                <div>
                  <div class="text-xs font-medium text-gray-800">全屏字幕擦除</div>
                  <div class="text-[10px] text-gray-400">开启后使用全屏擦除模式（推荐）</div>
                </div>
                <input
                  v-model="autoFullScreenErase"
                  type="checkbox"
                  :disabled="autoIsProcessing || autoSkipSubtitleErasure"
                  class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
              </label>

              <label class="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-3 py-2">
                <div>
                  <div class="text-xs font-medium text-gray-800">关闭字幕显示</div>
                  <div class="text-[10px] text-gray-400">渲染时不显示翻译后的字幕</div>
                </div>
                <input
                  v-model="autoHideSubtitles"
                  type="checkbox"
                  :disabled="autoIsProcessing"
                  class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                />
              </label>

              <label class="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 opacity-60">
                <div>
                  <div class="text-xs font-medium text-gray-800">口播连续版</div>
                  <div class="text-[10px] text-gray-400">即将上线</div>
                </div>
                <input
                  v-model="autoContinuousDubbing"
                  type="checkbox"
                  disabled
                  class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-not-allowed"
                />
              </label>

              <button @click="startAutoTranslation" :disabled="autoIsProcessing || autoUploadedVideos.length === 0 || autoTargetLanguages.length === 0" :title="autoUploadedVideos.length === 0 ? '请先确认上传视频' : autoTargetLanguages.length === 0 ? '请至少选择一种目标语言' : ''" class="w-full py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
                {{ autoIsProcessing ? '处理中...' : `提交 (消耗${autoTranslationPointCost}积分)` }}
              </button>

              <div class="pt-1">
                <div class="flex items-center justify-between mb-2">
                  <label class="block text-[11px] text-gray-500">目标语言和音色</label>
                  <span class="text-[11px] text-indigo-600">已选 {{ autoTargetLanguages.length }} 门</span>
                </div>
                <div class="text-[10px] text-gray-500 mb-2">点击语言卡片选择该语言，点击"选择音色"按钮为该语言选择音色（选择后会记住）</div>
                <div class="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-1">
                  <div
                    v-for="language in LANGUAGE_OPTIONS"
                    :key="language.code"
                    class="relative"
                  >
                    <div
                      class="w-full px-2.5 py-2 rounded-lg border text-left text-xs transition"
                      :class="autoTargetLanguages.includes(language.code) ? 'border-indigo-500 bg-indigo-50 text-indigo-700 shadow-sm' : 'border-gray-200 bg-white text-gray-700'"
                    >
                      <div class="flex items-start justify-between mb-1">
                        <button
                          type="button"
                          @click="toggleAutoTargetLanguage(language.code)"
                          class="flex-1 text-left"
                        >
                          <span class="font-medium">{{ language.name }}</span>
                        </button>
                        <!-- 试听按钮 -->
                        <button
                          type="button"
                          @click.stop="playLanguageVoice(language.code)"
                          class="w-5 h-5 flex items-center justify-center rounded-full bg-white border border-gray-300 hover:bg-indigo-50 hover:border-indigo-400 transition shadow-sm flex-shrink-0"
                          :class="currentPlayingLanguage === language.code ? 'bg-indigo-100 border-indigo-500' : ''"
                          title="试听"
                        >
                          <svg v-if="currentPlayingLanguage === language.code" class="w-2.5 h-2.5 text-indigo-600" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                          </svg>
                          <svg v-else class="w-2.5 h-2.5 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M8 5v14l11-7z"/>
                          </svg>
                        </button>
                      </div>
                      <div class="text-[10px] opacity-70 mb-1">
                        <template v-if="customVoiceMap[language.code]">
                          {{ customVoiceMap[language.code].name }} · {{ customVoiceMap[language.code].gender === 'male' ? '男声' : customVoiceMap[language.code].gender === 'female' ? '女声' : '其他' }}
                          <span class="text-indigo-600">（自定义）</span>
                        </template>
                        <template v-else>
                          {{ language.voice }} · {{ language.gender }}
                        </template>
                      </div>
                      <!-- 所有语言都显示选择音色按钮 -->
                      <button
                        type="button"
                        @click.stop="openVoiceModalForLanguage(language.code)"
                        :disabled="autoIsProcessing"
                        class="w-full px-2 py-0.5 text-[10px] rounded border transition disabled:opacity-50 disabled:cursor-not-allowed"
                        :class="customVoiceMap[language.code] ? 'border-indigo-400 bg-indigo-50 text-indigo-700' : 'border-gray-300 bg-white text-gray-600 hover:bg-gray-50'"
                      >
                        {{ customVoiceMap[language.code] ? '更换音色' : '选择音色' }}
                      </button>
                    </div>
                  </div>
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

              <div class="pt-1">
                <label class="block text-[11px] text-gray-500 mb-1">任务标签</label>
                <div class="flex gap-2">
                  <input
                    type="text"
                    v-model="autoTagInput"
                    @keyup.enter="addAutoTag"
                    placeholder="输入标签按回车添加"
                    :disabled="autoIsProcessing"
                    class="flex-1 px-2 py-1.5 border border-gray-300 rounded-md bg-white text-xs focus:outline-none focus:ring-2 focus:ring-indigo-600 disabled:opacity-50"
                  />
                  <button
                    type="button"
                    @click="addAutoTag"
                    :disabled="autoIsProcessing || !autoTagInput.value || !autoTagInput.value.trim()"
                    class="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md text-xs font-medium hover:bg-gray-200 transition disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    添加
                  </button>
                </div>
                <div v-if="autoTaskTags.length > 0" class="flex flex-wrap gap-1.5 mt-2">
                  <span
                    v-for="tag in autoTaskTags"
                    :key="tag"
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-[10px]"
                  >
                    {{ tag }}
                    <button
                      type="button"
                      @click="removeAutoTag(tag)"
                      :disabled="autoIsProcessing"
                      class="hover:text-indigo-900 disabled:opacity-50"
                    >
                      ×
                    </button>
                  </span>
                </div>
                <div v-if="autoSavedTags.length > 0 && autoTaskTags.length === 0" class="mt-2">
                  <div class="text-[10px] text-gray-400 mb-1">快捷选择：</div>
                  <div class="flex flex-wrap gap-1">
                    <button
                      type="button"
                      v-for="tag in autoSavedTags.slice(0, 6)"
                      :key="tag"
                      @click="selectSavedTag(tag)"
                      :disabled="autoIsProcessing"
                      class="px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 text-[10px] hover:bg-gray-200 transition disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {{ tag }}
                    </button>
                  </div>
                </div>
              </div>

              <div class="pt-1">
                <label class="block text-[11px] text-gray-500 mb-1">字体大小</label>
                <input
                  type="number"
                  v-model.number="autoFontSize"
                  :disabled="autoIsProcessing"
                  @input="updateSubtitlePreview"
                  class="w-full px-2 py-1.5 border border-gray-300 rounded-md bg-white text-xs focus:outline-none focus:ring-2 focus:ring-indigo-600 disabled:opacity-50"
                />
                <div v-if="autoPreviewVideoRef && autoPreviewVideoRef.videoHeight" class="text-[10px] text-gray-400 mt-1">
                  视频分辨率: {{ autoPreviewVideoRef.videoWidth }}x{{ autoPreviewVideoRef.videoHeight }}
                  <br>预览字体: {{ subtitlePreviewFontSize }}px
                </div>
              </div>

              <div class="pt-1">
                <div class="flex items-center justify-between mb-1">
                  <label class="block text-[11px] text-gray-500">字幕位置（距底部）</label>
                  <span class="text-[11px] text-indigo-600">{{ subtitleBottomPosition }}%</span>
                </div>
                <input
                  type="range"
                  v-model.number="subtitleBottomPosition"
                  min="0"
                  max="40"
                  step="1"
                  :disabled="autoIsProcessing"
                  class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600 disabled:opacity-50"
                />
                <div class="flex justify-between text-[10px] text-gray-400 mt-1">
                  <span>底部</span>
                  <span>中间</span>
                </div>
              </div>

              <div class="pt-1">
                <label class="flex items-center justify-between rounded-lg border border-gray-200 bg-white px-3 py-2">
                  <div>
                    <div class="text-xs font-medium text-gray-800">显示字幕预览</div>
                    <div class="text-[10px] text-gray-400">在视频上预览字幕效果</div>
                  </div>
                  <input
                    v-model="showSubtitlePreview"
                    type="checkbox"
                    :disabled="autoIsProcessing || !autoVideoObjectUrl"
                    class="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                </label>
              </div>

              <!-- Test Version Toggle -->
              <div class="mt-2 flex items-center justify-center">
                <label class="flex items-center space-x-1.5 cursor-pointer">
                  <input
                    v-model="useTestVersion"
                    type="checkbox"
                    :disabled="autoIsProcessing"
                    class="h-3 w-3 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span class="text-xs text-gray-600">启用测试版本</span>
                </label>
              </div>
            </div>
          </div>
        </aside>

        <!-- Center Workspace -->
        <section class="flex-1 bg-white relative overflow-y-auto h-full">
          <div class="w-full flex flex-col items-center justify-start p-6 pt-10 2xl:pt-16 pb-20">
            <div class="relative">
              <!-- Two videos side by side when viewing history -->
              <ResponsiveVideoContainer
                v-if="autoSelectedHistoryTask"
                show-comparison
                :original-video-url="autoSelectedHistoryTask.original_video_url"
                :translated-video-url="autoSelectedHistoryTask.result_video_url"
                original-label="原视频"
                :translated-label="getSelectedTaskLanguageName(autoSelectedHistoryTask)"
              >
                <template #original-placeholder>
                  <div class="text-center">
                    <div class="text-gray-400 text-sm mb-1">无原视频链接</div>
                    <div class="text-gray-400 text-xs">原视频未保存</div>
                  </div>
                </template>
                <template #translated-placeholder>
                  <div class="text-center">
                    <div class="text-sm" :class="autoSelectedHistoryTask.status === 'failed' ? 'text-red-600' : 'text-indigo-600'">
                      {{ autoSelectedHistoryTask.status === 'failed' ? '视频生成失败' : '视频还在生成中' }}
                    </div>
                    <div class="text-xs text-gray-500 mt-1">{{ getAutoStatusText(autoSelectedHistoryTask.status, autoSelectedHistoryTask) }}</div>
                  </div>
                </template>
              </ResponsiveVideoContainer>
              <!-- Single video for uploaded video preview with subtitle overlay -->
              <div v-else-if="autoVideoObjectUrl" class="inline-block">
                <!-- 9:16 响应式比例容器 -->
                <div class="relative bg-black rounded-lg shadow overflow-hidden w-[340px] md:w-[360px] 2xl:w-[420px]" style="aspect-ratio: 9/16;">
                  <!-- 视频层 -->
                  <video
                    ref="autoPreviewVideoRef"
                    :src="autoVideoObjectUrl"
                    controls
                    class="absolute inset-0 w-full h-full object-contain"
                    @loadedmetadata="onVideoLoaded"
                  ></video>

                  <!-- 字幕预view层 -->
                  <div
                    v-if="showSubtitlePreview"
                    class="absolute left-0 right-0 pointer-events-none text-center"
                    :style="{
                      top: `${100 - subtitleBottomPosition}%`,
                      fontSize: `${subtitlePreviewFontSize}px`
                    }"
                  >
                    <div
                      class="inline-block px-4 py-2 font-bold"
                      :style="getSubtitlePreviewStyle()"
                    >
                      示例字幕文本
                    </div>
                  </div>

                  <!-- 拖拽控制层 -->
                  <div
                    v-if="showSubtitlePreview"
                    class="absolute left-0 right-0 cursor-ns-resize flex items-center justify-center"
                    :style="{
                      top: `${100 - subtitleBottomPosition}%`,
                      height: '60px',
                      transform: 'translateY(-50%)'
                    }"
                    @mousedown="startDragSubtitle"
                  >
                    <div class="bg-indigo-500 bg-opacity-80 text-white px-3 py-1 rounded-full text-xs flex items-center gap-2 shadow-lg">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                      </svg>
                      <span>拖动调整位置</span>
                    </div>
                  </div>
                </div>
              </div>
              <!-- Single video for history (translated only) when not selected -->
              <video v-else-if="currentVideoUrl" :src="currentVideoUrl" controls autoplay class="max-w-[80%] max-h-[70vh] rounded-lg shadow"></video>
              <div v-else class="text-gray-400 text-sm">暂无视频</div>
            </div>
            <div v-if="!currentVideoUrl && !autoSelectedHistoryTask && autoVideoFiles.length > 0" class="mt-4 w-[340px] md:w-[360px] 2xl:w-[420px]">
              <div class="flex items-center justify-between mb-3">
                <span class="text-sm font-semibold text-gray-800">待上传视频</span>
                <span class="text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-1 rounded-full">{{ autoPreviewVideoIndex + 1 }} / {{ autoVideoFiles.length }}</span>
              </div>
              <div class="flex flex-wrap gap-2">
                <div
                  v-for="(file, index) in autoVideoFiles"
                  :key="`${file.name}-${index}`"
                  class="group relative flex-1 min-w-[140px]"
                >
                  <button
                    type="button"
                    @click="switchAutoPreviewVideo(index)"
                    class="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg transition-all duration-200 text-left"
                    :class="getAutoVideoFileButtonClass(file, index) === 'bg-indigo-600 text-white'
                      ? 'bg-indigo-600 text-white shadow-md'
                      : getAutoVideoFileButtonClass(file, index).includes('bg-green-50')
                      ? 'bg-green-50 text-green-700 border border-green-200'
                      : 'bg-white text-gray-700 border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50/50'"
                    :title="file.name"
                  >
                    <div class="flex-shrink-0">
                      <svg class="w-5 h-5" :class="getAutoVideoFileButtonClass(file, index) === 'bg-indigo-600 text-white' ? 'text-white' : getAutoVideoFileButtonClass(file, index).includes('bg-green-50') ? 'text-green-600' : 'text-gray-400'" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium truncate">{{ file.name }}</p>
                      <p class="text-xs mt-0.5" :class="getAutoVideoFileButtonClass(file, index) === 'bg-indigo-600 text-white' ? 'text-indigo-100' : 'text-gray-500'">
                        {{ (file.size / 1024 / 1024).toFixed(2) }} MB
                      </p>
                    </div>
                    <div v-if="getAutoVideoFileButtonClass(file, index).includes('bg-green-50')" class="flex-shrink-0">
                      <svg class="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  </button>
                  <button
                    type="button"
                    @click.stop="removeAutoVideoFile(index)"
                    class="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-white shadow-md hover:bg-red-600 transition-all opacity-0 group-hover:opacity-100"
                    title="删除"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              <button
                type="button"
                @click="confirmAutoVideoUpload"
                :disabled="autoIsUploading || autoPendingVideoFiles.length === 0"
                class="mt-4 w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition-all duration-200 hover:bg-indigo-700 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:shadow-none"
              >
                <span v-if="autoIsUploading" class="flex items-center justify-center gap-2">
                  <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  上传中... {{ autoUploadProgress }}%
                </span>
                <span v-else>{{ autoUploadedVideos.length > 0 ? '继续上传' : '确认上传' }}</span>
              </button>
              <div v-if="autoUploadedVideos.length > 0" class="mt-3 flex items-center justify-center gap-2 text-xs text-green-600 bg-green-50 px-3 py-2 rounded-lg">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                已上传 {{ autoUploadedVideos.length }} 个视频，待上传 {{ autoPendingVideoFiles.length }} 个视频
              </div>
            </div>
            <!-- Language Switcher for Multi-language Videos -->
            <div v-if="currentPlayingTask && getCompletedLanguageResults(currentPlayingTask).length > 1" class="mt-4 pt-4 border-t border-gray-200 w-[340px] md:w-[360px] 2xl:w-[420px]">
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
        <aside class="w-full lg:w-96 2xl:w-[420px] border-l border-gray-200 bg-gray-50 p-3 space-y-3 overflow-y-auto h-full pb-10">
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
                  <p class="text-gray-900 text-xs font-medium text-center">待上传 {{ autoVideoFiles.length }} 个视频</p>
                </div>
              </div>
            </div>
          </div>

          <!-- History Card -->
          <div
            class="bg-white rounded-xl border border-gray-200 shadow-sm transition-all duration-200 flex flex-col"
            :class="isHistoryExpanded ? 'fixed inset-6 z-40' : 'max-h-[calc(100vh-240px)]'"
          >
            <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between shrink-0">
              <h3 class="text-sm font-medium text-gray-900">自动翻译记录</h3>
              <div class="flex gap-1">
                <button @click="isHistoryExpanded = !isHistoryExpanded" class="p-1.5 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-md transition" :title="isHistoryExpanded ? '收起' : '展开'">
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" /></svg>
                </button>
                <button @click="refreshAutoTranslationHistory" class="p-1.5 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-md transition" :class="{ 'animate-spin': autoIsRefreshing }" title="刷新">
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
                </button>
              </div>
            </div>
            <div class="p-3 flex-1 overflow-y-auto min-h-0">
              <div v-if="autoAvailableTags.length > 0 || autoTagSearchQuery || autoFilterTag" class="mb-3">
                <div class="mb-2 flex items-center justify-between gap-2">
                  <div class="text-[11px] text-gray-500">按标签筛选：</div>
                  <button
                    v-if="autoTagSearchQuery || autoShowAllTags"
                    type="button"
                    @click="showRecentAutoTags"
                    class="text-[10px] font-medium text-indigo-600 hover:text-indigo-700"
                  >
                    最近标签
                  </button>
                  <button
                    v-else
                    type="button"
                    @click="showAllAutoTags"
                    class="text-[10px] font-medium text-indigo-600 hover:text-indigo-700"
                  >
                    查看全部标签
                  </button>
                </div>
                <div class="relative mb-2">
                  <input
                    v-model="autoTagSearchQuery"
                    type="text"
                    placeholder="搜索标签，如：永"
                    class="w-full rounded-md border border-gray-200 bg-white py-1.5 pl-7 pr-7 text-[11px] text-gray-700 placeholder:text-gray-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                    @keydown.enter.prevent="selectFirstMatchedAutoTag"
                  />
                  <svg class="absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-4.35-4.35m1.35-5.65a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  <button
                    v-if="autoTagSearchQuery"
                    type="button"
                    @click="clearAutoTagSearch"
                    class="absolute right-1.5 top-1/2 flex h-5 w-5 -translate-y-1/2 items-center justify-center rounded-full text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
                    title="清空搜索"
                  >
                    <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div v-if="autoFilterTag" class="mb-2 inline-flex items-center gap-1 rounded-full bg-indigo-50 px-2 py-1 text-[10px] text-indigo-700">
                  当前标签：{{ autoFilterTag.name }}
                  <button type="button" @click="selectAutoTag(null)" class="font-semibold text-indigo-500 hover:text-indigo-700">×</button>
                </div>
                <div v-if="autoTagSearchQuery" class="mb-2 text-[10px] text-gray-400">匹配 {{ autoAvailableTags.length }}/{{ autoTagTotal }} 个标签，按 Enter 选择第一个</div>
                <div v-else-if="autoShowAllTags" class="mb-2 text-[10px] text-gray-400">全部标签 {{ autoAvailableTags.length }}/{{ autoTagTotal }}</div>
                <div v-else class="mb-2 text-[10px] text-gray-400">最近使用标签</div>
                <div class="flex flex-wrap gap-1.5 overflow-y-auto pr-1" :class="autoShowAllTags || autoTagSearchQuery ? 'max-h-44' : 'max-h-24'">
                  <button
                    type="button"
                    @click="selectAutoTag(null)"
                    class="px-2.5 py-1 rounded-full text-[10px] transition"
                    :class="!autoFilterTag ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
                  >
                    全部
                  </button>
                  <button
                    v-for="tag in autoDisplayedTags"
                    :key="tag.id"
                    type="button"
                    @click="selectAutoTag(tag)"
                    class="px-2.5 py-1 rounded-full text-[10px] transition"
                    :class="autoFilterTag?.id === tag.id ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
                  >
                    {{ tag.name }}<span class="ml-1 opacity-70">{{ tag.usage_count }}</span>
                  </button>
                </div>
                <div v-if="autoAvailableTags.length === 0 && autoTagSearchQuery.trim()" class="rounded-md bg-gray-50 px-3 py-2 text-center text-[11px] text-gray-400">
                  未找到匹配标签
                </div>
              </div>
              <div class="mb-3">
                <div class="text-[11px] text-gray-500 mb-2">按语言筛选：</div>
                <select
                  v-model="autoFilterLanguage"
                  class="w-full px-2 py-1.5 border border-gray-300 rounded-md bg-white text-xs focus:outline-none focus:ring-2 focus:ring-indigo-600"
                >
                  <option value="">全部语言</option>
                  <option
                    v-for="lang in LANGUAGE_OPTIONS"
                    :key="lang.code"
                    :value="lang.code"
                  >
                    {{ lang.name }}
                  </option>
                </select>
              </div>
              <div v-if="autoExpandedHistory.length > 0" class="mb-3 rounded-lg border border-gray-100 bg-gray-50/80 p-2">
                <div class="flex flex-wrap items-center justify-between gap-2">
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      @click="toggleSelectAllAutoHistory"
                      class="px-2.5 py-1 rounded-md border text-[11px] font-medium transition"
                      :class="isAutoCurrentPageFullySelected ? 'border-indigo-600 bg-indigo-600 text-white shadow-sm' : 'border-gray-200 bg-white text-gray-700 hover:border-indigo-300 hover:text-indigo-600'"
                    >
                      {{ isAutoCurrentPageFullySelected ? '取消' : '全选' }}
                    </button>
                    <span class="text-[10px] text-gray-500">已选 {{ autoSelectedHistoryItems.length }}/{{ autoExpandedHistory.length }}</span>
                  </div>
                  <button
                    type="button"
                    @click="downloadSelectedAutoHistory"
                    :disabled="autoDownloadableSelectedHistoryItems.length === 0 || autoIsDownloadingSelected"
                    class="px-2.5 py-1 rounded-md bg-green-50 text-[11px] font-medium text-green-700 transition hover:bg-green-100 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {{ autoIsDownloadingSelected ? '打包中...' : '下载选中' }}<span v-if="autoDownloadableSelectedHistoryItems.length > 0 && !autoIsDownloadingSelected">({{ autoDownloadableSelectedHistoryItems.length }})</span>
                  </button>
                </div>
              </div>
              <div v-if="autoExpandedHistory.length === 0" class="text-center py-6 text-gray-400 text-xs">暂无自动翻译记录</div>
              <div v-else :class="isHistoryExpanded ? 'grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] items-start gap-3 pr-1 pb-3' : 'space-y-2.5'">
                <div
                  v-for="item in autoExpandedHistory"
                  :key="item.id"
                  @click="playExpandedVideo(item)"
                  class="relative overflow-hidden rounded-lg border cursor-pointer hover:border-indigo-400 transition"
                  :class="[isHistoryExpanded ? 'p-0' : 'p-2.5', isAutoHistoryItemSelected(item) ? 'border-indigo-500 bg-indigo-50/40 ring-2 ring-indigo-200 shadow-sm' : 'border-gray-200 bg-white']"
                >
                  <div v-if="isHistoryExpanded && (item.result_video_url || item.videoUrl)" class="w-full rounded-t-lg overflow-hidden flex items-center justify-center bg-gray-50">
                    <video
                      :src="item.result_video_url || item.videoUrl"
                      controls
                      preload="metadata"
                      class="max-w-full h-auto block"
                      @click.stop
                    ></video>
                  </div>
                  <div v-else-if="isHistoryExpanded && autoHistoryThumbnails[item.id]" class="w-full rounded-t-lg overflow-hidden flex items-center justify-center bg-gray-50">
                    <img :src="autoHistoryThumbnails[item.id]" class="max-w-full h-auto block" />
                  </div>
                  <div class="relative z-10" :class="isHistoryExpanded ? 'p-2.5' : ''">
                  <div class="flex justify-between items-start gap-2">
                    <button
                      type="button"
                      @click.stop="toggleAutoHistoryItemSelection(item)"
                      class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border transition"
                      :class="isAutoHistoryItemSelected(item) ? 'border-indigo-600 bg-indigo-600 text-white shadow-sm' : 'border-gray-300 bg-white text-transparent hover:border-indigo-400 hover:text-indigo-300'"
                      :title="isAutoHistoryItemSelected(item) ? '取消选中' : '选中任务'"
                    >
                      <svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                      </svg>
                    </button>
                    <div class="flex-1 min-w-0">
                      <p v-if="editingAutoTaskId !== item.taskId" class="text-gray-900 text-xs font-medium truncate">{{ item.original_filename }}</p>
                      <input v-else v-model="editingAutoTaskName" @click.stop @blur="saveAutoTaskName" @keyup.enter="saveAutoTaskName" @keyup.esc="cancelEditAutoTaskName" ref="autoEditInput" class="text-gray-900 text-xs font-medium w-full border border-indigo-400 rounded px-1 py-0.5 focus:outline-none focus:ring-2 focus:ring-indigo-200" />
                      <p class="text-gray-500 text-[11px] mt-1">{{ formatDate(item.created_at) }}</p>
                      <p class="text-indigo-600 text-[11px] mt-0.5 font-medium">{{ item.languageName }}</p>
                    </div>
                    <div class="flex flex-col items-end gap-1 shrink-0">
                      <button @click.stop="startEditAutoTaskName({ id: item.taskId, original_filename: item.original_filename })" class="px-2 py-0.5 text-[10px] text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded transition" title="编辑名称">
                        编辑
                      </button>
                      <a v-if="item.result_video_url || item.videoUrl" :href="item.result_video_url || item.videoUrl" download @click.stop class="px-2 py-0.5 text-[10px] text-green-600 bg-green-50 hover:bg-green-100 rounded transition" title="下载视频">
                        下载
                      </a>
                      <span class="px-2 py-0.5 rounded-full text-[11px] font-medium shrink-0" :class="getAutoStatusClass(item.status, item)">{{ getAutoStatusText(item.status, item) }}</span>
                    </div>
                  </div>
                  <div v-if="item.tags && item.tags.length > 0" class="flex flex-wrap gap-1 mt-2">
                    <span
                      v-for="tag in item.tags"
                      :key="tag"
                      class="px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 text-[10px]"
                    >
                      {{ tag }}
                    </span>
                  </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Pagination Controls for Auto Translation History - Fixed at bottom -->
            <div class="flex justify-between items-center px-3 py-2 border-t border-gray-100 shrink-0 bg-white">
              <button @click="changeAutoPage(autoCurrentPage - 1)" :disabled="autoCurrentPage === 1" class="px-2.5 py-1 text-[11px] border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">上一页</button>
              <div class="flex items-center space-x-1 text-[11px] text-gray-600">
                <span>第</span><span class="font-medium">{{ autoCurrentPage }}</span><span>页 / 共</span><span class="font-medium">{{ autoTotalPages }}</span><span>页</span>
              </div>
              <button @click="changeAutoPage(autoCurrentPage + 1)" :disabled="autoCurrentPage === autoTotalPages" class="px-2.5 py-1 text-[11px] border border-gray-300 rounded-md hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed">下一页</button>
            </div>
          </div>
        </aside>
      </div>

      <!-- Image Translate Feature (Four-column) -->
      <div v-else-if="currentFeature === 'image-translate'" class="flex min-h-screen">
        <!-- Left Process Config Column -->
        <aside v-if="isDesktop" class="w-72 flex-col border-r border-gray-200 bg-gray-50 py-4 px-3 space-y-3 flex">
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

    <!-- Voice List Modal -->
    <div v-if="showVoiceModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="closeVoiceModal">
      <div class="bg-white rounded-lg shadow-xl w-[1000px] max-h-[80vh] mx-4 overflow-hidden flex flex-col" @click.stop>
        <div class="p-4 border-b border-gray-200 flex justify-between items-center flex-shrink-0">
          <div>
            <h2 class="text-lg font-semibold text-gray-900">选择音色 - {{ getLanguageName(currentSelectingLanguage) }}</h2>
            <p class="text-xs text-gray-500 mt-1">为该语言选择一个音色（默认TTS或自定义音色）</p>
          </div>
          <button @click="closeVoiceModal" class="text-gray-400 hover:text-gray-600">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Default TTS Voice Section -->
        <div class="p-4 border-b border-gray-100 flex-shrink-0">
          <h3 class="text-sm font-medium text-gray-700 mb-2">默认TTS音色</h3>
          <div
            @click="selectDefaultVoice"
            class="p-3 rounded-lg border transition cursor-pointer"
            :class="selectedVoice === null ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-indigo-300'"
          >
            <div class="flex justify-between items-start">
              <div class="flex-1">
                <div class="font-medium text-gray-900 text-sm">{{ getDefaultVoiceForLanguage(currentSelectingLanguage)?.voice || '默认音色' }}</div>
                <div class="text-xs text-gray-500 mt-1">{{ getDefaultVoiceForLanguage(currentSelectingLanguage)?.gender || '默认' }}</div>
              </div>
              <div v-if="selectedVoice === null" class="text-indigo-600 flex-shrink-0 ml-2">
                <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        <!-- Custom Voices Section -->
        <div class="p-4 flex-shrink-0">
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-sm font-medium text-gray-700">自定义音色（ElevenLabs）</h3>
            <button
              type="button"
              @click="openAddVoiceModal"
              class="px-3 py-1 bg-indigo-600 text-white rounded-md text-xs font-medium hover:bg-indigo-700 transition"
            >
              添加音色
            </button>
          </div>
          <div class="flex gap-2 mb-2">
            <select v-model="voiceFilterGender" @change="filterVoices" class="flex-1 px-2 py-1.5 border border-gray-300 rounded-md text-xs focus:outline-none focus:ring-2 focus:ring-indigo-600">
              <option value="">全部性别</option>
              <option value="male">男声</option>
              <option value="female">女声</option>
              <option value="other">其他</option>
            </select>
          </div>
        </div>

        <!-- Voice List -->
        <div class="flex-1 overflow-y-auto px-4 pb-4">
          <div v-if="filteredVoices.length === 0" class="text-center py-8 text-gray-500 text-sm">暂无自定义音色，点击"添加音色"按钮添加</div>
          <div class="grid grid-cols-4 gap-3">
            <div
              v-for="voice in filteredVoices"
              :key="voice.id"
              class="p-3 rounded-lg border transition flex flex-col relative"
              :class="selectedVoice?.id === voice.id ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:border-indigo-300'"
            >
              <div @click="selectVoice(voice)" class="cursor-pointer flex-1">
                <div class="flex justify-between items-start flex-shrink-0">
                  <div class="font-medium text-gray-900 text-sm truncate flex-1">{{ voice.name }}</div>
                  <div v-if="selectedVoice?.id === voice.id" class="text-indigo-600 flex-shrink-0 ml-2">
                    <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                    </svg>
                  </div>
                </div>
                <div class="text-xs text-gray-500 mt-1">{{ voice.gender === 'male' ? '男声' : voice.gender === 'female' ? '女声' : '其他' }}</div>
                <div v-if="voice.description" class="text-xs text-gray-400 mt-1 line-clamp-2">{{ voice.description }}</div>
              </div>
              <!-- Play button -->
              <button
                @click.stop="playVoicePreview(voice)"
                :disabled="isGeneratingPreview && playingVoiceId === voice.id"
                class="mt-2 w-full px-2 py-1 text-xs rounded border transition flex items-center justify-center gap-1"
                :class="playingVoiceId === voice.id ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'"
              >
                <svg v-if="isGeneratingPreview && playingVoiceId === voice.id" class="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <svg v-else-if="playingVoiceId === voice.id" class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
                <svg v-else class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" />
                </svg>
                <span>{{ isGeneratingPreview && playingVoiceId === voice.id ? '生成中' : playingVoiceId === voice.id ? '停止' : '试听' }}</span>
              </button>
            </div>
          </div>
        </div>

        <div class="p-4 border-t border-gray-200 flex justify-end gap-2">
          <button
            type="button"
            @click="closeVoiceModal"
            class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 transition"
          >
            取消
          </button>
          <button
            type="button"
            @click="confirmVoiceSelection"
            class="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition"
          >
            确认
          </button>
        </div>
      </div>
    </div>

    <!-- Add Voice Modal -->
    <div v-if="showAddVoiceModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click="showAddVoiceModal = false">
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4" @click.stop>
        <div class="p-4 border-b border-gray-200 flex justify-between items-center">
          <h2 class="text-lg font-semibold text-gray-900">添加音色</h2>
          <button @click="showAddVoiceModal = false" class="text-gray-400 hover:text-gray-600">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="p-4 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">音色名称</label>
            <input v-model="newVoice.name" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" placeholder="例如：George" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">音色ID</label>
            <input v-model="newVoice.voice_id" type="text" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" placeholder="例如：JBFqnCBsd6RMkjVDRZzb" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">语言</label>
            <select v-model="newVoice.language" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600">
              <option v-for="lang in LANGUAGE_OPTIONS" :key="lang.code" :value="lang.code">{{ lang.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">性别</label>
            <select v-model="newVoice.gender" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600">
              <option value="male">男声</option>
              <option value="female">女声</option>
              <option value="other">其他</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">音色描述</label>
            <textarea v-model="newVoice.description" rows="2" class="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600" placeholder="可选的音色描述"></textarea>
          </div>
        </div>
        <div class="p-4 border-t border-gray-200 flex justify-end gap-2">
          <button
            type="button"
            @click="showAddVoiceModal = false"
            class="px-4 py-2 border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 transition"
          >
            取消
          </button>
          <button
            type="button"
            @click="addVoice"
            :disabled="isAddingVoice || !newVoice.name || !newVoice.voice_id"
            class="px-4 py-2 bg-indigo-600 text-white rounded-md text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isAddingVoice ? '添加中...' : '添加' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Gift Card Redeem Modal -->
  <div v-if="showGiftCardModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl shadow-2xl max-w-md w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <h2 class="text-xl font-semibold text-gray-900">点卡兑换</h2>
          <button @click="closeGiftCardModal" class="text-gray-400 hover:text-gray-600 transition">
            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      <div class="p-6 space-y-4">
        <!-- 卡密输入框 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">点卡卡密</label>
          <input
            v-model="giftCardCode"
            type="text"
            placeholder="请输入16位卡密"
            class="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
            :disabled="isRedeeming"
          />
        </div>

        <!-- 价格说明 -->
        <div class="bg-indigo-50 rounded-lg p-4">
          <p class="text-sm text-indigo-900 font-medium mb-2">💰 价格说明</p>
          <p class="text-sm text-indigo-700">10 积分 = 1 RMB</p>
        </div>

        <!-- 点卡面额说明 -->
        <div class="bg-gray-50 rounded-lg p-4">
          <p class="text-sm text-gray-900 font-medium mb-3">📋 点卡面额</p>
          <div class="space-y-2 text-sm text-gray-700">
            <div class="flex justify-between">
              <span>100 积分</span>
              <span class="text-gray-500">= 10 元</span>
            </div>
            <div class="flex justify-between">
              <span>1,000 积分</span>
              <span class="text-gray-500">= 100 元</span>
            </div>
            <div class="flex justify-between">
              <span>5,000 积分</span>
              <span class="text-gray-500">= 500 元</span>
            </div>
            <div class="flex justify-between">
              <span>50,000 积分</span>
              <span class="text-gray-500">= 5,000 元</span>
            </div>
          </div>
        </div>

        <!-- 客服二维码 -->
        <div class="bg-white border border-gray-200 rounded-lg p-4 text-center">
          <p class="text-sm text-gray-700 font-medium mb-3">📱 购买点卡请联系客服</p>
          <div class="flex justify-center">
            <div class="w-48 h-48 bg-gray-100 rounded-lg flex items-center justify-center">
              <p class="text-gray-400 text-sm">请联系客服购买点卡</p>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-2">请将客服二维码图片放置到 public/qrcode.png</p>
        </div>

        <!-- 错误提示 -->
        <div v-if="giftCardError" class="bg-red-50 border border-red-200 rounded-lg p-3">
          <p class="text-sm text-red-600">{{ giftCardError }}</p>
        </div>

        <!-- 成功提示 -->
        <div v-if="giftCardSuccess" class="bg-green-50 border border-green-200 rounded-lg p-3">
          <p class="text-sm text-green-600">{{ giftCardSuccess }}</p>
        </div>
      </div>
      <div class="p-6 border-t border-gray-200 flex justify-end gap-3">
        <button
          @click="closeGiftCardModal"
          class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition"
          :disabled="isRedeeming"
        >
          取消
        </button>
        <button
          @click="redeemGiftCard"
          :disabled="isRedeeming || !giftCardCode.trim()"
          class="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ isRedeeming ? '兑换中...' : '立即兑换' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import OSS from 'ali-oss'
import { useAuthStore } from '@/stores/auth'
import { useLayoutStore } from '@/stores/layout'
import { useBreakpoint } from '@/composables/useBreakpoint'
import { UploadFilled } from '@element-plus/icons-vue'
import MobileHeader from '@/components/MobileHeader.vue'
import MobileDrawer from '@/components/MobileDrawer.vue'
import ResponsiveVideoContainer from '@/components/ResponsiveVideoContainer.vue'

const router = useRouter()
const authStore = useAuthStore()
const layoutStore = useLayoutStore()
const { isMobile, isTablet, isDesktop } = useBreakpoint()

const LANGUAGE_OPTIONS = [
  { code: 'zh', name: '中文', voice: 'xiaoyun', gender: '女声' },
  { code: 'en', name: '英语', voice: 'abby_ecmix', gender: '女声' },
  { code: 'ja', name: '日语', voice: 'tomoka', gender: '女声' },
  { code: 'ko', name: '韩语', voice: 'Kyong', gender: '女声' },
  { code: 'th', name: '泰语', voice: 'waan', gender: '女声' },
  { code: 'vi', name: '越南语', voice: 'tien', gender: '女声' },
  { code: 'es', name: '西班牙语', voice: 'camila', gender: '女声' },
  { code: 'fr', name: '法语', voice: 'clara', gender: '女声' },
  { code: 'de', name: '德语', voice: 'hanna', gender: '女声' },
  { code: 'id', name: '印尼语', voice: 'indah', gender: '女声' },
  { code: 'ms', name: '马来语', voice: 'farah', gender: '女声' },
  { code: 'fil', name: '菲律宾语', voice: 'tala', gender: '女声' },
  { code: 'ru', name: '俄语', voice: 'masha', gender: '女声' },
  { code: 'it', name: '意大利语', voice: 'perla', gender: '女声' },
  { code: 'yue', name: '粤语', voice: 'kelly', gender: '女声' }
]

const DEFAULT_AUTO_SUBTITLE_PARAMS = {
  alignment: 'BottomCenter',
  font: 'Alibaba PuHuiTi',
  font_size: 84,
  font_color: '#ffffff',
  outline: 2,
  outline_colour: '#000000',
  y: 0.9
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
const isUserCardExpanded = ref(false)

// Gift card state
const showGiftCardModal = ref(false)
const giftCardCode = ref('')
const isRedeeming = ref(false)
const giftCardError = ref('')
const giftCardSuccess = ref('')

// Voice modal state
const showVoiceModal = ref(false)
const showAddVoiceModal = ref(false)
const customVoices = ref([])
const filteredVoices = ref([])
const selectedVoice = ref(null) // 保持单选，但可以多次选择不同音色
const voiceFilterLanguage = ref('')
const voiceFilterGender = ref('')
const newVoice = ref({ name: '', voice_id: '', language: 'zh', gender: 'female', description: '' })
const isAddingVoice = ref(false)
const isLoggingIn = ref(false)
const voicePreviewAudio = ref(null)
const playingVoiceId = ref(null)
const isGeneratingPreview = ref(false)

// History expand state
const isHistoryExpanded = ref(false)

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

// Gift card functions
const closeGiftCardModal = () => {
  showGiftCardModal.value = false
  giftCardCode.value = ''
  giftCardError.value = ''
  giftCardSuccess.value = ''
}

const redeemGiftCard = async () => {
  if (!giftCardCode.value.trim()) {
    giftCardError.value = '请输入点卡卡密'
    return
  }

  isRedeeming.value = true
  giftCardError.value = ''
  giftCardSuccess.value = ''

  try {
    const response = await axios.post(
      `${API_BASE}/gift-cards/redeem`,
      { card_code: giftCardCode.value.trim() },
      {
        headers: { 'Authorization': `Bearer ${authStore.token}` }
      }
    )

    giftCardSuccess.value = `兑换成功！获得 ${response.data.points_added} 积分，当前余额：${response.data.new_balance} 积分`
    userPoints.value = response.data.new_balance

    // 3秒后关闭弹窗
    setTimeout(() => {
      closeGiftCardModal()
    }, 3000)

  } catch (error) {
    if (error.response?.data?.detail) {
      giftCardError.value = error.response.data.detail
    } else {
      giftCardError.value = '兑换失败，请稍后重试'
    }
  } finally {
    isRedeeming.value = false
  }
}

// Voice modal functions
const openVoiceModalForLanguage = async (languageCode) => {
  currentSelectingLanguage.value = languageCode
  showVoiceModal.value = true
  await fetchCustomVoices()

  // Filter voices for the selected language
  voiceFilterLanguage.value = languageCode
  filterVoices()

  // Pre-select current voice if exists
  if (customVoiceMap.value[languageCode]) {
    const currentVoice = customVoiceMap.value[languageCode]
    if (currentVoice.isCustom) {
      selectedVoice.value = customVoices.value.find(v => v.id === currentVoice.id) || null
    } else {
      selectedVoice.value = null // Default voice
    }
  } else {
    selectedVoice.value = null // Default voice
  }
}

const closeVoiceModal = () => {
  // Stop audio playback
  if (voicePreviewAudio.value) {
    voicePreviewAudio.value.pause()
    voicePreviewAudio.value = null
  }
  playingVoiceId.value = null
  showVoiceModal.value = false
  currentSelectingLanguage.value = null
  selectedVoice.value = null
}

const getDefaultVoiceForLanguage = (languageCode) => {
  return LANGUAGE_OPTIONS.find(lang => lang.code === languageCode)
}

const selectDefaultVoice = () => {
  selectedVoice.value = null
}

const openAddVoiceModal = () => {
  showAddVoiceModal.value = true
  newVoice.value = {
    name: '',
    voice_id: '',
    language: currentSelectingLanguage.value || 'zh',
    gender: 'female',
    description: ''
  }
}

const fetchCustomVoices = async () => {
  try {
    const token = localStorage.getItem('token')
    const response = await axios.get('/api/custom-voices', {
      headers: { Authorization: `Bearer ${token}` }
    })
    customVoices.value = response.data
  } catch (error) {
    console.error('Failed to fetch custom voices:', error)
    customVoices.value = []
  }
}

const filterVoices = () => {
  filteredVoices.value = customVoices.value.filter(voice => {
    const languageMatch = !voiceFilterLanguage.value || voice.language === voiceFilterLanguage.value
    const genderMatch = !voiceFilterGender.value || voice.gender === voiceFilterGender.value
    return languageMatch && genderMatch
  })
}

const selectVoice = (voice) => {
  selectedVoice.value = voice
}

const confirmVoiceSelection = () => {
  if (!currentSelectingLanguage.value) return

  const languageCode = currentSelectingLanguage.value

  if (selectedVoice.value === null) {
    // User selected default voice - remove custom voice mapping
    delete customVoiceMap.value[languageCode]
  } else {
    // User selected a custom voice - store single voice object
    customVoiceMap.value[languageCode] = {
      id: selectedVoice.value.id,
      name: selectedVoice.value.name,
      voice_id: selectedVoice.value.voice_id,
      gender: selectedVoice.value.gender,
      isCustom: true
    }
  }

  // Save to localStorage for future use
  try {
    localStorage.setItem('customVoiceMap', JSON.stringify(customVoiceMap.value))
  } catch (e) {
    console.warn('Failed to save voice map to localStorage:', e)
  }

  // Ensure language is selected
  if (!autoTargetLanguages.value.includes(languageCode)) {
    autoTargetLanguages.value.push(languageCode)
  }

  closeVoiceModal()
}

const playVoicePreview = async (voice) => {
  try {
    // 如果正在播放同一个音色，则停止播放
    if (playingVoiceId.value === voice.id && voicePreviewAudio.value) {
      voicePreviewAudio.value.pause()
      voicePreviewAudio.value = null
      playingVoiceId.value = null
      return
    }

    // 停止之前的播放
    if (voicePreviewAudio.value) {
      voicePreviewAudio.value.pause()
      voicePreviewAudio.value = null
    }

    playingVoiceId.value = voice.id
    isGeneratingPreview.value = true

    // 检查音频文件是否已存在
    const audioUrl = `${API_BASE}/hello-voices/${voice.voice_id}.mp3`

    try {
      // 尝试直接播放已存在的文件
      const audio = new Audio(audioUrl)
      audio.onended = () => {
        playingVoiceId.value = null
        voicePreviewAudio.value = null
      }
      audio.onerror = async () => {
        // 文件不存在，生成新的预览音频
        console.log('Audio file not found, generating preview...')
        await generateAndPlayPreview(voice)
      }
      await audio.play()
      voicePreviewAudio.value = audio
      isGeneratingPreview.value = false
    } catch (error) {
      // 播放失败，尝试生成新的预览音频
      await generateAndPlayPreview(voice)
    }
  } catch (error) {
    console.error('Failed to play voice preview:', error)
    ElMessage.error('播放试听失败')
    playingVoiceId.value = null
    isGeneratingPreview.value = false
  }
}

const generateAndPlayPreview = async (voice) => {
  try {
    // 调用后端生成预览音频
    const response = await axios.post(`${API_BASE}/generate-voice-preview`, {
      voice_id: voice.voice_id,
      language: voice.language
    })

    if (response.data.status === 'success') {
      const audioUrl = `${API_BASE}${response.data.audio_url}`
      const audio = new Audio(audioUrl)
      audio.onended = () => {
        playingVoiceId.value = null
        voicePreviewAudio.value = null
      }
      await audio.play()
      voicePreviewAudio.value = audio
    }
  } finally {
    isGeneratingPreview.value = false
  }
}

const removeCustomVoice = (languageCode) => {
  delete customVoiceMap.value[languageCode]

  // Save to localStorage
  try {
    localStorage.setItem('customVoiceMap', JSON.stringify(customVoiceMap.value))
  } catch (e) {
    console.warn('Failed to save voice map to localStorage:', e)
  }
}

const addVoice = async () => {
  if (!newVoice.value.name || !newVoice.value.voice_id) {
    return
  }

  isAddingVoice.value = true
  try {
    const token = localStorage.getItem('token')
    const response = await axios.post('/api/custom-voices', newVoice.value, {
      headers: { Authorization: `Bearer ${token}` }
    })
    customVoices.value.push(response.data)
    filterVoices()
    showAddVoiceModal.value = false
    newVoice.value = {
      name: '',
      voice_id: '',
      language: currentSelectingLanguage.value || 'zh',
      gender: 'female',
      description: ''
    }
  } catch (error) {
    console.error('Failed to add voice:', error)
    alert('添加音色失败，请稍后重试')
  } finally {
    isAddingVoice.value = false
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
const customVoiceMap = ref({}) // Map language code to single voice object: { id, name, voice_id, gender, isCustom }
const currentSelectingLanguage = ref(null) // Track which language is being selected for voice

// Load saved voice preferences from localStorage
try {
  const savedVoiceMap = localStorage.getItem('customVoiceMap')
  if (savedVoiceMap) {
    customVoiceMap.value = JSON.parse(savedVoiceMap)
  }
} catch (e) {
  console.warn('Failed to load saved voice map:', e)
  customVoiceMap.value = {}
}
const autoSkipSubtitleErasure = ref(false)
const autoFullScreenErase = ref(false)
const autoHideSubtitles = ref(false)
const autoContinuousDubbing = ref(false)
const autoSubtitleStyleId = ref('default')
const selectedAutoSubtitleStyle = computed(() => AUTO_SUBTITLE_STYLE_OPTIONS.find(style => style.id === autoSubtitleStyleId.value) || AUTO_SUBTITLE_STYLE_OPTIONS[0])
const autoTranslationPointCost = computed(() => {
  let languagePoints = 10 + Math.max(0, autoTargetLanguages.value.length - 1) * 5

  // 全屏字幕擦除纳入基础语言积分，随时长倍增
  if (autoFullScreenErase.value) {
    languagePoints += 5
  }

  // 计算所有视频的总积分
  const totalPoints = autoUploadedVideos.value.reduce((sum, video) => {
    const duration = video.duration || 0
    const timeUnits = Math.ceil(duration / 60) // 以60秒为一个单位
    return sum + languagePoints * Math.max(1, timeUnits)
  }, 0)

  return Math.max(languagePoints, totalPoints) // 至少扣除一个语言的基础积分
})
const autoPendingVideoFiles = computed(() => autoVideoFiles.value.filter(file => !autoUploadedVideos.value.some(item => item.file === file)))
const autoIsProcessing = ref(false)
const autoProgress = ref({ step: 0, status: '' })
const autoTaskHistory = ref([])
const autoVideoInputRef = ref(null)
const autoCurrentPage = ref(1)
const autoTotalPages = ref(1)
const autoPageSize = ref(8)
const autoIsRefreshing = ref(false)
const autoIsDownloadingSelected = ref(false)
const showSubmitAnimation = ref(false)
const showSubmitSuccessCard = ref(false)
const showAutoSubtitleStyleModal = ref(false)
const editingAutoTaskId = ref(null)
const editingAutoTaskName = ref('')
const autoEditInput = ref(null)
const autoTaskTags = ref([])
const autoTagInput = ref('')
const useTestVersion = ref(false)
const autoSavedTags = ref([])
const autoFontSize = ref(60)
const subtitleBottomPosition = ref(30)
const showSubtitlePreview = ref(false)
const videoMetadataLoaded = ref(0) // Counter to force computed recalculation
const subtitlePreviewFontSize = computed(() => {
  // Access videoMetadataLoaded to establish reactive dependency for re-calculation when video loads
  const _ = videoMetadataLoaded.value

  // Dynamically get the client height of the video preview player, or fallback to 640px if not loaded
  const renderedHeight = autoPreviewVideoRef.value?.clientHeight || 640
  const REFERENCE_VIDEO_HEIGHT = 1920 // Assume 1080x1920 as reference (vertical video)

  // Scale the font size to fit the rendered preview container
  // This ensures consistent subtitle size regardless of actual video resolution and responsive layout
  const scale = renderedHeight / REFERENCE_VIDEO_HEIGHT

  return Math.round(autoFontSize.value * scale)
})
const autoPreviewVideoRef = ref(null)
const isDraggingSubtitle = ref(false)
const dragStartY = ref(0)
const dragStartPosition = ref(0)

try {
  const saved = localStorage.getItem('autoSavedTags')
  if (saved) {
    autoSavedTags.value = JSON.parse(saved)
  }
} catch (e) {
  console.warn('Failed to load saved tags:', e)
  autoSavedTags.value = []
}

const API_BASE = '/api'

// Subtitle preview functions
const getSubtitlePreviewStyle = () => {
  const style = selectedAutoSubtitleStyle.value
  if (!style || !style.params) {
    return {
      color: '#ffffff',
      textShadow: '2px 2px 4px rgba(0,0,0,0.8), -1px -1px 2px rgba(0,0,0,0.8), 1px -1px 2px rgba(0,0,0,0.8), -1px 1px 2px rgba(0,0,0,0.8)'
    }
  }

  const params = style.params
  const outlineColor = params.outline_colour || '#000000'
  const backColor = params.back_colour || 'transparent'
  const fontColor = params.font_color || '#ffffff'
  const outline = params.outline || 2

  // Create text shadow for outline effect
  const shadows = []
  for (let i = -outline; i <= outline; i++) {
    for (let j = -outline; j <= outline; j++) {
      if (i !== 0 || j !== 0) {
        shadows.push(`${i}px ${j}px 0 ${outlineColor}`)
      }
    }
  }

  return {
    color: fontColor,
    textShadow: shadows.join(', '),
    backgroundColor: backColor !== 'transparent' ? backColor : undefined,
    padding: backColor !== 'transparent' ? '4px 8px' : undefined,
    borderRadius: backColor !== 'transparent' ? '4px' : undefined,
    fontFamily: params.font || 'Alibaba PuHuiTi, SimSun, sans-serif'
  }
}

const updateSubtitlePreview = () => {
  // Force re-render of subtitle preview
  if (showSubtitlePreview.value) {
    showSubtitlePreview.value = false
    nextTick(() => {
      showSubtitlePreview.value = true
    })
  }
}

const onVideoLoaded = () => {
  // Video loaded, can now show subtitle preview
  if (autoVideoObjectUrl.value) {
    // Increment counter to trigger subtitlePreviewFontSize recalculation
    videoMetadataLoaded.value++
    // Use nextTick to ensure video dimensions are available
    nextTick(() => {
      showSubtitlePreview.value = true
    })
  }
}

const startDragSubtitle = (e) => {
  isDraggingSubtitle.value = true
  dragStartY.value = e.clientY
  dragStartPosition.value = subtitleBottomPosition.value

  document.addEventListener('mousemove', onDragSubtitle)
  document.addEventListener('mouseup', stopDragSubtitle)
  e.preventDefault()
}

const onDragSubtitle = (e) => {
  if (!isDraggingSubtitle.value || !autoPreviewVideoRef.value) return

  const videoElement = autoPreviewVideoRef.value
  const videoRect = videoElement.getBoundingClientRect()
  const videoHeight = videoRect.height

  // Calculate position change
  // Dragging up (negative deltaY) should decrease subtitleBottomPosition (move subtitle up, closer to top)
  // Dragging down (positive deltaY) should increase subtitleBottomPosition (move subtitle down, closer to bottom)
  const deltaY = dragStartY.value - e.clientY  // Positive when dragging up
  const deltaPercent = (deltaY / videoHeight) * 100

  // Update position (clamp between 0 and 40%)
  let newPosition = dragStartPosition.value + deltaPercent
  newPosition = Math.max(0, Math.min(40, newPosition))
  subtitleBottomPosition.value = Math.round(newPosition)
}

const stopDragSubtitle = () => {
  isDraggingSubtitle.value = false
  document.removeEventListener('mousemove', onDragSubtitle)
  document.removeEventListener('mouseup', stopDragSubtitle)
}

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
      bucket: config.bucket,
      secure: true
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

const getVoiceName = (langCode, customVoiceId) => {
  if (customVoiceId) {
    return customVoiceId
  }
  const language = LANGUAGE_OPTIONS.find(language => language.code === langCode)
  if (language) {
    return `${language.voice}（${language.gender}）`
  }
  return '默认音色'
}

const getAlignmentName = (alignment) => {
  const alignmentMap = {
    'BottomCenter': '底部居中',
    'BottomLeft': '底部左侧',
    'BottomRight': '底部右侧',
    'TopCenter': '顶部居中',
    'TopLeft': '顶部左侧',
    'TopRight': '顶部右侧',
    'Center': '居中'
  }
  return alignmentMap[alignment] || alignment || '底部居中'
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

// 语音试听功能
let currentAudio = null

const playLanguageVoice = async (languageCode) => {
  // 如果正在播放同一个语言，停止播放
  if (currentPlayingLanguage.value === languageCode && currentAudio) {
    currentAudio.pause()
    currentAudio = null
    currentPlayingLanguage.value = null
    return
  }

  // 停止之前的播放
  if (currentAudio) {
    currentAudio.pause()
    currentAudio = null
  }

  currentPlayingLanguage.value = languageCode

  // Check if custom voice is selected for this language
  const customVoice = customVoiceMap.value[languageCode]

  if (customVoice && customVoice.isCustom) {
    // Play custom voice preview
    try {
      const audioUrl = `${API_BASE}/hello-voices/${customVoice.voice_id}.mp3`
      currentAudio = new Audio(audioUrl)

      currentAudio.onended = () => {
        currentPlayingLanguage.value = null
        currentAudio = null
      }

      currentAudio.onerror = async () => {
        // File not found, try to generate
        try {
          const response = await axios.post(`${API_BASE}/generate-voice-preview`, {
            voice_id: customVoice.voice_id,
            language: languageCode
          })

          if (response.data.status === 'success') {
            const newAudioUrl = `${API_BASE}${response.data.audio_url}`
            currentAudio = new Audio(newAudioUrl)
            currentAudio.onended = () => {
              currentPlayingLanguage.value = null
              currentAudio = null
            }
            await currentAudio.play()
          }
        } catch (err) {
          console.error('Failed to generate preview:', err)
          currentPlayingLanguage.value = null
          currentAudio = null
        }
      }

      await currentAudio.play()
    } catch (err) {
      console.error('播放失败:', err)
      currentPlayingLanguage.value = null
      currentAudio = null
    }
  } else {
    // Play default TTS voice
    const audioPath = `/hello_voices/hello_${languageCode}.mp3`
    currentAudio = new Audio(audioPath)

    currentAudio.play().catch(err => {
      console.error('播放失败:', err)
      currentPlayingLanguage.value = null
    })

    currentAudio.onended = () => {
      currentPlayingLanguage.value = null
      currentAudio = null
    }

    currentAudio.onerror = () => {
      currentPlayingLanguage.value = null
      currentAudio = null
    }
  }
}

const buildAutoSubtitleParams = () => ({
  ...DEFAULT_AUTO_SUBTITLE_PARAMS,
  ...selectedAutoSubtitleStyle.value.params,
  font_size: autoFontSize.value,
  alignment: 'TopCenter',
  // When alignment is TopCenter, Y represents the distance from video top to subtitle TOP edge
  // subtitleBottomPosition is distance from video bottom (e.g., 10% from bottom)
  // Convert to distance from top: if 10% from bottom, then top edge is at (100 - 10)% = 90% from top
  y: (100 - subtitleBottomPosition.value) / 100
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

const handleFileSelect = (file, fileList) => {
  if (file.raw && file.raw.type.startsWith('video/')) {
    // Element Plus的Upload组件会自动管理fileList
    // 确保文件列表正确更新
    console.log('文件选择:', file.name)
    // 创建预览 URL
    if (fileList.length > 0) {
      const firstFile = fileList[0]
      if (firstFile.raw) {
        currentVideoUrl.value = URL.createObjectURL(firstFile.raw)
      }
    }
  } else {
    // 如果不是视频文件，从列表中移除
    const index = fileList.indexOf(file)
    if (index > -1) {
      fileList.splice(index, 1)
    }
    alert('请选择视频文件')
  }
}

const handleFileRemove = (file, fileList) => {
  // Element Plus的Upload组件会自动管理fileList
  // 清理预览 URL
  if (fileList.length === 0) {
    currentVideoUrl.value = ''
    if (currentVideoUrl.value) {
      URL.revokeObjectURL(currentVideoUrl.value)
    }
  } else {
    // 如果还有文件，显示第一个文件的预览
    const firstFile = fileList[0]
    if (firstFile.raw) {
      currentVideoUrl.value = URL.createObjectURL(firstFile.raw)
    }
  }
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
  // 直接加8小时转换为北京时间
  const beijingTime = new Date(date.getTime() + 8 * 60 * 60 * 1000)
  return beijingTime.toLocaleString('zh-CN', {
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
    // Clear history video URL to ensure preview shows the new video
    currentVideoUrl.value = ''
    autoSelectedHistoryTask.value = null
    currentPlayingTask.value = null
    currentPlayingLanguage.value = null
    // Reset subtitle preview to hide it until video metadata loads
    showSubtitlePreview.value = false
    videoMetadataLoaded.value = 0
    e.target.value = ''
  }
}

// 多文件并发上传到 OSS
// MAX_CONCURRENT_FILES：同时进行分片上传的文件数上限
// PART_PARALLEL_PER_FILE：每个文件内部并行的分片数
// 总并发连接数 ≈ MAX_CONCURRENT_FILES * PART_PARALLEL_PER_FILE，需要控制在浏览器对单域名连接数限制以内
// PART_SIZE：分片大小。10MB 在 20-200MB 的短视频场景能保证足够的并行度，丢包重传代价也较小
// MAX_RETRIES_PER_FILE：单文件失败重试次数。配合 checkpoint 实现断点续传，每次重试只补传未完成的分片
const MAX_CONCURRENT_FILES = 5
const PART_PARALLEL_PER_FILE = 5
const PART_SIZE = 10 * 1024 * 1024 // 10MB
const MAX_RETRIES_PER_FILE = 5

const buildAutoOssKey = (file) => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '').slice(0, 15)
  const randomStr = Math.random().toString(36).substring(2, 10)
  const ext = (file.name.split('.').pop() || 'mp4').toLowerCase()
  return `auto_translate/1/${timestamp}_${randomStr}.${ext}`
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms))

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

    // 预先计算每个文件的 ossKey 和 duration，避免在并发上传中阻塞
    const tasks = await Promise.all(filesToUpload.map(async (file) => ({
      file,
      ossKey: buildAutoOssKey(file),
      duration: await getVideoDuration(file),
    })))

    // 按文件维度跟踪每个文件的上传进度（0..1），用于聚合整体进度
    const fileProgress = new Array(totalFiles).fill(0)
    const updateOverallProgress = () => {
      const sum = fileProgress.reduce((acc, p) => acc + p, 0)
      autoUploadProgress.value = Math.min(100, Math.round((sum / totalFiles) * 100))
    }

    const failures = []

    // 单文件上传：失败自动重试，复用 checkpoint 实现断点续传
    const uploadOne = async (task, index) => {
      let checkpoint = null
      let lastError = null

      for (let attempt = 1; attempt <= MAX_RETRIES_PER_FILE; attempt++) {
        try {
          await ossClient.multipartUpload(task.ossKey, task.file, {
            // 续传：第 2 次起会带着上一轮的 checkpoint，SDK 自动跳过已完成分片
            checkpoint,
            // ali-oss 浏览器端 progress 签名: (percentage 0..1, cpt)
            async progress(percentage, cpt) {
              if (cpt) checkpoint = cpt
              fileProgress[index] = percentage
              updateOverallProgress()
            },
            partSize: PART_SIZE,
            parallel: PART_PARALLEL_PER_FILE,
          })

          // success
          fileProgress[index] = 1
          updateOverallProgress()
          autoUploadedVideos.value.push({
            file: task.file,
            ossKey: task.ossKey,
            duration: task.duration,
          })
          return
        } catch (err) {
          lastError = err
          console.warn(
            `Upload attempt ${attempt}/${MAX_RETRIES_PER_FILE} failed for ${task.file.name}:`,
            err?.message || err
          )
          if (attempt < MAX_RETRIES_PER_FILE) {
            // 退避重试: 1s, 2s, 3s, 3s, ...
            await sleep(1000 * Math.min(attempt, 3))
          }
        }
      }

      console.error(`Upload finally failed for ${task.file.name} after ${MAX_RETRIES_PER_FILE} attempts`)
      failures.push({ name: task.file.name, error: lastError })
    }

    // worker 并发池：始终最多 MAX_CONCURRENT_FILES 个文件同时上传
    let cursor = 0
    const worker = async () => {
      while (true) {
        const i = cursor++
        if (i >= tasks.length) break
        await uploadOne(tasks[i], i)
      }
    }

    const workerCount = Math.min(MAX_CONCURRENT_FILES, tasks.length)
    await Promise.all(Array.from({ length: workerCount }, () => worker()))

    console.log('Videos uploaded successfully:', autoUploadedVideos.value.map(item => item.ossKey))

    if (failures.length > 0) {
      const detail = failures.map(f => `${f.name}: ${f.error?.message || f.error}`).join('\n')
      alert(`部分视频上传失败 (${failures.length}/${totalFiles})，可重新选择失败文件后再试:\n${detail}`)
    }
  } catch (error) {
    console.error('Failed to upload video:', error)
    alert('视频上传失败: ' + error.message)
  } finally {
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

  // Save tags to localStorage for future use
  if (autoTaskTags.value.length > 0) {
    const newTags = autoTaskTags.value.filter(tag => !autoSavedTags.value.includes(tag))
    if (newTags.length > 0) {
      autoSavedTags.value = [...new Set([...autoSavedTags.value, ...newTags])]
      localStorage.setItem('autoSavedTags', JSON.stringify(autoSavedTags.value))
    }
  }

  // Show success card immediately
  showSubmitSuccessCard.value = true
  setTimeout(() => {
    showSubmitSuccessCard.value = false
  }, 3000)

  try {
    for (const uploadedVideo of autoUploadedVideos.value) {
      const fileUrl = ossClient.signatureUrl(uploadedVideo.ossKey, { expires: 604800 })

      // Build custom voice map: { language_code: voice_id }
      // voice_id can be null (default TTS) or a custom voice ID
      const languageVoiceMap = {}
      for (const langCode of autoTargetLanguages.value) {
        if (customVoiceMap.value[langCode] && customVoiceMap.value[langCode].isCustom) {
          // Custom voice selected
          languageVoiceMap[langCode] = customVoiceMap.value[langCode].voice_id
        } else {
          // Default TTS voice (send null or omit)
          languageVoiceMap[langCode] = null
        }
      }

      // Submit auto translation task (will be processed in background)
      await axios.post(
        `${API_BASE}/video-translation/submit-auto`,
        {
          original_filename: uploadedVideo.file.name,
          target_language: autoTargetLanguages.value[0],
          target_languages: autoTargetLanguages.value,
          oss_key: uploadedVideo.ossKey,
          file_url: fileUrl,
          original_video_url: fileUrl,
          skip_subtitle_erasure: autoSkipSubtitleErasure.value,
          full_screen_erase: autoFullScreenErase.value,
          hide_subtitles: autoHideSubtitles.value,
          continuous_dubbing: autoContinuousDubbing.value,
          subtitle_params: buildAutoSubtitleParams(),
          tags: autoTaskTags.value,
          custom_voice_map: languageVoiceMap,
          use_test_version: useTestVersion.value
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
    // 不清空 customVoiceMap，保留用户的音色选择
    // customVoiceMap.value = {}
    autoSkipSubtitleErasure.value = false
    autoFullScreenErase.value = true
    autoContinuousDubbing.value = false
    autoSubtitleStyleId.value = 'default'
    autoTaskTags.value = []

    // Reload history to show the new task after animation
    setTimeout(async () => {
      await loadAutoTranslationHistory()
      await loadAutoTags({ query: '', showAll: false })
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

// 获取视频时长的辅助函数
const getVideoDuration = (file) => {
  return new Promise((resolve) => {
    const video = document.createElement('video')
    video.preload = 'metadata'
    video.onloadedmetadata = () => {
      window.URL.revokeObjectURL(video.src)
      resolve(video.duration || 0)
    }
    video.onerror = () => {
      window.URL.revokeObjectURL(video.src)
      resolve(0) // 如果获取失败，返回0
    }
    video.src = URL.createObjectURL(file)
  })
}

const autoFilterTag = ref(null)
const autoTagSearchQuery = ref('')
const autoFilterLanguage = ref('')
const autoAvailableTags = ref([])
const autoTagTotal = ref(0)
const autoShowAllTags = ref(false)
const autoTagRequestSequence = ref(0)

// Limit recently used tags to 3 rows (approximately 9 tags)
const autoDisplayedTags = computed(() => {
  if (autoShowAllTags.value || autoTagSearchQuery.value.trim()) {
    return autoAvailableTags.value
  }
  // Show only first 9 tags (3 rows) for recently used tags
  return autoAvailableTags.value.slice(0, 9)
})
const autoExpandedHistory = ref([])
const autoHistoryThumbnails = ref({})
const autoSelectedHistoryIds = ref([])
const autoSelectedHistoryItems = computed(() => autoExpandedHistory.value.filter(item => autoSelectedHistoryIds.value.includes(item.id)))
const autoDownloadableSelectedHistoryItems = computed(() => autoSelectedHistoryItems.value.filter(item => item.result_video_url || item.videoUrl))
const isAutoCurrentPageFullySelected = computed(() => autoExpandedHistory.value.length > 0 && autoExpandedHistory.value.every(item => autoSelectedHistoryIds.value.includes(item.id)))

const syncAutoHistorySelectionWithCurrentPage = () => {
  const currentPageIds = new Set(autoExpandedHistory.value.map(item => item.id))
  autoSelectedHistoryIds.value = autoSelectedHistoryIds.value.filter(id => currentPageIds.has(id))
}

const isAutoHistoryItemSelected = (item) => autoSelectedHistoryIds.value.includes(item.id)

const toggleAutoHistoryItemSelection = (item) => {
  if (isAutoHistoryItemSelected(item)) {
    autoSelectedHistoryIds.value = autoSelectedHistoryIds.value.filter(id => id !== item.id)
  } else {
    autoSelectedHistoryIds.value = [...autoSelectedHistoryIds.value, item.id]
  }
}

const toggleSelectAllAutoHistory = () => {
  autoSelectedHistoryIds.value = isAutoCurrentPageFullySelected.value
    ? []
    : autoExpandedHistory.value.map(item => item.id)
}

const getAutoHistoryDownloadExtension = (item) => {
  const videoUrl = item.result_video_url || item.videoUrl || ''
  const urlPath = videoUrl.split('?')[0].split('#')[0]
  const urlMatch = urlPath.match(/\.([a-zA-Z0-9]{2,5})$/)
  const nameMatch = (item.original_filename || '').match(/\.([a-zA-Z0-9]{2,5})$/)

  return (urlMatch?.[1] || nameMatch?.[1] || 'mp4').toLowerCase()
}

const sanitizeAutoHistoryDownloadName = (name) => (name || 'translated-video').replace(/[\\/:*?"<>|]/g, '_')

const getAutoHistoryDownloadName = (item) => {
  const baseName = sanitizeAutoHistoryDownloadName((item.original_filename || 'translated-video').replace(/\.[^/.]+$/, ''))
  const languageName = sanitizeAutoHistoryDownloadName(item.languageName || item.languageCode || 'translation')
  const extension = getAutoHistoryDownloadExtension(item)

  return `${baseName}_${languageName}.${extension}`
}

const triggerBrowserDownload = (url, filename) => {
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const getAutoHistoryArchiveDownloadName = () => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '').slice(0, 15)
  return `selected-translations_${timestamp}.zip`
}

const getDownloadErrorMessage = async (error) => {
  const data = error.response?.data
  if (data instanceof Blob) {
    try {
      const text = await data.text()
      const parsed = JSON.parse(text)
      return parsed.detail || error.message
    } catch (parseError) {
      return error.message
    }
  }
  return data?.detail || error.message
}

const downloadSelectedAutoHistory = async () => {
  if (autoIsDownloadingSelected.value) return

  const items = autoDownloadableSelectedHistoryItems.value
  if (items.length === 0) {
    alert('请先选择要下载的视频')
    return
  }

  // 首次批量下载时，提示用户允许多文件下载
  const isFirstTime = !localStorage.getItem('batch_download_tip_shown')
  if (isFirstTime && items.length > 1) {
    const userConfirm = confirm(
      `即将下载 ${items.length} 个视频文件\n\n` +
      '提示：浏览器可能会询问是否允许下载多个文件，请点击"允许"\n\n' +
      '点击"确定"开始下载'
    )
    if (!userConfirm) return
    localStorage.setItem('batch_download_tip_shown', 'true')
  }

  autoIsDownloadingSelected.value = true

  try {
    const totalCount = items.length
    let downloadedCount = 0
    let skippedCount = 0

    // 创建进度提示浮窗
    const progressDiv = document.createElement('div')
    progressDiv.id = 'batch-download-progress'
    progressDiv.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: white;
      padding: 16px 24px;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.15);
      z-index: 9999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      min-width: 280px;
      border: 1px solid #e5e7eb;
    `
    progressDiv.innerHTML = `
      <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <div style="width: 32px; height: 32px; border: 3px solid #e5e7eb; border-top-color: #4f46e5; border-radius: 50%; animation: spin 1s linear infinite; margin-right: 12px;"></div>
        <div style="font-weight: 600; font-size: 15px; color: #111827;">批量下载进行中</div>
      </div>
      <div id="download-progress" style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">正在下载: 0/${totalCount}</div>
      <div style="font-size: 12px; color: #9ca3af;">请稍候，每个文件间隔约1秒...</div>
    `

    // 添加旋转动画
    const style = document.createElement('style')
    style.textContent = `
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `
    document.head.appendChild(style)
    document.body.appendChild(progressDiv)

    // 逐个下载文件
    for (let i = 0; i < items.length; i++) {
      const item = items[i]
      const url = item.result_video_url || item.videoUrl

      if (!url) {
        console.warn(`跳过无效项: ${item.original_filename}`)
        skippedCount++
        continue
      }

      // 使用隐藏 iframe 触发下载
      const iframe = document.createElement('iframe')
      iframe.style.cssText = 'display:none;position:fixed;width:1px;height:1px;top:-100px;left:-100px;'
      iframe.src = url
      document.body.appendChild(iframe)

      // 更新进度
      downloadedCount++
      const progressEl = document.getElementById('download-progress')
      if (progressEl) {
        progressEl.textContent = `正在下载: ${downloadedCount}/${totalCount}${skippedCount > 0 ? ` (跳过${skippedCount}个)` : ''}`
      }

      // 5秒后移除 iframe
      setTimeout(() => {
        if (iframe.parentNode) {
          document.body.removeChild(iframe)
        }
      }, 5000)

      // 添加延迟避免浏览器拦截（除了最后一个文件）
      if (i < items.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }

    // 下载完成提示
    setTimeout(() => {
      const progressDiv = document.getElementById('batch-download-progress')
      if (progressDiv) {
        progressDiv.innerHTML = `
          <div style="display: flex; align-items: center; margin-bottom: 12px;">
            <div style="width: 32px; height: 32px; background: #10b981; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-right: 12px;">
              <svg style="width: 20px; height: 20px; color: white;" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path>
              </svg>
            </div>
            <div style="font-weight: 600; font-size: 15px; color: #10b981;">下载完成</div>
          </div>
          <div style="font-size: 14px; color: #6b7280; margin-bottom: 4px;">已触发 ${downloadedCount} 个文件下载${skippedCount > 0 ? `，跳过 ${skippedCount} 个` : ''}</div>
          <div style="font-size: 12px; color: #9ca3af;">请在浏览器下载管理器中查看</div>
        `
        setTimeout(() => {
          if (progressDiv.parentNode) {
            document.body.removeChild(progressDiv)
          }
        }, 3000)
      }
    }, 500)

  } catch (error) {
    console.error('批量下载失败:', error)
    alert('下载失败: ' + error.message)

    // 移除进度提示
    const progressDiv = document.getElementById('batch-download-progress')
    if (progressDiv && progressDiv.parentNode) {
      document.body.removeChild(progressDiv)
    }
  } finally {
    autoIsDownloadingSelected.value = false
  }
}

const generateHistoryVideoThumbnail = (item) => {
  const videoUrl = item.result_video_url || item.videoUrl
  if (!videoUrl || autoHistoryThumbnails.value[item.id]) return

  const video = document.createElement('video')
  video.crossOrigin = 'anonymous'
  video.muted = true
  video.preload = 'metadata'
  video.src = videoUrl

  const cleanup = () => {
    video.removeAttribute('src')
    video.load()
  }

  video.onloadeddata = () => {
    try {
      video.currentTime = Math.min(1, video.duration || 1)
    } catch (error) {
      cleanup()
    }
  }

  video.onseeked = () => {
    try {
      const canvas = document.createElement('canvas')
      const videoWidth = video.videoWidth || 320
      const videoHeight = video.videoHeight || 180
      const maxThumbWidth = 320
      const scale = Math.min(1, maxThumbWidth / videoWidth)
      canvas.width = Math.round(videoWidth * scale)
      canvas.height = Math.round(videoHeight * scale)
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
      autoHistoryThumbnails.value = {
        ...autoHistoryThumbnails.value,
        [item.id]: canvas.toDataURL('image/jpeg', 0.72)
      }
    } catch (error) {
      console.warn('Failed to generate history thumbnail:', error)
    } finally {
      cleanup()
    }
  }

  video.onerror = cleanup
}

const loadAutoTags = async ({ query = autoTagSearchQuery.value, showAll = autoShowAllTags.value } = {}) => {
  const requestSequence = autoTagRequestSequence.value + 1
  autoTagRequestSequence.value = requestSequence
  const trimmedQuery = query.trim()
  const params = {
    is_auto: true,
    sort: trimmedQuery ? 'recent' : (showAll ? 'popular' : 'recent'),
    limit: trimmedQuery ? 50 : (showAll ? 200 : 10)
  }

  if (trimmedQuery) {
    params.q = trimmedQuery
  }

  const response = await axios.get(
    `${API_BASE}/video-translation/tags`,
    {
      params,
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    }
  )

  if (requestSequence !== autoTagRequestSequence.value) {
    return
  }

  autoAvailableTags.value = response.data.items || []
  autoTagTotal.value = response.data.total || 0
}

const loadAutoTranslationHistory = async () => {
  try {
    const params = {
      is_auto: true,
      page: autoCurrentPage.value,
      page_size: autoPageSize.value
    }
    if (autoFilterTag.value?.id) {
      params.tag_id = autoFilterTag.value.id
    }
    if (autoFilterLanguage.value) {
      params.language = autoFilterLanguage.value
    }
    const requestConfig = {
      headers: {
        'Authorization': `Bearer ${authStore.token}`
      }
    }
    const response = await axios.get(
      `${API_BASE}/video-translation/tasks`,
      {
        params,
        ...requestConfig
      }
    )

    const expandedItems = []

    response.data.items.forEach(task => {
      const taskHasResults = task.language_results && typeof task.language_results === 'object' && Object.keys(task.language_results).length > 0

      if (taskHasResults) {
        Object.entries(task.language_results).forEach(([langCode, result]) => {
          if (!autoFilterLanguage.value || langCode === autoFilterLanguage.value) {
            expandedItems.push({
              id: `${task.id}-${langCode}`,
              taskId: task.id,
              original_filename: task.original_filename,
              languageCode: langCode,
              languageName: getLanguageName(langCode),
              videoUrl: result?.result_video_url || null,
              result_video_url: result?.result_video_url || null,
              original_video_url: task.original_video_url || null,
              target_languages: [langCode],
              status: result?.status || task.status,
              current_stage: task.current_stage,
              created_at: task.created_at,
              tags: task.tags || []
            })
          }
        })
      } else {
        expandedItems.push({
          id: `${task.id}-main`,
          taskId: task.id,
          original_filename: task.original_filename,
          languageCode: task.target_language || '',
          languageName: task.target_language ? getLanguageName(task.target_language) : '',
          videoUrl: task.result_video_url || null,
          result_video_url: task.result_video_url || null,
          original_video_url: task.original_video_url || null,
          target_languages: task.target_languages || (task.target_language ? [task.target_language] : []),
          status: task.status,
          current_stage: task.current_stage,
          created_at: task.created_at,
          tags: task.tags || []
        })
      }
    })

    // 直接使用展开后的数据，不再进行客户端分页
    autoExpandedHistory.value = expandedItems
    autoExpandedHistory.value.forEach(generateHistoryVideoThumbnail)

    // 使用后端返回的分页信息
    autoTotalPages.value = response.data.total_pages || 1

    syncAutoHistorySelectionWithCurrentPage()
  } catch (error) {
    console.error('Failed to load auto translation history:', error)
  }
}

const clearAutoTagSearch = () => {
  autoTagSearchQuery.value = ''
  autoShowAllTags.value = false
  loadAutoTags({ query: '', showAll: false })
}

const selectAutoTag = (tag) => {
  filterByTag(tag)
  loadAutoTranslationHistory()
}

const selectFirstMatchedAutoTag = async () => {
  await loadAutoTags({ query: autoTagSearchQuery.value.trim(), showAll: false })
  const firstMatchedTag = autoAvailableTags.value[0]
  if (firstMatchedTag) {
    selectAutoTag(firstMatchedTag)
  }
}

const filterByTag = (tag) => {
  autoFilterTag.value = tag
}

const showAllAutoTags = () => {
  autoShowAllTags.value = true
  loadAutoTags({ query: '', showAll: true })
}

const showRecentAutoTags = () => {
  autoTagSearchQuery.value = ''
  autoShowAllTags.value = false
  loadAutoTags({ query: '', showAll: false })
}

let autoTagSearchTimer = null
watch(autoTagSearchQuery, (query) => {
  if (autoTagSearchTimer) {
    clearTimeout(autoTagSearchTimer)
  }

  autoTagSearchTimer = setTimeout(() => {
    const trimmedQuery = query.trim()
    autoShowAllTags.value = false
    loadAutoTags({ query: trimmedQuery, showAll: false })
  }, 250)
})

watch(autoFilterLanguage, () => {
  autoCurrentPage.value = 1
  loadAutoTranslationHistory()
})

watch(autoFilterTag, () => {
  autoCurrentPage.value = 1
  loadAutoTranslationHistory()
})

const getSelectedTaskLanguageName = (task) => {
  if (!task || !task.target_languages || task.target_languages.length === 0) {
    return '翻译后'
  }
  const langCode = task.target_languages[0]
  const langOpt = LANGUAGE_OPTIONS.find(o => o.code === langCode)
  return langOpt ? `${langOpt.name}` : '翻译后'
}

const filterByLanguage = (langCode) => {
  autoFilterLanguage.value = langCode
}

const playExpandedVideo = (item) => {
  currentVideoUrl.value = ''
  autoVideoObjectUrl.value = ''
  autoSelectedHistoryTask.value = {
    original_filename: item.original_filename,
    original_video_url: item.original_video_url || null,
    result_video_url: item.result_video_url || item.videoUrl || null,
    target_languages: item.target_languages || (item.languageCode ? [item.languageCode] : []),
    status: item.status,
    current_stage: item.current_stage
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

    // Update in autoTaskHistory
    const task = autoTaskHistory.value.find(t => t.id === editingAutoTaskId.value)
    if (task) {
      task.original_filename = editingAutoTaskName.value.trim()
    }

    // Update in autoExpandedHistory (for immediate UI update)
    const expandedItems = autoExpandedHistory.value.filter(item => item.taskId === editingAutoTaskId.value)
    expandedItems.forEach(item => {
      item.original_filename = editingAutoTaskName.value.trim()
    })

    cancelEditAutoTaskName()
  } catch (error) {
    console.error('Failed to update auto task name:', error)
    alert('更新失败: ' + (error.response?.data?.detail || error.message))
    cancelEditAutoTaskName()
  }
}

const addAutoTag = () => {
  if (!autoTagInput.value) return
  const tag = autoTagInput.value.trim()
  if (tag && !autoTaskTags.value.includes(tag)) {
    autoTaskTags.value.push(tag)
    autoTagInput.value = ''
  }
}

const removeAutoTag = (tag) => {
  autoTaskTags.value = autoTaskTags.value.filter(t => t !== tag)
}

const selectSavedTag = (tag) => {
  if (!autoTaskTags.value.includes(tag)) {
    autoTaskTags.value.push(tag)
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
  loadAutoTags()
  fetchUserPoints()
  fetchCustomVoices()
})
</script>
