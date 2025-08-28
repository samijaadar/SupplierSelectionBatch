import os
import boto3
import pandas as pd
import io

from supplierRankingSys import SupplierRankingSystem

s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION")
)

bucket_name = os.getenv("S3_BUCKET")

def list_folders(bucket):
    """List top-level folders in the bucket"""
    response = s3.list_objects_v2(Bucket=bucket, Delimiter="/")
    prefixes = response.get("CommonPrefixes", [])
    return [p["Prefix"] for p in prefixes]


def move_folder(bucket, source_prefix, target_prefix):
    """Move folder by copying objects then deleting original ones"""
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=source_prefix):
        for obj in page.get("Contents", []):
            source_key = obj["Key"]
            target_key = source_key.replace(source_prefix, target_prefix, 1)

            s3.copy_object(
                Bucket=bucket,
                CopySource={"Bucket": bucket, "Key": source_key},
                Key=target_key,
            )

            s3.delete_object(Bucket=bucket, Key=source_key)


def read_csv_from_s3(bucket, key, **kwargs):
    """Read CSV file from S3 into DataFrame"""
    obj = s3.get_object(Bucket=bucket, Key=key)
    return pd.read_csv(io.BytesIO(obj["Body"].read()), **kwargs)


def read_txt_from_s3(bucket, key):
    """Read TXT file from S3 into list of lines"""
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8").splitlines()


if __name__ == "__main__":
    folders = list_folders(bucket_name)

    for folder in folders:
        if folder.startswith("done/") or folder.startswith("ko/"):
            print(f"⏩ Skipping folder: {folder}")
            continue

        print(f"Processing folder: {folder}")
        try:
            criteria_configuration_file = folder + "criteria_configuration.csv"
            df = read_csv_from_s3(bucket_name, criteria_configuration_file, header=None)
            df = df.dropna(how="all")

            df = df[[0, 1, 2]]
            df.columns = ["Criterion", "Weight", "Beneficial"]

            df = df[df["Criterion"] != "Criterion"]

            df["Weight"] = pd.to_numeric(df["Weight"], errors="coerce")
            df["Beneficial"] = df["Beneficial"].astype(str).str.strip().map({"True": True, "False": False})

            beneficial = df[df["Beneficial"]]["Criterion"].tolist()
            non_beneficial = df[~df["Beneficial"]]["Criterion"].tolist()
            weights = dict(zip(df["Criterion"], df["Weight"]))

            company_info_file = folder + "company_info.txt"
            lines = read_txt_from_s3(bucket_name, company_info_file)
            lines = [line.strip() for line in lines if line.strip()]

            company_name = lines[1]
            contact_email = lines[2]

            data_file = folder + "data.csv"
            data = read_csv_from_s3(bucket_name, data_file)

            system = SupplierRankingSystem(beneficial, non_beneficial, weights)
            system.rank(data, company_name, contact_email)

            move_folder(bucket_name, folder, f"done/{folder}")

        except Exception as e:
            print(f"⚠️ Error on {folder}: {e}")
            move_folder(bucket_name, folder, f"ko/{folder}")
