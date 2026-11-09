from __future__ import annotations

from pathlib import Path

from fdctl.models import CaseContext
from fdctl.services.report_layout import case_snapshot_path
from fdctl.utils import ensure_dir, now_iso


def _line(path: Path, note: str) -> str:
    return f"- {path} - {note}"


def write_report_index(case: CaseContext, schema: dict) -> Path:
    output = case.report_dir / "Muc_luc_bao_cao.md"
    ensure_dir(output.parent)
    lines = [
        "# Mục lục báo cáo điều tra",
        "",
        f"- Case: {case.case_id}",
        f"- Ứng dụng: {case.app_id}",
        f"- Thời điểm tạo: {now_iso()}",
        "",
        "## Tài liệu nên mở trước",
        "",
        _line(case.report_dir / "Interactive_Crime_Scene_Replay.html", "🎬 TÁI HIỆN HIỆN TRƯỜNG KỸ THUẬT SỐ TƯƠNG TÁC (Xem lại tin nhắn, dòng thời gian, chứng cứ trực quan)"),
        _line(case_snapshot_path(case), "Snapshot dữ liệu để xem trực tiếp trong ứng dụng"),
        _line(case.root / "case.json", "Metadata của case"),
        _line(case.info_dir / "collection_summary.json", "Tóm tắt thu thập"),
        _line(case.exports_dir / "analysis_summary.json", "Tóm tắt phân tích"),
        "",
        "## Thư mục 8 lớp dữ liệu",
        "",
    ]
    for name in [
        "01_Case_Info",
        "02_Live_Response",
        "03_Acquired_Files",
        "04_Browser_Artifacts",
        "05_Autopsy_Case",
        "06_Screenshots",
        "07_Exports",
        "08_Report",
    ]:
        lines.append(f"- {case.root / name}")

    lines.extend(
        [
            "",
            "## Tài nguyên xuất chính",
            "",
        ]
    )
    for resource in schema.get("resources", []):
        lines.append(f"- {resource.get('path', '')}")

    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def write_handover_report(case: CaseContext, schema: dict) -> Path:
    output = case.report_dir / "Bien_ban_ban_giao.md"
    ensure_dir(output.parent)
    summary = schema.get("summary", {})
    collection = schema.get("collection", {})
    detection = collection.get("detection", {}) if isinstance(collection, dict) else {}
    lines = [
        "# Biên bản bàn giao điều tra",
        "",
        f"- Case: {case.case_id}",
        f"- Ứng dụng: {case.app_id}",
        f"- Thời điểm lập biên bản: {now_iso()}",
        "",
        "## Kết quả chính",
        "",
        f"- Số file/artifact đã sao chép: {summary.get('artifactCount', 0)}",
        f"- Số process ghi nhận: {summary.get('processCount', 0)}",
        f"- Số kết nối TCP ghi nhận: {summary.get('tcpCount', 0)}",
        f"- Số message phục dựng (Tổng cộng): {summary.get('recoveredMessages', 0)}",
        f"- Số tin nhắn riêng 1-1 (Direct Messages): {summary.get('directMessages', 0)}",
        f"- Số tin nhắn nhóm / kênh (Group Messages): {summary.get('groupMessages', 0)}",
        f"- Số tin nhắn đối tượng mục tiêu: {summary.get('targetUserRows', 0)}",
        f"- Số attachment nhận diện: {summary.get('attachments', 0)}",
        f"- Số lỗi sao chép: {summary.get('copyErrorCount', 0)}",
        "",
        "## Đường dẫn ứng dụng phát hiện",
        "",
    ]
    for path in detection.get("installPaths", []):
        lines.append(f"- {path}")
    if not detection.get("installPaths"):
        lines.append("- Không ghi nhận đường dẫn ứng dụng rõ ràng trong lần chạy này.")

    lines.extend(
        [
            "",
            "## Tài liệu bàn giao",
            "",
            f"- {case_snapshot_path(case)}",
            f"- {case.report_dir / 'Muc_luc_bao_cao.md'}",
            f"- {case.info_dir / 'collection_summary.json'}",
            f"- {case.exports_dir / 'analysis_summary.json'}",
        ]
    )

    output.write_text("\n".join(lines), encoding="utf-8")
    return output
