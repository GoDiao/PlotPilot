<template>
  <n-modal
    v-model:show="show"
    preset="card"
    title="涓婚璁剧疆"
    style="width: min(560px, 96vw)"
    :mask-closable="false"
    :segmented="{ content: 'soft', footer: 'soft' }"
  >
    <!-- 鈺愨晲鈺?涓婚閫夋嫨 鈺愨晲鈺?-->
    <div class="theme-section">
      <div class="theme-preview-bar">
        <div
          class="theme-preview-card"
          :class="{
            'is-dark': themeStore.isDark,
            'is-anchor': themeStore.isAnchor,
            'is-paper': themeStore.isPaper,
            'is-ocean': themeStore.isOcean,
          }"
        >
          <div class="preview-header">
            <span class="preview-dot"></span>
            <span class="preview-dot"></span>
            <span class="preview-dot"></span>
          </div>
          <div class="preview-body">
            <div class="preview-line long"></div>
            <div class="preview-line medium"></div>
            <div class="preview-line short"></div>
          </div>
        </div>
      </div>

      <div class="theme-mode-cards">
        <div
          v-for="option in themeOptions"
          :key="option.value"
          class="theme-mode-card"
          :class="{ active: themeStore.mode === option.value }"
          :data-mode="option.value"
          @click="handleThemeChange(option.value)"
        >
          <div class="mode-card-icon" v-html="option.icon"></div>
          <div class="mode-card-info">
            <div class="mode-card-name">{{ option.label }}</div>
            <div class="mode-card-desc">{{ option.desc }}</div>
          </div>
          <div v-if="themeStore.mode === option.value" class="mode-card-check">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
          </div>
        </div>
      </div>

      <n-alert type="info" style="margin-top: 20px" :bordered="false">
        涓婚鍒囨崲浼氱珛鍗崇敓鏁堝苟鑷姩淇濆瓨銆傞€夋嫨銆岃窡闅忕郴缁熴€嶆椂锛屽皢鏍规嵁鎿嶄綔绯荤粺鐨勪寒/鏆楁ā寮忚嚜鍔ㄥ垏鎹€?
      </n-alert>
    </div>
  </n-modal>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMessage } from 'naive-ui'
import { useThemeStore, type ThemeMode } from '@/stores/themeStore'

const show = defineModel<boolean>('show', { default: false })
const message = useMessage()
const themeStore = useThemeStore()

const themeOptions = computed(() => [
  {
    value: 'light' as ThemeMode,
    label: '娴呰壊',
    desc: '清爽明亮的默认主题',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="26" height="26"><circle cx="12" cy="12" r="5" fill="#f59e0b"/><path d="M12 2v2m0 16v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M2 12h2m16 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/></svg>',
  },
  {
    value: 'dark' as ThemeMode,
    label: '娣辫壊',
    desc: '鎶ょ溂鏆楄壊涓婚锛岄€傚悎澶滈棿鍐欎綔',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="26" height="26"><path d="M12 3a9 9 0 109 9c0-.46-.04-.92-.1-1.36A7 7 0 0112 3z" fill="#818cf8"/></svg>',
  },
  {
    value: 'anchor' as ThemeMode,
    label: '榛戦噾',
    desc: '涓绘挱闄愬畾鑹诧紝濂㈠崕鏆楅噾椋庢牸',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="26" height="26"><defs><linearGradient id="ag" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#d4a843"/><stop offset="100%" stop-color="#f5d485"/></linearGradient></defs><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" fill="url(#ag)"/></svg>',
  },
  {
    value: 'paper' as ThemeMode,
    label: '绾搁〉',
    desc: '温润纸感，适合白天长时间写作',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="26" height="26"><path d="M5 3h10l4 4v14H5z" fill="#fff4df" stroke="#8b5e34" stroke-width="1.6"/><path d="M15 3v5h5" fill="none" stroke="#c89b6b" stroke-width="1.6"/><path d="M8 12h8M8 16h6" stroke="#8b5e34" stroke-width="1.7" stroke-linecap="round"/></svg>',
  },
  {
    value: 'ocean' as ThemeMode,
    label: '娣辨捣',
    desc: '鏌斿拰澧ㄨ摑锛岄€傚悎澶滈棿娌夋蹈鍐欎綔',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="26" height="26"><defs><linearGradient id="og" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#76d1c8"/><stop offset="100%" stop-color="#24515a"/></linearGradient></defs><path d="M3 15c3-5 6 3 9-2s6 3 9-2v7H3z" fill="url(#og)"/><path d="M5 8c2-2 4 2 6 0s4 2 8-1" stroke="#76d1c8" stroke-width="2" fill="none" stroke-linecap="round"/></svg>',
  },
  {
    value: 'auto' as ThemeMode,
    label: '璺熼殢绯荤粺',
    desc: '鑷姩鍖归厤鎿嶄綔绯荤粺鍋忓ソ璁剧疆',
    icon: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="26" height="26"><rect x="2" y="4" width="20" height="16" rx="2" stroke="#94a3b8" stroke-width="2" fill="none"/><path d="M8 14h8M10 10h4" stroke="#94a3b8" stroke-width="2" stroke-linecap="round"/></svg>',
  },
])

