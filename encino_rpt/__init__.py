"""Reporteador financiero sobre `list[dict]` (paquete `encino_rpt`)."""

from .models import (
                     Chart,
                     ConditionalRule,
                     Detail,
                     Format,
                     Group,
                     Image,
                     Kpi,
                     Link,
                     Pivot,
                     ReportMeta,
                     ReportResult,
                     Series,
                     Total,
)
from .report import Report

__all__ = [
                     "Chart",
                     "ConditionalRule",
                     "Detail",
                     "Format",
                     "Group",
                     "Image",
                     "Kpi",
                     "Link",
                     "Pivot",
                     "Report",
                     "ReportMeta",
                     "ReportResult",
                     "Series",
                     "Total",
]
