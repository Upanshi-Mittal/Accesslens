
from typing import Optional, List, Dict, Any
import asyncpg
import json
import logging
from datetime import datetime
from uuid import UUID
from ..models.schemas import AuditReport, UnifiedIssue, AuditRequest, AuditSummary
from ..core.config import settings

class ReportStorage:


    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._logger = logging.getLogger(__name__)
        self._in_memory_store: Dict[str, AuditReport] = {}

    async def initialize(self):

        if not settings.database_url:
            self._logger.warning("No database URL configured, using in-memory storage")
            return

        try:
            self._pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )


            await self._create_tables()
            self._logger.info("Database connection pool created successfully")

        except Exception as e:
            self._logger.error(f"Failed to initialize database: {e}")
            self._logger.warning("Falling back to in-memory storage")
            self._pool = None

    async def _create_tables(self):

        if not self._pool:
            return

        async with self._pool.acquire() as conn:

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id UUID PRIMARY KEY,
                    url TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    score FLOAT NOT NULL,
                    summary JSONB NOT NULL,
                    metadata JSONB NOT NULL,
                    request JSONB NOT NULL
                )
            """)


            await conn.execute("""
                CREATE TABLE IF NOT EXISTS issues (
                    id UUID PRIMARY KEY,
                    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    description TEXT,
                    issue_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    confidence TEXT NOT NULL,
                    confidence_score FLOAT NOT NULL,
                    source TEXT NOT NULL,
                    wcag_criteria JSONB,
                    location JSONB,
                    remediation JSONB,
                    evidence JSONB,
                    engine_name TEXT NOT NULL,
                    tags TEXT[]
                )
            """)


            await conn.execute("""
                CREATE TABLE IF NOT EXISTS accessibility_trees (
                    report_id UUID PRIMARY KEY REFERENCES reports(id) ON DELETE CASCADE,
                    tree_data JSONB NOT NULL
                )
            """)


            await conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_url ON reports(url)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_reports_timestamp ON reports(timestamp DESC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_issues_report_id ON issues(report_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues(severity)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_issues_type ON issues(issue_type)")


            await conn.execute("""
                CREATE OR REPLACE VIEW report_summaries AS
                SELECT 
                    r.id,
                    r.url,
                    r.timestamp,
                    r.score,
                    (r.summary->>'total_issues')::int as total_issues,
                    (r.summary->'by_severity'->>'critical')::int as critical_count,
                    (r.summary->'by_severity'->>'serious')::int as serious_count,
                    (r.summary->'by_severity'->>'moderate')::int as moderate_count,
                    (r.summary->'by_severity'->>'minor')::int as minor_count,
                    r.summary->>'confidence_avg' as avg_confidence
                FROM reports r
            """)

            self._logger.info("Database tables created/verified")

    async def save_report(self, report: AuditReport) -> str:

        if not self._pool:

            self._in_memory_store[report.id] = report
            self._logger.debug(f"Saved report {report.id} to in-memory storage")
            return report.id

        try:
            async with self._pool.acquire() as conn:
                async with conn.transaction():

                    await conn.execute("""
                        INSERT INTO reports (id, url, timestamp, score, summary, metadata, request)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                        report.id,
                        report.request.url,
                        report.timestamp,
                        report.summary.score,
                        json.dumps(report.summary.dict()),
                        json.dumps(report.metadata),
                        json.dumps(report.request.dict())
                    )


                    for issue in report.issues:
                        await conn.execute("""
                            INSERT INTO issues (
                                id, report_id, title, description, issue_type,
                                severity, confidence, confidence_score, source,
                                wcag_criteria, location, remediation, evidence,
                                engine_name, tags
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                        """,
                            issue.id,
                            report.id,
                            issue.title,
                            issue.description,
                            issue.issue_type,
                            issue.severity.value,
                            issue.confidence.value,
                            issue.confidence_score,
                            issue.source.value,
                            json.dumps([c.dict() for c in issue.wcag_criteria]),
                            json.dumps(issue.location.dict() if issue.location else None),
                            json.dumps(issue.remediation.dict() if issue.remediation else None),
                            json.dumps(issue.evidence.dict() if issue.evidence else None),
                            issue.engine_name,
                            issue.tags
                        )


                    if report.accessibility_tree:
                        await conn.execute("""
                            INSERT INTO accessibility_trees (report_id, tree_data)
                            VALUES ($1, $2)
                        """,
                            report.id,
                            json.dumps(report.accessibility_tree)
                        )

            self._logger.info(f"Saved report {report.id} to database with {len(report.issues)} issues")
            return report.id

        except Exception as e:
            self._logger.error(f"Failed to save report to database: {e}")

            self._in_memory_store[report.id] = report
            return report.id

    async def get_report(self, report_id: str) -> Optional[AuditReport]:


        if report_id in self._in_memory_store:
            return self._in_memory_store[report_id]

        if not self._pool:
            return None

        try:
            async with self._pool.acquire() as conn:

                report_row = await conn.fetchrow(
                    "SELECT * FROM reports WHERE id = $1",
                    report_id
                )

                if not report_row:
                    return None


                issue_rows = await conn.fetch(
                    "SELECT * FROM issues WHERE report_id = $1 ORDER BY severity, confidence_score",
                    report_id
                )


                tree_row = await conn.fetchrow(
                    "SELECT tree_data FROM accessibility_trees WHERE report_id = $1",
                    report_id
                )


                return await self._reconstruct_report(report_row, issue_rows, tree_row)

        except Exception as e:
            self._logger.error(f"Failed to retrieve report {report_id}: {e}")
            return None

    async def _reconstruct_report(self, report_row, issue_rows, tree_row) -> AuditReport:



        request_data = json.loads(report_row['request'])
        request = AuditRequest(**request_data)


        summary_data = json.loads(report_row['summary'])
        summary = AuditSummary(**summary_data)


        issues = []
        for row in issue_rows:

            wcag_criteria = json.loads(row['wcag_criteria']) if row['wcag_criteria'] else []
            location = json.loads(row['location']) if row['location'] else None
            remediation = json.loads(row['remediation']) if row['remediation'] else None
            evidence = json.loads(row['evidence']) if row['evidence'] else None


            issue = UnifiedIssue(
                id=row['id'],
                title=row['title'],
                description=row['description'],
                issue_type=row['issue_type'],
                severity=row['severity'],
                confidence=row['confidence'],
                confidence_score=row['confidence_score'],
                source=row['source'],
                wcag_criteria=wcag_criteria,
                location=location,
                remediation=remediation,
                evidence=evidence,
                engine_name=row['engine_name'],
                tags=row['tags']
            )
            issues.append(issue)


        accessibility_tree = json.loads(tree_row['tree_data']) if tree_row else None


        metadata = json.loads(report_row['metadata']) if report_row['metadata'] else {}

        return AuditReport(
            id=report_row['id'],
            request=request,
            timestamp=report_row['timestamp'],
            summary=summary,
            issues=issues,
            accessibility_tree=accessibility_tree,
            metadata=metadata
        )

    async def list_reports(
        self,
        limit: int = 100,
        offset: int = 0,
        url: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:

        if not self._pool:

            reports = list(self._in_memory_store.values())
            reports.sort(key=lambda x: x.timestamp, reverse=True)
            return [
                {
                    "id": r.id,
                    "url": r.request.url,
                    "timestamp": r.timestamp,
                    "score": r.summary.score,
                    "total_issues": r.summary.total_issues,
                    "critical_count": r.summary.by_severity.get("critical", 0),
                    "serious_count": r.summary.by_severity.get("serious", 0),
                    "moderate_count": r.summary.by_severity.get("moderate", 0),
                    "minor_count": r.summary.by_severity.get("minor", 0),
                    "avg_confidence": r.summary.confidence_avg
                }
                for r in reports[offset:offset+limit]
            ]

        try:
            async with self._pool.acquire() as conn:

                query = "SELECT * FROM report_summaries WHERE 1=1"
                params = []
                param_count = 1

                if url:
                    query += f" AND url = ${param_count}"
                    params.append(url)
                    param_count += 1

                if from_date:
                    query += f" AND timestamp >= ${param_count}"
                    params.append(from_date)
                    param_count += 1

                if to_date:
                    query += f" AND timestamp <= ${param_count}"
                    params.append(to_date)
                    param_count += 1

                if min_score is not None:
                    query += f" AND score >= ${param_count}"
                    params.append(min_score)
                    param_count += 1

                query += f" ORDER BY timestamp DESC LIMIT ${param_count} OFFSET ${param_count + 1}"
                params.extend([limit, offset])

                rows = await conn.fetch(query, *params)

                return [dict(row) for row in rows]

        except Exception as e:
            self._logger.error(f"Failed to list reports: {e}")
            return []

    async def delete_report(self, report_id: str) -> bool:


        if report_id in self._in_memory_store:
            del self._in_memory_store[report_id]

        if not self._pool:
            return True

        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM reports WHERE id = $1",
                    report_id
                )
                return result == "DELETE 1"

        except Exception as e:
            self._logger.error(f"Failed to delete report {report_id}: {e}")
            return False

    async def get_report_stats(self) -> Dict[str, Any]:

        if not self._pool:

            reports = list(self._in_memory_store.values())
            if not reports:
                return {
                    "total_reports": 0,
                    "avg_score": 0,
                    "total_issues": 0,
                    "unique_urls": 0
                }

            return {
                "total_reports": len(reports),
                "avg_score": sum(r.summary.score for r in reports) / len(reports),
                "total_issues": sum(r.summary.total_issues for r in reports),
                "unique_urls": len(set(r.request.url for r in reports))
            }

        try:
            async with self._pool.acquire() as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_reports,
                        AVG(score) as avg_score,
                        SUM((summary->>'total_issues')::int) as total_issues,
                        COUNT(DISTINCT url) as unique_urls
                    FROM reports
                """)

                return dict(stats)

        except Exception as e:
            self._logger.error(f"Failed to get report stats: {e}")
            return {
                "total_reports": 0,
                "avg_score": 0,
                "total_issues": 0,
                "unique_urls": 0
            }

    async def get_url_history(self, url: str, limit: int = 10) -> List[Dict[str, Any]]:

        return await self.list_reports(
            url=url,
            limit=limit,
            offset=0
        )

    async def cleanup_old_reports(self, days: int = 30) -> int:

        if not self._pool:

            cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
            to_delete = [
                rid for rid, report in self._in_memory_store.items()
                if report.timestamp.timestamp() < cutoff
            ]
            for rid in to_delete:
                del self._in_memory_store[rid]
            return len(to_delete)

        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM reports 
                    WHERE timestamp < NOW() - INTERVAL '1 day' * $1
                """, days)


                count = int(result.split()[1]) if result.startswith("DELETE") else 0
                self._logger.info(f"Cleaned up {count} reports older than {days} days")
                return count

        except Exception as e:
            self._logger.error(f"Failed to cleanup old reports: {e}")
            return 0

    async def close(self):

        if self._pool:
            await self._pool.close()
            self._logger.info("Database connection pool closed")


report_storage = ReportStorage()