function handleThemeChange(newMode: ThemeMode) {
  const opt = themeOptions.value.find((o) => o.value === newMode)
  const label = opt?.label ?? newMode

  const applyTheme = () => {
    themeStore.setTheme(newMode)
  }

  if ('startViewTransition' in document) {
    // Chrome/Edge 111+锛氶〉闈㈡埅鍥?+ 浜ゅ弶娣″叆娣″嚭锛屽钩婊戞棤闂儊
    ;(document as Document & { startViewTransition: (cb: () => void) => void })
      .startViewTransition(applyTheme)
  } else {
    // 闄嶇骇锛欳SS transition 鏂规锛團irefox / Safari锛?
    const root = (document as any).documentElement as HTMLElement
    root.classList.add('theme-transitioning')
    applyTheme()
    setTimeout(() => root.classList.remove('theme-transitioning'), 360)
  }

  message.success(`宸插垏鎹㈠埌${label}涓婚`)
}
</script>

<style scoped>
.theme-section {
  min-height: 200px;
}

/* 鈹€鈹€ 棰勮鍗＄墖 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ */
.theme-preview-bar {
  display: flex;
  justify-content: center;
  margin-bottom: 28px;
}

.theme-preview-card {
  width: 260px;
  height: 148px;
  border-radius: 14px;
  overflow: hidden;
  border: 2px solid var(--app-border, #e2e8f0);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    0 4px 16px rgba(15, 23, 42, 0.06),
    0 1px 3px rgba(15, 23, 42, 0.04);
}

.theme-preview-card.is-dark {
  background: #0c1222;
  border-color: #334155;
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.35),
    0 2px 8px rgba(0, 0, 0, 0.2);
}

/* 榛戦噾妯″紡棰勮鍗＄墖锛氶噾鑹茶竟妗?+ 寰噾搴?*/
[data-theme='anchor'] .theme-preview-card.is-dark,
.theme-preview-card.is-anchor {
  background: linear-gradient(145deg, #0d0e14, #12141c);
  border-color: rgba(201, 162, 39, 0.2);
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.4),
    0 2px 8px rgba(201, 162, 39, 0.08),
    inset 0 1px 0 rgba(212, 168, 67, 0.05);
}

