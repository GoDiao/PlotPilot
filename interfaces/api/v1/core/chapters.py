"""Chapter API 路由"""
import logging
from typing import List, Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path
from pydantic import BaseModel, Field

from application.core.services.chapter_service import ChapterService
from application.core.services.chapter_quality_gate_service import ChapterQualityGateService
from application.core.services.trustworthy_creation_service import TrustworthyCreationService
from application.core.services.novel_service import NovelService
from application.core.dtos.chapter_dto import ChapterDTO
from application.core.dtos.novel_dto import NovelDTO
from application.audit.dtos.chapter_review_dto import ChapterReviewDTO
from application.core.dtos.chapter_structure_dto import ChapterStructureDTO
from application.engine.services.chapter_aftermath_pipeline import ChapterAftermathPipeline
from interfaces.api.dependencies import (
    get_chapter_service,
    get_chapter_quality_gate_service,
    get_novel_service,
    get_chapter_aftermath_pipeline,
    get_trustworthy_creation_service,
    get_chapter_rewrite_service,
)
from domain.shared.exceptions import EntityNotFoundError
logger = logging.getLogger(__name__)


async def _run_chapter_aftermath(
    novel_id: str,
    chapter_number: int,
    content: str,
    pipeline: ChapterAftermathPipeline,
) -> None:
    """与托管/守护进程同源的章后管线（叙事/向量、文风、KG；三元组与伏笔单次 LLM）。"""
    await pipeline.run_after_chapter_saved(novel_id, chapter_number, content)


async def _run_locked_chapter_sync(
    novel_id: str,
    chapter_number: int,
    content: str,
    pipeline: ChapterAftermathPipeline,
    gate_service: ChapterQualityGateService,
) -> None:
    await pipeline.run_after_chapter_saved(novel_id, chapter_number, content)
    gate_service.mark_synced(novel_id, chapter_number)


router = APIRouter(tags=["chapters"])


# Request Models
class UpdateChapterContentRequest(BaseModel):
    """更新章节内容请求"""
    content: str = Field(..., min_length=0, max_length=100000, description="章节内容")


class RewriteResetRequest(BaseModel):
    restore_content: bool = Field(default=False, description="是否恢复写前正文；默认清空为草稿以便重写")


class SaveChapterReviewRequest(BaseModel):
    """保存章节审阅请求"""
    status: Literal[
        "draft",
        "reviewed",
        "approved",
        "review_pending",
        "revision_required",
        "locked",
        "synced",
    ] = Field(..., description="审阅状态")
    memo: str = Field(default="", description="审阅备注")


class MarkRevisionRequiredRequest(BaseModel):
    """标记章节需修订请求"""
    memo: str = Field(default="", description="修订说明")


class ChapterPreflightRequest(BaseModel):
    """生成前上下文预检请求"""
    outline: str = Field(default="", description="前端输入或当前章大纲")
    context_preview: dict = Field(default_factory=dict, description="可选上下文预览结果")


class ChapterReviewResponse(BaseModel):
    """章节审阅响应"""
    status: str
    memo: str
    created_at: str
    updated_at: str


class ChapterStructureResponse(BaseModel):
    """章节结构响应"""
    word_count: int
    paragraph_count: int
    dialogue_ratio: float
    scene_count: int
    pacing: str


class ChapterGateIssueResponse(BaseModel):
    """章节质量门禁问题。"""
    code: str
    severity: str
    message: str
    action: str = ""


class ChapterQualityGateResponse(BaseModel):
    """章节质量门禁响应。"""
    novel_id: str
    chapter_number: int
    gate_status: str
    chapter_status: str
    review_status: str
    can_enter_next: bool
    can_lock: bool
    word_count: int
    issues: List[ChapterGateIssueResponse]
    suggestions: List[str]


class ChapterIssueTaskResponse(BaseModel):
    """章节问题任务。"""
    id: str
    source: str
    code: str
    severity: str
    title: str
    evidence: str = ""
    basis: str = ""
    confidence: float = 1.0
    recommended_action: str = ""


class ChapterPreflightResponse(BaseModel):
    """生成前上下文预检响应。"""
    novel_id: str
    chapter_number: int
    outline_source: str
    selected_outline: str
    authority_lock: List[str]
    warnings: List[str]
    hard_conflicts: List[str]
    selected_authority: List[str]


