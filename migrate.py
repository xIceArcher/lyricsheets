import argparse
import boto3
import time
from print import *

db = boto3.resource('dynamodb')
table = db.Table('Lyrics')

def get_song_json(name: str):
    try:
        resp = table.get_item(Key={'str_id': f'{name}'})
        return resp['Item']
    except Exception as e:
        print(f'Failed to get lyrics for {name}')
        return None

def main():
    parser = argparse.ArgumentParser(
        description='Migrates songs in DynamoDB to Google Sheets'
    )

    resp = table.scan(ExclusiveStartKey={'str_id': 'kodoku_teleport'})
    for item in resp['Items']:
        try:
            print(item['str_id'])
            print_song(spreadsheetId, item)
            time.sleep(10)
        except Exception as e:
            print(e)
            continue

    if 'LastEvaluatedKey' in resp and resp['LastEvaluatedKey'] != '':
        print(resp['LastEvaluatedKey'])


if __name__ == '__main__':
    main()