.theme-preview-card.is-paper {
  background: #fffaf0;
  border-color: rgba(139, 94, 52, 0.22);
  box-shadow:
    0 5px 18px rgba(94, 69, 45, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.theme-preview-card.is-ocean {
  background: linear-gradient(145deg, #0b171b, #132328);
  border-color: rgba(118, 209, 200, 0.2);
  box-shadow:
    0 6px 24px rgba(0, 0, 0, 0.38),
    0 2px 10px rgba(118, 209, 200, 0.08);
}

.preview-header {
  display: flex;
  gap: 6px;
  padding: 11px 13px;
  background: var(--app-surface-subtle);
  transition: background 0.4s ease;
}

.is-dark .preview-header {
  background: #1a2332;
}

.is-paper .preview-header {
  background: #fbf2e3;
}

.is-ocean .preview-header {
  background: #0e1d22;
}

.preview-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #cbd5e1;
  transition: background 0.4s ease;
}

.is-dark .preview-dot {
  background: #374151;
}

.is-paper .preview-dot {
  background: #d8bd98;
}

.is-ocean .preview-dot {
  background: #24515a;
}

.preview-body {
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 9px;
  background: var(--app-surface);
  transition: background 0.4s ease;
}

.is-dark .preview-body {
  background: #0c1222;
}

.is-paper .preview-body {
  background: #fffaf0;
}

.is-ocean .preview-body {
  background: #132328;
}

.preview-line {
  height: 8px;
  border-radius: 4px;
  background: #e2e8f0;
  transition: background 0.4s ease;
}

.is-dark .preview-line {
  background: #1e293b;
}

.is-paper .preview-line {
  background: #ead7bd;
}

.is-ocean .preview-line {
  background: #1f4148;
}

.preview-line.long { width: 100%; }
.preview-line.medium { width: 70%; }
.preview-line.short { width: 42%; }

/* 鈹€鈹€ 涓夐€夊崱 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ */
.theme-mode-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.theme-mode-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 15px 18px;
  border-radius: 13px;
  border: 1.5px solid var(--app-border, #e2e8f0);
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--app-surface);
}

.theme-mode-card:hover {
  border-color: #a5b4fc;
  background: rgba(79, 70, 229, 0.02);
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.08);
}

.theme-mode-card.active {
  border-color: #4f46e5;
  background: rgba(79, 70, 229, 0.05);
  box-shadow:
    0 0 0 3px rgba(79, 70, 229, 0.08),
    0 2px 8px rgba(79, 70, 229, 0.1);
}

/* 榛戦噾妯″紡婵€娲绘€侊細閲戣壊鍏夋檿 */
.theme-mode-card.active[data-mode="anchor"] {
  border-color: var(--color-gold, #d4a843);
  background: linear-gradient(135deg, rgba(212, 168, 67, 0.06), rgba(245, 212, 133, 0.03));
  box-shadow:
    0 0 0 3px rgba(212, 168, 67, 0.12),
    0 2px 12px rgba(212, 168, 67, 0.15);
}

.theme-mode-card.active[data-mode="paper"] {
  border-color: #8b5e34;
  background: linear-gradient(135deg, rgba(139, 94, 52, 0.08), rgba(255, 250, 240, 0.58));
  box-shadow:
    0 0 0 3px rgba(139, 94, 52, 0.1),
    0 2px 12px rgba(94, 69, 45, 0.13);
}

.theme-mode-card.active[data-mode="ocean"] {
  border-color: #76d1c8;
  background: linear-gradient(135deg, rgba(118, 209, 200, 0.1), rgba(36, 81, 90, 0.08));
  box-shadow:
    0 0 0 3px rgba(118, 209, 200, 0.12),
    0 2px 12px rgba(118, 209, 200, 0.12);
}

.mode-card-icon {
  flex-shrink: 0;
  width: 46px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: var(--app-surface-subtle);
  border: 1px solid var(--app-border, #e2e8f0);
  transition: all 0.2s ease;
}

.theme-mode-card.active .mode-card-icon {
  background: rgba(79, 70, 229, 0.1);
  border-color: rgba(79, 70, 229, 0.2);
}

.theme-mode-card.active[data-mode="anchor"] .mode-card-icon {
  background: rgba(212, 168, 67, 0.1);
  border-color: rgba(212, 168, 67, 0.25);
}

.theme-mode-card.active[data-mode="paper"] .mode-card-icon {
  background: rgba(139, 94, 52, 0.1);
  border-color: rgba(139, 94, 52, 0.25);
}

.theme-mode-card.active[data-mode="ocean"] .mode-card-icon {
  background: rgba(118, 209, 200, 0.12);
  border-color: rgba(118, 209, 200, 0.28);
}

.mode-card-info {
  flex: 1;
  min-width: 0;
}

.mode-card-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--app-text-primary);
}

