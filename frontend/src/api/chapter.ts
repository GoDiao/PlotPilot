import { apiClient } from './config'

export interface ChapterDTO {
  id: string
  novel_id: string
  number: number
  title: string
  content: string
  status: string
  word_count: number
  created_at: string
  updated_at: string
}

export interface UpdateChapterRequest {
  content: string
}

export interface ChapterReviewDTO {
  status: string
  memo: string
  created_at: string
  updated_at: string
}

export interface ChapterStructureDTO {
  word_count: number
  paragraph_count: number
  dialogue_ratio: number
  scene_count: number
  pacing: string
}

export interface ChapterGateIssueDTO {
  code: string
  severity: 'blocker' | 'major' | 'minor' | string
  message: string
  action: string
}

export interface ChapterQualityGateDTO {
  novel_id: string
  chapter_number: number
  gate_status: 'pass' | 'needs_revision' | 'blocked' | 'review_pending' | string
  chapter_status: string
  review_status: string
  can_enter_next: boolean
  can_lock: boolean
  word_count: number
  issues: ChapterGateIssueDTO[]
  suggestions: string[]
}

export interface ChapterIssueTaskDTO {
  id: string
  source: string
  code: string
  severity: string
  title: string
  evidence: string
  basis: string
  confidence: number
  recommended_action: string
}

export interface ChapterPreflightDTO {
  novel_id: string
  chapter_number: number
  outline_source: string
  selected_outline: string
  authority_lock: string[]
  warnings: string[]
  hard_conflicts: string[]
  selected_authority: string[]
}

export interface ChapterMemoryEntryDTO {
  id: string
  novel_id: string
  chapter_number: number
  memory_layer: 'draft' | 'pending' | 'canonical'
  source: string
  entry_type: string
  content: string
  payload: Record<string, unknown>
  status: string
  issue_id?: string
}

export interface ChapterRevisionDraftDTO {
  id: string
  novel_id: string
  chapter_number: number
  source: string
  variant_label: string
  original_content: string
  revised_content: string
  diff_text: string
  status: string
  created_at: string
}

export interface ChapterReviewAiResponse {
  ok: boolean
  status: string
  memo: string
  saved: boolean
}

export interface ChapterRewritePreviewDTO {
  has_snapshot: boolean
  mode: 'snapshot_restore' | 'soft_reset' | string
  snapshot?: Record<string, unknown> | null
  warnings: string[]
  has_later_completed_chapters?: boolean
}

