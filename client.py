"""
Enterprise Knowledge Graph Provenance & Anti-Hallucination Tracer (Zero External Dependencies)
Provides cryptographic chunk hashing, reverse claim attribution, and RBAC boundary validation.
"""
import hashlib
import time
import re
import json
from typing import Dict, Any, List, Optional

CLEARANCE_LEVELS = {
    "PUBLIC": 0,
    "INTERNAL": 1,
    "CONFIDENTIAL": 2,
    "RESTRICTED": 3
}

class KnowledgeGraphProvenanceTracer:
    def __init__(self):
        self.chunks: Dict[str, Dict[str, Any]] = {}
        self.inverted_index: Dict[str, List[str]] = {}

    def _tokenize(self, text: str) -> List[str]:
        """Simple standard-library alphanumeric tokenizer."""
        return re.findall(r"\b[a-zA-Z0-9_]{3,}\b", text.lower())

    def index_knowledge_chunk(
        self,
        doc_id: str,
        chunk_id: str,
        content: str,
        classification: str = "INTERNAL",
        author: str = "system",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Cryptographically fingerprints and indexes an enterprise knowledge chunk."""
        sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        tokens = self._tokenize(content)
        now = time.time()

        chunk_record = {
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "content": content,
            "sha256": sha,
            "classification": classification.upper(),
            "author": author,
            "token_count": len(tokens),
            "indexed_at": now,
            "metadata": metadata or {}
        }

        self.chunks[chunk_id] = chunk_record

        # Update inverted index
        for t in set(tokens):
            self.inverted_index.setdefault(t, []).append(chunk_id)

        return {
            "indexed": True,
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "sha256": sha,
            "classification": classification.upper()
        }

    def trace_claim_provenance(
        self,
        claim_text: str,
        top_k: int = 3,
        min_confidence: float = 0.35
    ) -> Dict[str, Any]:
        """
        Reverse-verifies an agent claim against the cryptographically indexed knowledge base.
        Calculates Jaccard & token-overlap attribution confidence scores.
        """
        claim_tokens = set(self._tokenize(claim_text))
        if not claim_tokens:
            return {"claim": claim_text, "status": "EMPTY_CLAIM", "sources": []}

        candidate_scores: Dict[str, float] = {}
        for token in claim_tokens:
            for cid in self.inverted_index.get(token, []):
                candidate_scores[cid] = candidate_scores.get(cid, 0.0) + 1.0

        if not candidate_scores:
            return {
                "claim": claim_text,
                "status": "UNVERIFIED_HALLUCINATION_RISK",
                "attribution_score": 0.0,
                "sources": []
            }

        scored_sources = []
        for cid, hit_count in candidate_scores.items():
            chunk = self.chunks[cid]
            chunk_tokens = set(self._tokenize(chunk["content"]))
            union_len = len(claim_tokens.union(chunk_tokens))
            jaccard = (hit_count / union_len) if union_len > 0 else 0.0

            # Direct containment ratio
            containment = hit_count / len(claim_tokens)
            composite_confidence = 0.65 * containment + 0.35 * jaccard

            scored_sources.append({
                "chunk_id": cid,
                "doc_id": chunk["doc_id"],
                "classification": chunk["classification"],
                "author": chunk["author"],
                "sha256": chunk["sha256"],
                "confidence_score": round(composite_confidence, 4),
                "matched_tokens": int(hit_count),
                "excerpt": chunk["content"][:160] + ("..." if len(chunk["content"]) > 160 else "")
            })

        scored_sources.sort(key=lambda x: x["confidence_score"], reverse=True)
        top_matches = scored_sources[:top_k]

        best_score = top_matches[0]["confidence_score"] if top_matches else 0.0
        status = "VERIFIED" if best_score >= 0.70 else ("PARTIALLY_SUPPORTED" if best_score >= min_confidence else "UNVERIFIED")

        # Generate cryptographic provenance token
        prov_payload = f"{claim_text}:{best_score}:{top_matches[0]['sha256'] if top_matches else 'none'}"
        prov_token = "GP-PROV-" + hashlib.sha256(prov_payload.encode("utf-8")).hexdigest()[:24]

        return {
            "claim": claim_text,
            "status": status,
            "attribution_score": best_score,
            "provenance_token": prov_token,
            "supporting_sources": top_matches
        }

    def verify_lineage_clearance(
        self,
        claim_result: Dict[str, Any],
        requester_role: str = "EMPLOYEE"
    ) -> Dict[str, Any]:
        """
        Audits whether the requester has legal access to view the supporting provenance sources.
        Redacts confidential or restricted sources if requester lacks clearance.
        """
        role_map = {
            "INTERN": 0,      # PUBLIC only
            "CONTRACTOR": 0,  # PUBLIC only
            "EMPLOYEE": 1,    # PUBLIC + INTERNAL
            "MANAGER": 2,     # + CONFIDENTIAL
            "EXECUTIVE": 3    # ALL including RESTRICTED
        }
        user_clearance = role_map.get(requester_role.upper(), 1)
        sources = claim_result.get("supporting_sources", [])

        redacted_sources = []
        violations = 0

        for src in sources:
            src_clearance_level = CLEARANCE_LEVELS.get(src["classification"], 1)
            if user_clearance >= src_clearance_level:
                redacted_sources.append(src)
            else:
                violations += 1
                redacted_sources.append({
                    "chunk_id": src["chunk_id"],
                    "doc_id": src["doc_id"],
                    "classification": src["classification"],
                    "access": "DENIED_REDACTED",
                    "reason": f"Clearance level '{src['classification']}' exceeds role '{requester_role}'"
                })

        return {
            "requester_role": requester_role,
            "clearance_granted": violations == 0,
            "boundary_violations": violations,
            "sanitized_sources": redacted_sources
        }

    def get_provenance_stats(self) -> Dict[str, Any]:
        return {
            "total_chunks_indexed": len(self.chunks),
            "total_unique_terms": len(self.inverted_index),
            "classifications": {
                lvl: sum(1 for c in self.chunks.values() if c["classification"] == lvl)
                for lvl in CLEARANCE_LEVELS
            }
        }
