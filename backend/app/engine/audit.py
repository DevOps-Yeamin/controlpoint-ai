import hashlib
import json
import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.models.entities import AuditLog
from backend.app.schemas.schemas import AuditChainVerifyResponse

GENESIS_HASH = "0" * 64

class AuditLogger:
    @staticmethod
    def _format_timestamp(ts: datetime.datetime) -> str:
        """Format timestamp consistently for deterministic hashing."""
        if ts.tzinfo is not None:
            ts = ts.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return ts.strftime("%Y-%m-%dT%H:%M:%S")

    @staticmethod
    def _compute_hash(
        sequence_number: int,
        timestamp_str: str,
        agent_id: str,
        decision: str,
        prev_entry_hash: str,
        req_hash: str,
        res_hash: str
    ) -> str:
        """Compute SHA-256 for audit block entry."""
        digest_input = f"{sequence_number}|{timestamp_str}|{agent_id}|{decision}|{prev_entry_hash}|{req_hash}|{res_hash}"
        return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()

    @staticmethod
    def log_event(
        db: Session,
        agent_id: str,
        agent_role: str,
        tool_name: str,
        operation: str,
        requested_fields: List[str],
        decision: str,
        reason: str,
        redacted_fields: List[str],
        request_payload: Any = None,
        response_payload: Any = None
    ) -> AuditLog:
        """Create a tamper-evident hash-chained audit log entry."""
        req_json = json.dumps(request_payload or {}, sort_keys=True, default=str)
        res_json = json.dumps(response_payload or {}, sort_keys=True, default=str)

        # Hash payloads (secrets or full data are not logged directly into plaintext hash block)
        req_hash = hashlib.sha256(req_json.encode("utf-8")).hexdigest()
        res_hash = hashlib.sha256(res_json.encode("utf-8")).hexdigest()

        # Get latest entry to chain hashes
        latest_entry = db.query(AuditLog).order_by(AuditLog.sequence_number.desc()).first()

        if latest_entry:
            seq = latest_entry.sequence_number + 1
            prev_hash = latest_entry.entry_hash
        else:
            seq = 1
            prev_hash = GENESIS_HASH

        now = datetime.datetime.now(datetime.timezone.utc)
        timestamp_str = AuditLogger._format_timestamp(now)

        entry_hash = AuditLogger._compute_hash(
            sequence_number=seq,
            timestamp_str=timestamp_str,
            agent_id=agent_id,
            decision=decision,
            prev_entry_hash=prev_hash,
            req_hash=req_hash,
            res_hash=res_hash
        )

        audit_record = AuditLog(
            sequence_number=seq,
            timestamp=now,
            agent_id=agent_id,
            agent_role=agent_role,
            tool_name=tool_name,
            operation=operation,
            requested_fields=json.dumps(requested_fields or []),
            decision=decision,
            reason=reason,
            redacted_fields=json.dumps(redacted_fields or []),
            request_payload_hash=req_hash,
            response_payload_hash=res_hash,
            prev_entry_hash=prev_hash,
            entry_hash=entry_hash
        )

        db.add(audit_record)
        db.commit()
        db.refresh(audit_record)
        return audit_record

    @staticmethod
    def verify_chain(db: Session) -> AuditChainVerifyResponse:
        """
        Verify the cryptographic hash-chain integrity of all audit records.
        Detects tampering, deletion, or modification of audit history.
        """
        logs = db.query(AuditLog).order_by(AuditLog.sequence_number.asc()).all()
        total = len(logs)
        if total == 0:
            return AuditChainVerifyResponse(
                is_valid=True,
                total_records=0,
                verified_records=0
            )

        expected_prev_hash = GENESIS_HASH
        expected_seq = 1

        for log in logs:
            if log.sequence_number != expected_seq:
                return AuditChainVerifyResponse(
                    is_valid=False,
                    total_records=total,
                    verified_records=expected_seq - 1,
                    broken_sequence=log.sequence_number,
                    error_message=f"Sequence gap detected: expected {expected_seq}, found {log.sequence_number}"
                )

            if log.prev_entry_hash != expected_prev_hash:
                return AuditChainVerifyResponse(
                    is_valid=False,
                    total_records=total,
                    verified_records=expected_seq - 1,
                    broken_sequence=log.sequence_number,
                    error_message=f"Hash-chain broken at sequence {log.sequence_number}: prev_entry_hash does not match previous entry's hash"
                )

            # Recompute entry hash with normalized timestamp string
            timestamp_str = AuditLogger._format_timestamp(log.timestamp)
            recomputed = AuditLogger._compute_hash(
                sequence_number=log.sequence_number,
                timestamp_str=timestamp_str,
                agent_id=log.agent_id,
                decision=log.decision,
                prev_entry_hash=log.prev_entry_hash,
                req_hash=log.request_payload_hash,
                res_hash=log.response_payload_hash
            )

            if recomputed != log.entry_hash:
                return AuditChainVerifyResponse(
                    is_valid=False,
                    total_records=total,
                    verified_records=expected_seq - 1,
                    broken_sequence=log.sequence_number,
                    error_message=f"Tampering detected at sequence {log.sequence_number}: stored entry_hash does not match recomputed SHA-256 digest"
                )

            expected_prev_hash = log.entry_hash
            expected_seq += 1

        return AuditChainVerifyResponse(
            is_valid=True,
            total_records=total,
            verified_records=total
        )
