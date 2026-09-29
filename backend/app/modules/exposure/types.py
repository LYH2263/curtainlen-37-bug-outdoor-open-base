"""空间曝晒类型枚举与标签。单一事实来源，前后端共用（前端经 /api/exposure/types 读取）。"""
from enum import Enum


class ExposureType(str, Enum):
    INDOOR = "indoor"            # 普通室内：订货米 = 基础米
    OUTDOOR_UV = "outdoor_uv"    # 户外抗紫外：订货米 = 基础米 + 固定加米


LABELS = {
    ExposureType.INDOOR: "普通室内",
    ExposureType.OUTDOOR_UV: "户外抗紫外",
}


class ExposureError(ValueError):
    """曝晒类型相关错误（未知类型、非法加米配置等），服务层转为 422。"""


def parse(value) -> ExposureType:
    try:
        return ExposureType(str(value))
    except ValueError:
        raise ExposureError(f"unknown exposure type: {value!r}")


def label_of(value) -> str:
    try:
        return LABELS[parse(value)]
    except ExposureError:
        return str(value)
