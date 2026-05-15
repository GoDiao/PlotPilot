<template>
  <div class="cc-panel">
    <n-empty v-if="!currentChapterNumber" description="请先从左侧选择一个章节" style="margin-top: 40px" />

    <n-scrollbar v-else class="cc-scroll">
      <n-space vertical :size="12" style="padding: 8px 4px 16px">
        <n-alert v-if="readOnly" type="warning" :show-icon="true" size="small">
          托管运行中：仅可查看
        </n-alert>

        <!-- 本章规划 -->
        <n-card v-if="chapterPlan" size="small" :bordered="true" class="cc-card-plan">
          <template #header>
            <span class="card-title">📋 本章规划</span>
          </template>
          <n-descriptions :column="1" label-placement="left" size="small" label-style="white-space: nowrap">
            <n-descriptions-item label="标题">{{ chapterPlan.title || '—' }}</n-descriptions-item>
            <n-descriptions-item v-if="chapterPlan.outline" label="大纲">
              <n-text style="font-size: 12px; white-space: pre-wrap">{{ chapterPlan.outline }}</n-text>
            </n-descriptions-item>
            <n-descriptions-item v-if="chapterPlan.pov_character_id" label="视角">
              {{ getCharacterName(chapterPlan.pov_character_id) }}
            </n-descriptions-item>
            <n-descriptions-item v-if="chapterPlan.timeline_start || chapterPlan.timeline_end" label="时间线">
              {{ chapterPlan.timeline_start || '—' }} → {{ chapterPlan.timeline_end || '—' }}
            </n-descriptions-item>
            <n-descriptions-item v-if="planMoodLine" label="基调">
              {{ planMoodLine }}
            </n-descriptions-item>
          </n-descriptions>
        </n-card>

        <!-- 节拍规划 -->
        <n-card v-if="hasChapterBlueprint" size="small" :bordered="true" class="cc-card-blueprint">
          <template #header>
            <span class="card-title">📘 本章蓝图</span>
          </template>
          <n-space vertical :size="10">
            <div class="blueprint-summary-grid">
              <div v-if="chapterBlueprint?.narrative_function" class="blueprint-summary-item">
                <span class="blueprint-label">章节功能</span>
                <strong>{{ chapterBlueprint.narrative_function }}</strong>
              </div>
              <div v-if="chapterBlueprint?.target_tension" class="blueprint-summary-item">
                <span class="blueprint-label">目标张力</span>
                <n-tag size="small" :type="tensionTagType(chapterBlueprint.target_tension)">
                  {{ chapterBlueprint.target_tension }}/10
                </n-tag>
              </div>
              <div v-if="chapterBlueprint?.tension_phase" class="blueprint-summary-item">
                <span class="blueprint-label">张力阶段</span>
                <strong>{{ chapterBlueprint.tension_phase }}</strong>
              </div>
              <div v-if="chapterBlueprint?.pov" class="blueprint-summary-item">
                <span class="blueprint-label">POV</span>
                <strong>{{ chapterBlueprint.pov }}</strong>
              </div>
            </div>

            <n-descriptions :column="1" label-placement="top" size="small">
              <n-descriptions-item v-if="chapterBlueprint?.outline" label="蓝图大纲">
                <n-text class="blueprint-text">{{ chapterBlueprint.outline }}</n-text>
              </n-descriptions-item>
              <n-descriptions-item v-if="chapterBlueprintList('must_happen').length" label="必写事件">
                <div class="blueprint-chip-list">
                  <n-tag v-for="item in chapterBlueprintList('must_happen')" :key="item" size="small" type="success">
                    {{ item }}
                  </n-tag>
                </div>
              </n-descriptions-item>
              <n-descriptions-item v-if="chapterBlueprintList('must_not_happen').length" label="禁写事项">
                <div class="blueprint-chip-list">
                  <n-tag v-for="item in chapterBlueprintList('must_not_happen')" :key="item" size="small" type="warning">
                    {{ item }}
                  </n-tag>
                </div>
              </n-descriptions-item>
              <n-descriptions-item v-if="chapterBlueprint?.handoff_to_next" label="章末承接">
                <n-text class="blueprint-text">{{ chapterBlueprint.handoff_to_next }}</n-text>
              </n-descriptions-item>
              <n-descriptions-item v-if="chapterBlueprintList('characters').length" label="登场角色">
                <div class="blueprint-chip-list">
                  <n-tag v-for="item in chapterBlueprintList('characters')" :key="item" size="small">
                    {{ item }}
                  </n-tag>
                </div>
              </n-descriptions-item>
              <n-descriptions-item v-if="chapterBlueprintList('locations').length" label="地点">
                <div class="blueprint-chip-list">
                  <n-tag v-for="item in chapterBlueprintList('locations')" :key="item" size="small" type="info">
                    {{ item }}
                  </n-tag>
                </div>
              </n-descriptions-item>
              <n-descriptions-item v-if="chapterBlueprintList('foreshadowing_actions').length" label="伏笔动作">
                <div class="blueprint-chip-list">
                  <n-tag v-for="item in chapterBlueprintList('foreshadowing_actions')" :key="item" size="small" type="error">
                    {{ item }}
                  </n-tag>
                </div>
              </n-descriptions-item>
            </n-descriptions>
          </n-space>
        </n-card>

        <n-card v-if="showBeatsCard" size="small" :bordered="true">
          <template #header>
            <span class="card-title">🎬 节拍规划</span>
          </template>
          <n-tabs type="segment" size="small" animated>
            <n-tab-pane name="macro" tab="宏观">
              <n-text depth="3" style="font-size: 11px; display: block; margin-bottom: 8px">
                章节大纲 — 作者意图总览
              </n-text>
              <div v-if="chapterPlan?.outline?.trim()" class="macro-outline-text">
                {{ chapterPlan.outline }}
              </div>
              <n-empty v-else description="暂无大纲数据" size="small" />
            </n-tab-pane>
            
            <n-tab-pane name="micro" tab="微观">
              <n-text depth="3" style="font-size: 11px; display: block; margin-bottom: 8px">
                写作时智能拆分，控制节奏和感官细节；下方为本章节拍（优先展示落库的微观节拍，否则与叙事节拍/大纲一致）
              </n-text>
              <n-space v-if="microBeats.length" vertical :size="8" style="margin-top: 12px">
                <div v-for="(beat, i) in microBeats" :key="i" class="micro-beat-item">
                  <div class="micro-beat-header">
                    <n-tag :type="getBeatTypeColor(beat.focus)" size="small" round>
                      {{ beatFocusLabel(beat.focus) }}
                    </n-tag>
                    <n-text strong style="margin-left: 8px">节拍 {{ i + 1 }}</n-text>
                    <n-text
                      v-if="beat.target_words > 0"
                      depth="3"
                      style="margin-left: 8px; font-size: 12px"
                    >
                      （约 {{ beat.target_words }} 字）
                    </n-text>
                  </div>
                  <div class="micro-beat-desc">{{ beat.description }}</div>
                </div>
              </n-space>
              <n-empty v-else description="暂无节拍：请在知识库填写本章叙事节拍，或待章节生成/审阅落库后自动写入" size="small" />
            </n-tab-pane>
          </n-tabs>
        </n-card>

        <n-alert v-if="storyNodeNotFound" type="warning" :show-icon="true">
          未在结构树中找到第 {{ currentChapterNumber }} 章的规划节点
        </n-alert>

        <!-- 全托管管线摘要 -->
        <n-card
          v-if="autopilotChapterReview && currentChapterNumber === autopilotChapterReview.chapter_number"
          size="small"
          :bordered="true"
        >
          <template #header>
            <span class="card-title">🤖 自动审阅</span>
          </template>
          <n-space vertical :size="8">
            <div class="review-row">
              <n-text depth="3">张力</n-text>
              <div class="tension-bar">
                <div class="tension-fill" :style="{ width: `${autopilotChapterReview.tension * 10}%` }"></div>
                <n-text class="tension-value">{{ autopilotChapterReview.tension }}/10</n-text>
              </div>
            </div>
            <div class="review-row">
              <n-text depth="3">叙事同步</n-text>
              <n-tag
                :type="autopilotChapterReview.narrative_sync_ok ? 'success' : 'warning'"
                size="small"
                round
              >
                {{ autopilotChapterReview.narrative_sync_ok ? '已落库' : '异常' }}
              </n-tag>
            </div>
            <div class="review-row">
              <n-text depth="3">文风相似度</n-text>
              <n-text>
                {{
                  autopilotChapterReview.similarity_score != null
                    ? Number(autopilotChapterReview.similarity_score).toFixed(3)
                    : '—'
                }}
              </n-text>
            </div>
            <div class="review-row">
              <n-text depth="3">漂移告警</n-text>
              <n-tag :type="autopilotChapterReview.drift_alert ? 'error' : 'success'" size="small" round>
                {{ autopilotChapterReview.drift_alert ? '是' : '否' }}
              </n-tag>
            </div>
            <div v-if="autopilotChapterReview.at" class="review-row">
              <n-text depth="3">审阅时间</n-text>
              <n-text depth="3" style="font-size: 12px">{{ formatTime(autopilotChapterReview.at) }}</n-text>
            </div>
          </n-space>
        </n-card>
      </n-space>
    </n-scrollbar>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useWorkbenchRefreshStore } from '../../stores/workbenchRefreshStore'