.mode-card-desc {
  font-size: 12.5px;
  color: var(--app-text-secondary);
  margin-top: 3px;
}

.mode-card-check {
  flex-shrink: 0;
  color: #4f46e5;
  display: flex;
  align-items: center;
}

.theme-mode-card.active[data-mode="anchor"] .mode-card-check {
  color: var(--color-gold, #d4a843);
}

.theme-mode-card.active[data-mode="paper"] .mode-card-check {
  color: #8b5e34;
}

.theme-mode-card.active[data-mode="ocean"] .mode-card-check {
  color: #76d1c8;
}
</style>

<style scoped>
.theme-section {
  min-height: 200px;
}

.theme-preview-bar {
  justify-content: flex-start;
  margin-bottom: 24px;
}

.theme-preview-card {
  width: 100%;
  height: 150px;
  border-radius: 22px;
  border: 1px solid var(--aitext-split-border, #d9d9dd);
  box-shadow: none;
}

.theme-preview-card.is-dark,
.theme-preview-card.is-anchor,
.theme-preview-card.is-ocean {
  background: var(--cohere-green, #003c33);
  border-color: rgba(255,255,255,0.14);
  box-shadow: none;
}

.theme-preview-card.is-paper {
  background: var(--cohere-stone, #eeece7);
  border-color: var(--aitext-split-border, #d9d9dd);
  box-shadow: none;
}

.preview-header {
  background: transparent;
  border-bottom: 1px solid var(--aitext-split-border, #d9d9dd);
}

.is-dark .preview-header,
.is-ocean .preview-header,
.is-anchor .preview-header {
  background: transparent;
  border-bottom-color: rgba(255,255,255,0.14);
}

.preview-dot {
  width: 8px;
  height: 8px;
  background: var(--cohere-coral, #ff7759);
}

.preview-body {
  background: transparent;
  gap: 12px;
  padding: 20px;
}

.preview-line {
  height: 1px;
  border-radius: 0;
  background: var(--cohere-hairline, #d9d9dd);
}

.is-dark .preview-line,
.is-ocean .preview-line,
.is-anchor .preview-line {
  background: rgba(255,255,255,0.22);
}

.theme-mode-cards {
  gap: 0;
  border-top: 1px solid var(--aitext-split-border, #d9d9dd);
}

.theme-mode-card {
  gap: 16px;
  padding: 18px 0;
  border: 0;
  border-bottom: 1px solid var(--aitext-split-border, #d9d9dd);
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.theme-mode-card:hover,
.theme-mode-card.active,
.theme-mode-card.active[data-mode="anchor"],
.theme-mode-card.active[data-mode="paper"],
.theme-mode-card.active[data-mode="ocean"] {
  border-color: var(--aitext-split-border, #d9d9dd);
  background: transparent;
  box-shadow: none;
}

.mode-card-icon {
  width: 42px;
  height: 42px;
  border-radius: 9999px;
  background: var(--cohere-stone, #eeece7);
  border: 1px solid var(--aitext-split-border, #d9d9dd);
}

.theme-mode-card.active .mode-card-icon,
.theme-mode-card.active[data-mode="anchor"] .mode-card-icon,
.theme-mode-card.active[data-mode="paper"] .mode-card-icon,
.theme-mode-card.active[data-mode="ocean"] .mode-card-icon {
  background: var(--cohere-near-black, #17171c);
  border-color: var(--cohere-near-black, #17171c);
  color: #ffffff;
}

.mode-card-name {
  font-family: var(--font-display, sans-serif);
  font-size: 22px;
  font-weight: 400;
  letter-spacing: -0.04em;
}

.mode-card-desc {
  color: var(--app-text-muted, #93939f);
}

.mode-card-check,
.theme-mode-card.active[data-mode="anchor"] .mode-card-check,
.theme-mode-card.active[data-mode="paper"] .mode-card-check,
.theme-mode-card.active[data-mode="ocean"] .mode-card-check {
  color: var(--cohere-coral, #ff7759);
}
</style>
