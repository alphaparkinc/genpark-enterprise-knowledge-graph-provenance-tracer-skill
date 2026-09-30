"""Example usage for KnowledgeGraphProvenanceTracer."""
import json
from client import KnowledgeGraphProvenanceTracer

def main():
    print("=== Knowledge Graph Provenance & Anti-Hallucination Tracer Demo ===")
    tracer = KnowledgeGraphProvenanceTracer()

    # 1. Ingest enterprise sources (Tencent Docs / Meeting transcripts)
    print("\n--- 1. Indexing Enterprise Knowledge Sources ---")
    tracer.index_knowledge_chunk(
        doc_id="meeting_sync_2026_09",
        chunk_id="chunk_strat_01",
        content="Enterprise Work Agent WorkBuddy reduced reporting overhead by 68% across all financial divisions.",
        classification="INTERNAL",
        author="Strategy Director"
    )
    tracer.index_knowledge_chunk(
        doc_id="m_and_a_audit_2026",
        chunk_id="chunk_ma_02",
        content="Target acquisition escrow set to 45M USD with a 12-month earn-out clause.",
        classification="CONFIDENTIAL",
        author="Legal VP"
    )
    print("Indexed 2 document chunks with cryptographic SHA-256 signatures.")

    # 2. Reverse Claim Provenance Attribution
    print("\n--- 2. Verifying Agent Claim Attribution ---")
    claim = "WorkBuddy reduced reporting overhead by 68% in financial divisions."
    trace = tracer.trace_claim_provenance(claim)
    print(f"Claim: '{claim}'")
    print(f"Status: {trace['status']} (Attribution Confidence: {trace['attribution_score']})")
    print(f"Provenance Token: {trace['provenance_token']}")
    print("Supporting Sources:")
    print(json.dumps(trace["supporting_sources"], indent=2))

    # 3. RBAC Boundary Clearance Verification
    print("\n--- 3. Verifying Clearance for Low-Privilege Role (INTERN) vs MANAGER ---")
    claim_ma = "Target acquisition escrow set to 45M USD."
    trace_ma = tracer.trace_claim_provenance(claim_ma)
    
    intern_check = tracer.verify_lineage_clearance(trace_ma, requester_role="INTERN")
    print(f"INTERN Access Allowed: {intern_check['clearance_granted']} (Violations: {intern_check['boundary_violations']})")

    mgr_check = tracer.verify_lineage_clearance(trace_ma, requester_role="MANAGER")
    print(f"MANAGER Access Allowed: {mgr_check['clearance_granted']} (Violations: {mgr_check['boundary_violations']})")

if __name__ == "__main__":
    main()
