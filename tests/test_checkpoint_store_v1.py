import hashlib, json
import pytest
from pattern_breakout.checkpoint_store_v1 import publish_checkpoint,load_current_checkpoint

class Body:
 def __init__(self,b): self.b=b
 def read(self): return self.b
class S3:
 def __init__(self): self.x={}
 def put_object(self,**k): self.x[(k["Bucket"],k["Key"])]=k["Body"]
 def get_object(self,**k): return {"Body":Body(self.x[(k["Bucket"],k["Key"])])}

def test_round_trip_and_content_addressed_idempotency():
 s=S3(); raw=b'{"x":1}\n'; h=hashlib.sha256(raw).hexdigest(); m={"source_hash":"sha256:"+h}
 p1=publish_checkpoint(s,"b",stage="candidates",as_of_date="2026-09-20",metadata=m,jsonl=raw)
 p2=publish_checkpoint(s,"b",stage="candidates",as_of_date="2026-09-20",metadata=m,jsonl=raw)
 assert p1["jsonl_key"]==p2["jsonl_key"]
 p,m2,r=load_current_checkpoint(s,"b",stage="candidates")
 assert r==raw and m2==m

def test_rejects_hash_mismatch():
 with pytest.raises(ValueError):
  publish_checkpoint(S3(),"b",stage="morphology",as_of_date="2026-09-20",metadata={"source_hash":"sha256:bad"},jsonl=b"x")

def test_load_fails_closed_on_corruption():
 s=S3(); raw=b"x"; h=hashlib.sha256(raw).hexdigest()
 publish_checkpoint(s,"b",stage="t1-execution",as_of_date="2026-09-20",metadata={"source_hash":"sha256:"+h},jsonl=raw)
 key="pattern-breakout/production/t1-execution/runs/2026-09-20/"+h+".jsonl"; s.x[("b",key)]=b"corrupt"
 with pytest.raises(ValueError): load_current_checkpoint(s,"b",stage="t1-execution")