class ChapterMemoryEntryRequest(BaseModel):
    memory_layer: Literal["draft", "pending", "canonical"]
    source: str = "manual"
    entry_type: str = "note"
    content: str
    payload: dict = Field(default_factory=dict)
    issue_id: str | None = None


class ChapterIssueActionRequest(BaseModel):
    issue_id: str
    action: Literal[
        "fix_text",
        "update_bible",
        "mark_false_positive",
        "accept_new_setting",
        "ignore",
    ]
    memo: str = ""


class ApplyRevisionDraftRequest(BaseModel):
    draft_id: str


class CreateChapterRequest(BaseModel):
    """创建章节请求"""
    chapter_id: str = Field(..., description="章节 ID")
    number: int = Field(..., gt=0, description="章节编号")
    title: str = Field(..., min_length=1, max_length=200, description="章节标题")
    content: str = Field(..., min_length=1, description="章节内容")


class EnsureChapterRequest(BaseModel):
    """确保章节存在请求（可选 title，不传则用「第N章」）"""
    title: str = Field(default="", max_length=200, description="章节标题（可选）")


# Routes
@router.get("/{novel_id}/chapters", response_model=List[ChapterDTO])
async def list_chapters(
    novel_id: str,
    service: ChapterService = Depends(get_chapter_service)
):
    """列出小说的所有章节

    Args:
        novel_id: 小说 ID
        service: Chapter 服务

    Returns:
        章节 DTO 列表
    """
    return service.list_chapters_by_novel(novel_id)


