from pattern_breakout.lifecycle_store_v1 import publish_lifecycle_checkpoint, load_current_lifecycle
import json

class S3:
    def __init__(self): self.x={}
    def put_object(self,**k): self.x[k["Key"]]=k["Body"]
    def get_object(self,**k):
        class B:
            def __init__(self,b): self.b=b
            def read(self): return self.b
        return {"Body":B(self.x[k["Key"]])}

def test_round_trip():
    import hashlib
    s=S3(); raw=b'{"state":"OPEN"}\n'; h=hashlib.sha256(raw).hexdigest()
    m={"source_hash":"sha256:"+h,"execution_ready":{"as_of_date":"2026-09-18"}}
    p=publish_lifecycle_checkpoint(s,"b",metadata=m,jsonl=raw)
    p2,m2,r=load_current_lifecycle(s,"b")
    assert p2["source_hash"]==p["source_hash"] and m2==m and r==raw

def test_idempotent_content_key():
    import hashlib
    s=S3(); raw=b"x\n"; h=hashlib.sha256(raw).hexdigest(); m={"source_hash":"sha256:"+h,"execution_ready":{"as_of_date":"2026-09-18"}}
    a=publish_lifecycle_checkpoint(s,"b",metadata=m,jsonl=raw); b=publish_lifecycle_checkpoint(s,"b",metadata=m,jsonl=raw)
    assert a["jsonl_key"]==b["jsonl_key"]
