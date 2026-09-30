"""MCP Server for Enterprise Knowledge Graph Provenance Tracer."""
import sys
import json
import time
from client import KnowledgeGraphProvenanceTracer

tracer = KnowledgeGraphProvenanceTracer()

def handle_call_tool(params):
    name = params.get("name")
    args = params.get("arguments", {})
    if name != "trace_knowledge_provenance":
        raise ValueError(f"Unknown tool: {name}")

    action = args.get("action", "trace_claim_provenance")
    if action == "index_knowledge_chunk":
        return tracer.index_knowledge_chunk(
            doc_id=args.get("doc_id", "doc_1"),
            chunk_id=args.get("chunk_id", f"c_{time.time()}"),
            content=args.get("content", ""),
            classification=args.get("classification", "INTERNAL"),
            author=args.get("author", "system")
        )
    elif action == "trace_claim_provenance":
        return tracer.trace_claim_provenance(
            claim_text=args.get("claim_text", "")
        )
    elif action == "verify_lineage_clearance":
        claim_res = tracer.trace_claim_provenance(args.get("claim_text", ""))
        return tracer.verify_lineage_clearance(claim_res, requester_role=args.get("requester_role", "EMPLOYEE"))
    elif action == "get_provenance_stats":
        return tracer.get_provenance_stats()
    else:
        raise ValueError(f"Invalid action: {action}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running self-test...")
        tracer.index_knowledge_chunk("tencent_doc_101", "chunk_1", "Project Phoenix delivered 42% revenue increase in Q3.", "CONFIDENTIAL", "Product VP")
        trace = tracer.trace_claim_provenance("Project Phoenix revenue rose 42% in Q3.")
        assert trace["status"] in ("VERIFIED", "PARTIALLY_SUPPORTED")
        assert len(trace["supporting_sources"]) >= 1
        clearance = tracer.verify_lineage_clearance(trace, "INTERN")
        assert clearance["clearance_granted"] is False
        print("Self-test PASSED!")
        sys.exit(0)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            msg_id = req.get("id")
            method = req.get("method")
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {"name": "KnowledgeGraphProvenanceTracer", "version": "1.0.0"},
                        "capabilities": {"tools": {}}
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [{
                            "name": "trace_knowledge_provenance",
                            "description": "Trace enterprise claim attribution to cryptographic document sources, verify clearance boundaries, and validate fact provenance.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string", "enum": ["index_knowledge_chunk", "trace_claim_provenance", "verify_lineage_clearance", "get_provenance_stats"]},
                                    "doc_id": {"type": "string"},
                                    "chunk_id": {"type": "string"},
                                    "content": {"type": "string"},
                                    "classification": {"type": "string"},
                                    "author": {"type": "string"},
                                    "claim_text": {"type": "string"},
                                    "requester_role": {"type": "string"}
                                },
                                "required": ["action"]
                            }
                        }]
                    }
                }
            elif method == "tools/call":
                res = handle_call_tool(req.get("params", {}))
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
                }
            else:
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            print(json.dumps(resp), flush=True)
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(e)}}
            print(json.dumps(err_resp), flush=True)

if __name__ == "__main__":
    main()