export const chapterApi = {
  /**
   * List all chapters for a novel
   * GET /api/v1/novels/{novelId}/chapters
   */
  listChapters: (novelId: string) =>
    apiClient.get<ChapterDTO[]>(`/novels/${novelId}/chapters`) as Promise<ChapterDTO[]>,

  /**
   * Get a specific chapter by number
   * GET /api/v1/novels/{novelId}/chapters/{chapterNumber}
   */
  getChapter: (novelId: string, chapterNumber: number) =>
    apiClient.get<ChapterDTO>(`/novels/${novelId}/chapters/${chapterNumber}`) as Promise<ChapterDTO>,

  /**
   * Update a chapter
   * PUT /api/v1/novels/{novelId}/chapters/{chapterNumber}
   */
  updateChapter: (novelId: string, chapterNumber: number, data: UpdateChapterRequest) =>
    apiClient.put<ChapterDTO>(`/novels/${novelId}/chapters/${chapterNumber}`, data) as Promise<ChapterDTO>,

  /**
   * Get chapter review
   * GET /api/v1/novels/{novelId}/chapters/{chapterNumber}/review
   */
  getChapterReview: (novelId: string, chapterNumber: number) =>
    apiClient.get<ChapterReviewDTO>(`/novels/${novelId}/chapters/${chapterNumber}/review`) as Promise<ChapterReviewDTO>,

  /**
   * Save chapter review
   * PUT /api/v1/novels/{novelId}/chapters/{chapterNumber}/review
   */
  saveChapterReview: (novelId: string, chapterNumber: number, status: string, memo: string) =>
    apiClient.put<ChapterReviewDTO>(`/novels/${novelId}/chapters/${chapterNumber}/review`, { status, memo }) as Promise<ChapterReviewDTO>,

  /**
   * AI review chapter
   * POST /api/v1/novels/{novelId}/chapters/{chapterNumber}/review-ai
   */
  reviewChapterAi: (novelId: string, chapterNumber: number, save: boolean) =>
    apiClient.post<ChapterReviewAiResponse>(`/novels/${novelId}/chapters/${chapterNumber}/review-ai`, { save }) as Promise<ChapterReviewAiResponse>,

  /**
   * Get chapter structure analysis
   * GET /api/v1/novels/{novelId}/chapters/{chapterNumber}/structure
   */
  getChapterStructure: (novelId: string, chapterNumber: number) =>
    apiClient.get<ChapterStructureDTO>(`/novels/${novelId}/chapters/${chapterNumber}/structure`) as Promise<ChapterStructureDTO>,

  /**
   * Get chapter quality gate
   * GET /api/v1/novels/{novelId}/chapters/{chapterNumber}/quality-gate
   */
  getQualityGate: (novelId: string, chapterNumber: number) =>
    apiClient.get<ChapterQualityGateDTO>(`/novels/${novelId}/chapters/${chapterNumber}/quality-gate`) as Promise<ChapterQualityGateDTO>,

  /**
   * List actionable chapter issue tasks
   * GET /api/v1/novels/{novelId}/chapters/{chapterNumber}/issue-tasks
   */
  listIssueTasks: (novelId: string, chapterNumber: number) =>
    apiClient.get<ChapterIssueTaskDTO[]>(`/novels/${novelId}/chapters/${chapterNumber}/issue-tasks`) as Promise<ChapterIssueTaskDTO[]>,

  /**
   * Run pre-generation context health check
   * POST /api/v1/novels/{novelId}/chapters/{chapterNumber}/preflight
   */
  preflight: (novelId: string, chapterNumber: number, outline = '', contextPreview: Record<string, unknown> = {}) =>
    apiClient.post<ChapterPreflightDTO>(`/novels/${novelId}/chapters/${chapterNumber}/preflight`, {
      outline,
      context_preview: contextPreview,
    }) as Promise<ChapterPreflightDTO>,

  /**
   * Lock chapter after author review
   * POST /api/v1/novels/{novelId}/chapters/{chapterNumber}/lock
   */
  lockChapter: (novelId: string, chapterNumber: number) =>
    apiClient.post<ChapterQualityGateDTO>(`/novels/${novelId}/chapters/${chapterNumber}/lock`) as Promise<ChapterQualityGateDTO>,

  /**
   * Mark chapter as requiring revision
   * POST /api/v1/novels/{novelId}/chapters/{chapterNumber}/revision-required
   */
  markRevisionRequired: (novelId: string, chapterNumber: number, memo = '') =>
    apiClient.post<ChapterQualityGateDTO>(`/novels/${novelId}/chapters/${chapterNumber}/revision-required`, { memo }) as Promise<ChapterQualityGateDTO>,

  listMemory: (novelId: string, chapterNumber: number, memoryLayer?: string) =>
    apiClient.get<ChapterMemoryEntryDTO[]>(`/novels/${novelId}/chapters/${chapterNumber}/memory`, {
      params: memoryLayer ? { memory_layer: memoryLayer } : undefined,
    }) as Promise<ChapterMemoryEntryDTO[]>,

  applyIssueAction: (novelId: string, chapterNumber: number, issueId: string, action: string, memo = '') =>
    apiClient.post(`/novels/${novelId}/chapters/${chapterNumber}/issue-actions`, {
      issue_id: issueId,
      action,
      memo,
    }) as Promise<Record<string, unknown>>,

  listRevisionDrafts: (novelId: string, chapterNumber: number) =>
    apiClient.get<ChapterRevisionDraftDTO[]>(`/novels/${novelId}/chapters/${chapterNumber}/revision-drafts`) as Promise<ChapterRevisionDraftDTO[]>,

  applyRevisionDraft: (novelId: string, chapterNumber: number, draftId: string) =>
    apiClient.post(`/novels/${novelId}/chapters/${chapterNumber}/revision-drafts/apply`, { draft_id: draftId }) as Promise<Record<string, unknown>>,

  rollbackLatest: (novelId: string, chapterNumber: number) =>
    apiClient.post(`/novels/${novelId}/chapters/${chapterNumber}/rollback-latest`) as Promise<Record<string, unknown>>,

  previewRewriteReset: (novelId: string, chapterNumber: number) =>
    apiClient.get<ChapterRewritePreviewDTO>(`/novels/${novelId}/chapters/${chapterNumber}/rewrite/preview`) as Promise<ChapterRewritePreviewDTO>,

  resetForRewrite: (novelId: string, chapterNumber: number, restoreContent = false) =>
    apiClient.post<Record<string, unknown>>(
      `/novels/${novelId}/chapters/${chapterNumber}/rewrite/reset`,
      { restore_content: restoreContent },
    ) as Promise<Record<string, unknown>>,

  /**
   * 确保章节在正文库中存在；若不存在则创建空白记录
   * POST /api/v1/novels/{novelId}/chapters/{chapterNumber}/ensure
   */
  ensureChapter: (novelId: string, chapterNumber: number, title = '') =>
    apiClient.post<ChapterDTO>(`/novels/${novelId}/chapters/${chapterNumber}/ensure`, { title }) as Promise<ChapterDTO>,
}
