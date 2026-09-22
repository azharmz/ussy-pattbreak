"""Atomically promote a fully verified v2 cohort for dashboard serving."""
import argparse,json,os
from datetime import datetime,timezone
import boto3
STAGES={"events":"breakout-events-v2","execution":"security-execution-v2","lifecycle":"lifecycle-v2"}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--signal-date",required=True);a=ap.parse_args()
 s=boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto");bucket=os.environ["R2_BUCKET_NAME"];p={}
 for alias,stage in STAGES.items():
  key=f"pattern-breakout/production/{stage}/by-signal-date/{a.signal_date}.json";o=s.get_object(Bucket=bucket,Key=key);x=json.loads(o["Body"].read());assert x["signal_date"]==a.signal_date and x["stage"]==stage;p[alias]=x
 manifest={"schema_version":"dashboard-v2-current-v1","signal_date":a.signal_date,"promoted_at":datetime.now(timezone.utc).isoformat(),"stages":p}
 body=(json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n").encode()
 s.put_object(Bucket=bucket,Key="pattern-breakout/production/dashboard-v2/current.json",Body=body,ContentType="application/json")
 print(json.dumps(manifest,sort_keys=True))
if __name__=="__main__":main()
