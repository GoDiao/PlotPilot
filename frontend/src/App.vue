<script setup lang="ts">
import { computed } from 'vue'
import { NConfigProvider, NMessageProvider, NDialogProvider, zhCN, dateZhCN, darkTheme } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import { useThemeStore } from './stores/themeStore'

const themeStore = useThemeStore()

const naiveTheme = computed(() =>
  themeStore.isDark ? darkTheme : undefined
)

// ─── 静态调色板（不随主题变化，提升出来避免 computed 重建字符串）─────────────
const LIGHT_PALETTE = {
  primary:        '#17171c',
  primaryHover:   '#000000',
  primaryPressed: '#003c33',
  primarySuppl:   '#1863dc',
  text1:          '#212121',
  text2:          '#575760',
  text3:          '#93939f',
  border:         '#d9d9dd',
  divider:        '#e5e7eb',
  surface:        '#ffffff',
  tableStriped:   '#fbfbfa',
  tableHover:     '#eeece7',
  inputBg:        '#ffffff',
  drawerBg:       '#eeece7',
  selectBorder:   '#9b60aa',
} as const

const DARK_PALETTE = {
  primary:        '#ffffff',
  primaryHover:   '#edfce9',
  primaryPressed: '#ffad9b',
  primarySuppl:   '#ff7759',
  text1:          '#f7faf7',
  text2:          '#cbd7d4',
  text3:          '#8fa39e',
  border:         'rgba(237, 252, 233, 0.16)',
  divider:        'rgba(237, 252, 233, 0.10)',
  surface:        '#071829',
  tableStriped:   '#0b2233',
  tableHover:     '#102b3f',
  inputBg:        '#06131f',
  drawerBg:       '#001f1b',
  selectBorder:   '#ffad9b',
} as const

const ANCHOR_PALETTE = {
  primary:        '#c9a227',
  primaryHover:   '#ddb930',
  primaryPressed: '#a88a1f',
  primarySuppl:   '#e8c84a',
  text1:          '#f0ead6',
  text2:          '#c4b99a',
  text3:          '#8a8070',
  border:         'rgba(201, 162, 39, 0.14)',
  divider:        'rgba(201, 162, 39, 0.06)',
  surface:        '#111620',
  tableStriped:   '#0d1018',
  tableHover:     '#181f2e',
  inputBg:        '#0d1018',
  drawerBg:       '#0a0c10',
  selectBorder:   '#c9a227',
} as const

const PAPER_PALETTE = {
  primary:        '#8b5e34',
  primaryHover:   '#a16f43',
  primaryPressed: '#6f4728',
  primarySuppl:   '#c89b6b',
  text1:          '#2f251c',
  text2:          '#5d4b3d',
  text3:          '#827064',
  border:         'rgba(94, 69, 45, 0.14)',
  divider:        'rgba(94, 69, 45, 0.08)',
  surface:        '#fffaf0',
  tableStriped:   '#fbf2e3',
  tableHover:     '#f8edda',
  inputBg:        '#fffdf7',
  drawerBg:       '#f4ead8',
  selectBorder:   '#8b5e34',
} as const

const OCEAN_PALETTE = {
  primary:        '#76d1c8',
  primaryHover:   '#9be1da',
  primaryPressed: '#4db7ad',
  primarySuppl:   '#b7eee8',
  text1:          '#e7f3f1',
  text2:          '#b8cfcc',
  text3:          '#7f9f9b',
  border:         'rgba(118, 209, 200, 0.14)',
  divider:        'rgba(118, 209, 200, 0.08)',
  surface:        '#132328',
  tableStriped:   '#0e1d22',
  tableHover:     '#1a3036',
  inputBg:        '#0e1d22',
  drawerBg:       '#0b171b',
  selectBorder:   '#76d1c8',
} as const

// 形状与间距等静态覆盖，与主题无关，freeze 后永不重建
const SHAPE_OVERRIDES: GlobalThemeOverrides = Object.freeze({
  common: {
    borderRadius:      '16px',
    borderRadiusSmall: '8px',
    fontSize:          '14px',
    fontSizeMedium:    '15px',
    lineHeight:        '1.5',
    heightMedium:      '40px',
  },
  Card:       { borderRadius: '22px', paddingMedium: '24px' },
  Button:     { borderRadiusMedium: '32px', borderRadiusSmall: '30px' },
  Input:      { borderRadius: '8px' },
  Scrollbar:  { width: '8px', height: '8px', borderRadius: '4px' },
  DataTable:  { borderRadius: '8px', thFontWeight: '500' },
  Tag:        { borderRadius: '30px' },
  Progress:   { railBorderRadius: '4px', fillBorderRadius: '4px' },
  Drawer:     { bodyPadding: '0' },
  Alert:      { border: 'none' },
})

// ─── 只有颜色部分是动态的，量少性能好 ─────────────────────────────────────
const themeOverrides = computed<GlobalThemeOverrides>(() => {
  const p = themeStore.isAnchor ? ANCHOR_PALETTE
          : themeStore.isOcean  ? OCEAN_PALETTE
          : themeStore.isPaper  ? PAPER_PALETTE
          : themeStore.isDark   ? DARK_PALETTE
          :                       LIGHT_PALETTE

  return {
    ...SHAPE_OVERRIDES,
    common: {
      ...SHAPE_OVERRIDES.common,
      primaryColor:        p.primary,
      primaryColorHover:   p.primaryHover,
      primaryColorPressed: p.primaryPressed,
      primaryColorSuppl:   p.primarySuppl,
      bodyColor:           p.text1,
      textColor1:          p.text1,
      textColor2:          p.text2,
      textColor3:          p.text3,
      borderColor:         p.border,
      dividerColor:        p.divider,
      cardColor:           p.surface,
      modalColor:          p.surface,
      popoverColor:        p.surface,
      tableColor:          p.surface,
      tableColorStriped:   p.tableStriped,
      tableColorHover:     p.tableHover,
      tableHeaderColor:    p.surface,
    },
    Select: {
      peers: {
        InternalSelection: {
          color:       p.inputBg,
          borderActive: p.selectBorder,
          borderFocus:  p.selectBorder,
        },
      },
    },
    Drawer: { ...SHAPE_OVERRIDES.Drawer, color: p.drawerBg },
    Tabs: {
      tabTextColorActiveLine: p.primary,
      tabTextColorHoverLine:  p.text2,
      barColor:               p.primary,
    },
    Switch: { railColorActive: p.primary },
    Alert:  { ...SHAPE_OVERRIDES.Alert, color: p.surface },
    Form:   { labelTextColorTop: p.text2 },
  }
})
</script>

<template>
  <n-config-provider
    :locale="zhCN"
    :date-locale="dateZhCN"
    :theme="naiveTheme"
    :theme-overrides="themeOverrides"
  >
    <n-message-provider>
      <n-dialog-provider>
        <router-view v-slot="{ Component }">
          <transition name="app-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<style>
.app-fade-enter-active,
.app-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.app-fade-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.app-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
