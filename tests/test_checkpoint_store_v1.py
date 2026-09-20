import gzip, hashlib, json
import pytest
from pattern_breakout.checkpoint_store_v1 import publish_checkpoint,load_current_checkpoint

class Body:
 def __init__(self,b): self.b=b
 def read(self): return self.b
class S3:
 def __init__(self): self.x={}; self.kw={}
 def put_object(self,**k): self.x[(k["Bucket"],k["Key"])]=k["Body"]; self.kw[(k["Bucket"],k["Key"])]=k
 def get_object(self,**k): return {"Body":Body(self.x[(k["Bucket"],k["Key"])])}
 def list_objects_v2(self,**k):
  pref=k["Prefix"]; items=[{"Key":key} for (bucket,key) in self.x if bucket==k["Bucket"] and key.startswith(pref)]
  return {"Contents":items,"IsTruncated":False}
 def delete_objects(self,**k):
  for o in k["Delete"]["Objects"]: self.x.pop((k["Bucket"],o["Key"]),None)
  return {}

def test_round_trip_and_content_addressed_idempotency():
 s=S3(); raw=b'{"x":1}\n'; h=hashlib.sha256(raw).hexdigest(); m={"source_hash":"sha256:"+h}
 p1=publish_checkpoint(s,"b",stage="candidates",as_of_date="2026-09-20",metadata=m,jsonl=raw)
 p2=publish_checkpoint(s,"b",stage="candidates",as_of_date="2026-09-20",metadata=m,jsonl=raw)
 assert p1["jsonl_key"]==p2["jsonl_key"]
 p,m2,r=load_current_checkpoint(s,"b",stage="candidates")
 assert r==raw and m2==m

def test_morphology_gzip_preserves_logical_identity_and_readback():
 s=S3(); raw=(b'{"x":1}\n'*1000); h=hashlib.sha256(raw).hexdigest(); m={"source_hash":"sha256:"+h}
 p=publish_checkpoint(s,"b",stage="morphology",as_of_date="2026-09-20",metadata=m,jsonl=raw)
 assert p["jsonl_key"].endswith(".jsonl.gz") and p["source_hash"]=="sha256:"+h
 stored=s.x[("b",p["jsonl_key"])]
 assert gzip.decompress(stored)==raw and len(stored)<len(raw)
 assert s.kw[("b",p["jsonl_key"])]["ContentEncoding"]=="gzip"
 _,meta,out=load_current_checkpoint(s,"b",stage="morphology")
 assert out==raw and meta["storage"]["logical_sha256"]==h
 assert meta["storage"]["stored_sha256"]==hashlib.sha256(stored).hexdigest()

def test_morphology_stored_corruption_fails_closed():
 s=S3(); raw=b'{"x":1}\n'; h=hashlib.sha256(raw).hexdigest()
 p=publish_checkpoint(s,"b",stage="morphology",as_of_date="2026-09-20",metadata={"source_hash":"sha256:"+h},jsonl=raw)
 s.x[("b",p["jsonl_key"])]=s.x[("b",p["jsonl_key"])]+b"x"
 with pytest.raises(ValueError): load_current_checkpoint(s,"b",stage="morphology")

def test_rejects_hash_mismatch():
 with pytest.raises(ValueError):
  publish_checkpoint(S3(),"b",stage="morphology",as_of_date="2026-09-20",metadata={"source_hash":"sha256:bad"},jsonl=b"x")

def test_load_fails_closed_on_corruption():
 s=S3(); raw=b"x"; h=hashlib.sha256(raw).hexdigest()
 publish_checkpoint(s,"b",stage="t1-execution",as_of_date="2026-09-20",metadata={"source_hash":"sha256:"+h},jsonl=raw)
 key="pattern-breakout/production/t1-execution/runs/2026-09-20/"+h+".jsonl"; s.x[("b",key)]=b"corrupt"
 with pytest.raises(ValueError): load_current_checkpoint(s,"b",stage="t1-execution")

def test_morphology_retention_keeps_current_and_previous_dates():
 s=S3()
 for d,x in [("2026-09-17",1),("2026-09-18",2),("2026-09-19",3)]:
  raw=(json.dumps({"x":x})+"\n").encode(); h=hashlib.sha256(raw).hexdigest()
  p=publish_checkpoint(s,"b",stage="morphology",as_of_date=d,metadata={"source_hash":"sha256:"+h},jsonl=raw)
 assert p["retention"]["keep_dates"]==["2026-09-19","2026-09-18"]
 keys=[k for (b,k) in s.x if "/morphology/runs/" in k]
 assert not any("/2026-09-17/" in k for k in keys)
 assert any("/2026-09-18/" in k for k in keys) and any("/2026-09-19/" in k for k in keys)

def test_same_day_same_logical_snapshot_does_not_multiply_payload_keys():
 s=S3(); raw=b'{"x":1}\n'; h=hashlib.sha256(raw).hexdigest(); m={"source_hash":"sha256:"+h}
 publish_checkpoint(s,"b",stage="morphology",as_of_date="2026-09-20",metadata=m,jsonl=raw)
 publish_checkpoint(s,"b",stage="morphology",as_of_date="2026-09-20",metadata=m,jsonl=raw)
 payload=[k for (b,k) in s.x if k.endswith(".jsonl.gz")]
 assert len(payload)==1

def test_retention_refuses_policy_that_could_drop_current():
 from pattern_breakout.checkpoint_store_v1 import enforce_morphology_retention
 s=S3()
 with pytest.raises(ValueError): enforce_morphology_retention(s,"b",{"as_of_date":"2026-09-20"},keep_dates=1)
