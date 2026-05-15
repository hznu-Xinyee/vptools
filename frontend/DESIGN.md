# DESIGN.md - Conversational AI Web Interface Design System

## 1. Core Philosophy (核心设计理念)
*   **Minimalism (极简主义):** 消除一切不必要的视觉噪音。UI 是内容的容器，绝不能喧宾夺主。
*   **Content-First (内容优先):** 对话和信息是核心。通过留白和排版来引导视觉焦点。
*   **Monochrome Elegance (黑白灰美学):** 极度克制色彩的使用。仅在绝对必要的状态（如错误、成功、强调）才使用彩色，主色调依赖灰度阶梯。
*   **Fluid & Responsive (流畅且响应式):** 动画必须是克制且迅速的（< 200ms），布局必须完美适配桌面端和移动端。

## 2. Color Palette (色彩规范)
设计必须支持深色（Dark）和浅色（Light）双模式。以深色模式为优先设计基准。

### Dark Mode (深色模式)
*   **Background (主背景):** `#212121` (Tailwind: `neutral-800` / `zinc-800`) - 用于主对话区。
*   **Surface / Sidebar (侧边栏/表面):** `#171717` (Tailwind: `neutral-900` / `zinc-900`) - 用于侧边栏和次要面板。
*   **Primary Text (主文本):** `#ECECEC` (Tailwind: `neutral-200`) - 用于正文和主要标题。
*   **Secondary Text (次文本):** `#B4B4B4` (Tailwind: `neutral-400`) - 用于时间戳、占位符、次要说明。
*   **Borders & Dividers (边框/分割线):** `#383838` (Tailwind: `neutral-700` / `white/10`) - 极细，仅用于微妙的边界划分。
*   **Input Background (输入框背景):** `#2F2F2F` (Tailwind: `neutral-700`) - 微微凸起于主背景。

### Light Mode (浅色模式)
*   **Background (主背景):** `#FFFFFF` - 纯白。
*   **Surface / Sidebar (侧边栏/表面):** `#F9F9F9` (Tailwind: `gray-50`) - 极浅的灰色。
*   **Primary Text (主文本):** `#0D0D0D` (Tailwind: `neutral-900`) - 接近纯黑，保持高对比度。
*   **Secondary Text (次文本):** `#6B7280` (Tailwind: `gray-500`)。
*   **Borders & Dividers (边框/分割线):** `#E5E7EB` (Tailwind: `gray-200`)。

## 3. Typography (排版与字体)
*   **Font Family (字体栈):** 
    *   Sans-serif: `Söhne`, `Inter`, `San Francisco`, `Helvetica Neue`, `sans-serif` (要求现代、干净的无衬线体)。
    *   Monospace: `Fira Code`, `JetBrains Mono`, `ui-monospace` (用于代码块)。
*   **Font Sizes (字号):**
    *   Body (正文): `16px` (移动端可为 `15px`)，行高 `1.5` 到 `1.6`。
    *   Small (小字): `14px`，用于侧边栏列表和 Meta 信息。
    *   H1/H2: `24px` / `20px`，仅在初始欢迎页使用，对话流中极少使用大标题。
*   **Font Weight (字重):**
    *   Regular (400) 用于主体文本。
    *   Medium (500) 用于按钮和导航栏标题。
    *   Semibold (600) 用于强调或代码块头部。

## 4. Layout & Grid (布局规范)
*   **Global Layout:**
    *   Left Sidebar (左侧边栏): 固定宽度 `260px`。在移动端默认隐藏，通过汉堡菜单呼出 (Drawer/Off-canvas)。
    *   Main Content (主内容区): 占据剩余宽度。
*   **Chat Area (对话区):**
    *   **Max Width (最大宽度):** 对话气泡或文本块的最大宽度限制在 `768px`（针对大屏），确保阅读视线的舒适度（约 65-75 个字符每行）。
    *   **Alignment (对齐):** 整体居中对齐。AI 的回答和 User 的提问在视觉流上保持统一的左对齐，但可以通过不同的头像（Avatar）或极轻微的背景色差进行区分。
*   **Bottom Input Area (底部输入区):**
    *   固定在屏幕底部（Sticky bottom）。
    *   背景需使用渐变遮罩（Gradient mask）或毛玻璃效果（Backdrop-blur），以防文字与滚动内容重叠。
    *   输入框最大宽度同对话区（`768px`），随内容自动增高（Auto-expand textarea），最高限制在 `200px` 左右，超出滚动。

## 5. UI Components (核心组件约束)

### 5.1 Buttons (按钮)
*   **Primary (主按钮):** 纯色背景（深色模式下用纯白/极浅灰，浅色模式下用纯黑），文本反色。无边框，极小圆角 (`rounded-md` 约 6px)。
*   **Ghost / Icon Button (幽灵/图标按钮):** 透明背景，悬停（Hover）时出现 `#ececec1a` (深色) 或 `#0000000d` (浅色) 的极淡背景色。用于点赞、复制、重新生成等操作。

### 5.2 Code Blocks (代码块)
*   **Background:** 必须是深色（如 `#000000` 或 `#1E1E1E`），即使在浅色模式下也保持深色，以符合程序员习惯。
*   **Header:** 顶部包含语言名称和“Copy code”按钮。Header 背景色略浅于代码区（如 `#2D2D2D`）。
*   **Border Radius:** `8px` (`rounded-lg`)。
*   **Syntax Highlighting:** 采用低饱和度的语法高亮配色（如类似 VSC Dark+ 或 One Dark）。

### 5.3 Inputs (输入组件)
*   **Padding:** 内部填充充裕（如 `p-3` 或 `p-4`）。
*   **Border:** 默认状态无明显边框（或与背景同色），Focus 状态下仅有轻微的外发光（Ring）或边框颜色加深，绝不使用刺眼的强调色（如亮蓝）。
*   **Shadow:** 轻微的阴影 (`shadow-sm`) 使输入框从背景中微微浮起。

## 6. Animations & Transitions (动画与过渡)
*   **Speed:** 快速且利落。过渡时间控制在 `150ms` - `200ms`。
*   **Easing:** `ease-in-out`。
*   **Usage:** 仅用于 Hover 状态改变、侧边栏展开/收起、弹窗呼出。绝不使用弹跳（Bouncy）或夸张的入场动画。
*   **Streaming Text:** AI 生成文本时，文字应该逐字或逐块平滑出现，不应有卡顿感。光标（Cursor）闪烁频率为标准系统频率。

## 7. AI Code Generation Instructions (针对 AI 生成代码的强制指令)
在编写 Vue/React/HTML 结构时，必须严格遵守以下准则：
1.  **禁止发明颜色：** 仅使用本规范中定义的黑、白、灰、透明色阶。
2.  **拒绝冗余装饰：** 不得使用卡片阴影（除了输入框和下拉菜单）、复杂的渐变色（除非是底部遮罩）或圆角超过 `12px` 的元素。
3.  **Tailwind 优先：** 如果使用 Tailwind CSS，请大量使用 `neutral` 色板，`max-w-3xl`（用于主内容宽），`mx-auto`（用于居中），以及 `ring-0`，`focus:outline-none` 等原子类来覆盖浏览器默认样式。
4.  **像素级精确：** 确保所有的 Padding 和 Margin 遵循 4px 或 8px 的倍数（如 `p-2`, `mb-4`）。