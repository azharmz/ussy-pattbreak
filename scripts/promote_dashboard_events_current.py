"""Promote the newest verified breakout-event checkpoint for dashboard serving.

Event publication is independent of T+1 execution/lifecycle.  This pointer is
therefore deliberately separate from dashboard-v2/current.json, which remains
the atomic completed execution/lifecycle cohort.
"""
import argparse,json,os
from datetime import datetime,timezone
import boto3
from botocore.exceptions import ClientError

EVENT_PREFIX="pattern-breakout/production/breakout-events-v2"
CURRENT="pattern-breakout/production/dashboard-events-v2/current.json"

def client():
 return boto3.client("s3",endpoint_url=os.environ["R2_ENDPOINT"],aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],region_name="auto")

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--signal-date",required=True);a=ap.parse_args();s=client();bucket=os.environ["R2_BUCKET_NAME"]
 key=f"{EVENT_PREFIX}/by-signal-date/{a.signal_date}.json"
 event=json.loads(s.get_object(Bucket=bucket,Key=key)["Body"].read())
 assert event["stage"]=="breakout-events-v2" and event["signal_date"]==a.signal_date
 try:
  current=json.loads(s.get_object(Bucket=bucket,Key=CURRENT)["Body"].read())
  if current["signal_date"]>a.signal_date:
   print(json.dumps({"status":"ALREADY_NEWER","current_signal_date":current["signal_date"]},sort_keys=True));return
 except ClientError as exc:
  if exc.response.get("Error",{}).get("Code") not in {"NoSuchKey","404","NotFound"}:raise
 pointer={**event,"schema_version":"dashboard-events-v2-current-v1","promoted_at":datetime.now(timezone.utc).isoformat()}
 s.put_object(Bucket=bucket,Key=CURRENT,Body=(json.dumps(pointer,sort_keys=True,separators=(",",":"))+"\n").encode(),ContentType="application/json")
 print(json.dumps({"status":"READY",**pointer},sort_keys=True))

if __name__=="__main__":main()