import { planningApi } from '../../api/planning'
import type { ChapterBlueprint, StoryNode } from '../../api/planning'
import { knowledgeApi } from '../../api/knowledge'
import type { ChapterSummary } from '../../api/knowledge'
import { bibleApi, type CharacterDTO } from '../../api/bible'
import type { AutopilotChapterAudit } from './ChapterStatusPanel.vue'

const props = withDefaults(
  defineProps<{
    slug: string
    currentChapterNumber?: number | null
    readOnly?: boolean
    autopilotChapterReview?: AutopilotChapterAudit | null
  }>(),
  {
    currentChapterNumber: null,
    readOnly: false,
    autopilotChapterReview: null,
  }
)

const storyNodeNotFound = ref(false)
const chapterPlan = ref<StoryNode | null>(null)
const knowledgeChapter = ref<ChapterSummary | null>(null)

// Bible 数据用于 ID -> name 映射
const bibleCharacters = ref<CharacterDTO[]>([])

// 获取人物名称
const getCharacterName = (charId: string): string => {
  const char = bibleCharacters.value.find(c => c.id === charId)
  return char ? char.name : charId
}

const planMoodLine = computed(() => {
  const m = chapterPlan.value?.metadata
  if (!m || typeof m !== 'object') return ''
  const mood = m.mood ?? m.emotion ?? m.tone
  if (typeof mood === 'string' && mood.trim()) return mood
  if (Array.isArray(m.moods) && m.moods.length) return m.moods.join('、')
  return ''
})

