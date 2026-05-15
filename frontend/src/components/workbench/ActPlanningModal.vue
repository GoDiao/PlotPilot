<template>
  <n-modal
    v-model:show="show"
    preset="card"
    style="width: min(920px, 96vw)"
    :mask-closable="false"
    :segmented="{ content: true, footer: 'soft' }"
    :title="`规划章节 — ${actTitle}`"
  >
    <template #header-extra>
      <n-text depth="3" style="font-size: 12px">AI 为本幕生成章节大纲，确认后写入结构树</n-text>
    </template>

    <!-- 生成前：配置 -->
    <n-space v-if="!generated" vertical :size="16">
      <n-alert type="info" :show-icon="true">
        AI 将根据本幕的叙事目标与 Bible 信息，自动为每章生成标题和大纲。生成后可编辑再确认。
      </n-alert>

      <n-form-item label="本幕章节数" :show-feedback="false">
        <n-input-number
          v-model:value="chapterCount"
          :min="2"
          :max="20"
          :disabled="loading"
          style="width: 120px"
        />
        <n-text depth="3" style="margin-left: 8px; font-size: 12px">（不填则由 AI 自主决定）</n-text>
      </n-form-item>

      <n-space justify="end" :size="10">
        <n-button :disabled="loading" @click="close">取消</n-button>
        <n-button type="primary" :loading="loading" @click="generate">AI 生成章节规划</n-button>
      </n-space>
    </n-space>

    <!-- 生成后：预览 + 编辑 -->
    <n-space v-else vertical :size="16">
      <n-alert type="success" :show-icon="true">
        已生成 {{ chapters.length }} 章规划，可在下方直接修改标题或大纲后确认。
      </n-alert>

      <n-card v-if="actBlueprint" size="small" embedded>
        <n-space vertical :size="8">
          <n-text strong>本幕蓝图</n-text>
          <n-grid :cols="2" :x-gap="10" :y-gap="8" responsive="screen">
            <n-form-item-gi label="幕级梗概" :show-feedback="false">
              <n-input v-model:value="actBlueprint.synopsis" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" size="small" />
            </n-form-item-gi>
            <n-form-item-gi label="叙事目标" :show-feedback="false">
              <n-input v-model:value="actBlueprint.narrative_goal" type="textarea" :autosize="{ minRows: 2, maxRows: 4 }" size="small" />
            </n-form-item-gi>
            <n-form-item-gi label="核心冲突" :show-feedback="false">
              <n-input v-model:value="actBlueprint.core_conflict" size="small" />
            </n-form-item-gi>
            <n-form-item-gi label="交给下一幕" :show-feedback="false">
              <n-input v-model:value="actBlueprint.handoff_to_next" size="small" />
            </n-form-item-gi>
          </n-grid>
        </n-space>
      </n-card>

      <n-scrollbar style="max-height: 52vh">
        <n-space vertical :size="8" style="padding-right: 8px">
          <n-card
            v-for="(ch, idx) in chapters"
            :key="idx"
            size="small"
            :bordered="true"
            style="background: var(--n-color)"
          >
            <n-space vertical :size="6">
              <n-input
                v-model:value="ch.title"
                placeholder="章节标题"
                :disabled="confirming"
                size="small"
              />
              <n-input
                v-model:value="ch.outline"
                type="textarea"
                placeholder="本章大纲"
                :autosize="{ minRows: 2, maxRows: 5 }"
                :disabled="confirming"
                size="small"
              />
              <n-grid :cols="3" :x-gap="8" :y-gap="6" responsive="screen">
                <n-form-item-gi label="本章功能" :show-feedback="false">
                  <n-input v-model:value="ch.blueprint.narrative_function" placeholder="setup/rise/cooldown..." size="small" :disabled="confirming" />
                </n-form-item-gi>
                <n-form-item-gi label="目标张力" :show-feedback="false">
                  <n-input-number v-model:value="ch.blueprint.target_tension" :min="1" :max="10" size="small" :disabled="confirming" style="width: 100%" />
                </n-form-item-gi>
                <n-form-item-gi label="张力阶段" :show-feedback="false">
                  <n-input v-model:value="ch.blueprint.tension_phase" placeholder="铺垫/升温/爆点/余波" size="small" :disabled="confirming" />
                </n-form-item-gi>
              </n-grid>
              <n-grid :cols="2" :x-gap="8" :y-gap="6" responsive="screen">
                <n-form-item-gi label="必写事件" :show-feedback="false">
                  <n-input
                    :value="listToText(ch.blueprint.must_happen)"
                    type="textarea"
                    :autosize="{ minRows: 2, maxRows: 4 }"
                    size="small"
                    :disabled="confirming"
                    @update:value="(v: string) => ch.blueprint.must_happen = textToList(v)"
                  />
                </n-form-item-gi>
                <n-form-item-gi label="禁写/禁提前泄露" :show-feedback="false">
                  <n-input
                    :value="listToText(ch.blueprint.must_not_happen)"
                    type="textarea"
                    :autosize="{ minRows: 2, maxRows: 4 }"
                    size="small"
                    :disabled="confirming"
                    @update:value="(v: string) => ch.blueprint.must_not_happen = textToList(v)"
                  />
                </n-form-item-gi>
              </n-grid>
              <n-input
                v-model:value="ch.blueprint.handoff_to_next"
                placeholder="章末承接点：下一章必须从哪里接住"
                size="small"
                :disabled="confirming"
              />
              <n-space :size="6">
                <n-tag v-for="el in ch.bible_elements" :key="el" size="small" round>{{ el }}</n-tag>
              </n-space>
            </n-space>
          </n-card>
        </n-space>
      </n-scrollbar>

      <n-space justify="end" :size="10">
        <n-button :disabled="confirming" @click="reset">重新生成</n-button>
        <n-button :disabled="confirming" @click="close">取消</n-button>
        <n-button type="primary" :loading="confirming" @click="confirm">确认并保存到结构树</n-button>
      </n-space>
    </n-space>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { planningApi, type ActBlueprint, type ChapterBlueprint } from '../../api/planning'

