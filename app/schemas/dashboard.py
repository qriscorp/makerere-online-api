from typing import List, Literal, Optional

from pydantic import BaseModel

DashboardAccent = Literal["emerald", "violet", "gold", "sky", "crimson"]
DashboardTrend = Literal["up", "down", "neutral"]
DashboardIconKey = Literal[
    "graduation_cap",
    "users",
    "book_open",
    "dollar_sign",
    "calendar",
    "file_text",
    "trending_up",
    "credit_card",
    "clipboard_check",
    "award",
]
DashboardMetricKey = Literal["enrollments", "completions", "assessments"]


class DashboardKpiItem(BaseModel):
    key: str
    icon: DashboardIconKey
    value: str
    label: str
    delta: Optional[str] = None
    trend: Optional[DashboardTrend] = None
    breakdown: Optional[str] = None
    accent: DashboardAccent


class DashboardSecondaryStatItem(BaseModel):
    key: str
    icon: DashboardIconKey
    label: str
    value: str


class DashboardOverviewResponse(BaseModel):
    kpis: List[DashboardKpiItem]
    secondary_stats: List[DashboardSecondaryStatItem]


class DashboardActivityPoint(BaseModel):
    date: str
    value: int


class DashboardActivityResponse(BaseModel):
    metric: DashboardMetricKey
    days: int
    points: List[DashboardActivityPoint]