const chapterBlueprint = computed<ChapterBlueprint | null>(() => {
  const raw = chapterPlan.value?.metadata?.blueprint
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return null
  return raw as ChapterBlueprint
})

const hasChapterBlueprint = computed(() => {
  const blueprint = chapterBlueprint.value
  if (!blueprint) return false
  return Object.values(blueprint).some(value => {
    if (Array.isArray(value)) return value.some(item => String(item || '').trim())
    if (typeof value === 'number') return Number.isFinite(value)
    return String(value ?? '').trim().length > 0
  })
})

function chapterBlueprintList(key: keyof ChapterBlueprint): string[] {
  const value = chapterBlueprint.value?.[key]
  if (!Array.isArray(value)) return []
  return value.map(item => String(item || '').trim()).filter(Boolean)
}

function tensionTagType(value: number): 'success' | 'warning' | 'error' | 'info' | 'default' {
  if (value >= 8) return 'error'
  if (value >= 6) return 'warning'
  if (value >= 3) return 'info'
  return 'success'
}

const BEAT_LINE_CAP = 48
/** 与后端 chapter_narrative_sync._beats_from_structure_outline 一致：先按换行，再按句读拆，避免一整段只算一条节拍 */
const BEAT_SENTENCE_SPLIT = /[；;。！？!?]+/