interface ChapterDraft {
  title: string
  outline: string
  bible_elements: string[]
  blueprint: ChapterBlueprint
  metadata?: { blueprint?: ChapterBlueprint; [key: string]: unknown }
  [key: string]: unknown
}

const props = defineProps<{
  show: boolean
  actId: string
  actTitle: string
}>()

const emit = defineEmits<{
  (e: 'update:show', v: boolean): void
  (e: 'confirmed'): void
}>()

const message = useMessage()

const show = computed({
  get: () => props.show,
  set: (v) => emit('update:show', v),
})

const loading = ref(false)
const confirming = ref(false)
const generated = ref(false)
const chapterCount = ref<number | null>(null)
const chapters = ref<ChapterDraft[]>([])
const actBlueprint = ref<ActBlueprint | null>(null)

watch(
  () => props.show,
  (v) => { if (!v) reset() }
)

function reset() {
  generated.value = false
  chapters.value = []
  actBlueprint.value = null
  loading.value = false
  confirming.value = false
}

function close() {
  emit('update:show', false)
}

async function generate() {
  loading.value = true
  try {
    const res = await planningApi.generateActChapters(props.actId, {
      chapter_count: chapterCount.value ?? undefined,
    }) as any
    const raw: any[] = res.chapters ?? res.data?.chapters ?? []
    actBlueprint.value = res.act_blueprint ?? res.data?.act_blueprint ?? null
    chapters.value = raw.map(normalizeChapterDraft)
    if (!chapters.value.length) {
      message.warning('AI 未返回章节数据，请重试')
      return
    }
    generated.value = true
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '生成失败，请检查 API Key')
  } finally {
    loading.value = false
  }
}

async function confirm() {
  confirming.value = true
  try {
    await planningApi.confirmActChapters(props.actId, { chapters: chapters.value.map(toConfirmPayload) })
    message.success('章节已写入结构树')
    emit('confirmed')
    emit('update:show', false)
  } catch (e: any) {
    message.error(e?.response?.data?.detail || '保存失败')
  } finally {
    confirming.value = false
  }
}

function normalizeChapterDraft(c: any): ChapterDraft {
  const existing = (c.blueprint ?? c.metadata?.blueprint ?? {}) as ChapterBlueprint
  const outline = c.outline ?? c.description ?? existing.outline ?? ''
  const blueprint: ChapterBlueprint = {
    narrative_function: c.narrative_function ?? existing.narrative_function ?? 'development',
    target_tension: Number(c.target_tension ?? existing.target_tension ?? 5),
    tension_phase: c.tension_phase ?? existing.tension_phase ?? '',
    outline,
    must_happen: textToList(c.must_happen ?? existing.must_happen),
    must_not_happen: textToList(c.must_not_happen ?? existing.must_not_happen),
    handoff_to_next: c.handoff_to_next ?? existing.handoff_to_next ?? '',
    pov: c.pov ?? existing.pov ?? c.pov_character_id ?? '',
    characters: textToList(c.characters ?? existing.characters),
    locations: textToList(c.locations ?? existing.locations),
    foreshadowing_actions: textToList(c.foreshadowing_actions ?? existing.foreshadowing_actions),
  }
  return {
    ...c,
    title: c.title ?? '',
    outline,
    bible_elements: c.bible_elements ?? [],
    blueprint,
    metadata: {
      ...(typeof c.metadata === 'object' && c.metadata ? c.metadata : {}),
      blueprint,
    },
  }
}

function toConfirmPayload(ch: ChapterDraft) {
  const blueprint = { ...ch.blueprint, outline: ch.outline }
  return {
    ...ch,
    outline: ch.outline,
    narrative_function: blueprint.narrative_function,
    target_tension: blueprint.target_tension,
    tension_phase: blueprint.tension_phase,
    must_happen: blueprint.must_happen,
    must_not_happen: blueprint.must_not_happen,
    handoff_to_next: blueprint.handoff_to_next,
    pov: blueprint.pov,
    characters: blueprint.characters,
    locations: blueprint.locations,
    foreshadowing_actions: blueprint.foreshadowing_actions,
    blueprint,
    metadata: {
      ...(ch.metadata ?? {}),
      blueprint,
    },
  }
}

function textToList(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(String).map(v => v.trim()).filter(Boolean)
  if (typeof value === 'string') return value.split(/\n|；|;/).map(v => v.trim()).filter(Boolean)
  if (value == null) return []
  return [String(value).trim()].filter(Boolean)
}

function listToText(value: unknown): string {
  return textToList(value).join('\n')
}
</script>