@router.post("/{novel_id}/chapters", response_model=NovelDTO, status_code=201)
async def create_chapter(
    novel_id: str,
    request: CreateChapterRequest,
    novel_service: NovelService = Depends(get_novel_service)
):
    """创建章节

    Args:
        novel_id: 小说 ID
        request: 创建章节请求
        novel_service: Novel 服务

    Returns:
        更新后的小说 DTO
    """
    try:
        return novel_service.add_chapter(
            novel_id=novel_id,
            chapter_id=request.chapter_id,
            number=request.number,
            title=request.title,
            content=request.content
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{novel_id}/chapters/{chapter_number}", response_model=ChapterDTO)
async def get_chapter(
    novel_id: str,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: ChapterService = Depends(get_chapter_service)
):
    """获取章节详情

    Args:
        novel_id: 小说 ID
        chapter_number: 章节号
        service: Chapter 服务

    Returns:
        章节 DTO

    Raises:
        HTTPException: 如果章节不存在
    """
    chapter = service.get_chapter_by_novel_and_number(novel_id, chapter_number)
    if chapter is None:
        raise HTTPException(
            status_code=404,
            detail=f"Chapter not found: {novel_id}/chapter-{chapter_number}"
        )
    return chapter


@router.post("/{novel_id}/chapters/{chapter_number}/ensure", response_model=ChapterDTO)
async def ensure_chapter(
    novel_id: str,
    request: EnsureChapterRequest,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: ChapterService = Depends(get_chapter_service)
):
    """确保章节在正文库中存在；若不存在则创建空白记录（不校验章节号连续性）。

    适用于结构树手动添加章节节点后、用户点击想直接开始写作的场景。
    """
    return service.ensure_chapter(novel_id, chapter_number, request.title)


@router.put("/{novel_id}/chapters/{chapter_number}", response_model=ChapterDTO)
async def update_chapter(
    novel_id: str,
    request: UpdateChapterContentRequest,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: ChapterService = Depends(get_chapter_service),
    gate_service: ChapterQualityGateService = Depends(get_chapter_quality_gate_service),
    rewrite_service=Depends(get_chapter_rewrite_service),
):
    """更新章节内容。保存仅产生草稿/待审，不直接写入强长期记忆。"""
    try:
        rewrite_service.create_prewrite_snapshot(novel_id, chapter_number, "manual_update_chapter")
        chapter = service.update_chapter_by_novel_and_number(
            novel_id,
            chapter_number,
            request.content
        )
        gate_service.mark_review_pending(
            novel_id,
            chapter_number,
            "正文已更新，等待作者审稿与锁定后再进入长期记忆。",
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return chapter


@router.get("/{novel_id}/chapters/{chapter_number}/rewrite/preview")
async def preview_chapter_rewrite_reset(
    novel_id: str,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    rewrite_service=Depends(get_chapter_rewrite_service),
):
    return rewrite_service.preview_reset(novel_id, chapter_number)


@router.post("/{novel_id}/chapters/{chapter_number}/rewrite/reset")
async def reset_chapter_for_rewrite(
    novel_id: str,
    request: RewriteResetRequest = RewriteResetRequest(),
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    rewrite_service=Depends(get_chapter_rewrite_service),
    gate_service: ChapterQualityGateService = Depends(get_chapter_quality_gate_service),
):
    try:
        result = rewrite_service.reset_for_rewrite(
            novel_id,
            chapter_number,
            restore_content=request.restore_content,
        )
        gate_service.mark_review_pending(
            novel_id,
            chapter_number,
            "章节已重写回退，等待重新生成/编辑后审稿。",
        )
        return result
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{novel_id}/chapters/{chapter_number}/review", response_model=ChapterReviewResponse)
async def get_chapter_review(
    novel_id: str,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: ChapterService = Depends(get_chapter_service)
):
    """获取章节审阅

    Args:
        novel_id: 小说 ID
        chapter_number: 章节号
        service: Chapter 服务

    Returns:
        章节审阅信息

    Raises:
        HTTPException: 如果章节不存在
    """
    try:
        review = service.get_chapter_review(novel_id, chapter_number)
        return ChapterReviewResponse(
            status=review.status,
            memo=review.memo,
            created_at=review.created_at.isoformat(),
            updated_at=review.updated_at.isoformat()
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{novel_id}/chapters/{chapter_number}/review", response_model=ChapterReviewResponse)
async def save_chapter_review(
    novel_id: str,
    request: SaveChapterReviewRequest,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: ChapterService = Depends(get_chapter_service)
):
    """保存章节审阅

    Args:
        novel_id: 小说 ID
        chapter_number: 章节号
        request: 审阅请求
        service: Chapter 服务

    Returns:
        保存后的审阅信息

    Raises:
        HTTPException: 如果章节不存在
    """
    try:
        review = service.save_chapter_review(
            novel_id,
            chapter_number,
            request.status,
            request.memo
        )
        return ChapterReviewResponse(
            status=review.status,
            memo=review.memo,
            created_at=review.created_at.isoformat(),
            updated_at=review.updated_at.isoformat()
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{novel_id}/chapters/{chapter_number}/quality-gate", response_model=ChapterQualityGateResponse)
async def get_chapter_quality_gate(
    novel_id: str,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: ChapterQualityGateService = Depends(get_chapter_quality_gate_service),
):
    """获取本章是否可进入下一章的质量门禁。"""
    try:
        return service.evaluate(novel_id, chapter_number)
    except (EntityNotFoundError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{novel_id}/chapters/{chapter_number}/issue-tasks", response_model=List[ChapterIssueTaskResponse])
async def list_chapter_issue_tasks(
    novel_id: str,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: ChapterQualityGateService = Depends(get_chapter_quality_gate_service),
):
    """把门禁/诊断问题聚合为可处理任务。"""
    try:
        return service.list_issue_tasks(novel_id, chapter_number)
    except (EntityNotFoundError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{novel_id}/chapters/{chapter_number}/preflight", response_model=ChapterPreflightResponse)
async def preflight_chapter_generation(
    novel_id: str,
    request: ChapterPreflightRequest,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: ChapterQualityGateService = Depends(get_chapter_quality_gate_service),
):
    """生成前上下文健康检查。"""
    try:
        return service.preflight(
            novel_id,
            chapter_number,
            outline=request.outline,
            context_preview=request.context_preview,
        )
    except (EntityNotFoundError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{novel_id}/chapters/{chapter_number}/lock", response_model=ChapterQualityGateResponse)
async def lock_chapter(
    novel_id: str,
    background_tasks: BackgroundTasks,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: ChapterQualityGateService = Depends(get_chapter_quality_gate_service),
    chapter_service: ChapterService = Depends(get_chapter_service),
    pipeline: ChapterAftermathPipeline = Depends(get_chapter_aftermath_pipeline),
    rewrite_service=Depends(get_chapter_rewrite_service),
):
    """锁定章节，允许其作为后续强上下文候选。"""
    try:
        rewrite_service.create_prewrite_snapshot(novel_id, chapter_number, "lock_chapter")
        gate = service.lock_chapter(novel_id, chapter_number)
        if gate.can_enter_next:
            chapter = chapter_service.get_chapter_by_novel_and_number(novel_id, chapter_number)
            background_tasks.add_task(
                _run_locked_chapter_sync,
                novel_id,
                chapter_number,
                chapter.content or "",
                pipeline,
                service,
            )
        return gate
    except (EntityNotFoundError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{novel_id}/chapters/{chapter_number}/revision-required", response_model=ChapterQualityGateResponse)
async def mark_chapter_revision_required(
    novel_id: str,
    request: MarkRevisionRequiredRequest,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: ChapterQualityGateService = Depends(get_chapter_quality_gate_service),
):
    """标记章节需要修订，阻止其继续污染后续上下文。"""
    try:
        return service.mark_revision_required(novel_id, chapter_number, request.memo)
    except (EntityNotFoundError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{novel_id}/chapters/{chapter_number}/memory")
async def list_chapter_memory(
    novel_id: str,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    memory_layer: str | None = None,
    service: TrustworthyCreationService = Depends(get_trustworthy_creation_service),
):
    return service.list_memory_entries(novel_id, chapter_number, memory_layer)


@router.post("/{novel_id}/chapters/{chapter_number}/memory")
async def add_chapter_memory(
    novel_id: str,
    request: ChapterMemoryEntryRequest,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: TrustworthyCreationService = Depends(get_trustworthy_creation_service),
):
    return service.add_memory_entry(
        novel_id,
        chapter_number,
        request.memory_layer,
        request.source,
        request.entry_type,
        request.content,
        request.payload,
        request.issue_id,
    )


@router.post("/{novel_id}/chapters/{chapter_number}/issue-actions")
async def apply_chapter_issue_action(
    novel_id: str,
    request: ChapterIssueActionRequest,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: TrustworthyCreationService = Depends(get_trustworthy_creation_service),
):
    return service.apply_issue_action(
        novel_id,
        chapter_number,
        request.issue_id,
        request.action,
        request.memo,
    )


@router.get("/{novel_id}/chapters/{chapter_number}/revision-drafts")
async def list_revision_drafts(
    novel_id: str,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: TrustworthyCreationService = Depends(get_trustworthy_creation_service),
):
    return service.list_revision_drafts(novel_id, chapter_number)


@router.post("/{novel_id}/chapters/{chapter_number}/revision-drafts/apply")
async def apply_revision_draft(
    novel_id: str,
    request: ApplyRevisionDraftRequest,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: TrustworthyCreationService = Depends(get_trustworthy_creation_service),
):
    try:
        return service.apply_revision_draft(request.draft_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{novel_id}/chapters/{chapter_number}/rollback-latest")
async def rollback_latest_chapter_snapshot(
    novel_id: str,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: TrustworthyCreationService = Depends(get_trustworthy_creation_service),
):
    try:
        return service.rollback_latest_snapshot(novel_id, chapter_number)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{novel_id}/chapters/{chapter_number}/review-ai")
async def ai_review_chapter(
    novel_id: str,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: ChapterService = Depends(get_chapter_service)
):
    """AI 审阅章节

    Args:
        novel_id: 小说 ID
        chapter_number: 章节号
        service: Chapter 服务

    Returns:
        AI 审阅结果

    Raises:
        HTTPException: 如果章节不存在或内容为空
    """
    try:
        # 获取章节
        chapter = service.get_chapter_by_novel_and_number(novel_id, chapter_number)
        if chapter is None:
            raise HTTPException(status_code=404, detail=f"Chapter not found: {novel_id}/chapter-{chapter_number}")

        # 检查内容是否为空
        if not chapter.content or not chapter.content.strip():
            raise HTTPException(status_code=400, detail="Chapter content is empty")

        # TODO: 实现 AI 审阅逻辑
        # 这里需要集成 LLM 服务进行审阅
        return {
            "message": "AI review not yet implemented",
            "status": "pending"
        }
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{novel_id}/chapters/{chapter_number}/structure", response_model=ChapterStructureResponse)
async def get_chapter_structure(
    novel_id: str,
    chapter_number: int = Path(..., gt=0, description="章节编号"),
    service: ChapterService = Depends(get_chapter_service)
):
    """获取章节结构分析

    Args:
        novel_id: 小说 ID
        chapter_number: 章节号
        service: Chapter 服务

    Returns:
        章节结构分析

    Raises:
        HTTPException: 如果章节不存在
    """
    try:
        structure = service.get_chapter_structure(novel_id, chapter_number)
        return ChapterStructureResponse(
            word_count=structure.word_count,
            paragraph_count=structure.paragraph_count,
            dialogue_ratio=structure.dialogue_ratio,
            scene_count=structure.scene_count,
            pacing=structure.pacing
        )
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