function expandRawBeatLines(raw: string[]): string[] {
  const out: string[] = []
  for (const line of raw) {
    const t = String(line || '').trim()
    if (!t) continue
    const byNewline = t.split(/\n+/).map(s => s.trim()).filter(Boolean)
    for (const chunk of byNewline) {
      const subs = chunk.split(BEAT_SENTENCE_SPLIT).map(s => s.trim()).filter(Boolean)
      if (subs.length <= 1) {
        out.push(chunk)
      } else {
        out.push(...subs)
      }
      if (out.length >= BEAT_LINE_CAP) {
        return out.slice(0, BEAT_LINE_CAP)
      }
    }
  }
  return out.slice(0, BEAT_LINE_CAP)
}

const beatLines = computed(() => {
  const k = knowledgeChapter.value
  let raw: string[] = []
  if (k?.beat_sections?.length) {
    raw = k.beat_sections.map(s => String(s || '').trim()).filter(Boolean)
  } else {
    const ol = chapterPlan.value?.outline?.trim()
    if (!ol) return []
    raw = ol.split(/\n+/).map(s => s.trim()).filter(s => s.length > 0)
  }
  return expandRawBeatLines(raw)
})

const showBeatsCard = computed(() => {
  if (!props.currentChapterNumber) return false
  if (beatLines.value.length > 0) return true
  return !!(chapterPlan.value?.outline?.trim() || knowledgeChapter.value)
})

interface MicroBeat {
  description: string
  target_words: number
  focus: string
}

const BEAT_FOCUS_LABELS: Record<string, string> = {
  sensory: '感官',
  dialogue: '对话',
  action: '动作',
  emotion: '情绪',
  pacing: '节奏',
  transition: '过渡',
}

function beatFocusLabel(focus: string): string {
  const key = (focus || '').trim()
  if (BEAT_FOCUS_LABELS[key]) return BEAT_FOCUS_LABELS[key]
  if (!key) return '节拍'
  return key
}

function normalizeMicroBeatItems(raw: unknown[]): MicroBeat[] {
  const out: MicroBeat[] = []
  for (const item of raw) {
    if (item == null) continue
    if (typeof item === 'string') {
      const d = item.trim()
      if (d) out.push({ description: d, target_words: 0, focus: 'pacing' })
      continue
    }
    if (typeof item === 'object' && !Array.isArray(item)) {
      const o = item as Record<string, unknown>
      const desc = String(o.description ?? o.text ?? o.summary ?? '').trim()
      if (!desc) continue
      const tw = o.target_words
      const targetWords =
        typeof tw === 'number' && Number.isFinite(tw)
          ? tw
          : typeof tw === 'string' && tw.trim() !== '' && Number.isFinite(Number(tw))
            ? Number(tw)
            : 0
      const focus = String(o.focus ?? o.type ?? 'pacing').trim() || 'pacing'
      out.push({ description: desc, target_words: targetWords, focus })
    }
  }
  return out
}

/** 结构化微观节拍（micro_beats）；若无则用 beat_sections / 大纲行作为可读占位，与「宏观」同源数据、卡片化展示 */
const microBeats = computed<MicroBeat[]>(() => {
  const k = knowledgeChapter.value
  if (k?.micro_beats && Array.isArray(k.micro_beats) && k.micro_beats.length > 0) {
    const parsed = normalizeMicroBeatItems(k.micro_beats as unknown[])
    if (parsed.length > 0) return parsed
  }
  const lines = beatLines.value
  if (lines.length > 0) {
    return lines.map(line => ({
      description: line,
      target_words: 0,
      focus: 'pacing',
    }))
  }
  return []
})

const getBeatTypeColor = (focus: string): 'success' | 'warning' | 'error' | 'info' | 'default' => {
  const colorMap: Record<string, 'success' | 'warning' | 'error' | 'info' | 'default'> = {
    sensory: 'info',
    dialogue: 'success',
    action: 'warning',
    emotion: 'error',
    pacing: 'default',
    transition: 'info',
  }
  return colorMap[focus] || 'default'
}

function formatTime(t: string) {
  try {
    return new Date(t).toLocaleString('zh-CN', {
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return t
  }
}

function findChapterNode(nodes: StoryNode[], num: number): StoryNode | null {
  for (const node of nodes) {
    if (node.node_type === 'chapter' && node.number === num) return node
    if (node.children?.length) {
      const found = findChapterNode(node.children, num)
      if (found) return found
    }
  }
  return null
}

const resolveStoryNode = async () => {
  chapterPlan.value = null
  storyNodeNotFound.value = false
  if (!props.currentChapterNumber) return
  try {
    const res = await planningApi.getStructure(props.slug)
    const roots = res.data?.nodes ?? []
    const node = findChapterNode(roots, props.currentChapterNumber)
    if (node) {
      chapterPlan.value = node
    } else {
      storyNodeNotFound.value = true
    }
  } catch {
    storyNodeNotFound.value = true
  }
}

async function loadKnowledgeChapter() {
  knowledgeChapter.value = null
  if (!props.slug || !props.currentChapterNumber) return
  try {
    const k = await knowledgeApi.getKnowledge(props.slug)
    const row = k.chapters?.find(c => c.chapter_id === props.currentChapterNumber)
    knowledgeChapter.value = row ?? null
  } catch {
    knowledgeChapter.value = null
  }
}

// 加载 Bible 数据用于名称映射
async function loadBible() {
  try {
    const bible = await bibleApi.getBible(props.slug)
    bibleCharacters.value = bible.characters || []
  } catch {
    bibleCharacters.value = []
  }
}

watch(() => props.slug, async (slug) => {
  if (slug) {
    chapterPlan.value = null
    storyNodeNotFound.value = false
    await Promise.all([
      loadBible(),
      resolveStoryNode(),
      loadKnowledgeChapter()
    ])
  }
})

watch(() => props.currentChapterNumber, async () => {
  await resolveStoryNode()
  await loadKnowledgeChapter()
}, { immediate: false })

const refreshStore = useWorkbenchRefreshStore()
const { deskTick } = storeToRefs(refreshStore)
watch(deskTick, async () => {
  await resolveStoryNode()
  await loadKnowledgeChapter()
})

onMounted(async () => {
  await loadBible()
  await resolveStoryNode()
  await loadKnowledgeChapter()
})
</script>

<style scoped>
.cc-panel {
  padding: 0;
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.cc-scroll {
  flex: 1;
  min-height: 0;
}

.card-title {
  font-size: 13px;
  font-weight: 600;
}

.cc-card-blueprint {
  background: linear-gradient(135deg, rgba(14, 165, 233, 0.06), rgba(99, 102, 241, 0.04));
  border-color: rgba(99, 102, 241, 0.16);
}

.blueprint-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.blueprint-summary-item {
  min-width: 0;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(99, 102, 241, 0.12);
}

.blueprint-label {
  display: block;
  margin-bottom: 4px;
  color: var(--n-text-color-3);
  font-size: 11px;
}

.blueprint-text {
  display: block;
  font-size: 12px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.blueprint-chip-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* 节拍列表 */
.cc-beat-list {
  margin: 8px 0 0;
  padding-left: 1.2em;
  font-size: 12px;
  line-height: 1.8;
}

/* 宏观大纲 */
.macro-outline-text {
  font-size: 15px;
  line-height: 1.9;
  color: var(--n-text-color-1);
  white-space: pre-wrap;
}

/* 微观节拍 */
.micro-beat-item {
  padding: 12px 14px;
  border-radius: 10px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.04) 0%, rgba(139, 92, 246, 0.02) 100%);
  border: 1px solid rgba(99, 102, 241, 0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.micro-beat-item:hover {
  border-color: rgba(99, 102, 241, 0.2);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.06) 0%, rgba(139, 92, 246, 0.04) 100%);
}

.micro-beat-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.micro-beat-desc {
  margin-top: 6px;
  padding-left: 12px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--n-text-color-2);
  border-left: 2px solid var(--n-border-color);
}

.micro-beat-item:hover .micro-beat-desc {
  border-left-color: var(--n-primary-color);
}

/* 审阅行 */
.review-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

/* 张力进度条 */
.tension-bar {
  position: relative;
  width: 100px;
  height: 20px;
  background: var(--n-color-modal);
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--n-border-color);
}

.tension-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #f59e0b, #ef4444);
  border-radius: 10px;
  transition: width 0.3s ease;
}

.tension-value {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 11px;
  font-weight: 600;
  color: var(--n-text-color-1);
}
</style>
